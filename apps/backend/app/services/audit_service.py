from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog, EventCategory, EventType
from app.repositories import AuditLogRepository


class AuditService:
    """Service for audit logging operations."""
    
    def __init__(self, db: Session, tenant_id: UUID | None = None):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = AuditLogRepository(db, tenant_id)
    
    def log_event(
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
        extra_data: dict | None = None,
    ) -> AuditLog:
        """Create a new audit log entry."""
        from fastapi.encoders import jsonable_encoder
        
        return self.repo.create_log(
            event_type=event_type,
            event_category=event_category,
            user_id=user_id,
            tenant_id=tenant_id or self.tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=jsonable_encoder(old_value) if old_value else None,
            new_value=jsonable_encoder(new_value) if new_value else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=jsonable_encoder(extra_data) if extra_data else None
        )
    
    def log_login(
        self,
        user_id: UUID,
        tenant_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True
    ) -> AuditLog:
        """Log a login event."""
        event_type = EventType.LOGIN if success else EventType.LOGIN_FAILED
        return self.log_event(
            event_type=event_type,
            event_category=EventCategory.auth,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="User",
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={"success": success}
        )
    
    def log_logout(
        self,
        user_id: UUID,
        tenant_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> AuditLog:
        """Log a logout event."""
        return self.log_event(
            event_type=EventType.LOGOUT,
            event_category=EventCategory.auth,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="User",
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_user_created(
        self,
        actor_id: UUID,
        user_id: UUID,
        tenant_id: UUID | None,
        user_data: dict,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> AuditLog:
        """Log user creation."""
        # Remove sensitive data
        safe_data = {k: v for k, v in user_data.items() if k != "password_hash"}
        return self.log_event(
            event_type=EventType.USER_CREATED,
            event_category=EventCategory.user_mgmt,
            user_id=actor_id,
            tenant_id=tenant_id,
            resource_type="User",
            resource_id=user_id,
            new_value=safe_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_user_updated(
        self,
        actor_id: UUID,
        user_id: UUID,
        tenant_id: UUID | None,
        old_data: dict,
        new_data: dict,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> AuditLog:
        """Log user update."""
        return self.log_event(
            event_type=EventType.USER_UPDATED,
            event_category=EventCategory.user_mgmt,
            user_id=actor_id,
            tenant_id=tenant_id,
            resource_type="User",
            resource_id=user_id,
            old_value=old_data,
            new_value=new_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_user_activation(
        self,
        actor_id: UUID,
        user_id: UUID,
        tenant_id: UUID | None,
        activated: bool,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> AuditLog:
        """Log user activation/deactivation."""
        event_type = EventType.USER_ACTIVATED if activated else EventType.USER_DEACTIVATED
        return self.log_event(
            event_type=event_type,
            event_category=EventCategory.user_mgmt,
            user_id=actor_id,
            tenant_id=tenant_id,
            resource_type="User",
            resource_id=user_id,
            old_value={"is_active": not activated},
            new_value={"is_active": activated},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_role_change(
        self,
        actor_id: UUID,
        user_id: UUID,
        tenant_id: UUID | None,
        role_name: str,
        assigned: bool,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> AuditLog:
        """Log role assignment/revocation."""
        event_type = EventType.ROLE_ASSIGNED if assigned else EventType.ROLE_REVOKED
        return self.log_event(
            event_type=event_type,
            event_category=EventCategory.role_mgmt,
            user_id=actor_id,
            tenant_id=tenant_id,
            resource_type="UserRole",
            resource_id=user_id,
            new_value={"role": role_name, "action": "assigned" if assigned else "revoked"},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_tenant_created(
        self,
        actor_id: UUID,
        tenant_id: UUID,
        tenant_data: dict,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> AuditLog:
        """Log tenant creation."""
        return self.log_event(
            event_type=EventType.TENANT_CREATED,
            event_category=EventCategory.tenant_mgmt,
            user_id=actor_id,
            tenant_id=tenant_id,
            resource_type="Tenant",
            resource_id=tenant_id,
            new_value=tenant_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_logs(
        self,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        event_type: str | None = None,
        event_category: EventCategory | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        size: int = 50
    ) -> tuple[list[AuditLog], int]:
        """Get audit logs with pagination."""
        skip = (page - 1) * size
        
        logs = self.repo.get_logs(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            event_category=event_category,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=size
        )
        
        total = self.repo.count_logs(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            event_category=event_category,
            start_date=start_date,
            end_date=end_date
        )
        
        return logs, total
