from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.datetime_utils import utc_now
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    ForbiddenException,
)
from app.core.security import hash_password
from app.core.avatar_storage import validate_image, save_avatar, delete_avatar, read_avatar
from app.models import User, EventCategory
from app.repositories import UserRepository, RoleRepository, TenantRepository, ClientRepository
from app.schemas import UserCreate, UserUpdate
from app.services.audit_service import AuditService


class UserService:
    """Service for user management operations."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID | None = None,
        current_user_id: UUID | None = None,
        is_superadmin: bool = False
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.is_superadmin = is_superadmin
        self.user_repo = UserRepository(db, None if is_superadmin else tenant_id)
        self.role_repo = RoleRepository(db)
        self.tenant_repo = TenantRepository(db)
        self.client_repo = ClientRepository(db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    def _link_client(self, user_id: UUID, client_id: UUID | None) -> None:
        """(Re)link a Client (company) record to this user's portal login, or unlink."""
        # Unlink whatever client currently points at this user (if any). Flush immediately —
        # the unique index on clients.user_id would otherwise reject the new link below
        # while both rows still reference this user_id within the same flush.
        existing = self.client_repo.get_by_user_id(user_id)
        if existing and (client_id is None or existing.id != client_id):
            existing.user_id = None
            self.db.flush()

        if client_id is None:
            return

        client = self.client_repo.get_active_by_id(client_id)
        if not client:
            raise BadRequestException("Invalid client_id")
        if client.user_id is not None and client.user_id != user_id:
            raise ConflictException("This client is already linked to another user")

        client.user_id = user_id
    
    def get_user(self, user_id: UUID) -> User:
        """Get a user by ID."""
        user = self.user_repo.get_with_roles(user_id)
        if not user:
            raise NotFoundException("User not found")

        # Check tenant access
        if not self.is_superadmin and user.tenant_id != self.tenant_id:
            raise ForbiddenException("Cannot access user from another tenant")

        return user

    def upload_avatar(
        self,
        user_id: UUID,
        content: bytes,
        content_type: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """Validate, store, and attach a profile picture to a user."""
        user = self.get_user(user_id)
        ext = validate_image(content, content_type)

        old_path = user.avatar_path
        user.avatar_path = save_avatar("users", content, ext)
        self.db.flush()
        delete_avatar(old_path)

        self.audit_service.log_event(
            event_type="USER_AVATAR_UPDATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=user.tenant_id,
            resource_type="user",
            resource_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    def remove_avatar(
        self,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """Remove a user's profile picture, if any."""
        user = self.get_user(user_id)
        delete_avatar(user.avatar_path)
        user.avatar_path = None
        self.db.flush()

        self.audit_service.log_event(
            event_type="USER_AVATAR_REMOVED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=user.tenant_id,
            resource_type="user",
            resource_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    def get_avatar(self, user_id: UUID) -> tuple[bytes, str]:
        """Read a user's stored profile picture."""
        user = self.get_user(user_id)
        if not user.avatar_path:
            raise NotFoundException("No avatar set for this user")
        return read_avatar(user.avatar_path)
    
    def get_users(
        self,
        page: int = 1,
        size: int = 50,
        is_active: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None
    ) -> tuple[list[User], int]:
        """Get paginated list of users."""
        skip = (page - 1) * size

        users = self.user_repo.get_all_with_roles(
            skip=skip,
            limit=size,
            is_active=is_active,
            search=search,
            tenant_id=tenant_id
        )

        total = self.user_repo.count_filtered(
            is_active=is_active,
            search=search,
            tenant_id=tenant_id
        )

        return users, total
    
    def create_user(
        self,
        data: UserCreate,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> User:
        """Create a new user."""
        # Validate email uniqueness
        if self.user_repo.is_email_taken(data.email):
            raise ConflictException("Email already registered")
        
        # Determine tenant_id
        user_tenant_id = data.tenant_id
        if not self.is_superadmin:
            # Non-superadmin can only create users in their tenant
            user_tenant_id = self.tenant_id
        
        # Validate tenant if specified
        if user_tenant_id:
            tenant = self.tenant_repo.get_active_by_id(user_tenant_id)
            if not tenant:
                raise BadRequestException("Invalid or inactive tenant")
            
            # Check max users limit
            current_count = self.tenant_repo.count_users(user_tenant_id)
            if current_count >= tenant.max_users:
                raise BadRequestException(
                    f"Tenant has reached maximum user limit ({tenant.max_users})"
                )
        
        # Validate roles
        roles = []
        if data.role_ids:
            roles = self.role_repo.get_by_ids(data.role_ids)
            if len(roles) != len(data.role_ids):
                raise BadRequestException("One or more invalid role IDs")
            
            # SuperAdmin can only assign TenantAdmin role (no TransportAdmin/Accounts/Clients unless they are TenantAdmin themselves).
            # Non-superadmin cannot assign SuperAdmin role.
            for role in roles:
                if self.is_superadmin and role.name != "TenantAdmin":
                    raise ForbiddenException("SuperAdmin can only assign TenantAdmin role")
                if not self.is_superadmin and role.name == "SuperAdmin":
                    raise ForbiddenException("Cannot assign SuperAdmin role")
        
        # Create user
        user_data = {
            "email": data.email,
            "password_hash": hash_password(data.password),
            "first_name": data.first_name,
            "last_name": data.last_name,
            "phone": data.phone,
            "tenant_id": user_tenant_id,
            "timezone": data.timezone or get_settings().DEFAULT_TIMEZONE,
            "is_active": True,
            "is_verified": False,
        }
        
        user = self.user_repo.create(user_data)
        
        # Assign roles
        for role in roles:
            self.user_repo.assign_role(
                user_id=user.id,
                role_id=role.id,
                tenant_id=user_tenant_id,
                assigned_by=self.current_user_id
            )

        # Link to a Client (company) record for portal access, if specified
        if data.client_id is not None:
            self._link_client(user.id, data.client_id)

        # Log audit
        self.audit_service.log_user_created(
            actor_id=self.current_user_id,
            user_id=user.id,
            tenant_id=user_tenant_id,
            user_data={"email": user.email, "first_name": user.first_name, "last_name": user.last_name},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        
        # Refresh to get roles
        return self.user_repo.get_with_roles(user.id)
    
    def update_user(
        self,
        user_id: UUID,
        data: UserUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> User:
        """Update a user."""
        user = self.get_user(user_id)
        
        # Capture old values for audit
        old_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "is_active": user.is_active,
            "timezone": user.timezone,
        }
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        # Re-link / unlink the Client record (handled separately — not a User column)
        if "client_id" in update_data:
            self._link_client(user.id, update_data.pop("client_id"))

        # Check if activation status is changing
        activation_changed = False
        if "is_active" in update_data and update_data["is_active"] != user.is_active:
            activation_changed = True
            was_active = user.is_active

        self.user_repo.update(user, update_data)
        
        # Log audit
        new_data = {k: v for k, v in update_data.items()}
        self.audit_service.log_user_updated(
            actor_id=self.current_user_id,
            user_id=user_id,
            tenant_id=user.tenant_id,
            old_data=old_data,
            new_data=new_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log activation change separately
        if activation_changed:
            self.audit_service.log_user_activation(
                actor_id=self.current_user_id,
                user_id=user_id,
                tenant_id=user.tenant_id,
                activated=update_data["is_active"],
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        self.db.commit()
        return self.user_repo.get_with_roles(user_id)
    
    def delete_user(
        self,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> None:
        """Soft delete a user."""
        user = self.get_user(user_id)
        
        # Cannot delete yourself
        if user_id == self.current_user_id:
            raise BadRequestException("Cannot delete your own account")
        
        # Soft delete
        self.user_repo.soft_delete(user)
        
        # Revoke all tokens
        from app.repositories import RefreshTokenRepository
        token_repo = RefreshTokenRepository(self.db)
        token_repo.revoke_all_user_tokens(user_id)
        
        # Log audit
        self.audit_service.log_event(
            event_type="USER_DELETED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=user.tenant_id,
            resource_type="User",
            resource_id=user_id,
            old_value={"email": user.email, "is_deleted": False},
            new_value={"is_deleted": True},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
    
    def activate_user(
        self,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> User:
        """Activate a user."""
        user = self.get_user(user_id)
        
        if user.is_active:
            raise BadRequestException("User is already active")
        
        user.is_active = True
        
        self.audit_service.log_user_activation(
            actor_id=self.current_user_id,
            user_id=user_id,
            tenant_id=user.tenant_id,
            activated=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        return self.user_repo.get_with_roles(user_id)
    
    def deactivate_user(
        self,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> User:
        """Deactivate a user."""
        user = self.get_user(user_id)
        
        # Cannot deactivate yourself
        if user_id == self.current_user_id:
            raise BadRequestException("Cannot deactivate your own account")
        
        if not user.is_active:
            raise BadRequestException("User is already inactive")
        
        user.is_active = False
        
        # Revoke all tokens
        from app.repositories import RefreshTokenRepository
        token_repo = RefreshTokenRepository(self.db)
        token_repo.revoke_all_user_tokens(user_id)
        
        self.audit_service.log_user_activation(
            actor_id=self.current_user_id,
            user_id=user_id,
            tenant_id=user.tenant_id,
            activated=False,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        return self.user_repo.get_with_roles(user_id)
    
    def assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> User:
        """Assign a role to a user."""
        user = self.get_user(user_id)
        
        # Get role
        role = self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundException("Role not found")
        
        # Check permissions
        if self.is_superadmin and role.name != "TenantAdmin":
            raise ForbiddenException("SuperAdmin can only assign TenantAdmin role")
        if not self.is_superadmin and role.name == "SuperAdmin":
            raise ForbiddenException("Cannot assign SuperAdmin role")
        
        # Check if already assigned
        existing = self.user_repo.get_user_role(user_id, role_id)
        if existing:
            raise ConflictException("Role already assigned to user")
        
        # Assign role
        self.user_repo.assign_role(
            user_id=user_id,
            role_id=role_id,
            tenant_id=user.tenant_id,
            assigned_by=self.current_user_id
        )
        
        # Log audit
        self.audit_service.log_role_change(
            actor_id=self.current_user_id,
            user_id=user_id,
            tenant_id=user.tenant_id,
            role_name=role.name,
            assigned=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        return self.user_repo.get_with_roles(user_id)
    
    def revoke_role(
        self,
        user_id: UUID,
        role_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> User:
        """Revoke a role from a user."""
        user = self.get_user(user_id)
        
        # Get role
        role = self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundException("Role not found")
        
        # Find assignment
        user_role = self.user_repo.get_user_role(user_id, role_id)
        if not user_role:
            raise NotFoundException("Role not assigned to user")
        
        # Revoke
        self.user_repo.revoke_role(user_role)
        
        # Log audit
        self.audit_service.log_role_change(
            actor_id=self.current_user_id,
            user_id=user_id,
            tenant_id=user.tenant_id,
            role_name=role.name,
            assigned=False,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        return self.user_repo.get_with_roles(user_id)
    
    def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> None:
        """Change a user's password."""
        from app.core.security import verify_password
        
        user = self.get_user(user_id)
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise BadRequestException("Current password is incorrect")
        
        # Update password
        user.password_hash = hash_password(new_password)
        user.password_changed_at = utc_now()
        
        # Revoke all refresh tokens (force re-login)
        from app.repositories import RefreshTokenRepository
        token_repo = RefreshTokenRepository(self.db)
        token_repo.revoke_all_user_tokens(user_id)
        
        # Log audit
        self.audit_service.log_event(
            event_type="PASSWORD_CHANGE",
            event_category=EventCategory.auth,
            user_id=user_id,
            tenant_id=user.tenant_id,
            resource_type="User",
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
