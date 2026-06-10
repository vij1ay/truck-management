from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Repository for role operations."""
    
    def __init__(self, db: Session):
        super().__init__(Role, db)
    
    def get_by_name(self, name: str) -> Role | None:
        """Get a role by name."""
        stmt = select(Role).where(Role.name == name)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_all_roles(self) -> list[Role]:
        """Get all roles."""
        stmt = select(Role).order_by(Role.name)
        return list(self.db.execute(stmt).scalars().all())
    
    def get_system_roles(self) -> list[Role]:
        """Get all system roles."""
        stmt = select(Role).where(Role.is_system_role == True).order_by(Role.name)
        return list(self.db.execute(stmt).scalars().all())
    
    def get_by_ids(self, role_ids: list[UUID]) -> list[Role]:
        """Get multiple roles by their IDs."""
        if not role_ids:
            return []
        stmt = select(Role).where(Role.id.in_(role_ids))
        return list(self.db.execute(stmt).scalars().all())
