import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDMixin


class EventCategory(str, enum.Enum):
    auth = "auth"
    user_mgmt = "user_mgmt"
    role_mgmt = "role_mgmt"
    tenant_mgmt = "tenant_mgmt"


class AuditLog(Base, UUIDMixin):
    """Audit log for tracking system events."""
    
    __tablename__ = "audit_logs"
    
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(Enum(EventCategory), nullable=False, index=True)
    
    # Resource tracking
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Change tracking
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    extra_data = Column(JSONB, default=dict, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.event_type} by user_id={self.user_id}>"


# Event type constants
class EventType:
    # Auth events
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET_REQUESTED = "PASSWORD_RESET_REQUESTED"
    PASSWORD_RESET_COMPLETED = "PASSWORD_RESET_COMPLETED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    
    # User management events
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USER_ACTIVATED = "USER_ACTIVATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    
    # Role management events
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REVOKED = "ROLE_REVOKED"
    ROLE_CHANGE = "ROLE_CHANGE"
    
    # Tenant management events
    TENANT_CREATED = "TENANT_CREATED"
    TENANT_UPDATED = "TENANT_UPDATED"
    TENANT_DELETED = "TENANT_DELETED"
    TENANT_ACTIVATED = "TENANT_ACTIVATED"
    TENANT_DEACTIVATED = "TENANT_DEACTIVATED"
