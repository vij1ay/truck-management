import enum
from sqlalchemy import Column, String, Boolean, Integer, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class SubscriptionTier(str, enum.Enum):
    trial = "trial"
    basic = "basic"
    premium = "premium"
    enterprise = "enterprise"


class Tenant(BaseModel):
    """Tenant model for multi-tenant architecture."""
    
    __tablename__ = "tenants"
    
    name = Column(String(255), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    subscription_tier = Column(
        Enum(SubscriptionTier),
        default=SubscriptionTier.trial,
        nullable=False
    )
    max_users = Column(Integer, default=10, nullable=False)
    settings = Column(JSONB, default=dict, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="tenant", lazy="dynamic")
    user_roles = relationship("UserRole", back_populates="tenant", lazy="dynamic")
    refresh_tokens = relationship("RefreshToken", back_populates="tenant", lazy="dynamic")
    audit_logs = relationship("AuditLog", back_populates="tenant", lazy="dynamic")
    trucks = relationship("Truck", back_populates="tenant", lazy="dynamic")
    drivers = relationship("Driver", back_populates="tenant", lazy="dynamic")
    clients = relationship("Client", back_populates="tenant", lazy="dynamic")
    loads = relationship("Load", back_populates="tenant", lazy="dynamic")

    def __repr__(self):
        return f"<Tenant {self.name}>"
