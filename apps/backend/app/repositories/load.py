from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.orm import Session

from app.models.load import Load, LoadStatus
from app.repositories.base import TenantAwareRepository


class LoadRepository(TenantAwareRepository[Load]):
    """Repository for load data access with tenant isolation."""

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(Load, db, tenant_id)

    def get_next_seq_no(self, year: int) -> int:
        """
        Return the next sequential load number for this tenant+year.
        Uses MAX(load_seq_no) + 1 — safe under low concurrency (Phase 3).
        """
        stmt = (
            select(func.coalesce(func.max(Load.load_seq_no), 0))
            .where(
                and_(
                    Load.tenant_id == self.tenant_id,
                    extract("year", Load.created_at) == year,
                )
            )
        )
        current_max = self.db.execute(stmt).scalar_one()
        return int(current_max) + 1

    def get_all_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        status: LoadStatus | None = None,
        client_id: UUID | None = None,
        driver_id: UUID | None = None,
        pickup_date_from: date | None = None,
        pickup_date_to: date | None = None,
        goods_type: str | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> list[Load]:
        """Get loads with optional filters."""
        stmt = select(Load).where(Load.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)

        stmt = self._apply_filters(
            stmt, status=status, client_id=client_id, driver_id=driver_id,
            pickup_date_from=pickup_date_from, pickup_date_to=pickup_date_to,
            goods_type=goods_type, search=search,
        )

        if tenant_id is not None:
            stmt = stmt.where(Load.tenant_id == tenant_id)

        stmt = stmt.order_by(Load.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_filtered(
        self,
        status: LoadStatus | None = None,
        client_id: UUID | None = None,
        driver_id: UUID | None = None,
        pickup_date_from: date | None = None,
        pickup_date_to: date | None = None,
        goods_type: str | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> int:
        """Count loads matching filters."""
        stmt = select(func.count()).select_from(Load).where(Load.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)

        stmt = self._apply_filters(
            stmt, status=status, client_id=client_id, driver_id=driver_id,
            pickup_date_from=pickup_date_from, pickup_date_to=pickup_date_to,
            goods_type=goods_type, search=search,
        )

        if tenant_id is not None:
            stmt = stmt.where(Load.tenant_id == tenant_id)

        return self.db.execute(stmt).scalar_one()

    def _apply_filters(self, stmt, *, status, client_id, driver_id, pickup_date_from,
                       pickup_date_to, goods_type, search):
        """Apply common filter conditions to a statement."""
        if status:
            stmt = stmt.where(Load.status == status)
        if client_id:
            stmt = stmt.where(Load.client_id == client_id)
        if driver_id:
            stmt = stmt.where(Load.allocated_driver_id == driver_id)
        if pickup_date_from:
            stmt = stmt.where(Load.pickup_date >= pickup_date_from)
        if pickup_date_to:
            stmt = stmt.where(Load.pickup_date <= pickup_date_to)
        if goods_type:
            stmt = stmt.where(Load.goods_type == goods_type)
        if search:
            term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Load.load_no.ilike(term),
                    Load.origin.ilike(term),
                    Load.destination.ilike(term),
                    Load.goods_description.ilike(term),
                )
            )
        return stmt

    def check_duplicate_booking(
        self,
        client_id: UUID,
        origin: str,
        destination: str,
        pickup_date: date,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """
        Return True if an active (non-cancelled, non-deleted) load already exists
        for the same client+route+date within this tenant.
        """
        stmt = (
            select(func.count())
            .select_from(Load)
            .where(
                and_(
                    Load.is_deleted == False,
                    Load.client_id == client_id,
                    Load.origin.ilike(origin),
                    Load.destination.ilike(destination),
                    Load.pickup_date == pickup_date,
                    Load.status != LoadStatus.CANCELLED,
                )
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        if exclude_id:
            stmt = stmt.where(Load.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0
