import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.dependencies.auth import get_current_user_context, require_roles, CurrentUser
from app.dependencies.database import get_db
from app.models import User
from app.models.invoice import InvoiceStatus
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse,
    PaymentCreate, PaymentResponse,
)
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])
logger = get_logger(__name__)


def get_invoice_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> InvoiceService:
    return InvoiceService(
        db=db,
        tenant_id=context.tenant_id,
        current_user_id=context.user_id,
        is_superadmin=context.is_superadmin,
    )


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    service: Annotated[InvoiceService, Depends(get_invoice_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: InvoiceStatus | None = None,
    client_id: UUID | None = None,
    load_id: UUID | None = None,
):
    invoices, total = service.get_invoices(page=page, size=size, status=status, client_id=client_id, load_id=load_id)
    return InvoiceListResponse(
        items=invoices, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    data: InvoiceCreate,
    service: Annotated[InvoiceService, Depends(get_invoice_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "Accounts"))],
):
    return service.create_invoice(data)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    service: Annotated[InvoiceService, Depends(get_invoice_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
):
    return service.get_invoice(invoice_id)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    data: InvoiceUpdate,
    service: Annotated[InvoiceService, Depends(get_invoice_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "Accounts"))],
):
    return service.update_invoice(invoice_id, data)


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: UUID,
    service: Annotated[InvoiceService, Depends(get_invoice_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "Accounts"))],
):
    logger.info(f"Send invoice invoice_id={invoice_id}")
    return service.send_invoice(invoice_id)


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    invoice_id: UUID,
    service: Annotated[InvoiceService, Depends(get_invoice_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
):
    logger.info(f"Cancel invoice invoice_id={invoice_id}")
    return service.cancel_invoice(invoice_id)


@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: UUID,
    service: Annotated[InvoiceService, Depends(get_invoice_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
):
    service.delete_invoice(invoice_id)


@router.post("/{invoice_id}/payments", response_model=PaymentResponse, status_code=201)
async def record_payment(
    invoice_id: UUID,
    data: PaymentCreate,
    service: Annotated[InvoiceService, Depends(get_invoice_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "Accounts"))],
):
    logger.info(f"Record payment invoice_id={invoice_id} amount={data.amount} method={data.payment_method}")
    return service.record_payment(invoice_id, data)
