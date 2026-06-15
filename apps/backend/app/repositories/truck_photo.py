from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.truck_photo import TruckPhoto
from app.repositories.base import TenantAwareRepository


class TruckPhotoRepository(TenantAwareRepository[TruckPhoto]):
    """Repository for a truck's photo gallery (max 6 per truck, enforced in
    TruckService)."""

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(TruckPhoto, db, tenant_id)

    def get_all_by_truck(self, truck_id: UUID) -> list[TruckPhoto]:
        """Get a truck's photos ordered by position."""
        stmt = select(TruckPhoto).where(TruckPhoto.truck_id == truck_id)
        stmt = self._apply_tenant_filter(stmt)
        stmt = stmt.order_by(TruckPhoto.position)
        return list(self.db.execute(stmt).scalars().all())

    def count_by_truck(self, truck_id: UUID) -> int:
        """Count a truck's photos."""
        stmt = select(func.count()).select_from(TruckPhoto).where(TruckPhoto.truck_id == truck_id)
        stmt = self._apply_tenant_filter(stmt)
        return self.db.execute(stmt).scalar_one()
