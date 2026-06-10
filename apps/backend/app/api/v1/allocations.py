from datetime import date
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.dependencies.auth import get_current_user_context, require_roles, CurrentUser
from app.dependencies.database import get_db
from app.middleware.tenant_context import get_client_ip
from app.schemas.allocation import (
    AllocationCreate, AllocationUpdate, DeallocationRequest,
    AllocationResponse, AvailableTrucksResponse, AvailableDriversResponse,
    AvailableTruckItem, AvailableDriverItem,
)
from app.services import AllocationService

router = APIRouter(tags=["Allocations"])
logger = get_logger(__name__)


# ── Service factory ────────────────────────────────────────────────────────────

def get_allocation_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> AllocationService:
    return AllocationService(
        db=db,
        tenant_id=context.tenant_id,
        current_user_id=context.user_id,
        is_superadmin=context.is_superadmin,
        current_user_roles=context.roles,
    )


# ── Response converters ────────────────────────────────────────────────────────

def _to_alloc_response(alloc) -> AllocationResponse:
    return AllocationResponse(
        id=alloc.id,
        load_id=alloc.load_id,
        truck_id=alloc.truck_id,
        driver_id=alloc.driver_id,
        pickup_date=alloc.pickup_date,
        effective_delivery_date=alloc.effective_delivery_date,
        is_active=alloc.is_active,
        allocated_by=alloc.allocated_by,
        deactivated_at=alloc.deactivated_at,
        deactivated_by=alloc.deactivated_by,
        notes=alloc.notes,
        created_at=alloc.created_at,
    )


# ── Allocation endpoints (nested under loads) ─────────────────────────────────

loads_sub = APIRouter(prefix="/loads/{load_id}", tags=["Allocations"])


@loads_sub.post("/allocate", status_code=200)
async def allocate_load(
    request: Request,
    load_id: UUID,
    data: AllocationCreate,
    service: Annotated[AllocationService, Depends(get_allocation_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
):
    """
    Assign truck + driver to a CONFIRMED load.
    Transitions load → ALLOCATED.
    Both truck and driver must be available and conflict-free.
    """
    from app.schemas.load import LoadResponse
    from app.api.v1.loads import _to_response

    logger.info(
        f"Allocate load load_id={load_id} truck_id={data.truck_id} driver_id={data.driver_id}"
    )

    load = service.allocate(
        load_id=load_id,
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@loads_sub.put("/allocate", status_code=200)
async def reallocate_load(
    request: Request,
    load_id: UUID,
    data: AllocationUpdate,
    service: Annotated[AllocationService, Depends(get_allocation_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
):
    """
    Swap truck/driver on an ALLOCATED load (e.g. breakdown recovery).
    Old allocation is deactivated. Load stays ALLOCATED.
    """
    from app.api.v1.loads import _to_response

    logger.info(
        f"Reallocate load load_id={load_id} truck_id={data.truck_id} driver_id={data.driver_id}"
    )

    load = service.reallocate(
        load_id=load_id,
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@loads_sub.delete("/allocate", status_code=200)
async def deallocate_load(
    request: Request,
    load_id: UUID,
    service: Annotated[AllocationService, Depends(get_allocation_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
    data: DeallocationRequest = DeallocationRequest(),
):
    """
    Remove allocation. Reverts load to CONFIRMED.
    Restores truck and driver availability.
    """
    from app.api.v1.loads import _to_response

    logger.info(f"Deallocate load load_id={load_id}")

    load = service.deallocate(
        load_id=load_id,
        reason=data.reason if data else None,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return _to_response(load)


@loads_sub.get("/allocation", response_model=Optional[AllocationResponse])
async def get_allocation(
    load_id: UUID,
    service: Annotated[AllocationService, Depends(get_allocation_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts")
    )],
):
    """Get the current active allocation record for a load."""
    logger.info(f"Get allocation load_id={load_id}")
    alloc = service.get_allocation(load_id)
    if alloc is None:
        return None
    return _to_alloc_response(alloc)


# ── Availability endpoints ─────────────────────────────────────────────────────

avail_router = APIRouter(prefix="/allocations", tags=["Allocations"])


@avail_router.get("/trucks/available", response_model=AvailableTrucksResponse)
async def get_available_trucks(
    service: Annotated[AllocationService, Depends(get_allocation_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
    pickup_date: date = Query(...),
    delivery_date: date | None = Query(None),
):
    """List trucks available (no conflict) for the given date range."""
    logger.info(
        f"Get available trucks pickup_date={pickup_date} delivery_date={delivery_date or pickup_date}"
    )
    eff_delivery = delivery_date or pickup_date
    trucks = service.get_available_trucks(pickup_date, eff_delivery)
    return AvailableTrucksResponse(
        items=[
            AvailableTruckItem(
                id=t.id,
                registration_no=t.registration_no,
                truck_type=t.truck_type,
                capacity_tons=t.capacity_tons,
                make=t.make,
                model=t.model,
            )
            for t in trucks
        ],
        total=len(trucks),
        pickup_date=pickup_date,
        effective_delivery_date=eff_delivery,
    )


@avail_router.get("/drivers/available", response_model=AvailableDriversResponse)
async def get_available_drivers(
    service: Annotated[AllocationService, Depends(get_allocation_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
    pickup_date: date = Query(...),
    delivery_date: date | None = Query(None),
):
    """List drivers available (no conflict, valid license) for the given date range."""
    logger.info(
        f"Get available drivers pickup_date={pickup_date} delivery_date={delivery_date or pickup_date}"
    )
    eff_delivery = delivery_date or pickup_date
    drivers = service.get_available_drivers(pickup_date, eff_delivery)
    return AvailableDriversResponse(
        items=[
            AvailableDriverItem(
                id=d.id,
                first_name=d.first_name,
                last_name=d.last_name,
                phone=d.phone,
                license_no=d.license_no,
                license_class=d.license_class,
                license_expiry=d.license_expiry,
            )
            for d in drivers
        ],
        total=len(drivers),
        pickup_date=pickup_date,
        effective_delivery_date=eff_delivery,
    )
