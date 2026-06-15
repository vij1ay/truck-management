import math
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.avatar_storage import read_avatar, save_avatar, validate_image
from app.core.exceptions import BadRequestException, NotFoundException
from app.core.logger import get_logger
from app.dependencies.auth import get_current_user_context, require_roles, CurrentUser
from app.dependencies.database import get_db
from app.middleware.tenant_context import get_client_ip
from app.models import DocumentType, EntityType
from app.models.load import GoodsType, LoadStatus
from app.schemas import (
    LoadCreate, LoadUpdate, LoadStatusTransition, LoadCancelRequest, LoadCheckpointRequest,
    LoadResponse, LoadListResponse, LoadHistoryResponse,
    DocumentCreate, DocumentResponse, DocumentListResponse,
)
from app.services import LoadService, DocumentService

router = APIRouter(prefix="/loads", tags=["Loads"])
logger = get_logger(__name__)


# ── Service factory ────────────────────────────────────────────────────────────

def get_load_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> LoadService:
    return LoadService(
        db=db,
        tenant_id=context.tenant_id,
        current_user_id=context.user_id,
        is_superadmin=context.is_superadmin,
        current_user_roles=context.roles,
    )


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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_response(load) -> LoadResponse:
    return LoadResponse(
        id=load.id,
        tenant_id=load.tenant_id,
        load_no=load.load_no,
        load_seq_no=load.load_seq_no,
        status=load.status,
        client_id=load.client_id,
        client_name=load.client.company_name if load.client else None,
        origin=load.origin,
        destination=load.destination,
        distance_km=load.distance_km,
        pickup_date=load.pickup_date,
        expected_delivery_date=load.expected_delivery_date,
        actual_delivery_date=load.actual_delivery_date,
        goods_type=load.goods_type,
        goods_description=load.goods_description,
        weight_kg=load.weight_kg,
        volume_cbm=load.volume_cbm,
        quantity=load.quantity,
        freight_amount=load.freight_amount,
        advance_amount=load.advance_amount,
        balance_amount=load.balance_amount,
        special_instructions=load.special_instructions,
        notes=load.notes,
        booked_by=load.booked_by,
        cancelled_by=load.cancelled_by,
        cancellation_reason=load.cancellation_reason,
        cancelled_at=load.cancelled_at,
        allocated_truck_id=load.allocated_truck_id,
        allocated_driver_id=load.allocated_driver_id,
        allocated_at=load.allocated_at,
        allocated_by=load.allocated_by,
        is_editable=load.is_editable,
        is_deletable=load.is_deletable,
        created_at=load.created_at,
        updated_at=load.updated_at,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=LoadListResponse)
async def list_loads(
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Client", "Driver")
    )],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: LoadStatus | None = None,
    client_id: UUID | None = None,
    goods_type: GoodsType | None = None,
    pickup_date_from: date | None = None,
    pickup_date_to: date | None = None,
    search: str | None = None,
    tenant_id: UUID | None = None,
):
    """List loads with optional filters (paginated)."""
    logger.info(
        f"List loads page={page} size={size} status={status} client_id={client_id} goods_type={goods_type} tenant_id={tenant_id}"
    )
    loads, total = service.get_loads(
        page=page, size=size, status=status, client_id=client_id,
        pickup_date_from=pickup_date_from, pickup_date_to=pickup_date_to,
        goods_type=goods_type.value if goods_type else None,
        search=search, tenant_id=tenant_id,
    )
    return LoadListResponse(
        items=[_to_response(l) for l in loads],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("", response_model=LoadResponse, status_code=201)
async def create_load(
    request: Request,
    data: LoadCreate,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Client")
    )],
):
    """Create a new load booking (status starts as DRAFT)."""
    logger.info(
        f"Create load request client_id={data.client_id} origin={data.origin} destination={data.destination}"
    )
    load = service.create_load(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@router.get("/{load_id}", response_model=LoadResponse)
async def get_load(
    load_id: UUID,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Client", "Driver")
    )],
):
    """Get a load by ID."""
    logger.info(f"Get load load_id={load_id}")
    load = service.get_load(load_id)
    return _to_response(load)


@router.patch("/{load_id}", response_model=LoadResponse)
async def update_load(
    request: Request,
    load_id: UUID,
    data: LoadUpdate,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
):
    """Update load metadata (only allowed for DRAFT and CONFIRMED loads)."""
    logger.info(f"Update load load_id={load_id}")
    load = service.update_load(
        load_id=load_id, data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@router.delete("/{load_id}", status_code=204)
async def delete_load(
    request: Request,
    load_id: UUID,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
):
    """
    Soft-delete a load. Requires TenantAdmin.
    Only DRAFT or CANCELLED loads can be deleted.
    """
    logger.info(f"Delete load load_id={load_id}")
    service.delete_load(
        load_id=load_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.post("/{load_id}/transition", response_model=LoadResponse)
async def transition_load_status(
    request: Request,
    load_id: UUID,
    data: LoadStatusTransition,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
):
    """
    Transition load status following the state machine:
    DRAFT → CONFIRMED → ALLOCATED → IN_TRANSIT → DELIVERED
    Any state (except terminal) can go to CANCELLED.
    IN_TRANSIT → CANCELLED requires TenantAdmin.
    """
    logger.info(f"Transition load load_id={load_id} to_status={data.to_status}")
    load = service.transition_status(
        load_id=load_id,
        to_status=data.to_status,
        remarks=data.remarks,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@router.post("/{load_id}/start-trip", response_model=LoadResponse)
async def start_trip(
    request: Request,
    load_id: UUID,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Driver")
    )],
):
    """Start trip (Driver workflow): Transition load from ALLOCATED to IN_TRANSIT."""
    logger.info(f"Start trip load_id={load_id}")
    load = service.transition_status(
        load_id=load_id,
        to_status=LoadStatus.IN_TRANSIT,
        remarks="Trip started by driver",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@router.post("/{load_id}/deliver", response_model=LoadResponse)
async def deliver_load(
    request: Request,
    load_id: UUID,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Driver")
    )],
):
    """Mark delivered (Driver workflow): Transition load from IN_TRANSIT to DELIVERED."""
    logger.info(f"Deliver load load_id={load_id}")
    load = service.transition_status(
        load_id=load_id,
        to_status=LoadStatus.DELIVERED,
        remarks="Delivered by driver",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@router.post("/{load_id}/cancel", response_model=LoadResponse)
async def cancel_load(
    request: Request,
    load_id: UUID,
    data: LoadCancelRequest,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
):
    """Cancel a load with a mandatory reason. IN_TRANSIT requires TenantAdmin."""
    logger.info(f"Cancel load load_id={load_id}")
    load = service.cancel_load(
        load_id=load_id, reason=data.reason,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@router.get("/{load_id}/history", response_model=list[LoadHistoryResponse])
async def get_load_history(
    load_id: UUID,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Driver")
    )],
):
    """Get the full status history trail for a load."""
    logger.info(f"Get load history load_id={load_id}")
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


@router.get("/{load_id}/documents", response_model=DocumentListResponse)
async def list_load_documents(
    load_id: UUID,
    service: Annotated[LoadService, Depends(get_load_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Driver")
    )],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """List documents (e.g. POD) attached to a load."""
    logger.info(f"List load documents load_id={load_id} page={page} size={size}")
    service.get_load(load_id)
    docs, total = doc_service.get_documents(
        page=page, size=size,
        entity_type=EntityType.LOAD,
        entity_id=load_id,
    )
    return DocumentListResponse(
        items=docs, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("/{load_id}/documents", response_model=DocumentResponse, status_code=201)
async def add_load_document(
    request: Request,
    load_id: UUID,
    data: DocumentCreate,
    service: Annotated[LoadService, Depends(get_load_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
):
    """Attach a document (e.g. POD) to a load."""
    service.get_load(load_id)

    if data.entity_id != load_id or data.entity_type != EntityType.LOAD:
        raise BadRequestException("entity_id and entity_type must match the load")

    logger.info(f"Add load document load_id={load_id} document_type={data.document_type}")
    return doc_service.create_document(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.post("/{load_id}/documents/pod", response_model=DocumentResponse, status_code=201)
async def upload_load_pod_photo(
    request: Request,
    load_id: UUID,
    service: Annotated[LoadService, Depends(get_load_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Driver")
    )],
    file: UploadFile = File(...),
):
    """Upload a Proof-of-Delivery photo for a load — Driver workflow (mirrors
    the Client Portal's document upload, `app/api/v1/portal.py:
    upload_my_load_document`, reusing the same image storage)."""
    service.get_load(load_id)

    content = await file.read()
    ext = validate_image(content, file.content_type)
    storage_path = save_avatar("load_documents", content, ext)

    logger.info(f"Upload POD photo load_id={load_id}")
    return doc_service.create_document(
        DocumentCreate(
            entity_type=EntityType.LOAD,
            entity_id=load_id,
            document_type=DocumentType.POD,
            file_name=file.filename or "pod.jpg",
            file_size_bytes=len(content),
            mime_type=file.content_type,
            storage_path=storage_path,
        ),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.get("/{load_id}/documents/{document_id}/file")
async def get_load_document_file(
    load_id: UUID,
    document_id: UUID,
    service: Annotated[LoadService, Depends(get_load_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Driver")
    )],
):
    """Image bytes for a load document uploaded via the app (e.g. a POD
    photo) — 404 if the document doesn't belong to this load or has no file."""
    service.get_load(load_id)

    doc = doc_service.get_document(document_id)
    if doc.entity_type != EntityType.LOAD or doc.entity_id != load_id or not doc.has_file:
        raise NotFoundException("Document not found")

    content, mime_type = read_avatar(doc.storage_path)
    return Response(content=content, media_type=mime_type)


@router.post("/{load_id}/checkpoints", response_model=LoadResponse)
async def add_load_checkpoint(
    request: Request,
    load_id: UUID,
    data: LoadCheckpointRequest,
    service: Annotated[LoadService, Depends(get_load_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Driver")
    )],
):
    """Record an informational checkpoint (e.g. "Reached Pickup", "Loaded") on
    a load's timeline — Driver workflow, no status change."""
    logger.info(f"Add load checkpoint load_id={load_id} label={data.label!r}")
    load = service.add_checkpoint(
        load_id=load_id, label=data.label,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)
