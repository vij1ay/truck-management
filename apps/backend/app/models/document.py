import enum
from datetime import date
from sqlalchemy import Column, String, Date, BigInteger, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DocumentType(str, enum.Enum):
    RC_BOOK = "rc_book"
    INSURANCE = "insurance"
    FITNESS = "fitness"
    POLLUTION = "pollution"
    PERMIT = "permit"
    DRIVER_LICENSE = "driver_license"
    MEDICAL = "medical"
    CONTRACT = "contract"
    POD = "pod"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"
    REJECTED = "rejected"


class EntityType(str, enum.Enum):
    TRUCK = "truck"
    DRIVER = "driver"
    CLIENT = "client"
    LOAD = "load"


class Document(BaseModel):
    """Document model - shared sub-resource for trucks, drivers, and clients."""

    __tablename__ = "documents"

    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Polymorphic association (entity type + entity id)
    entity_type = Column(SAEnum(EntityType, name="entitytype", values_callable=lambda obj: [e.value for e in obj]), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Document classification
    document_type = Column(SAEnum(DocumentType, name="documenttype", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    document_status = Column(
        SAEnum(DocumentStatus, name="documentstatus", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DocumentStatus.ACTIVE
    )

    # File metadata
    file_url = Column(String(1024), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Relative path under UPLOAD_DIR for files uploaded via the app (e.g. the
    # Client Portal's "Upload Document" — see `app/core/avatar_storage.py`,
    # `save_avatar("load_documents", ...)`). Distinct from `file_url`, which is
    # an admin-entered external link and never written by upload endpoints.
    # Never serialized directly — only via `has_file` (mirrors `avatar_path`).
    storage_path = Column(String(512), nullable=True)

    # Validity
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)

    # Uploaded by user
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    tenant = relationship("Tenant")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<Document {self.document_type} for {self.entity_type}:{self.entity_id}>"

    @property
    def has_file(self) -> bool:
        """Whether a file was uploaded for this document (vs. metadata-only)."""
        return bool(self.storage_path)

    @property
    def is_expired(self) -> bool:
        """Check if the document has expired."""
        if self.expiry_date is None:
            return False
        return self.expiry_date < date.today()

    @property
    def days_until_expiry(self) -> int | None:
        """Return days remaining until expiry, None if no expiry date."""
        if self.expiry_date is None:
            return None
        delta = self.expiry_date - date.today()
        return delta.days

    def update_status(self) -> None:
        """Auto-update document status based on expiry."""
        if self.is_expired and self.document_status == DocumentStatus.ACTIVE:
            self.document_status = DocumentStatus.EXPIRED
