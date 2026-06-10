from uuid import UUID

from pydantic import BaseModel


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    
    page: int = 1
    size: int = 50


class MessageResponse(BaseModel):
    """Generic message response."""
    
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error_code: str
    message: str
    details: dict | None = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    version: str = "0.1.0"
