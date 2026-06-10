from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.dependencies.auth import require_roles
from app.dependencies.database import get_db
from app.models import User
from app.schemas import RoleResponse, RoleListResponse
from app.repositories import RoleRepository

router = APIRouter(prefix="/roles", tags=["Roles"])
logger = get_logger(__name__)


@router.get("", response_model=RoleListResponse)
async def list_roles(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))]
):
    """
    List all available roles.
    
    - Requires SuperAdmin or TenantAdmin role
    """
    logger.info("List roles")
    repo = RoleRepository(db)
    roles = repo.get_all_roles()
    
    return RoleListResponse(
        items=[_role_to_response(r) for r in roles],
        total=len(roles)
    )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))]
):
    """
    Get a role by ID.
    
    - Requires SuperAdmin or TenantAdmin role
    """
    logger.info(f"Get role role_id={role_id}")
    from uuid import UUID
    from app.core.exceptions import NotFoundException
    
    repo = RoleRepository(db)
    role = repo.get_by_id(UUID(role_id))
    
    if not role:
        raise NotFoundException("Role not found")
    
    return _role_to_response(role)


def _role_to_response(role) -> RoleResponse:
    """Convert Role model to RoleResponse schema."""
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=role.permissions or [],
        is_system_role=role.is_system_role,
        created_at=role.created_at,
        updated_at=role.updated_at
    )
