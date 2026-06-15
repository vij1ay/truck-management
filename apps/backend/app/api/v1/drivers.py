import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException
from app.core.logger import get_logger
from app.dependencies.auth import get_current_user_context, require_roles, CurrentUser
from app.dependencies.database import get_db
from app.middleware.tenant_context import get_client_ip
from app.models import User, Driver, DriverStatus, EntityType
from app.repositories import DriverRepository
from app.schemas import (
    DriverCreate, DriverUpdate, DriverResponse, DriverMeResponse, DriverListResponse,
    DriverAvailabilityUpdate,
    DocumentCreate, DocumentResponse, DocumentListResponse, TruckBasic,
)
from app.schemas.driver import DriverLocationUpdate, AssignedTruckBasic
from app.services import DriverService, DocumentService

router = APIRouter(prefix="/drivers", tags=["Drivers"])
logger = get_logger(__name__)


def get_driver_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> DriverService:
    return DriverService(
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


@router.get("", response_model=DriverListResponse)
async def list_drivers(
    service: Annotated[DriverService, Depends(get_driver_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: DriverStatus | None = None,
    is_available: bool | None = None,
    search: str | None = None,
    tenant_id: UUID | None = None,
):
    """List drivers with optional filters (paginated)."""
    logger.info(
        f"List drivers page={page} size={size} status={status} available={is_available} tenant_id={tenant_id}"
    )
    drivers, total = service.get_drivers(
        page=page, size=size, status=status,
        is_available=is_available, search=search, tenant_id=tenant_id,
    )
    return DriverListResponse(
        items=[_to_response(d) for d in drivers],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("", response_model=DriverResponse, status_code=201)
async def create_driver(
    request: Request,
    data: DriverCreate,
    service: Annotated[DriverService, Depends(get_driver_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Create a new driver."""
    logger.info(f"Create driver name={data.first_name} {data.last_name}")
    driver = service.create_driver(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(driver)


@router.get("/me", response_model=DriverMeResponse)
async def get_my_driver_profile(
    service: Annotated[DriverService, Depends(get_driver_service)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
):
    """
    Get the driver profile linked to the current login.

    Used by the mobile driver app's Profile / Vehicle Info screens. 404 if this
    account has no linked Driver record.
    """
    logger.info(f"Get my driver profile user_id={context.user_id}")
    driver = service.get_driver_by_user_id(context.user_id)
    return _to_me_response(driver)


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: UUID,
    service: Annotated[DriverService, Depends(get_driver_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
):
    """Get a driver by ID."""
    logger.info(f"Get driver driver_id={driver_id}")
    driver = service.get_driver(driver_id)
    return _to_response(driver)


@router.patch("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    request: Request,
    driver_id: UUID,
    data: DriverUpdate,
    service: Annotated[DriverService, Depends(get_driver_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Update a driver."""
    logger.info(f"Update driver driver_id={driver_id}")
    driver = service.update_driver(
        driver_id=driver_id, data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(driver)


@router.delete("/{driver_id}", status_code=204)
async def delete_driver(
    request: Request,
    driver_id: UUID,
    service: Annotated[DriverService, Depends(get_driver_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
):
    """Soft delete a driver. Requires TenantAdmin."""
    logger.info(f"Delete driver driver_id={driver_id}")
    service.delete_driver(
        driver_id=driver_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.post("/{driver_id}/toggle-availability", response_model=DriverResponse)
async def toggle_driver_availability(
    request: Request,
    driver_id: UUID,
    data: DriverAvailabilityUpdate,
    service: Annotated[DriverService, Depends(get_driver_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Toggle driver availability.

    - Cannot set available if license is expired.
    - Cannot set available if driver is BLACKLISTED or INACTIVE.
    """
    logger.info(f"Toggle driver availability driver_id={driver_id} available={data.is_available}")
    driver = service.toggle_availability(
        driver_id=driver_id, data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(driver)


@router.patch("/{driver_id}/location", response_model=DriverResponse)
async def update_driver_location(
    driver_id: UUID,
    data: DriverLocationUpdate,
    service: Annotated[DriverService, Depends(get_driver_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Driver"))],
):
    """Update driver GPS coordinates and/or base location.
    
    Can be called by the driver themselves or by any admin.
    Stores lat/lon for future real-time location tracking.
    """
    logger.info(f"Update driver location driver_id={driver_id}")
    driver = service.update_location(driver_id=driver_id, data=data)
    return _to_response(driver)


def _check_driver_self_access(
    driver_id: UUID,
    context: CurrentUser,
    db: Session,
) -> None:
    """A Driver may only view their own documents (Driver.user_id ==
    context.user_id). Admin/Accounts roles are unrestricted (already
    tenant-scoped via DriverService.get_driver)."""
    if context.is_superadmin or any(
        r in context.roles for r in ("TenantAdmin", "TransportAdmin", "Accounts")
    ):
        return

    driver_repo = DriverRepository(db, context.tenant_id)
    driver = driver_repo.get_by_user_id(context.user_id)
    if not driver or driver.id != driver_id:
        raise ForbiddenException("Cannot access documents for this driver")


@router.get("/{driver_id}/documents", response_model=DocumentListResponse)
async def list_driver_documents(
    driver_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[DriverService, Depends(get_driver_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Driver"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """List all documents for a specific driver — a Driver may only list
    their own documents."""
    logger.info(f"List driver documents driver_id={driver_id} page={page} size={size}")
    service.get_driver(driver_id)
    _check_driver_self_access(driver_id, context, db)
    docs, total = doc_service.get_documents(
        page=page, size=size,
        entity_type=EntityType.DRIVER,
        entity_id=driver_id,
    )
    return DocumentListResponse(
        items=docs, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("/{driver_id}/documents", response_model=DocumentResponse, status_code=201)
async def add_driver_document(
    request: Request,
    driver_id: UUID,
    data: DocumentCreate,
    service: Annotated[DriverService, Depends(get_driver_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Upload/add a document for a driver."""
    from app.core.exceptions import BadRequestException

    service.get_driver(driver_id)

    if data.entity_id != driver_id or data.entity_type != EntityType.DRIVER:
        raise BadRequestException("entity_id and entity_type must match the driver")

    logger.info(f"Add driver document driver_id={driver_id} document_type={data.document_type}")
    return doc_service.create_document(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


def _to_response(driver: Driver) -> DriverResponse:
    return DriverResponse(
        id=driver.id,
        tenant_id=driver.tenant_id,
        employee_id=driver.employee_id,
        first_name=driver.first_name,
        last_name=driver.last_name,
        full_name=driver.full_name,
        phone=driver.phone,
        email=driver.email,
        address=driver.address,
        license_no=driver.license_no,
        license_class=driver.license_class,
        license_expiry=driver.license_expiry,
        status=driver.status,
        is_available=driver.is_available,
        is_license_valid=driver.is_license_valid,
        is_allocatable=driver.is_allocatable,
        base_location=driver.base_location,
        current_lat=driver.current_lat,
        current_lon=driver.current_lon,
        assigned_trucks=[
            AssignedTruckBasic(
                id=t.id,
                registration_no=t.registration_no,
                truck_type=t.truck_type
            ) for t in (driver.assigned_trucks or [])
        ],
        emergency_contact_name=driver.emergency_contact_name,
        emergency_contact_phone=driver.emergency_contact_phone,
        notes=driver.notes,
        created_at=driver.created_at,
        updated_at=driver.updated_at,
    )


def _to_me_response(driver: Driver) -> DriverMeResponse:
    """DriverResponse fields plus the truck currently assigned to this driver."""
    current_truck = driver.trucks[0] if driver.trucks else None
    return DriverMeResponse(
        **_to_response(driver).model_dump(),
        current_truck=TruckBasic(
            id=current_truck.id,
            registration_no=current_truck.registration_no,
            make=current_truck.make,
            model=current_truck.model,
            has_avatar=current_truck.has_avatar,
        ) if current_truck else None,
    )
