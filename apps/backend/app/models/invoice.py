import enum
from sqlalchemy import (
    Column, String, Boolean, Numeric, Integer,
    ForeignKey, Text, Enum as SAEnum, Date, DateTime, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    DUMMY = "dummy"
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"


INVOICE_ALLOWED_TRANSITIONS: dict[InvoiceStatus, list[InvoiceStatus]] = {
    InvoiceStatus.DRAFT:      [InvoiceStatus.SENT, InvoiceStatus.CANCELLED],
    InvoiceStatus.SENT:       [InvoiceStatus.PARTIAL, InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.CANCELLED],
    InvoiceStatus.PARTIAL:    [InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.CANCELLED],
    InvoiceStatus.OVERDUE:    [InvoiceStatus.PARTIAL, InvoiceStatus.PAID, InvoiceStatus.CANCELLED],
    InvoiceStatus.PAID:       [],
    InvoiceStatus.CANCELLED:  [],
}


class Invoice(BaseModel):
    """Invoice generated from a delivered load."""

    __tablename__ = "invoices"

    __table_args__ = (
        Index("ix_invoices_tenant_invoice_no", "tenant_id", "invoice_no", unique=True),
        Index("ix_invoices_tenant_status", "tenant_id", "status"),
        Index("ix_invoices_tenant_client", "tenant_id", "client_id"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    load_id = Column(UUID(as_uuid=True), ForeignKey("loads.id", ondelete="RESTRICT"), nullable=True, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)

    invoice_no = Column(String(20), nullable=False, index=True)
    invoice_seq_no = Column(Integer, nullable=False)

    status = Column(
        SAEnum(InvoiceStatus, name="invoicestatus", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
    )

    issued_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)

    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    paid_amount = Column(Numeric(15, 2), nullable=False, default=0)

    notes = Column(Text, nullable=True)

    # Relationships
    tenant = relationship("Tenant")
    load = relationship("Load")
    client = relationship("Client")
    payments = relationship("Payment", back_populates="invoice", lazy="select")

    @property
    def outstanding_amount(self):
        return float(self.total_amount or 0) - float(self.paid_amount or 0)

    def can_transition_to(self, new_status: InvoiceStatus) -> bool:
        return new_status in INVOICE_ALLOWED_TRANSITIONS.get(self.status, [])


class Payment(BaseModel):
    """Payment recorded against an invoice."""

    __tablename__ = "payments"

    __table_args__ = (
        Index("ix_payments_tenant_invoice", "tenant_id", "invoice_id"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True)

    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(Date, nullable=False)

    payment_method = Column(
        SAEnum(PaymentMethod, name="paymentmethod", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=PaymentMethod.DUMMY,
    )

    reference_no = Column(String(100), nullable=True)
    gateway_response = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    recorded_by_user = relationship("User", foreign_keys=[recorded_by])
