from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.models.driver import Driver, DriverStatus
from app.repositories.base import TenantAwareRepository


class DriverRepository(TenantAwareRepository[Driver]):
    """Repository for driver data access with tenant isolation."""

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(Driver, db, tenant_id)

    def get_by_user_id(self, user_id: UUID) -> Driver | None:
        """Get a driver by linked user ID."""
        stmt = select(Driver).where(
            and_(Driver.user_id == user_id, Driver.is_deleted == False)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        status: DriverStatus | None = None,
        is_available: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> list[Driver]:
        """Get drivers with optional filters."""
        stmt = select(Driver).where(Driver.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)

        if status:
            stmt = stmt.where(Driver.status == status)
        if is_available is not None:
            stmt = stmt.where(Driver.is_available == is_available)
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Driver.first_name.ilike(search_term),
                    Driver.last_name.ilike(search_term),
                    Driver.phone.ilike(search_term),
                    Driver.license_no.ilike(search_term),
                    Driver.employee_id.ilike(search_term),
                )
            )
        if tenant_id is not None:
            stmt = stmt.where(Driver.tenant_id == tenant_id)

        stmt = stmt.order_by(Driver.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_filtered(
        self,
        status: DriverStatus | None = None,
        is_available: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> int:
        """Count drivers matching filters."""
        stmt = select(func.count()).select_from(Driver).where(Driver.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)

        if status:
            stmt = stmt.where(Driver.status == status)
        if is_available is not None:
            stmt = stmt.where(Driver.is_available == is_available)
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Driver.first_name.ilike(search_term),
                    Driver.last_name.ilike(search_term),
                    Driver.phone.ilike(search_term),
                    Driver.license_no.ilike(search_term),
                    Driver.employee_id.ilike(search_term),
                )
            )
        if tenant_id is not None:
            stmt = stmt.where(Driver.tenant_id == tenant_id)

        return self.db.execute(stmt).scalar_one()

    def check_license_conflict(
        self, license_no: str, exclude_id: UUID | None = None
    ) -> bool:
        """Check if a license number is already in use within this tenant."""
        stmt = select(func.count()).select_from(Driver).where(
            and_(
                Driver.is_deleted == False,
                Driver.license_no.ilike(license_no),
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        if exclude_id:
            stmt = stmt.where(Driver.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0

    def check_employee_id_conflict(
        self, employee_id: str, exclude_id: UUID | None = None
    ) -> bool:
        """Check if an employee ID is already in use within this tenant."""
        stmt = select(func.count()).select_from(Driver).where(
            and_(
                Driver.is_deleted == False,
                Driver.employee_id == employee_id,
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        if exclude_id:
            stmt = stmt.where(Driver.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0
