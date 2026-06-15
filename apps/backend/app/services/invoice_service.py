from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models import EventCategory, Tenant
from app.models.invoice import Invoice, InvoiceStatus, Payment, PaymentMethod
from app.models.load import Load
from app.repositories.invoice import InvoiceRepository, PaymentRepository
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, PaymentCreate
from app.services.audit_service import AuditService
from app.services.invoice_pdf import generate_invoice_pdf
from app.services.payment import get_payment_gateway


class InvoiceService:

    def __init__(
        self,
        db: Session,
        tenant_id: UUID | None = None,
        current_user_id: UUID | None = None,
        is_superadmin: bool = False,
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.is_superadmin = is_superadmin
        self.invoice_repo = InvoiceRepository(db, tenant_id)
        self.payment_repo = PaymentRepository(db, tenant_id)
        self.audit = AuditService(db, tenant_id)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _generate_invoice_no(self, year: int, seq_no: int) -> str:
        return f"INV-{year}-{seq_no:06d}"

    def _get_invoice(self, invoice_id: UUID) -> Invoice:
        inv = self.invoice_repo.get_active_by_id(invoice_id)
        if not inv:
            raise NotFoundException("Invoice not found")
        return inv

    def _enrich(self, inv: Invoice) -> Invoice:
        """Attach client_name and load_no as dynamic attributes for serialisation."""
        inv.client_name = inv.client.company_name if inv.client else None
        inv.load_no = inv.load.load_no if inv.load else None
        inv.payments = self.payment_repo.get_by_invoice(inv.id)
        return inv

    # ── Read ───────────────────────────────────────────────────────────────────

    def get_invoice(self, invoice_id: UUID) -> Invoice:
        return self._enrich(self._get_invoice(invoice_id))

    def generate_pdf(self, invoice_id: UUID) -> bytes:
        inv = self._enrich(self._get_invoice(invoice_id))
        tenant = self.db.get(Tenant, inv.tenant_id)
        return generate_invoice_pdf(inv, tenant)

    def get_invoices(
        self,
        page: int = 1,
        size: int = 50,
        status: InvoiceStatus | None = None,
        client_id: UUID | None = None,
        load_id: UUID | None = None,
        tenant_id: UUID | None = None,
    ) -> tuple[list[Invoice], int]:
        self.refresh_overdue()
        skip = (page - 1) * size
        items = self.invoice_repo.get_all_filtered(
            skip=skip, limit=size, status=status, client_id=client_id, load_id=load_id,
            tenant_id=tenant_id, include_all_tenants=self.is_superadmin,
        )
        total = self.invoice_repo.count_filtered(
            status=status, client_id=client_id, load_id=load_id,
            tenant_id=tenant_id, include_all_tenants=self.is_superadmin,
        )
        return [self._enrich(i) for i in items], total

    # ── Overdue alerting ───────────────────────────────────────────────────────

    def refresh_overdue(self) -> list[Invoice]:
        """Flip SENT/PARTIAL invoices past their due_date to OVERDUE. Returns the updated invoices."""
        candidates = self.invoice_repo.get_overdue_candidates()
        updated = []
        for inv in candidates:
            old_status = inv.status
            self.invoice_repo.update(inv, {"status": InvoiceStatus.OVERDUE})
            self.audit.log_event(
                event_type="INVOICE_OVERDUE",
                event_category=EventCategory.user_mgmt,
                user_id=self.current_user_id,
                tenant_id=self.tenant_id,
                resource_type="Invoice",
                resource_id=inv.id,
                old_value={"status": old_status},
                new_value={"status": InvoiceStatus.OVERDUE},
            )
            updated.append(inv)
        if updated:
            self.db.commit()
        return updated

    # ── Create ─────────────────────────────────────────────────────────────────

    def create_invoice(self, data: InvoiceCreate) -> Invoice:
        if data.load_id:
            existing = self.invoice_repo.get_by_load_id(data.load_id)
            if existing:
                raise ConflictException(f"Invoice {existing.invoice_no} already exists for this load")

        seq_no = self.invoice_repo.get_next_seq_no()
        year = datetime.now(timezone.utc).year
        invoice_no = self._generate_invoice_no(year, seq_no)

        subtotal = data.subtotal
        tax_amount = (subtotal * data.tax_rate / 100).quantize(Decimal("0.01"))
        total_amount = subtotal + tax_amount

        invoice_data = {
            "load_id": data.load_id,
            "client_id": data.client_id,
            "invoice_no": invoice_no,
            "invoice_seq_no": seq_no,
            "status": InvoiceStatus.DRAFT,
            "issued_date": data.issued_date,
            "due_date": data.due_date,
            "subtotal": subtotal,
            "tax_rate": data.tax_rate,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "paid_amount": Decimal("0"),
            "notes": data.notes,
        }
        inv = self.invoice_repo.create(invoice_data)

        self.audit.log_event(
            event_type="INVOICE_CREATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Invoice",
            resource_id=inv.id,
            new_value={"invoice_no": invoice_no, "total_amount": str(total_amount)},
        )
        self.db.commit()
        return self._enrich(self.invoice_repo.get_active_by_id(inv.id))

    def create_from_load(self, load: Load) -> Invoice | None:
        """Auto-create a draft invoice when a load is delivered. Skips if freight is 0."""
        if not load.freight_amount or float(load.freight_amount) == 0:
            return None
        if self.invoice_repo.get_by_load_id(load.id):
            return None

        seq_no = self.invoice_repo.get_next_seq_no()
        year = datetime.now(timezone.utc).year
        invoice_no = self._generate_invoice_no(year, seq_no)
        subtotal = Decimal(str(load.freight_amount))

        invoice_data = {
            "load_id": load.id,
            "client_id": load.client_id,
            "invoice_no": invoice_no,
            "invoice_seq_no": seq_no,
            "status": InvoiceStatus.DRAFT,
            "issued_date": date.today(),
            "due_date": None,
            "subtotal": subtotal,
            "tax_rate": Decimal("0"),
            "tax_amount": Decimal("0"),
            "total_amount": subtotal,
            "paid_amount": Decimal("0"),
            "notes": f"Auto-generated from load {load.load_no}",
        }
        inv = self.invoice_repo.create(invoice_data)

        self.audit.log_event(
            event_type="INVOICE_AUTO_CREATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Invoice",
            resource_id=inv.id,
            new_value={"invoice_no": invoice_no, "load_no": load.load_no, "total_amount": str(subtotal)},
        )
        return inv

    # ── Update ─────────────────────────────────────────────────────────────────

    def update_invoice(self, invoice_id: UUID, data: InvoiceUpdate) -> Invoice:
        inv = self._get_invoice(invoice_id)
        if inv.status not in (InvoiceStatus.DRAFT, InvoiceStatus.SENT):
            raise BadRequestException("Only draft or sent invoices can be updated")
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        self.invoice_repo.update(inv, update_data)
        self.db.commit()
        return self._enrich(self.invoice_repo.get_active_by_id(invoice_id))

    def send_invoice(self, invoice_id: UUID) -> Invoice:
        inv = self._get_invoice(invoice_id)
        if not inv.can_transition_to(InvoiceStatus.SENT):
            raise BadRequestException(f"Cannot send invoice in '{inv.status}' status")
        self.invoice_repo.update(inv, {"status": InvoiceStatus.SENT})
        self.audit.log_event(
            event_type="INVOICE_SENT",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Invoice",
            resource_id=invoice_id,
            new_value={"status": InvoiceStatus.SENT},
        )
        self.db.commit()
        return self._enrich(self.invoice_repo.get_active_by_id(invoice_id))

    def cancel_invoice(self, invoice_id: UUID) -> Invoice:
        inv = self._get_invoice(invoice_id)
        if not inv.can_transition_to(InvoiceStatus.CANCELLED):
            raise BadRequestException(f"Cannot cancel invoice in '{inv.status}' status")
        self.invoice_repo.update(inv, {"status": InvoiceStatus.CANCELLED})
        self.db.commit()
        return self._enrich(self.invoice_repo.get_active_by_id(invoice_id))

    def delete_invoice(self, invoice_id: UUID) -> None:
        inv = self._get_invoice(invoice_id)
        if inv.status != InvoiceStatus.DRAFT:
            raise BadRequestException("Only draft invoices can be deleted")
        self.invoice_repo.soft_delete(inv)
        self.db.commit()

    # ── Payments ───────────────────────────────────────────────────────────────

    def record_payment(self, invoice_id: UUID, data: PaymentCreate) -> Payment:
        inv = self._get_invoice(invoice_id)
        if inv.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.DRAFT):
            raise BadRequestException(f"Cannot record payment on a '{inv.status}' invoice")

        outstanding = Decimal(str(inv.total_amount)) - Decimal(str(inv.paid_amount))
        if data.amount > outstanding:
            raise BadRequestException(
                f"Payment amount {data.amount} exceeds outstanding balance {outstanding}"
            )

        # Process via gateway
        gateway = get_payment_gateway(data.payment_method)
        result = gateway.process_payment(
            amount=data.amount,
            invoice_no=inv.invoice_no,
            metadata={"invoice_id": str(inv.id), "tenant_id": str(self.tenant_id)},
        )
        if not result.success:
            raise BadRequestException(f"Payment failed: {result.message}")

        payment_data = {
            "invoice_id": inv.id,
            "amount": data.amount,
            "payment_date": data.payment_date,
            "payment_method": data.payment_method,
            "reference_no": result.reference_no,
            "gateway_response": str(result.gateway_data),
            "notes": data.notes,
            "recorded_by": self.current_user_id,
        }
        payment = self.payment_repo.create(payment_data)

        # Update paid_amount and derive new status
        new_paid = Decimal(str(inv.paid_amount)) + data.amount
        if new_paid >= Decimal(str(inv.total_amount)):
            new_status = InvoiceStatus.PAID
        else:
            new_status = InvoiceStatus.PARTIAL

        self.invoice_repo.update(inv, {"paid_amount": new_paid, "status": new_status})

        self.audit.log_event(
            event_type="PAYMENT_RECORDED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Invoice",
            resource_id=invoice_id,
            new_value={
                "amount": str(data.amount),
                "method": data.payment_method,
                "reference_no": result.reference_no,
                "new_status": new_status,
            },
        )
        self.db.commit()
        return payment
