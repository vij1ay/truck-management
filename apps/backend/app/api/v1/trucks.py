import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query, UploadFile, File, Response
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException
from app.core.logger import get_logger
from app.dependencies.auth import get_current_user_context, require_roles, CurrentUser
from app.dependencies.database import get_db
from app.middleware.tenant_context import get_client_ip
from app.models import User, Truck, TruckType, TruckStatus, OwnershipType, EntityType
from app.repositories import DriverRepository
from app.schemas import (
    TruckCreate, TruckUpdate, TruckResponse, TruckListResponse, TruckPhotoResponse,
    DocumentCreate, DocumentResponse, DocumentListResponse, MessageResponse,
)
from app.services import TruckService, DocumentService

router = APIRouter(prefix="/trucks", tags=["Trucks"])
logger = get_logger(__name__)


def get_truck_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> TruckService:
    return TruckService(
        db=db,
        tenant_id=context.tenant_id,
        current_user_id=context.user_id,
        is_superadmin=context.is_superadmin,
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


@router.get("", response_model=TruckListResponse)
async def list_trucks(
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: TruckStatus | None = None,
    truck_type: TruckType | None = None,
    ownership_type: OwnershipType | None = None,
    is_available: bool | None = None,
    search: str | None = None,
    tenant_id: UUID | None = None,
):
    """List trucks with optional filters (paginated)."""
    logger.info(
        f"List trucks page={page} size={size} status={status} type={truck_type} ownership={ownership_type} available={is_available} tenant_id={tenant_id}"
    )
    trucks, total = service.get_trucks(
        page=page, size=size, status=status,
        truck_type=truck_type, ownership_type=ownership_type,
        is_available=is_available, search=search, tenant_id=tenant_id,
    )
    return TruckListResponse(
        items=[_to_response(t) for t in trucks],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("", response_model=TruckResponse, status_code=201)
async def create_truck(
    request: Request,
    data: TruckCreate,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Create a new truck."""
    logger.info(f"Create truck registration_no={data.registration_no}")
    truck = service.create_truck(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(truck)


@router.get("/{truck_id}", response_model=TruckResponse)
async def get_truck(
    truck_id: UUID,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
):
    """Get a truck by ID."""
    logger.info(f"Get truck truck_id={truck_id}")
    truck = service.get_truck(truck_id)
    return _to_response(truck)


@router.patch("/{truck_id}", response_model=TruckResponse)
async def update_truck(
    request: Request,
    truck_id: UUID,
    data: TruckUpdate,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Update a truck."""
    logger.info(f"Update truck truck_id={truck_id}")
    truck = service.update_truck(
        truck_id=truck_id, data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(truck)


@router.post("/{truck_id}/avatar", response_model=TruckResponse)
async def upload_truck_avatar(
    request: Request,
    truck_id: UUID,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
    file: Annotated[UploadFile, File()],
):
    """Upload (or replace) a truck's profile picture."""
    logger.info(f"Upload avatar truck_id={truck_id}")
    content = await file.read()
    truck = service.upload_avatar(
        truck_id=truck_id,
        content=content,
        content_type=file.content_type,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(truck)


@router.delete("/{truck_id}/avatar", response_model=TruckResponse)
async def remove_truck_avatar(
    request: Request,
    truck_id: UUID,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Remove a truck's profile picture."""
    logger.info(f"Remove avatar truck_id={truck_id}")
    truck = service.remove_avatar(
        truck_id=truck_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(truck)


@router.get("/{truck_id}/avatar")
async def get_truck_avatar(
    truck_id: UUID,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
):
    """Return a truck's profile picture (404 if none set)."""
    content, mime_type = service.get_avatar(truck_id)
    return Response(content=content, media_type=mime_type)


def _check_driver_truck_access(
    truck_id: UUID,
    context: CurrentUser,
    db: Session,
) -> None:
    """A Driver may only view photos for the truck currently assigned to them
    (Truck.assigned_driver_id). Admin/Accounts roles are unrestricted (already
    tenant-scoped via TruckService.get_truck)."""
    if context.is_superadmin or any(
        r in context.roles for r in ("TenantAdmin", "TransportAdmin", "Accounts")
    ):
        return

    driver_repo = DriverRepository(db, context.tenant_id)
    driver = driver_repo.get_by_user_id(context.user_id)
    if not driver or not any(t.id == truck_id for t in driver.trucks):
        raise ForbiddenException("Cannot access photos for this truck")


@router.get("/{truck_id}/photos", response_model=list[TruckPhotoResponse])
async def list_truck_photos(
    truck_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[TruckService, Depends(get_truck_service)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Driver"))],
):
    """List a truck's photo gallery (up to 6 photos)."""
    _check_driver_truck_access(truck_id, context, db)
    return service.list_photos(truck_id)


@router.post("/{truck_id}/photos", response_model=TruckPhotoResponse, status_code=201)
async def upload_truck_photo(
    request: Request,
    truck_id: UUID,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
    file: Annotated[UploadFile, File()],
):
    """Add a photo to a truck's gallery (max 6 photos)."""
    logger.info(f"Upload photo truck_id={truck_id}")
    content = await file.read()
    return service.upload_photo(
        truck_id=truck_id,
        content=content,
        content_type=file.content_type,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.delete("/{truck_id}/photos/{photo_id}", status_code=204)
async def remove_truck_photo(
    request: Request,
    truck_id: UUID,
    photo_id: UUID,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Remove a photo from a truck's gallery."""
    logger.info(f"Remove photo truck_id={truck_id} photo_id={photo_id}")
    service.remove_photo(
        truck_id=truck_id,
        photo_id=photo_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.get("/{truck_id}/photos/{photo_id}")
async def get_truck_photo(
    truck_id: UUID,
    photo_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[TruckService, Depends(get_truck_service)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Driver"))],
):
    """Return one of a truck's gallery photos."""
    _check_driver_truck_access(truck_id, context, db)
    content, mime_type = service.get_photo(truck_id, photo_id)
    return Response(content=content, media_type=mime_type)


@router.delete("/{truck_id}", status_code=204)
async def delete_truck(
    request: Request,
    truck_id: UUID,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
):
    """Soft delete a truck. Requires TenantAdmin."""
    logger.info(f"Delete truck truck_id={truck_id}")
    service.delete_truck(
        truck_id=truck_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.post("/{truck_id}/activate", response_model=TruckResponse)
async def activate_truck(
    request: Request,
    truck_id: UUID,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
):
    """Activate a truck."""
    logger.info(f"Activate truck truck_id={truck_id}")
    truck = service.activate_truck(
        truck_id=truck_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(truck)


@router.post("/{truck_id}/deactivate", response_model=TruckResponse)
async def deactivate_truck(
    request: Request,
    truck_id: UUID,
    service: Annotated[TruckService, Depends(get_truck_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
):
    """Deactivate a truck."""
    logger.info(f"Deactivate truck truck_id={truck_id}")
    truck = service.deactivate_truck(
        truck_id=truck_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(truck)


@router.get("/{truck_id}/documents", response_model=DocumentListResponse)
async def list_truck_documents(
    truck_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[TruckService, Depends(get_truck_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Driver"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """List all documents for a specific truck — a Driver may only list
    documents for the truck currently assigned to them."""
    logger.info(f"List truck documents truck_id={truck_id} page={page} size={size}")
    # Validate truck exists
    service.get_truck(truck_id)
    _check_driver_truck_access(truck_id, context, db)

    docs, total = doc_service.get_documents(
        page=page, size=size,
        entity_type=EntityType.TRUCK,
        entity_id=truck_id,
    )
    return DocumentListResponse(
        items=docs, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("/{truck_id}/documents", response_model=DocumentResponse, status_code=201)
async def add_truck_document(
    request: Request,
    truck_id: UUID,
    data: DocumentCreate,
    service: Annotated[TruckService, Depends(get_truck_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Upload/add a document for a truck."""
    from app.core.exceptions import BadRequestException

    # Validate truck exists
    service.get_truck(truck_id)

    # Enforce entity association
    if data.entity_id != truck_id or data.entity_type != EntityType.TRUCK:
        raise BadRequestException("entity_id and entity_type must match the truck")

    logger.info(f"Add truck document truck_id={truck_id} document_type={data.document_type}")
    doc = doc_service.create_document(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return doc


def _to_response(truck: Truck) -> TruckResponse:
    return TruckResponse(
        id=truck.id,
        tenant_id=truck.tenant_id,
        registration_no=truck.registration_no,
        ownership_type=truck.ownership_type,
        truck_type=truck.truck_type,
        status=truck.status,
        is_available=truck.is_available,
        make=truck.make,
        model=truck.model,
        year=truck.year,
        color=truck.color,
        capacity_tons=truck.capacity_tons,
        assigned_driver_id=truck.assigned_driver_id,
        owner_name=truck.owner_name,
        owner_contact=truck.owner_contact,
        contractor_name=truck.contractor_name,
        contractor_contact=truck.contractor_contact,
        contract_start_date=truck.contract_start_date,
        contract_end_date=truck.contract_end_date,
        lessor_name=truck.lessor_name,
        lessor_contact=truck.lessor_contact,
        lease_start_date=truck.lease_start_date,
        lease_end_date=truck.lease_end_date,
        notes=truck.notes,
        is_operational=truck.is_operational,
        has_avatar=truck.has_avatar,
        created_at=truck.created_at,
        updated_at=truck.updated_at,
    )
