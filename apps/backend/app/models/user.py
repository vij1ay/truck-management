from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model with tenant association."""
    
    __tablename__ = "users"
    
    # Tenant association (NULL for SuperAdmin)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Authentication
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Security
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    user_roles = relationship(
        "UserRole",
        back_populates="user",
        lazy="joined",
        foreign_keys="UserRole.user_id"
    )
    assigned_roles = relationship(
        "UserRole",
        back_populates="assigned_by_user",
        foreign_keys="UserRole.assigned_by",
        lazy="dynamic"
    )
    refresh_tokens = relationship("RefreshToken", back_populates="user", lazy="dynamic")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def roles(self) -> list:
        """Return list of active role objects."""
        return [
            ur.role for ur in self.user_roles 
            if not ur.is_deleted and ur.role is not None
        ]
    
    @property
    def role_names(self) -> list[str]:
        """Return list of active role names."""
        return [role.name for role in self.roles]
    
    @property
    def primary_role(self) -> str | None:
        """Return the primary (first) role name."""
        roles = self.role_names
        return roles[0] if roles else None
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return role_name in self.role_names
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission through any role."""
        return any(role.has_permission(permission) for role in self.roles)
    
    def is_superadmin(self) -> bool:
        """Check if user is a SuperAdmin."""
        return self.has_role("SuperAdmin")
