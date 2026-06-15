from datetime import date
from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel, field_validator, model_validator

from app.models.document import DocumentType, DocumentStatus, EntityType
from app.schemas.common import LocalDateTime


class DocumentCreate(BaseModel):
    entity_type: EntityType
    entity_id: UUID
    document_type: DocumentType
    file_name: str
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None
    storage_path: Optional[str] = None

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("File name cannot be empty")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "DocumentCreate":
        if self.issue_date and self.expiry_date:
            if self.expiry_date <= self.issue_date:
                raise ValueError("Expiry date must be after issue date")
        return self


class DocumentUpdate(BaseModel):
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    document_status: Optional[DocumentStatus] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "DocumentUpdate":
        if self.issue_date and self.expiry_date:
            if self.expiry_date <= self.issue_date:
                raise ValueError("Expiry date must be after issue date")
        return self


class DocumentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    entity_type: EntityType
    entity_id: UUID
    document_type: DocumentType
    document_status: DocumentStatus
    file_name: str
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_expired: bool
    days_until_expiry: Optional[int] = None
    uploaded_by: Optional[UUID] = None
    notes: Optional[str] = None
    has_file: bool = False
    created_at: LocalDateTime
    updated_at: LocalDateTime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int


class ExpiringDocumentResponse(BaseModel):
    """Used for documents expiring within N days."""
    items: List[DocumentResponse]
    days_threshold: int
    total: int
