from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.dependencies.auth import get_current_user, CurrentUser, get_current_user_context
from app.dependencies.database import get_db
from app.models import User, Tenant
from app.repositories import TenantRepository


async def get_tenant_id_from_user(
    user: Annotated[User, Depends(get_current_user)]
) -> UUID | None:
    """
    Extract tenant_id from the current user.
    
    Returns None for SuperAdmin users without a tenant.
    """
    return user.tenant_id


async def get_current_tenant(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> Tenant | None:
    """
    Get the current user's tenant.
    
    Returns None for SuperAdmin users without a tenant.
    """
    if not user.tenant_id:
        return None
    
    repo = TenantRepository(db)
    tenant = repo.get_active_by_id(user.tenant_id)
    
    if not tenant:
        raise NotFoundException("Tenant not found or inactive")
    
    return tenant


def enforce_tenant_access(resource_tenant_id: UUID | None):
    """
    Dependency factory to enforce tenant isolation for a specific resource.
    
    Usage:
        @router.get("/resource/{id}")
        def get_resource(
            resource: Resource = Depends(get_resource),
            _: None = Depends(enforce_tenant_access(resource.tenant_id))
        ):
            ...
    """
    async def tenant_checker(
        context: Annotated[CurrentUser, Depends(get_current_user_context)]
    ) -> None:
        if not context.can_access_tenant(resource_tenant_id):
            raise ForbiddenException("Access denied to this tenant's resources")
    
    return tenant_checker


async def validate_tenant_access(
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    tenant_id: UUID | None = None
) -> UUID | None:
    """
    Validate and return the appropriate tenant_id for operations.
    
    - SuperAdmin can specify any tenant_id or None
    - Other users are restricted to their own tenant
    
    Returns the effective tenant_id to use for operations.
    """
    if context.is_superadmin:
        # SuperAdmin can operate on any tenant
        return tenant_id
    
    # Non-superadmin users are restricted to their tenant
    if tenant_id and tenant_id != context.tenant_id:
        raise ForbiddenException("Cannot access other tenant's resources")
    
    return context.tenant_id


class TenantContext:
    """
    Context class for tenant-scoped operations.
    
    Provides utilities for working within a tenant context.
    """
    
    def __init__(
        self,
        user: User,
        tenant: Tenant | None = None
    ):
        self.user = user
        self.tenant = tenant
        self.tenant_id = tenant.id if tenant else user.tenant_id
        self.is_superadmin = user.is_superadmin()
    
    def filter_by_tenant(self, query):
        """Apply tenant filter to a query if not SuperAdmin."""
        if not self.is_superadmin and self.tenant_id:
            return query.filter_by(tenant_id=self.tenant_id)
        return query
    
    def validate_resource_access(self, resource_tenant_id: UUID | None) -> bool:
        """Check if user can access a resource based on tenant."""
        if self.is_superadmin:
            return True
        return self.tenant_id == resource_tenant_id


async def get_tenant_context(
    user: Annotated[User, Depends(get_current_user)],
    tenant: Annotated[Tenant | None, Depends(get_current_tenant)]
) -> TenantContext:
    """Get the tenant context for the current request."""
    return TenantContext(user, tenant)
