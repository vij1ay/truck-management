from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, not_
from sqlalchemy.orm import Session

from app.models.allocation import LoadAllocation
from app.models.driver import Driver, DriverStatus
from app.models.truck import Truck, TruckStatus
from app.repositories.base import TenantAwareRepository


class AllocationRepository(TenantAwareRepository[LoadAllocation]):
    """Repository for load allocation with conflict detection."""

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(LoadAllocation, db, tenant_id)

    # ── Conflict detection ─────────────────────────────────────────────────────

    def _overlap_condition(self, pickup: date, delivery: date):
        """
        Returns SQLAlchemy condition for date-range overlap.
        Two ranges [A_start, A_end] and [B_start, B_end] overlap when:
          A_start <= B_end  AND  A_end >= B_start
        """
        return and_(
            LoadAllocation.pickup_date <= delivery,
            LoadAllocation.effective_delivery_date >= pickup,
            LoadAllocation.is_active == True,
        )

    def check_truck_conflict(
        self,
        truck_id: UUID,
        pickup_date: date,
        effective_delivery_date: date,
        exclude_load_id: Optional[UUID] = None,
    ) -> bool:
        """Return True if truck has an active overlapping allocation."""
        stmt = (
            select(func.count())
            .select_from(LoadAllocation)
            .where(
                and_(
                    LoadAllocation.truck_id == truck_id,
                    self._overlap_condition(pickup_date, effective_delivery_date),
                )
            )
        )
        if exclude_load_id:
            stmt = stmt.where(LoadAllocation.load_id != exclude_load_id)
        return self.db.execute(stmt).scalar_one() > 0

    def check_driver_conflict(
        self,
        driver_id: UUID,
        pickup_date: date,
        effective_delivery_date: date,
        exclude_load_id: Optional[UUID] = None,
    ) -> bool:
        """Return True if driver has an active overlapping allocation."""
        stmt = (
            select(func.count())
            .select_from(LoadAllocation)
            .where(
                and_(
                    LoadAllocation.driver_id == driver_id,
                    self._overlap_condition(pickup_date, effective_delivery_date),
                )
            )
        )
        if exclude_load_id:
            stmt = stmt.where(LoadAllocation.load_id != exclude_load_id)
        return self.db.execute(stmt).scalar_one() > 0

    # ── Fetch ──────────────────────────────────────────────────────────────────

    def get_active_by_load_id(self, load_id: UUID) -> Optional[LoadAllocation]:
        """Get the current active allocation for a load (at most one)."""
        stmt = (
            select(LoadAllocation)
            .where(
                and_(
                    LoadAllocation.load_id == load_id,
                    LoadAllocation.is_active == True,
                )
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_by_load_id(self, load_id: UUID) -> list[LoadAllocation]:
        """Get full allocation history for a load (including deactivated)."""
        stmt = (
            select(LoadAllocation)
            .where(LoadAllocation.load_id == load_id)
            .order_by(LoadAllocation.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Availability queries ───────────────────────────────────────────────────

    def get_available_trucks(
        self,
        pickup_date: date,
        effective_delivery_date: date,
    ) -> list[Truck]:
        """
        Return trucks that are:
        - ACTIVE + is_available = True (not deleted)
        - Have NO active allocation overlapping the given date range
        - Belong to this tenant
        """
        # Sub-query: truck IDs that have a conflict
        conflict_subq = (
            select(LoadAllocation.truck_id)
            .where(self._overlap_condition(pickup_date, effective_delivery_date))
            .scalar_subquery()
        )

        stmt = (
            select(Truck)
            .where(
                and_(
                    Truck.is_deleted == False,
                    Truck.status == TruckStatus.ACTIVE,
                    Truck.is_available == True,
                    Truck.tenant_id == self.tenant_id,
                    not_(Truck.id.in_(conflict_subq)),
                )
            )
            .order_by(Truck.registration_no)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_available_drivers(
        self,
        pickup_date: date,
        effective_delivery_date: date,
    ) -> list[Driver]:
        """
        Return drivers that are:
        - AVAILABLE + is_available = True + valid license (not deleted)
        - Have NO active allocation overlapping the given date range
        - Belong to this tenant
        """
        conflict_subq = (
            select(LoadAllocation.driver_id)
            .where(self._overlap_condition(pickup_date, effective_delivery_date))
            .scalar_subquery()
        )

        stmt = (
            select(Driver)
            .where(
                and_(
                    Driver.is_deleted == False,
                    Driver.status == DriverStatus.AVAILABLE,
                    Driver.is_available == True,
                    Driver.license_expiry >= date.today(),
                    Driver.tenant_id == self.tenant_id,
                    not_(Driver.id.in_(conflict_subq)),
                )
            )
            .order_by(Driver.first_name, Driver.last_name)
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Deactivation ───────────────────────────────────────────────────────────

    def deactivate_by_load_id(
        self,
        load_id: UUID,
        deactivated_by_id: Optional[UUID] = None,
    ) -> Optional[LoadAllocation]:
        """Mark the active allocation for a load as inactive. Returns it."""
        alloc = self.get_active_by_load_id(load_id)
        if alloc:
            alloc.deactivate(deactivated_by_id=deactivated_by_id)
            self.db.flush()
        return alloc
