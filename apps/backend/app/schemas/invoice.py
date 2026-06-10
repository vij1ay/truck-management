from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.invoice import InvoiceStatus, PaymentMethod


# ── Payment schemas ────────────────────────────────────────────────────────────

class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    payment_date: date
    payment_method: PaymentMethod = PaymentMethod.DUMMY
    notes: str | None = None


class PaymentResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    amount: Decimal
    payment_date: date
    payment_method: PaymentMethod
    reference_no: str | None
    notes: str | None
    recorded_by: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Invoice schemas ────────────────────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    load_id: UUID | None = None
    client_id: UUID
    issued_date: date
    due_date: date | None = None
    subtotal: Decimal = Field(ge=0, decimal_places=2)
    tax_rate: Decimal = Field(ge=0, le=100, decimal_places=2, default=Decimal("0"))
    notes: str | None = None

    @model_validator(mode="after")
    def compute_tax(self):
        self.tax_amount = (self.subtotal * self.tax_rate / 100).quantize(Decimal("0.01"))
        self.total_amount = self.subtotal + self.tax_amount
        return self


class InvoiceUpdate(BaseModel):
    due_date: date | None = None
    notes: str | None = None


class InvoiceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    load_id: UUID | None
    client_id: UUID
    invoice_no: str
    status: InvoiceStatus
    issued_date: date
    due_date: date | None
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: float
    notes: str | None
    created_at: datetime
    updated_at: datetime
    client_name: str | None = None
    load_no: str | None = None
    payments: list[PaymentResponse] = []

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int
    page: int
    size: int
    pages: int
