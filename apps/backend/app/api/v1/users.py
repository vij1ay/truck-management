from typing import Annotated
from uuid import UUID
import math

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.dependencies.auth import (
    get_current_user,
    require_roles,
    CurrentUser,
    get_current_user_context,
)
from app.dependencies.database import get_db
from app.middleware.tenant_context import get_client_ip
from app.models import User
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    MessageResponse,
    PasswordChangeRequest,
    RoleAssignmentRequest,
    RoleBasic,
)
from app.services import UserService

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger(__name__)


def get_user_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)]
) -> UserService:
    """Create a UserService with the current user's context."""
    return UserService(
        db=db,
        tenant_id=context.tenant_id,
        current_user_id=context.user_id,
        is_superadmin=context.is_superadmin
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    is_active: bool | None = None,
    search: str | None = None
):
    """
    List users with pagination.
    
    - SuperAdmin: sees all users across tenants
    - TenantAdmin: sees only users in their tenant
    """
    logger.info(f"List users page={page} size={size} active={is_active}")
    users, total = service.get_users(
        page=page,
        size=size,
        is_active=is_active,
        search=search
    )
    
    return UserListResponse(
        items=[_user_to_response(u) for u in users],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 1
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    request: Request,
    data: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))]
):
    """
    Create a new user.
    
    - SuperAdmin: can create users in any tenant
    - TenantAdmin: can only create users in their tenant
    """
    logger.info(f"Create user email={data.email}")
    user = service.create_user(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    return _user_to_response(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get the current user's profile."""
    logger.info(f"Get current user profile user_id={current_user.id}")
    return _user_to_response(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)]
):
    """
    Get a user by ID.
    
    - SuperAdmin: can view any user
    - TenantAdmin: can view users in their tenant
    - Users can view their own profile
    """
    logger.info(f"Get user user_id={user_id}")
    # Allow users to view themselves
    if user_id != context.user_id:
        # Check for admin role
        if not context.is_superadmin and "TenantAdmin" not in context.roles:
            from app.core.exceptions import ForbiddenException
            raise ForbiddenException("Cannot view other users")
    
    user = service.get_user(user_id)
    return _user_to_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: UUID,
    data: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)]
):
    """
    Update a user.
    
    - SuperAdmin/TenantAdmin: can update any field for users in scope
    - Users can update limited fields (first_name, last_name, phone) for themselves
    """
    logger.info(f"Update user user_id={user_id}")
    # Allow users to update themselves with limited fields
    if user_id == context.user_id and not context.is_superadmin and "TenantAdmin" not in context.roles:
        # Only allow certain fields
        allowed_fields = {"first_name", "last_name", "phone"}
        update_fields = set(data.model_dump(exclude_unset=True).keys())
        if not update_fields.issubset(allowed_fields):
            from app.core.exceptions import ForbiddenException
            raise ForbiddenException("Can only update profile fields")
    elif user_id != context.user_id:
        # Must be admin to update others
        if not context.is_superadmin and "TenantAdmin" not in context.roles:
            from app.core.exceptions import ForbiddenException
            raise ForbiddenException("Cannot update other users")
    
    user = service.update_user(
        user_id=user_id,
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    return _user_to_response(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    request: Request,
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))]
):
    """
    Soft delete a user.
    
    - Requires SuperAdmin or TenantAdmin role
    - Cannot delete yourself
    """
    logger.info(f"Delete user user_id={user_id}")
    service.delete_user(
        user_id=user_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    request: Request,
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))]
):
    """Activate a deactivated user."""
    logger.info(f"Activate user user_id={user_id}")
    user = service.activate_user(
        user_id=user_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    return _user_to_response(user)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    request: Request,
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))]
):
    """
    Deactivate a user.
    
    - Cannot deactivate yourself
    - Revokes all user's sessions
    """
    logger.info(f"Deactivate user user_id={user_id}")
    user = service.deactivate_user(
        user_id=user_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    return _user_to_response(user)


@router.post("/{user_id}/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    user_id: UUID,
    data: PasswordChangeRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)]
):
    """
    Change user's password.
    
    - Users can only change their own password
    - Requires current password verification
    - Revokes all sessions after password change
    """
    # Only allow users to change their own password
    if user_id != context.user_id:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("Can only change your own password")
    
    logger.info(f"Change password user_id={user_id}")
    service.change_password(
        user_id=user_id,
        current_password=data.current_password,
        new_password=data.new_password,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    
    return MessageResponse(message="Password changed successfully. Please login again.")


@router.post("/{user_id}/roles", response_model=UserResponse)
async def assign_role(
    request: Request,
    user_id: UUID,
    data: RoleAssignmentRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))]
):
    """
    Assign a role to a user.
    
    - TenantAdmin cannot assign SuperAdmin role
    """
    logger.info(f"Assign role user_id={user_id} role_id={data.role_id}")
    user = service.assign_role(
        user_id=user_id,
        role_id=data.role_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    return _user_to_response(user)


@router.delete("/{user_id}/roles/{role_id}", response_model=UserResponse)
async def revoke_role(
    request: Request,
    user_id: UUID,
    role_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))]
):
    """Revoke a role from a user."""
    logger.info(f"Revoke role user_id={user_id} role_id={role_id}")
    user = service.revoke_role(
        user_id=user_id,
        role_id=role_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    return _user_to_response(user)


def _user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse schema."""
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        tenant_id=user.tenant_id,
        is_active=user.is_active,
        is_verified=user.is_verified,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=[RoleBasic(id=r.id, name=r.name) for r in user.roles]
    )
