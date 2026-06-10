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
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
)
from app.services import TenantService

router = APIRouter(prefix="/tenants", tags=["Tenants"])
logger = get_logger(__name__)


def get_tenant_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)]
) -> TenantService:
    """Create a TenantService with the current user's context."""
    return TenantService(
        db=db,
        current_user_id=context.user_id
    )


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    service: Annotated[TenantService, Depends(get_tenant_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    is_active: bool | None = None
):
    """
    List all tenants.
    
    - Requires SuperAdmin role
    """
    logger.info(f"List tenants page={page} size={size} active={is_active}")
    tenants, total = service.get_tenants(
        page=page,
        size=size,
        is_active=is_active
    )
    
    return TenantListResponse(
        items=[_tenant_to_response(t) for t in tenants],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 1
    )


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    request: Request,
    data: TenantCreate,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin"))]
):
    """
    Create a new tenant with admin user.
    
    - Requires SuperAdmin role
    - Creates the tenant and a TenantAdmin user
    """
    logger.info(f"Create tenant name={data.name}")
    tenant = service.create_tenant(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    return _tenant_to_response(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)]
):
    """
    Get a tenant by ID.
    
    - SuperAdmin: can view any tenant
    - TenantAdmin: can only view their own tenant
    """
    logger.info(f"Get tenant tenant_id={tenant_id}")
    # Check access
    if not context.is_superadmin:
        if context.tenant_id != tenant_id:
            from app.core.exceptions import ForbiddenException
            raise ForbiddenException("Cannot access other tenants")
    
    tenant = service.get_tenant(tenant_id)
    return _tenant_to_response(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    request: Request,
    tenant_id: UUID,
    data: TenantUpdate,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin"))]
):
    """
    Update a tenant.
    
    - Requires SuperAdmin role
    """
    logger.info(f"Update tenant tenant_id={tenant_id}")
    tenant = service.update_tenant(
        tenant_id=tenant_id,
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    return _tenant_to_response(tenant)


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(
    request: Request,
    tenant_id: UUID,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin"))]
):
    """
    Soft delete a tenant and all its users.
    
    - Requires SuperAdmin role
    - Cascades soft delete to all users
    - Revokes all tokens for tenant users
    """
    logger.info(f"Delete tenant tenant_id={tenant_id}")
    service.delete_tenant(
        tenant_id=tenant_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )


def _tenant_to_response(tenant) -> TenantResponse:
    """Convert Tenant model to TenantResponse schema."""
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        subscription_tier=tenant.subscription_tier,
        max_users=tenant.max_users,
        is_active=tenant.is_active,
        settings=tenant.settings or {},
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        user_count=getattr(tenant, "user_count", None)
    )
