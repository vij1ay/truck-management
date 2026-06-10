from datetime import date, timedelta
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentType, DocumentStatus, EntityType
from app.repositories.base import TenantAwareRepository


class DocumentRepository(TenantAwareRepository[Document]):
    """Repository for document data access."""

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(Document, db, tenant_id)

    def get_by_entity(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        include_deleted: bool = False,
    ) -> list[Document]:
        """Get all documents for a specific entity."""
        stmt = select(Document).where(
            and_(
                Document.entity_type == entity_type,
                Document.entity_id == entity_id,
            )
        )
        if not include_deleted:
            stmt = stmt.where(Document.is_deleted == False)
        stmt = self._apply_tenant_filter(stmt)
        stmt = stmt.order_by(Document.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_expiring_soon(self, days_threshold: int = 30) -> list[Document]:
        """Get documents expiring within the given number of days."""
        today = date.today()
        expiry_cutoff = today + timedelta(days=days_threshold)
        stmt = select(Document).where(
            and_(
                Document.is_deleted == False,
                Document.document_status == DocumentStatus.ACTIVE,
                Document.expiry_date != None,
                Document.expiry_date >= today,
                Document.expiry_date <= expiry_cutoff,
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        stmt = stmt.order_by(Document.expiry_date.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_expired(self) -> list[Document]:
        """Get documents that have passed their expiry date but are still ACTIVE."""
        today = date.today()
        stmt = select(Document).where(
            and_(
                Document.is_deleted == False,
                Document.document_status == DocumentStatus.ACTIVE,
                Document.expiry_date != None,
                Document.expiry_date < today,
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        return list(self.db.execute(stmt).scalars().all())

    def check_duplicate_type(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        document_type: DocumentType,
        exclude_id: UUID | None = None,
    ) -> bool:
        """Check if a document type already exists for this entity."""
        stmt = select(func.count()).select_from(Document).where(
            and_(
                Document.is_deleted == False,
                Document.entity_type == entity_type,
                Document.entity_id == entity_id,
                Document.document_type == document_type,
                Document.document_status != DocumentStatus.REJECTED,
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        if exclude_id:
            stmt = stmt.where(Document.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0

    def get_all_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        entity_type: EntityType | None = None,
        entity_id: UUID | None = None,
        document_type: DocumentType | None = None,
        document_status: DocumentStatus | None = None,
    ) -> list[Document]:
        """Get documents with optional filters."""
        stmt = select(Document).where(Document.is_deleted == False)
        stmt = self._apply_tenant_filter(stmt)

        if entity_type:
            stmt = stmt.where(Document.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(Document.entity_id == entity_id)
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if document_status:
            stmt = stmt.where(Document.document_status == document_status)

        stmt = stmt.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_filtered(
        self,
        entity_type: EntityType | None = None,
        entity_id: UUID | None = None,
        document_type: DocumentType | None = None,
        document_status: DocumentStatus | None = None,
    ) -> int:
        """Count documents matching filters."""
        stmt = select(func.count()).select_from(Document).where(Document.is_deleted == False)
        stmt = self._apply_tenant_filter(stmt)

        if entity_type:
            stmt = stmt.where(Document.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(Document.entity_id == entity_id)
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if document_status:
            stmt = stmt.where(Document.document_status == document_status)

        return self.db.execute(stmt).scalar_one()
