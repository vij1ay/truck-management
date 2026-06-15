from datetime import datetime
from typing import Annotated
from uuid import UUID
import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.dependencies.auth import (
    get_current_user,
    require_roles,
    CurrentUser,
    get_current_user_context,
)
from app.dependencies.database import get_db
from app.models import User, EventCategory
from app.schemas import (
    AuditLogResponse,
    AuditLogFilter,
    AuditLogListResponse,
)
from app.services import AuditService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])
logger = get_logger(__name__)


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    tenant_id: UUID | None = None,
    user_id: UUID | None = None,
    event_type: str | None = None,
    event_category: EventCategory | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """
    List audit logs with filters.

    - SuperAdmin: can view all logs
    - TenantAdmin: can only view logs for their tenant
    """
    logger.info(
        f"List audit logs page={page} size={size} tenant_filter={tenant_id} user_filter={user_id} "
        f"category={event_category} start={start_date} end={end_date}"
    )
    # Determine tenant filter based on role
    effective_tenant_id = None
    if not context.is_superadmin:
        effective_tenant_id = context.tenant_id
    elif tenant_id:
        effective_tenant_id = tenant_id

    service = AuditService(db, effective_tenant_id)

    logs, total = service.get_logs(
        tenant_id=effective_tenant_id,
        user_id=user_id,
        event_type=event_type,
        event_category=event_category,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size
    )
    
    return AuditLogListResponse(
        items=[_log_to_response(log) for log in logs],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 1
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))]
):
    """
    Get a specific audit log entry.
    
    - SuperAdmin: can view any log
    - TenantAdmin: can only view logs for their tenant
    """
    logger.info(f"Get audit log log_id={log_id}")
    from app.core.exceptions import NotFoundException, ForbiddenException
    from app.repositories import AuditLogRepository
    
    repo = AuditLogRepository(db)
    log = repo.get_by_id(log_id)
    
    if not log:
        raise NotFoundException("Audit log not found")
    
    # Check tenant access
    if not context.is_superadmin and log.tenant_id != context.tenant_id:
        raise ForbiddenException("Cannot access logs from other tenants")
    
    return _log_to_response(log)


def _log_to_response(log) -> AuditLogResponse:
    """Convert AuditLog model to AuditLogResponse schema."""
    return AuditLogResponse(
        id=log.id,
        tenant_id=log.tenant_id,
        user_id=log.user_id,
        user_email=log.user.email if log.user else None,
        event_type=log.event_type,
        event_category=log.event_category,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        old_value=log.old_value,
        new_value=log.new_value,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        extra_data=log.extra_data or {},
        created_at=log.created_at
    )
