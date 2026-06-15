from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.models.truck import Truck, TruckStatus, TruckType
from app.repositories.base import TenantAwareRepository


class TruckRepository(TenantAwareRepository[Truck]):
    """Repository for truck data access with tenant isolation."""

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(Truck, db, tenant_id)

    def get_all_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        status: TruckStatus | None = None,
        truck_type: TruckType | None = None,
        ownership_type: str | None = None,
        is_available: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> list[Truck]:
        """Get trucks with optional filters."""
        stmt = select(Truck).where(Truck.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)

        if status:
            stmt = stmt.where(Truck.status == status)
        if truck_type:
            stmt = stmt.where(Truck.truck_type == truck_type)
        if ownership_type:
            stmt = stmt.where(Truck.ownership_type == ownership_type)
        if is_available is not None:
            stmt = stmt.where(Truck.is_available == is_available)
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Truck.registration_no.ilike(search_term),
                    Truck.make.ilike(search_term),
                    Truck.model.ilike(search_term),
                    Truck.owner_name.ilike(search_term),
                )
            )
        if tenant_id is not None:
            stmt = stmt.where(Truck.tenant_id == tenant_id)

        stmt = stmt.order_by(Truck.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_filtered(
        self,
        status: TruckStatus | None = None,
        truck_type: TruckType | None = None,
        ownership_type: str | None = None,
        is_available: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> int:
        """Count trucks matching filters."""
        stmt = select(func.count()).select_from(Truck).where(Truck.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)

        if status:
            stmt = stmt.where(Truck.status == status)
        if truck_type:
            stmt = stmt.where(Truck.truck_type == truck_type)
        if ownership_type:
            stmt = stmt.where(Truck.ownership_type == ownership_type)
        if is_available is not None:
            stmt = stmt.where(Truck.is_available == is_available)
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Truck.registration_no.ilike(search_term),
                    Truck.make.ilike(search_term),
                    Truck.model.ilike(search_term),
                    Truck.owner_name.ilike(search_term),
                )
            )
        if tenant_id is not None:
            stmt = stmt.where(Truck.tenant_id == tenant_id)

        return self.db.execute(stmt).scalar_one()

    def check_registration_conflict(
        self, registration_no: str, exclude_id: UUID | None = None
    ) -> bool:
        """Check if a registration number is already in use within this tenant."""
        stmt = select(func.count()).select_from(Truck).where(
            and_(
                Truck.is_deleted == False,
                Truck.registration_no.ilike(registration_no),
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        if exclude_id:
            stmt = stmt.where(Truck.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0

    def get_by_registration(self, registration_no: str) -> Truck | None:
        """Get a truck by registration number within tenant."""
        stmt = select(Truck).where(
            and_(
                Truck.is_deleted == False,
                Truck.registration_no.ilike(registration_no),
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        return self.db.execute(stmt).scalar_one_or_none()
