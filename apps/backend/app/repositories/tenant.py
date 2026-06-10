from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for tenant operations."""
    
    def __init__(self, db: Session):
        super().__init__(Tenant, db)
    
    def get_by_name(self, name: str) -> Tenant | None:
        """Get a tenant by name."""
        stmt = select(Tenant).where(
            and_(
                Tenant.name == name,
                Tenant.is_deleted == False
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_by_domain(self, domain: str) -> Tenant | None:
        """Get a tenant by domain."""
        stmt = select(Tenant).where(
            and_(
                Tenant.domain == domain,
                Tenant.is_deleted == False
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_active_tenants(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[Tenant]:
        """Get all active tenants."""
        stmt = select(Tenant).where(
            and_(
                Tenant.is_active == True,
                Tenant.is_deleted == False
            )
        ).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
    
    def count_users(self, tenant_id: UUID) -> int:
        """Count users in a tenant."""
        from app.models import User
        stmt = select(func.count()).select_from(User).where(
            and_(
                User.tenant_id == tenant_id,
                User.is_deleted == False
            )
        )
        return self.db.execute(stmt).scalar_one()
    
    def is_name_taken(self, name: str, exclude_id: UUID | None = None) -> bool:
        """Check if a tenant name is already taken."""
        stmt = select(func.count()).select_from(Tenant).where(
            and_(
                Tenant.name == name,
                Tenant.is_deleted == False
            )
        )
        if exclude_id:
            stmt = stmt.where(Tenant.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0
