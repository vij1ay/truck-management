from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    ForbiddenException,
)
from app.core.security import hash_password
from app.models import Tenant, User, EventCategory
from app.repositories import TenantRepository, UserRepository, RoleRepository
from app.schemas import TenantCreate, TenantUpdate
from app.services.audit_service import AuditService


class TenantService:
    """Service for tenant management operations."""
    
    def __init__(
        self,
        db: Session,
        current_user_id: UUID | None = None
    ):
        self.db = db
        self.current_user_id = current_user_id
        self.tenant_repo = TenantRepository(db)
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.audit_service = AuditService(db)
    
    def get_tenant(self, tenant_id: UUID) -> Tenant:
        """Get a tenant by ID."""
        tenant = self.tenant_repo.get_active_by_id(tenant_id)
        if not tenant:
            raise NotFoundException("Tenant not found")
        return tenant
    
    def get_tenants(
        self,
        page: int = 1,
        size: int = 50,
        is_active: bool | None = None
    ) -> tuple[list[Tenant], int]:
        """Get paginated list of tenants."""
        skip = (page - 1) * size
        
        if is_active is not None:
            tenants = self.tenant_repo.get_active_tenants(skip=skip, limit=size)
        else:
            tenants = self.tenant_repo.get_all(skip=skip, limit=size)
        
        total = self.tenant_repo.count()
        
        # Add user counts
        for tenant in tenants:
            tenant.user_count = self.tenant_repo.count_users(tenant.id)
        
        return tenants, total
    
    def create_tenant(
        self,
        data: TenantCreate,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> Tenant:
        """Create a new tenant with admin user."""
        # Validate name uniqueness
        if self.tenant_repo.is_name_taken(data.name):
            raise ConflictException("Tenant name already exists")
        
        # Check if admin email is taken
        if self.user_repo.is_email_taken(data.admin_email):
            raise ConflictException("Admin email already registered")
        
        # Create tenant
        tenant_data = {
            "name": data.name,
            "domain": data.domain,
            "subscription_tier": data.subscription_tier,
            "max_users": data.max_users,
            "is_active": True,
            "settings": {},
        }
        
        tenant = self.tenant_repo.create(tenant_data)
        
        # Get TenantAdmin role
        tenant_admin_role = self.role_repo.get_by_name("TenantAdmin")
        if not tenant_admin_role:
            raise BadRequestException("TenantAdmin role not found. Please run seed script.")
        
        # Create admin user
        admin_user_data = {
            "email": data.admin_email,
            "password_hash": hash_password(data.admin_password),
            "first_name": data.admin_first_name,
            "last_name": data.admin_last_name,
            "tenant_id": tenant.id,
            "is_active": True,
            "is_verified": True,  # Admin is pre-verified
        }
        
        admin_repo = UserRepository(self.db, tenant.id)
        admin_user = admin_repo.create(admin_user_data)
        
        # Assign TenantAdmin role
        admin_repo.assign_role(
            user_id=admin_user.id,
            role_id=tenant_admin_role.id,
            tenant_id=tenant.id,
            assigned_by=self.current_user_id
        )
        
        # Log audit
        self.audit_service.log_tenant_created(
            actor_id=self.current_user_id,
            tenant_id=tenant.id,
            tenant_data={
                "name": tenant.name,
                "subscription_tier": tenant.subscription_tier.value,
                "admin_email": data.admin_email,
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        
        # Add user count
        tenant.user_count = 1
        return tenant
    
    def update_tenant(
        self,
        tenant_id: UUID,
        data: TenantUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> Tenant:
        """Update a tenant."""
        tenant = self.get_tenant(tenant_id)
        
        # Check name uniqueness if changing
        if data.name and data.name != tenant.name:
            if self.tenant_repo.is_name_taken(data.name, exclude_id=tenant_id):
                raise ConflictException("Tenant name already exists")
        
        # Capture old values for audit
        old_data = {
            "name": tenant.name,
            "subscription_tier": tenant.subscription_tier.value,
            "max_users": tenant.max_users,
            "is_active": tenant.is_active,
        }
        
        # Update
        update_data = data.model_dump(exclude_unset=True)
        self.tenant_repo.update(tenant, update_data)
        
        # Log audit
        self.audit_service.log_event(
            event_type="TENANT_UPDATED",
            event_category=EventCategory.tenant_mgmt,
            user_id=self.current_user_id,
            tenant_id=tenant_id,
            resource_type="Tenant",
            resource_id=tenant_id,
            old_value=old_data,
            new_value=update_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        
        # Add user count
        tenant.user_count = self.tenant_repo.count_users(tenant_id)
        return tenant
    
    def delete_tenant(
        self,
        tenant_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> None:
        """Soft delete a tenant and all its users."""
        tenant = self.get_tenant(tenant_id)
        
        # Soft delete tenant
        self.tenant_repo.soft_delete(tenant)
        
        # Soft delete all users in tenant
        from sqlalchemy import update
        from app.models import User
        from datetime import datetime
        
        stmt = (
            update(User)
            .where(User.tenant_id == tenant_id)
            .values(is_deleted=True, deleted_at=datetime.utcnow())
        )
        self.db.execute(stmt)
        
        # Revoke all tokens for tenant users
        from app.models import RefreshToken
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.tenant_id == tenant_id)
            .values(revoked=True, revoked_at=datetime.utcnow())
        )
        self.db.execute(stmt)
        
        # Log audit
        self.audit_service.log_event(
            event_type="TENANT_DELETED",
            event_category=EventCategory.tenant_mgmt,
            user_id=self.current_user_id,
            tenant_id=tenant_id,
            resource_type="Tenant",
            resource_id=tenant_id,
            old_value={"name": tenant.name, "is_deleted": False},
            new_value={"is_deleted": True},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
