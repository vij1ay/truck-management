from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.audit_log import EventCategory
from app.schemas.common import LocalDateTime


class AuditLogResponse(BaseModel):
    """Audit log entry response schema."""
    
    id: UUID
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    user_email: str | None = None
    event_type: str
    event_category: EventCategory
    resource_type: str | None = None
    resource_id: UUID | None = None
    old_value: dict | None = None
    new_value: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    extra_data: dict = Field(default_factory=dict)
    created_at: LocalDateTime

    model_config = {"from_attributes": True}


class AuditLogFilter(BaseModel):
    """Filter parameters for audit log queries."""
    
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    event_type: str | None = None
    event_category: EventCategory | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=1000)


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs."""
    
    items: list[AuditLogResponse]
    total: int
    page: int
    size: int
    pages: int
