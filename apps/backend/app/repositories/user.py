from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session, joinedload

from app.core.datetime_utils import utc_now
from app.models import User, UserRole, Role
from app.repositories.base import TenantAwareRepository


class UserRepository(TenantAwareRepository[User]):
    """Repository for user operations."""
    
    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(User, db, tenant_id)
    
    def get_by_email(self, email: str) -> User | None:
        """Get a user by email (across all tenants for login)."""
        stmt = select(User).where(
            and_(
                User.email == email,
                User.is_deleted == False
            )
        ).options(
            joinedload(User.user_roles).joinedload(UserRole.role),
            joinedload(User.tenant)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()
    
    def get_by_email_in_tenant(self, email: str) -> User | None:
        """Get a user by email within the current tenant."""
        stmt = select(User).where(
            and_(
                User.email == email,
                User.is_deleted == False
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_with_roles(self, user_id: UUID) -> User | None:
        """Get a user with their roles loaded."""
        stmt = select(User).where(
            and_(
                User.id == user_id,
                User.is_deleted == False
            )
        ).options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        )
        stmt = self._apply_tenant_filter(stmt)
        return self.db.execute(stmt).unique().scalar_one_or_none()
    
    def get_all_with_roles(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None
    ) -> list[User]:
        """Get all users with their roles."""
        stmt = select(User).where(User.is_deleted == False)
        stmt = self._apply_tenant_filter(stmt)

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )

        if tenant_id is not None:
            stmt = stmt.where(User.tenant_id == tenant_id)

        stmt = stmt.options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        ).offset(skip).limit(limit)

        return list(self.db.execute(stmt).unique().scalars().all())

    def count_filtered(
        self,
        is_active: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None
    ) -> int:
        """Count users with filters."""
        stmt = select(func.count()).select_from(User).where(User.is_deleted == False)
        stmt = self._apply_tenant_filter(stmt)

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )

        if tenant_id is not None:
            stmt = stmt.where(User.tenant_id == tenant_id)

        return self.db.execute(stmt).scalar_one()
    
    def is_email_taken(self, email: str, exclude_id: UUID | None = None) -> bool:
        """Check if an email is already taken."""
        stmt = select(func.count()).select_from(User).where(
            and_(
                User.email == email,
                User.is_deleted == False
            )
        )
        if exclude_id:
            stmt = stmt.where(User.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0
    
    def assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID | None = None,
        assigned_by: UUID | None = None
    ) -> UserRole:
        """Assign a role to a user."""
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            assigned_by=assigned_by,
            assigned_at=utc_now()
        )
        self.db.add(user_role)
        self.db.flush()
        return user_role
    
    def get_user_role(self, user_id: UUID, role_id: UUID) -> UserRole | None:
        """Get a specific user-role assignment."""
        stmt = select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.is_deleted == False
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def revoke_role(self, user_role: UserRole) -> None:
        """Soft delete a user-role assignment."""
        user_role.soft_delete()
        self.db.flush()
