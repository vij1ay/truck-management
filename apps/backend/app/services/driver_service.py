from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    ForbiddenException,
)
from app.models import Driver, DriverStatus, EventCategory
from app.models.truck import Truck
from app.repositories import DriverRepository
from app.schemas.driver import DriverCreate, DriverUpdate, DriverAvailabilityUpdate, DriverLocationUpdate
from app.services.audit_service import AuditService


class DriverService:
    """Service for driver management operations."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID | None = None,
        current_user_id: UUID | None = None,
        is_superadmin: bool = False,
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.is_superadmin = is_superadmin
        self.driver_repo = DriverRepository(db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    def get_driver(self, driver_id: UUID) -> Driver:
        """Get a driver by ID."""
        driver = self.driver_repo.get_active_by_id(driver_id)
        if not driver:
            raise NotFoundException("Driver not found")
        if not self.is_superadmin and driver.tenant_id != self.tenant_id:
            raise ForbiddenException("Cannot access driver from another tenant")
        return driver

    def get_driver_by_user_id(self, user_id: UUID) -> Driver:
        """Get the Driver record linked to a login (User.id), for GET /drivers/me.

        Not tenant-scoped on lookup — `user_id` comes from the caller's own JWT,
        so there's nothing to leak across tenants (mirrors Client.get_by_user_id
        used by the customer portal's /portal/me)."""
        driver = self.driver_repo.get_by_user_id(user_id)
        if not driver:
            raise NotFoundException("No driver profile linked to this account")
        return driver

    def get_drivers(
        self,
        page: int = 1,
        size: int = 50,
        status=None,
        is_available: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
    ) -> tuple[list[Driver], int]:
        """Get paginated list of drivers."""
        skip = (page - 1) * size
        drivers = self.driver_repo.get_all_filtered(
            skip=skip, limit=size,
            status=status, is_available=is_available, search=search, tenant_id=tenant_id,
            include_all_tenants=self.is_superadmin,
        )
        total = self.driver_repo.count_filtered(
            status=status, is_available=is_available, search=search, tenant_id=tenant_id,
            include_all_tenants=self.is_superadmin,
        )
        return drivers, total

    def create_driver(
        self,
        data: DriverCreate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Driver:
        """Create a new driver."""
        # License uniqueness per tenant
        if self.driver_repo.check_license_conflict(data.license_no):
            raise ConflictException(
                f"Driver with license '{data.license_no}' already exists in this tenant"
            )

        # Employee ID uniqueness per tenant (if provided)
        if data.employee_id and self.driver_repo.check_employee_id_conflict(data.employee_id):
            raise ConflictException(
                f"Driver with employee ID '{data.employee_id}' already exists in this tenant"
            )

        driver_data = data.model_dump(exclude={"assigned_truck_ids"})
        driver = self.driver_repo.create(driver_data)

        # Map qualified trucks (many-to-many)
        if data.assigned_truck_ids:
            trucks = self.db.query(Truck).filter(
                Truck.id.in_(data.assigned_truck_ids),
                Truck.tenant_id == self.tenant_id,
                Truck.is_deleted.is_(False)
            ).all()
            driver.assigned_trucks = trucks

        self.audit_service.log_event(
            event_type="DRIVER_CREATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Driver",
            resource_id=driver.id,
            new_value={
                "first_name": driver.first_name,
                "last_name": driver.last_name,
                "license_no": driver.license_no,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.driver_repo.get_active_by_id(driver.id)

    def update_driver(
        self,
        driver_id: UUID,
        data: DriverUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Driver:
        """Update a driver."""
        driver = self.get_driver(driver_id)
        update_data = data.model_dump(exclude_unset=True, exclude_none=True, exclude={"assigned_truck_ids"})

        # License uniqueness if changing license_no
        if "license_no" in update_data:
            if self.driver_repo.check_license_conflict(update_data["license_no"], exclude_id=driver_id):
                raise ConflictException("License number already in use by another driver")

        # Employee ID uniqueness if changing employee_id
        if "employee_id" in update_data and update_data["employee_id"]:
            if self.driver_repo.check_employee_id_conflict(update_data["employee_id"], exclude_id=driver_id):
                raise ConflictException("Employee ID already in use by another driver")

        old_data = {
            "first_name": driver.first_name,
            "last_name": driver.last_name,
            "status": driver.status,
            "is_available": driver.is_available,
        }

        self.driver_repo.update(driver, update_data)

        # Sync qualified trucks if provided
        if data.assigned_truck_ids is not None:
            trucks = self.db.query(Truck).filter(
                Truck.id.in_(data.assigned_truck_ids),
                Truck.tenant_id == self.tenant_id,
                Truck.is_deleted.is_(False)
            ).all()
            driver.assigned_trucks = trucks  # replaces existing assignments

        self.audit_service.log_event(
            event_type="DRIVER_UPDATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Driver",
            resource_id=driver_id,
            old_value=old_data,
            new_value=update_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.driver_repo.get_active_by_id(driver_id)

    def delete_driver(
        self,
        driver_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Soft delete a driver."""
        driver = self.get_driver(driver_id)
        self.driver_repo.soft_delete(driver)

        self.audit_service.log_event(
            event_type="DRIVER_DELETED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Driver",
            resource_id=driver_id,
            old_value={"is_deleted": False},
            new_value={"is_deleted": True},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()

    def toggle_availability(
        self,
        driver_id: UUID,
        data: DriverAvailabilityUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Driver:
        """Toggle driver availability."""
        driver = self.get_driver(driver_id)

        # Cannot set available if license is expired
        if data.is_available and not driver.is_license_valid:
            raise BadRequestException(
                f"Cannot mark driver as available: license expired on {driver.license_expiry}"
            )

        # Cannot mark available if driver is BLACKLISTED or INACTIVE
        if data.is_available and driver.status in (DriverStatus.BLACKLISTED, DriverStatus.INACTIVE):
            raise BadRequestException(
                f"Cannot mark driver as available: status is '{driver.status}'"
            )

        driver.is_available = data.is_available
        if data.status:
            driver.status = data.status
        elif data.is_available:
            driver.status = DriverStatus.AVAILABLE
        else:
            driver.status = DriverStatus.ON_LEAVE

        self.audit_service.log_event(
            event_type="DRIVER_AVAILABILITY_CHANGED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Driver",
            resource_id=driver_id,
            new_value={"is_available": data.is_available, "status": driver.status},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.driver_repo.get_active_by_id(driver_id)

    def update_location(
        self,
        driver_id: UUID,
        data: DriverLocationUpdate,
    ) -> Driver:
        """Update driver GPS coordinates and/or base location."""
        driver = self.get_driver(driver_id)

        if data.current_lat is not None:
            driver.current_lat = data.current_lat
        if data.current_lon is not None:
            driver.current_lon = data.current_lon
        if data.base_location is not None:
            driver.base_location = data.base_location

        self.db.commit()
        return self.driver_repo.get_active_by_id(driver_id)
