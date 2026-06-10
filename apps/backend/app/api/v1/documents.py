import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.dependencies.auth import get_current_user_context, require_roles, CurrentUser
from app.dependencies.database import get_db
from app.middleware.tenant_context import get_client_ip
from app.models import User, DocumentType, DocumentStatus, EntityType
from app.schemas import (
    DocumentUpdate, DocumentResponse, DocumentListResponse, ExpiringDocumentResponse,
)
from app.services import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = get_logger(__name__)


def get_doc_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> DocumentService:
    return DocumentService(
        db=db,
        tenant_id=context.tenant_id,
        current_user_id=context.user_id,
        is_superadmin=context.is_superadmin,
    )


@router.get("/expiring", response_model=ExpiringDocumentResponse)
async def get_expiring_documents(
    service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
    days: int = Query(30, ge=1, le=365, description="Days threshold for expiry check"),
):
    """Get all documents expiring within the specified number of days."""
    logger.info(f"List expiring documents days={days}")
    docs = service.get_expiring_documents(days_threshold=days)
    return ExpiringDocumentResponse(
        items=docs, days_threshold=days, total=len(docs),
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    entity_type: EntityType | None = None,
    entity_id: UUID | None = None,
    document_type: DocumentType | None = None,
    document_status: DocumentStatus | None = None,
):
    """List documents with optional filters (paginated)."""
    logger.info(
        f"List documents page={page} size={size} entity_type={entity_type} entity_id={entity_id} type={document_type} status={document_status}"
    )
    docs, total = service.get_documents(
        page=page, size=size,
        entity_type=entity_type, entity_id=entity_id,
        document_type=document_type, document_status=document_status,
    )
    return DocumentListResponse(
        items=docs, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
):
    """Get a document by ID."""
    logger.info(f"Get document document_id={document_id}")
    return service.get_document(document_id)


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    request: Request,
    document_id: UUID,
    data: DocumentUpdate,
    service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Update document metadata (file info, dates, status)."""
    logger.info(f"Update document document_id={document_id}")
    return service.update_document(
        document_id=document_id, data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    request: Request,
    document_id: UUID,
    service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
):
    """Soft delete a document."""
    logger.info(f"Delete document document_id={document_id}")
    service.delete_document(
        document_id=document_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
