from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ForbiddenException,
)
from app.models import Document, DocumentStatus, EntityType, EventCategory
from app.repositories import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services.audit_service import AuditService


class DocumentService:
    """Service for document management across all entities."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID | None = None,
        current_user_id: UUID | None = None,
        is_superadmin: bool = False,
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.is_superadmin = is_superadmin
        self.doc_repo = DocumentRepository(db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    def get_document(self, document_id: UUID) -> Document:
        """Get a document by ID."""
        doc = self.doc_repo.get_active_by_id(document_id)
        if not doc:
            raise NotFoundException("Document not found")
        if not self.is_superadmin and doc.tenant_id != self.tenant_id:
            raise ForbiddenException("Cannot access document from another tenant")
        return doc

    def get_documents(
        self,
        page: int = 1,
        size: int = 50,
        entity_type: EntityType | None = None,
        entity_id: UUID | None = None,
        document_type=None,
        document_status: DocumentStatus | None = None,
    ) -> tuple[list[Document], int]:
        """Get paginated documents with optional filters."""
        skip = (page - 1) * size
        docs = self.doc_repo.get_all_filtered(
            skip=skip, limit=size,
            entity_type=entity_type, entity_id=entity_id,
            document_type=document_type, document_status=document_status,
        )
        total = self.doc_repo.count_filtered(
            entity_type=entity_type, entity_id=entity_id,
            document_type=document_type, document_status=document_status,
        )
        return docs, total

    def get_documents_for_entity(
        self, entity_type: EntityType, entity_id: UUID
    ) -> list[Document]:
        """Get all documents for a specific entity."""
        return self.doc_repo.get_by_entity(entity_type, entity_id)

    def create_document(
        self,
        data: DocumentCreate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Document:
        """Create a new document for an entity."""
        doc_data = data.model_dump()
        doc_data["uploaded_by"] = self.current_user_id

        # Auto-set document_status based on expiry
        if data.expiry_date and data.expiry_date < date.today():
            doc_data["document_status"] = DocumentStatus.EXPIRED
        else:
            doc_data["document_status"] = DocumentStatus.ACTIVE

        doc = self.doc_repo.create(doc_data)

        self.audit_service.log_event(
            event_type="DOCUMENT_CREATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Document",
            resource_id=doc.id,
            new_value={
                "entity_type": data.entity_type,
                "entity_id": str(data.entity_id),
                "document_type": data.document_type,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.doc_repo.get_active_by_id(doc.id)

    def update_document(
        self,
        document_id: UUID,
        data: DocumentUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Document:
        """Update a document's metadata."""
        doc = self.get_document(document_id)
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)

        # Recompute status if expiry_date changes
        expiry = update_data.get("expiry_date", doc.expiry_date)
        if expiry and "document_status" not in update_data:
            if expiry < date.today():
                update_data["document_status"] = DocumentStatus.EXPIRED
            else:
                update_data["document_status"] = DocumentStatus.ACTIVE

        self.doc_repo.update(doc, update_data)

        self.audit_service.log_event(
            event_type="DOCUMENT_UPDATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Document",
            resource_id=document_id,
            new_value=update_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.doc_repo.get_active_by_id(document_id)

    def delete_document(
        self,
        document_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Soft delete a document."""
        doc = self.get_document(document_id)
        self.doc_repo.soft_delete(doc)

        self.audit_service.log_event(
            event_type="DOCUMENT_DELETED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Document",
            resource_id=document_id,
            old_value={"is_deleted": False},
            new_value={"is_deleted": True},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()

    def get_expiring_documents(self, days_threshold: int = 30) -> list[Document]:
        """Get documents expiring within the given number of days."""
        if days_threshold < 1 or days_threshold > 365:
            raise BadRequestException("Days threshold must be between 1 and 365")
        return self.doc_repo.get_expiring_soon(days_threshold)
