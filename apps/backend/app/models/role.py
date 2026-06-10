from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModelNoSoftDelete


class Role(BaseModelNoSoftDelete):
    """Role model for RBAC."""
    
    __tablename__ = "roles"
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    permissions = Column(JSONB, default=list, nullable=False)
    is_system_role = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role", lazy="dynamic")
    
    def __repr__(self):
        return f"<Role {self.name}>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if the role has a specific permission."""
        if "*:*" in self.permissions:
            return True
        
        resource, action = permission.split(":", 1) if ":" in permission else (permission, "*")
        
        for perm in self.permissions:
            perm_resource, perm_action = perm.split(":", 1) if ":" in perm else (perm, "*")
            
            if perm_resource == "*" or perm_resource == resource:
                if perm_action == "*" or perm_action == action:
                    return True
        
        return False


# Predefined system roles
SYSTEM_ROLES = [
    {
        "name": "SuperAdmin",
        "description": "Full system access across all tenants",
        "permissions": ["*:*"],
        "is_system_role": True,
    },
    {
        "name": "TenantAdmin",
        "description": "Full access within the tenant",
        "permissions": [
            "users:*",
            "roles:read",
            "audit_logs:read",
            "loads:*",
            "trucks:*",
            "drivers:*",
            "clients:*",
        ],
        "is_system_role": True,
    },
    {
        "name": "TransportAdmin",
        "description": "Manage transport operations",
        "permissions": [
            "loads:*",
            "trucks:*",
            "drivers:read",
            "drivers:update",
            "clients:read",
        ],
        "is_system_role": True,
    },
    {
        "name": "Accounts",
        "description": "Financial operations management",
        "permissions": [
            "invoices:*",
            "payments:*",
            "loads:read",
            "reports:read",
            "reports:export",
        ],
        "is_system_role": True,
    },
    {
        "name": "Client",
        "description": "Client portal access",
        "permissions": [
            "loads:read",
            "loads:create",
            "invoices:read",
        ],
        "is_system_role": True,
    },
    {
        "name": "Driver",
        "description": "Driver mobile app access",
        "permissions": [
            "loads:read",
            "loads:update_status",
            "documents:upload",
        ],
        "is_system_role": True,
    },
]
