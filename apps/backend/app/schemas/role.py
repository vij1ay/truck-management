from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """Base role schema."""
    
    name: str = Field(..., min_length=2, max_length=50)
    description: str | None = Field(None, max_length=500)
    permissions: list[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    """Schema for creating a new role."""
    pass


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    
    description: str | None = Field(None, max_length=500)
    permissions: list[str] | None = None


class RoleResponse(RoleBase):
    """Full role response schema."""
    
    id: UUID
    is_system_role: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class RoleListResponse(BaseModel):
    """List of roles."""
    
    items: list[RoleResponse]
    total: int


class RoleAssignmentRequest(BaseModel):
    """Request to assign a role to a user."""
    
    user_id: UUID
    role_id: UUID
    expires_at: datetime | None = None


class RoleAssignmentResponse(BaseModel):
    """Response for role assignment."""
    
    id: UUID
    user_id: UUID
    role_id: UUID
    role_name: str
    tenant_id: UUID | None = None
    assigned_at: datetime
    expires_at: datetime | None = None
    
    model_config = {"from_attributes": True}
