from datetime import datetime
from uuid import UUID

from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session, joinedload

from app.core.datetime_utils import utc_now
from app.models import AuditLog, EventCategory
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for audit log operations."""
    
    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(AuditLog, db)
        self.tenant_id = tenant_id
    
    def create_log(
        self,
        event_type: str,
        event_category: EventCategory,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        extra_data: dict | None = None
    ) -> AuditLog:
        """Create a new audit log entry."""
        log = AuditLog(
            tenant_id=tenant_id or self.tenant_id,
            user_id=user_id,
            event_type=event_type,
            event_category=event_category,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data or {},
            created_at=utc_now()
        )
        self.db.add(log)
        self.db.flush()
        return log
    
    def get_logs(
        self,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        event_type: str | None = None,
        event_category: EventCategory | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> list[AuditLog]:
        """Get audit logs with filters."""
        stmt = select(AuditLog).options(joinedload(AuditLog.user))

        # Apply tenant filter if not SuperAdmin
        if self.tenant_id:
            stmt = stmt.where(AuditLog.tenant_id == self.tenant_id)
        elif tenant_id:
            stmt = stmt.where(AuditLog.tenant_id == tenant_id)
        
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        if event_category:
            stmt = stmt.where(AuditLog.event_category == event_category)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if resource_id:
            stmt = stmt.where(AuditLog.resource_id == resource_id)
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
        
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        return list(self.db.execute(stmt).unique().scalars().all())
    
    def count_logs(
        self,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        event_type: str | None = None,
        event_category: EventCategory | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> int:
        """Count audit logs with filters."""
        from sqlalchemy import func
        
        stmt = select(func.count()).select_from(AuditLog)
        
        if self.tenant_id:
            stmt = stmt.where(AuditLog.tenant_id == self.tenant_id)
        elif tenant_id:
            stmt = stmt.where(AuditLog.tenant_id == tenant_id)
        
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        if event_category:
            stmt = stmt.where(AuditLog.event_category == event_category)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if resource_id:
            stmt = stmt.where(AuditLog.resource_id == resource_id)
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
        
        return self.db.execute(stmt).scalar_one()
