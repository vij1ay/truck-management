from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    InvalidTokenException,
    TokenExpiredException,
    AccountLockedException,
    TenantInactiveException,
)
from app.core.datetime_utils import utc_now
from app.core.security import decode_token, TokenPayload
from app.core.timezone_context import set_current_timezone
from app.dependencies.database import get_db
from app.models import User
from app.repositories import UserRepository

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> TokenPayload:
    """
    Extract and validate JWT token from Authorization header.
    
    Returns the decoded token payload.
    """
    try:
        payload = decode_token(credentials.credentials)
        return TokenPayload(payload)
    except JWTError as e:
        if "expired" in str(e).lower():
            raise TokenExpiredException()
        raise InvalidTokenException()


async def get_current_user(
    token: Annotated[TokenPayload, Depends(get_token_payload)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """
    Get the current authenticated user.
    
    Validates:
    - User exists
    - User is not deleted
    - User is active
    - User's tenant is active (if applicable)
    """
    # Get user from database
    repo = UserRepository(db)
    user = repo.get_with_roles(token.user_id)
    
    if not user:
        raise UnauthorizedException("User not found")
    
    if not user.is_active:
        raise AccountLockedException("Account is deactivated")
    
    # Check if user is locked
    if user.locked_until:
        if user.locked_until > utc_now():
            raise AccountLockedException(
                f"Account is locked until {user.locked_until.isoformat()}"
            )
    
    # Check tenant status (if user belongs to a tenant)
    if user.tenant and not user.tenant.is_active:
        raise TenantInactiveException()

    # Make this user's timezone available to response serializers (LocalDateTime)
    set_current_timezone(user.timezone)

    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get the current active user (alias for get_current_user)."""
    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_roles("SuperAdmin", "TenantAdmin"))])
        def admin_endpoint():
            ...
    """
    async def role_checker(
        user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        user_roles = user.role_names
        
        # Check if user has at least one of the allowed roles
        if not any(role in user_roles for role in allowed_roles):
            raise ForbiddenException(
                f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        
        return user
    
    return role_checker


def require_permission(permission: str):
    """
    Dependency factory for permission-based access control.
    
    Usage:
        @router.post("/users", dependencies=[Depends(require_permission("users:create"))])
        def create_user():
            ...
    """
    async def permission_checker(
        user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if not user.has_permission(permission):
            raise ForbiddenException(
                f"Access denied. Required permission: {permission}"
            )
        
        return user
    
    return permission_checker


# Convenience dependencies for common role checks
RequireSuperAdmin = Depends(require_roles("SuperAdmin"))
RequireTenantAdmin = Depends(require_roles("SuperAdmin", "TenantAdmin"))
RequireTransportAdmin = Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))
RequireAccounts = Depends(require_roles("SuperAdmin", "TenantAdmin", "Accounts"))


class CurrentUser:
    """
    Context class for holding current user information.
    
    Can be used to pass user context to services.
    """
    
    def __init__(self, user: User):
        self.user = user
        self.user_id = user.id
        self.tenant_id = user.tenant_id
        self.roles = user.role_names
        self.is_superadmin = user.is_superadmin()
    
    def can_access_tenant(self, tenant_id: UUID | None) -> bool:
        """Check if user can access a specific tenant."""
        if self.is_superadmin:
            return True
        return self.tenant_id == tenant_id
    
    def can_manage_user(self, target_user: User) -> bool:
        """Check if user can manage another user."""
        if self.is_superadmin:
            return True
        if "TenantAdmin" in self.roles:
            return self.tenant_id == target_user.tenant_id
        return False


async def get_current_user_context(
    user: Annotated[User, Depends(get_current_user)]
) -> CurrentUser:
    """Get a context object for the current user."""
    return CurrentUser(user)
