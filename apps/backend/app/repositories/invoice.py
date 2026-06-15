from datetime import date
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceStatus, Payment
from app.repositories.base import TenantAwareRepository


class InvoiceRepository(TenantAwareRepository[Invoice]):

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(Invoice, db, tenant_id)

    def get_all_filtered(
        self,
        skip: int = 0,
        limit: int = 50,
        status: InvoiceStatus | None = None,
        client_id: UUID | None = None,
        load_id: UUID | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)
        if status:
            stmt = stmt.where(Invoice.status == status)
        if client_id:
            stmt = stmt.where(Invoice.client_id == client_id)
        if load_id:
            stmt = stmt.where(Invoice.load_id == load_id)
        if tenant_id is not None:
            stmt = stmt.where(Invoice.tenant_id == tenant_id)
        stmt = stmt.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_filtered(
        self,
        status: InvoiceStatus | None = None,
        client_id: UUID | None = None,
        load_id: UUID | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> int:
        stmt = select(func.count()).select_from(Invoice).where(Invoice.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)
        if status:
            stmt = stmt.where(Invoice.status == status)
        if client_id:
            stmt = stmt.where(Invoice.client_id == client_id)
        if load_id:
            stmt = stmt.where(Invoice.load_id == load_id)
        if tenant_id is not None:
            stmt = stmt.where(Invoice.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one()

    def get_next_seq_no(self) -> int:
        stmt = select(func.coalesce(func.max(Invoice.invoice_seq_no), 0)).where(
            Invoice.tenant_id == self.tenant_id
        )
        return self.db.execute(stmt).scalar_one() + 1

    def get_by_load_id(self, load_id: UUID) -> Invoice | None:
        stmt = select(Invoice).where(
            and_(Invoice.load_id == load_id, Invoice.is_deleted == False)
        )
        stmt = self._apply_tenant_filter(stmt)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_overdue_candidates(self) -> list[Invoice]:
        """Invoices that are SENT/PARTIAL with a due_date in the past — not yet flagged OVERDUE."""
        stmt = select(Invoice).where(
            and_(
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIAL]),
                Invoice.due_date.is_not(None),
                Invoice.due_date < date.today(),
                Invoice.is_deleted == False,
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        return list(self.db.execute(stmt).scalars().all())


class PaymentRepository(TenantAwareRepository[Payment]):

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(Payment, db, tenant_id)

    def get_by_invoice(self, invoice_id: UUID) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(and_(Payment.invoice_id == invoice_id, Payment.is_deleted == False))
            .order_by(Payment.payment_date.asc())
        )
        stmt = self._apply_tenant_filter(stmt)
        return list(self.db.execute(stmt).scalars().all())

    def sum_paid(self, invoice_id: UUID) -> float:
        stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            and_(Payment.invoice_id == invoice_id, Payment.is_deleted == False)
        )
        return float(self.db.execute(stmt).scalar_one())
