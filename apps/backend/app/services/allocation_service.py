from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models import (
    Load, LoadStatus, LoadAllocation,
    Truck, Driver, DriverStatus, EventCategory,
)
from app.repositories import (
    LoadRepository, TruckRepository, DriverRepository, AllocationRepository,
)
from app.schemas.allocation import AllocationCreate, AllocationUpdate
from app.services.audit_service import AuditService
from app.services.load_service import LoadService


class AllocationService:
    """Service for assigning trucks and drivers to loads."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID | None = None,
        current_user_id: UUID | None = None,
        is_superadmin: bool = False,
        current_user_roles: list[str] | None = None,
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.is_superadmin = is_superadmin
        self.current_user_roles = current_user_roles or []

        self.load_repo = LoadRepository(db, tenant_id)
        self.truck_repo = TruckRepository(db, tenant_id)
        self.driver_repo = DriverRepository(db, tenant_id)
        self.alloc_repo = AllocationRepository(db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

        # Shared load service for status transitions
        self._load_svc = LoadService(
            db=db,
            tenant_id=tenant_id,
            current_user_id=current_user_id,
            is_superadmin=is_superadmin,
            current_user_roles=current_user_roles,
        )

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get_load(self, load_id: UUID) -> Load:
        load = self.load_repo.get_active_by_id(load_id)
        if not load:
            raise NotFoundException("Load not found")
        if not self.is_superadmin and load.tenant_id != self.tenant_id:
            raise ForbiddenException("Cannot access load from another tenant")
        return load

    def _get_truck(self, truck_id: UUID) -> Truck:
        truck = self.truck_repo.get_active_by_id(truck_id)
        if not truck:
            raise NotFoundException(f"Truck not found: {truck_id}")
        return truck

    def _get_driver(self, driver_id: UUID) -> Driver:
        driver = self.driver_repo.get_active_by_id(driver_id)
        if not driver:
            raise NotFoundException(f"Driver not found: {driver_id}")
        return driver

    def _effective_delivery_date(self, load: Load) -> date:
        """Return delivery date for overlap calculations; fallback = pickup + 1 day."""
        return load.expected_delivery_date or (load.pickup_date + timedelta(days=1))

    def _validate_truck(self, truck: Truck, load: Load) -> None:
        """Raise if truck cannot be allocated."""
        if not truck.is_operational:
            raise BadRequestException(
                f"Truck {truck.registration_no} is not operational "
                f"(status={truck.status}, available={truck.is_available})"
            )
        # Soft capacity validation
        if (
            truck.capacity_tons is not None
            and load.weight_kg is not None
            and float(load.weight_kg) > float(truck.capacity_tons) * 1000
        ):
            # Log but don't block (Phase 6 will hard-enforce)
            pass

    def _validate_driver(self, driver: Driver, load: Load) -> None:
        """Raise if driver cannot be allocated."""
        if not driver.is_allocatable:
            raise BadRequestException(
                f"Driver {driver.full_name} is not allocatable "
                f"(status={driver.status}, license_valid={driver.is_license_valid})"
            )
        # Driver must belong to the same tenant as the load
        if not self.is_superadmin and driver.tenant_id != load.tenant_id:
            raise ForbiddenException(
                "Driver must belong to the same tenant as the load"
            )

    def _check_conflicts(
        self,
        truck: Truck,
        driver: Driver,
        pickup_date: date,
        effective_delivery_date: date,
        exclude_load_id: UUID | None = None,
    ) -> None:
        """Raise ConflictException if truck or driver has an overlapping allocation."""
        if self.alloc_repo.check_truck_conflict(
            truck.id, pickup_date, effective_delivery_date, exclude_load_id
        ):
            raise ConflictException(
                f"Truck {truck.registration_no} already has an active allocation "
                f"overlapping {pickup_date} → {effective_delivery_date}"
            )
        if self.alloc_repo.check_driver_conflict(
            driver.id, pickup_date, effective_delivery_date, exclude_load_id
        ):
            raise ConflictException(
                f"Driver {driver.full_name} already has an active allocation "
                f"overlapping {pickup_date} → {effective_delivery_date}"
            )

    def _mark_truck_unavailable(self, truck: Truck) -> None:
        truck.is_available = False
        self.db.flush()

    def _mark_truck_available(self, truck: Truck) -> None:
        truck.is_available = True
        self.db.flush()

    def _mark_driver_on_trip(self, driver: Driver) -> None:
        driver.status = DriverStatus.ON_TRIP
        driver.is_available = False
        self.db.flush()

    def _mark_driver_available(self, driver: Driver) -> None:
        driver.status = DriverStatus.AVAILABLE
        driver.is_available = True
        self.db.flush()

    # ── Public API ─────────────────────────────────────────────────────────────

    def allocate(
        self,
        load_id: UUID,
        data: AllocationCreate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Load:
        """
        Assign truck + driver to a CONFIRMED load.
        Transitions load → ALLOCATED.
        Sets truck/driver as unavailable.
        """
        load = self._get_load(load_id)
        if load.status != LoadStatus.CONFIRMED:
            raise BadRequestException(
                f"Load must be in CONFIRMED status to allocate. Current: {load.status}"
            )

        truck = self._get_truck(data.truck_id)
        driver = self._get_driver(data.driver_id)
        eff_delivery = self._effective_delivery_date(load)

        # Check date-range conflicts FIRST (409 takes priority over 400)
        self._check_conflicts(truck, driver, load.pickup_date, eff_delivery)

        # Then validate operational/allocatable state
        self._validate_truck(truck, load)
        self._validate_driver(driver, load)

        # Create allocation record
        alloc = LoadAllocation(
            load_id=load.id,
            truck_id=truck.id,
            driver_id=driver.id,
            pickup_date=load.pickup_date,
            effective_delivery_date=eff_delivery,
            allocated_by=self.current_user_id,
            is_active=True,
            notes=data.notes,
        )
        self.db.add(alloc)
        self.db.flush()

        # Update load columns
        now = utc_now()
        load.allocated_truck_id = truck.id
        load.allocated_driver_id = driver.id
        load.allocated_at = now
        load.allocated_by = self.current_user_id

        # Mark resources as busy
        self._mark_truck_unavailable(truck)
        self._mark_driver_on_trip(driver)

        # Transition load status via LoadService (creates history entry)
        self._load_svc.transition_status(
            load_id=load_id,
            to_status=LoadStatus.ALLOCATED,
            remarks=f"Allocated truck {truck.registration_no} / driver {driver.full_name}",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.audit_service.log_event(
            event_type="LOAD_ALLOCATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Load",
            resource_id=load_id,
            new_value={
                "truck_id": str(truck.id),
                "driver_id": str(driver.id),
                "truck_reg": truck.registration_no,
                "driver_name": driver.full_name,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Note: transition_status already committed; commit here for alloc record
        self.db.commit()
        return self.load_repo.get_active_by_id(load_id)

    def reallocate(
        self,
        load_id: UUID,
        data: AllocationUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Load:
        """
        Swap truck and/or driver on an ALLOCATED load (e.g., breakdown).
        Old allocation is deactivated; new one created.
        Load stays in ALLOCATED status.
        """
        load = self._get_load(load_id)
        if load.status != LoadStatus.ALLOCATED:
            raise BadRequestException(
                f"Load must be in ALLOCATED status to reallocate. Current: {load.status}"
            )

        old_alloc = self.alloc_repo.get_active_by_load_id(load_id)
        new_truck = self._get_truck(data.truck_id)
        new_driver = self._get_driver(data.driver_id)
        eff_delivery = self._effective_delivery_date(load)

        truck_changing = old_alloc is None or old_alloc.truck_id != new_truck.id
        driver_changing = old_alloc is None or old_alloc.driver_id != new_driver.id

        # Only validate truck/driver that are actually changing
        if truck_changing:
            self._validate_truck(new_truck, load)
        if driver_changing:
            self._validate_driver(new_driver, load)

        # Exclude current load from conflict check (it already holds the slot)
        self._check_conflicts(
            new_truck, new_driver,
            load.pickup_date, eff_delivery,
            exclude_load_id=load_id
        )

        # Restore old truck/driver availability (if they are changing)
        if old_alloc:
            old_truck = self._get_truck(old_alloc.truck_id)
            old_driver = self._get_driver(old_alloc.driver_id)

            if old_alloc.truck_id != new_truck.id:
                self._mark_truck_available(old_truck)
            if old_alloc.driver_id != new_driver.id:
                self._mark_driver_available(old_driver)

            old_alloc.deactivate(
                deactivated_by_id=self.current_user_id,
                at=utc_now()
            )
            self.db.flush()

        # Create new allocation record
        new_alloc = LoadAllocation(
            load_id=load.id,
            truck_id=new_truck.id,
            driver_id=new_driver.id,
            pickup_date=load.pickup_date,
            effective_delivery_date=eff_delivery,
            allocated_by=self.current_user_id,
            is_active=True,
            notes=data.notes,
        )
        self.db.add(new_alloc)

        # Update load FK fields
        load.allocated_truck_id = new_truck.id
        load.allocated_driver_id = new_driver.id
        load.allocated_at = utc_now()
        load.allocated_by = self.current_user_id

        # Mark new resources busy
        self._mark_truck_unavailable(new_truck)
        self._mark_driver_on_trip(new_driver)

        self.audit_service.log_event(
            event_type="LOAD_REALLOCATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Load",
            resource_id=load_id,
            new_value={
                "new_truck_id": str(new_truck.id),
                "new_driver_id": str(new_driver.id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.load_repo.get_active_by_id(load_id)

    def deallocate(
        self,
        load_id: UUID,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Load:
        """
        Remove truck/driver assignment. Reverts load to CONFIRMED.
        Restores truck and driver availability.
        """
        load = self._get_load(load_id)
        if load.status != LoadStatus.ALLOCATED:
            raise BadRequestException(
                f"Load must be in ALLOCATED status to deallocate. Current: {load.status}"
            )

        alloc = self.alloc_repo.get_active_by_load_id(load_id)
        if alloc:
            old_truck = self._get_truck(alloc.truck_id)
            old_driver = self._get_driver(alloc.driver_id)

            alloc.deactivate(
                deactivated_by_id=self.current_user_id,
                at=utc_now()
            )
            self.db.flush()

            self._mark_truck_available(old_truck)
            self._mark_driver_available(old_driver)

        # Clear load allocation fields
        load.allocated_truck_id = None
        load.allocated_driver_id = None
        load.allocated_at = None
        load.allocated_by = None
        self.db.flush()

        # Revert load status to CONFIRMED via history
        self._load_svc.transition_status(
            load_id=load_id,
            to_status=LoadStatus.CONFIRMED,
            remarks=reason or "Deallocated",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.audit_service.log_event(
            event_type="LOAD_DEALLOCATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Load",
            resource_id=load_id,
            new_value={"reason": reason},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.load_repo.get_active_by_id(load_id)

    def get_allocation(self, load_id: UUID) -> LoadAllocation | None:
        """Return current active allocation for a load."""
        self._get_load(load_id)  # access check
        return self.alloc_repo.get_active_by_load_id(load_id)

    def get_available_trucks(
        self, pickup_date: date, effective_delivery_date: date
    ) -> list[Truck]:
        return self.alloc_repo.get_available_trucks(pickup_date, effective_delivery_date)

    def get_available_drivers(
        self, pickup_date: date, effective_delivery_date: date
    ) -> list[Driver]:
        return self.alloc_repo.get_available_drivers(pickup_date, effective_delivery_date)
