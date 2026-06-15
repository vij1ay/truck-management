"""Customer (Client) Portal — Phase 11+.

Read/write API surface for users with the "Client" role. A shipper's portal login
can be linked to a `Client` (company) record — and therefore a separate
relationship — in MORE THAN ONE tenant (carrier). Endpoints here aggregate across
every linked relationship via `ClientRepository.get_all_by_user_id()`.
"""
import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, Query, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.loads import _to_response
from app.core.avatar_storage import read_avatar, save_avatar, validate_image
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.logger import get_logger
from app.dependencies.auth import get_current_user_context, require_roles, CurrentUser
from app.dependencies.database import get_db
from app.middleware.tenant_context import get_client_ip
from app.models import Client, DocumentType, EntityType, Invoice, Load, User
from app.models.invoice import InvoiceStatus
from app.models.load import LoadStatus
from app.repositories import ClientRepository
from app.schemas import (
    DocumentCreate, DocumentListResponse, DocumentResponse, InvoiceResponse,
    LoadCancelRequest, LoadCreate, LoadResponse,
    LoadHistoryResponse, LoadUpdate, PortalLoadCreate, PortalLoadResponse, PortalLoadListResponse,
    PortalCarrierLink, PortalProfileResponse, PortalInvoiceResponse, PortalInvoiceListResponse,
)
from app.services import DocumentService, InvoiceService, LoadService

router = APIRouter(prefix="/portal", tags=["Portal"])
logger = get_logger(__name__)


async def get_my_clients(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> list[Client]:
    """Resolve EVERY Client (company) record linked to the logged-in portal user,
    across all tenants — a shipper may have a separate relationship with more than
    one carrier."""
    clients = ClientRepository(db).get_all_by_user_id(context.user_id)
    if not clients:
        raise NotFoundException("No client profile linked to this account")
    return clients


def _client_for_tenant(clients: list[Client], tenant_id: UUID) -> Client | None:
    return next((c for c in clients if c.tenant_id == tenant_id), None)


@router.get("/me", response_model=PortalProfileResponse)
async def get_my_profile(
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
):
    """Every carrier (tenant) relationship linked to the logged-in user."""
    return PortalProfileResponse(
        carriers=[
            PortalCarrierLink(tenant_id=c.tenant_id, tenant_name=c.tenant.name, client=c)
            for c in clients
        ]
    )


@router.get("/loads", response_model=PortalLoadListResponse)
async def list_my_loads(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: LoadStatus | None = None,
):
    """My Shipments — paginated list aggregated across every linked carrier."""
    logger.info(f"Portal list loads user_id={context.user_id} page={page} size={size} status={status}")

    merged: list[PortalLoadResponse] = []
    for client in clients:
        service = LoadService(
            db, tenant_id=client.tenant_id,
            current_user_id=context.user_id, current_user_roles=["Client"],
        )
        loads, _total = service.get_loads(size=200, status=status, client_id=client.id)
        for load in loads:
            merged.append(PortalLoadResponse(
                **_to_response(load).model_dump(),
                carrier_name=client.tenant.name,
            ))

    merged.sort(key=lambda l: l.pickup_date, reverse=True)

    total = len(merged)
    start = (page - 1) * size
    items = merged[start:start + size]

    return PortalLoadListResponse(
        items=items, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("/loads", response_model=LoadResponse, status_code=201)
async def create_my_load(
    request: Request,
    data: PortalLoadCreate,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
):
    """Submit a new booking request to one of the shipper's linked carriers
    (`tenant_id`). `client_id` is forced to this user's linked client for that
    carrier."""
    client = _client_for_tenant(clients, data.tenant_id)
    if not client:
        raise ForbiddenException("You don't have a relationship with this carrier")

    logger.info(f"Portal create load tenant_id={data.tenant_id} client_id={client.id} origin={data.origin} destination={data.destination}")
    load_data = LoadCreate(**data.model_dump(exclude={"tenant_id"}), client_id=client.id)
    service = LoadService(
        db, tenant_id=data.tenant_id,
        current_user_id=context.user_id, current_user_roles=["Client"],
    )
    load = service.create_load(
        data=load_data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


def _resolve_load_service(
    db: Session, context: CurrentUser, clients: list[Client], load_id: UUID
) -> LoadService:
    """Find which linked carrier (tenant) owns `load_id` and return a LoadService
    scoped to it. Raises NotFoundException if it belongs to none of them."""
    client_ids = [c.id for c in clients]
    row = db.execute(
        select(Load.tenant_id).where(
            Load.id == load_id,
            Load.client_id.in_(client_ids),
            Load.is_deleted == False,  # noqa: E712
        )
    ).first()
    if not row:
        raise NotFoundException("Load not found")

    return LoadService(
        db, tenant_id=row.tenant_id,
        current_user_id=context.user_id, current_user_roles=["Client"],
    )


@router.get("/loads/{load_id}", response_model=LoadResponse)
async def get_my_load(
    load_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
):
    """Shipment detail — 404 if this load doesn't belong to any of the caller's linked clients."""
    service = _resolve_load_service(db, context, clients, load_id)
    load = service.get_load(load_id)
    return _to_response(load)


@router.patch("/loads/{load_id}", response_model=LoadResponse)
async def update_my_load(
    request: Request,
    load_id: UUID,
    data: LoadUpdate,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
):
    """Edit a shipment request — 404 if it doesn't belong to any of the
    caller's linked clients; 400 if it's no longer DRAFT/CONFIRMED
    (`LoadService.update_load`'s `is_editable` check)."""
    service = _resolve_load_service(db, context, clients, load_id)
    load = service.update_load(
        load_id=load_id, data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@router.post("/loads/{load_id}/cancel", response_model=LoadResponse)
async def cancel_my_load(
    request: Request,
    load_id: UUID,
    data: LoadCancelRequest,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
):
    """Cancel a shipment request with a mandatory reason — 404 if it doesn't
    belong to any of the caller's linked clients. An IN_TRANSIT shipment
    requires carrier (TenantAdmin) approval and can't be cancelled here
    (`LoadService.cancel_load` raises 403)."""
    service = _resolve_load_service(db, context, clients, load_id)
    load = service.cancel_load(
        load_id=load_id, reason=data.reason,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@router.get("/loads/{load_id}/history", response_model=list[LoadHistoryResponse])
async def get_my_load_history(
    load_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
):
    """Status timeline for a shipment."""
    service = _resolve_load_service(db, context, clients, load_id)
    history = service.get_load_history(load_id)
    return [
        LoadHistoryResponse(
            id=h.id,
            load_id=h.load_id,
            from_status=h.from_status,
            to_status=h.to_status,
            changed_by=h.changed_by,
            remarks=h.remarks,
            changed_at=h.changed_at,
        )
        for h in history
    ]


@router.get("/loads/{load_id}/documents", response_model=DocumentListResponse)
async def get_my_load_documents(
    load_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """Documents (e.g. POD) attached to a shipment — 404 if not one of the caller's shipments."""
    service = _resolve_load_service(db, context, clients, load_id)
    service.get_load(load_id)

    doc_service = DocumentService(
        db, tenant_id=service.tenant_id,
        current_user_id=context.user_id, is_superadmin=False,
    )
    docs, total = doc_service.get_documents(
        page=page, size=size,
        entity_type=EntityType.LOAD,
        entity_id=load_id,
    )
    return DocumentListResponse(
        items=docs, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("/loads/{load_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_my_load_document(
    request: Request,
    load_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
    file: UploadFile = File(...),
):
    """Attach a photo (e.g. of a packing list or customs document) to a
    shipment — 404 if it doesn't belong to any of the caller's linked clients.
    Reuses the avatar/truck-photo image storage (`app/core/avatar_storage.py`,
    `entity_type="load_documents"`)."""
    service = _resolve_load_service(db, context, clients, load_id)
    service.get_load(load_id)

    content = await file.read()
    ext = validate_image(content, file.content_type)
    storage_path = save_avatar("load_documents", content, ext)

    doc_service = DocumentService(
        db, tenant_id=service.tenant_id,
        current_user_id=context.user_id, is_superadmin=False,
    )
    doc = doc_service.create_document(
        DocumentCreate(
            entity_type=EntityType.LOAD,
            entity_id=load_id,
            document_type=DocumentType.OTHER,
            file_name=file.filename or "document.jpg",
            file_size_bytes=len(content),
            mime_type=file.content_type,
            storage_path=storage_path,
        ),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return doc


@router.get("/loads/{load_id}/documents/{document_id}/file")
async def get_my_load_document_file(
    load_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
):
    """Image bytes for a shipment document uploaded via the Client Portal —
    404 if the shipment isn't one of the caller's, the document doesn't
    belong to this shipment, or it has no uploaded file."""
    service = _resolve_load_service(db, context, clients, load_id)
    service.get_load(load_id)

    doc_service = DocumentService(
        db, tenant_id=service.tenant_id,
        current_user_id=context.user_id, is_superadmin=False,
    )
    doc = doc_service.get_document(document_id)
    if doc.entity_type != EntityType.LOAD or doc.entity_id != load_id or not doc.has_file:
        raise NotFoundException("Document not found")

    content, mime_type = read_avatar(doc.storage_path)
    return Response(content=content, media_type=mime_type)


@router.get("/invoices", response_model=PortalInvoiceListResponse)
async def list_my_invoices(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: InvoiceStatus | None = None,
):
    """My Invoices — paginated list aggregated across every linked carrier."""
    logger.info(f"Portal list invoices user_id={context.user_id} page={page} size={size} status={status}")

    merged: list[PortalInvoiceResponse] = []
    for client in clients:
        service = InvoiceService(db, tenant_id=client.tenant_id, current_user_id=context.user_id)
        invoices, _total = service.get_invoices(size=200, status=status, client_id=client.id)
        for inv in invoices:
            merged.append(PortalInvoiceResponse(
                **InvoiceResponse.model_validate(inv).model_dump(),
                carrier_name=client.tenant.name,
            ))

    merged.sort(key=lambda i: i.issued_date, reverse=True)

    total = len(merged)
    start = (page - 1) * size
    items = merged[start:start + size]

    return PortalInvoiceListResponse(
        items=items, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.get("/invoices/{invoice_id}/pdf")
async def download_my_invoice_pdf(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("Client"))],
    clients: Annotated[list[Client], Depends(get_my_clients)],
):
    """Download an invoice PDF — 404 if it doesn't belong to any of the caller's linked clients."""
    client_ids = [c.id for c in clients]
    row = db.execute(
        select(Invoice.tenant_id).where(
            Invoice.id == invoice_id,
            Invoice.client_id.in_(client_ids),
            Invoice.is_deleted == False,  # noqa: E712
        )
    ).first()
    if not row:
        raise NotFoundException("Invoice not found")

    service = InvoiceService(db, tenant_id=row.tenant_id, current_user_id=context.user_id)
    inv = service.get_invoice(invoice_id)
    pdf_bytes = service.generate_pdf(invoice_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{inv.invoice_no}.pdf"'},
    )
