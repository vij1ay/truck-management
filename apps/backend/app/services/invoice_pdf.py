"""PDF rendering for invoices (Phase 10)."""
import io
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)

from app.models.invoice import Invoice
from app.models.tenant import Tenant


def _money(value) -> str:
    return f"{Decimal(str(value or 0)):,.2f}"


def generate_invoice_pdf(invoice: Invoice, tenant: Tenant | None) -> bytes:
    """Render an Invoice (with client/load/payments preloaded) to a PDF and return its bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("InvoiceTitle", parent=styles["Title"], alignment=2)  # right-aligned
    heading_style = styles["Heading2"]
    normal = styles["Normal"]

    elements = []

    # ── Header: tenant name + invoice title ─────────────────────────────────
    company_name = tenant.name if tenant else "Transport Management System"
    header_table = Table(
        [[Paragraph(f"<b>{company_name}</b>", styles["Heading1"]), Paragraph("INVOICE", title_style)]],
        colWidths=[None, None],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Invoice meta ─────────────────────────────────────────────────────────
    meta_rows = [
        ["Invoice No:", invoice.invoice_no, "Status:", invoice.status.value.upper()],
        ["Issued Date:", invoice.issued_date.isoformat(), "Due Date:", invoice.due_date.isoformat() if invoice.due_date else "-"],
    ]
    if getattr(invoice, "load_no", None):
        meta_rows.append(["Load No:", invoice.load_no, "", ""])

    meta_table = Table(meta_rows, colWidths=[30 * mm, 55 * mm, 30 * mm, 55 * mm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8 * mm))

    # ── Bill To ──────────────────────────────────────────────────────────────
    elements.append(Paragraph("Bill To", heading_style))
    client = invoice.client
    if client:
        lines = [f"<b>{client.company_name}</b>"]
        addr_parts = [p for p in [client.address, client.city, client.state, client.pincode] if p]
        if addr_parts:
            lines.append(", ".join(addr_parts))
        if client.phone:
            lines.append(f"Phone: {client.phone}")
        if client.gst_no:
            lines.append(f"GSTIN: {client.gst_no}")
        elements.append(Paragraph("<br/>".join(lines), normal))
    else:
        elements.append(Paragraph("-", normal))
    elements.append(Spacer(1, 8 * mm))

    # ── Line items ───────────────────────────────────────────────────────────
    if invoice.load:
        description = f"Freight charges — Load {invoice.load.load_no} ({invoice.load.origin} → {invoice.load.destination})"
    else:
        description = "Freight charges"

    items_data = [
        ["Description", "Subtotal", "Tax Rate", "Tax Amount", "Total"],
        [
            description,
            _money(invoice.subtotal),
            f"{Decimal(str(invoice.tax_rate or 0)):.2f}%",
            _money(invoice.tax_amount),
            _money(invoice.total_amount),
        ],
    ]
    items_table = Table(items_data, colWidths=[80 * mm, 28 * mm, 22 * mm, 28 * mm, 28 * mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 8 * mm))

    # ── Payment summary ──────────────────────────────────────────────────────
    summary_data = [
        ["Total Amount", _money(invoice.total_amount)],
        ["Paid Amount", _money(invoice.paid_amount)],
        ["Outstanding", _money(invoice.outstanding_amount)],
    ]
    summary_table = Table(summary_data, colWidths=[150 * mm, 36 * mm], hAlign="RIGHT")
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LINEABOVE", (0, -1), (-1, -1), 0.75, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(summary_table)

    # ── Payments received ────────────────────────────────────────────────────
    payments = list(getattr(invoice, "payments", None) or [])
    if payments:
        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph("Payments Received", heading_style))
        payment_rows = [["Date", "Method", "Reference", "Amount"]]
        for p in payments:
            payment_rows.append([
                p.payment_date.isoformat(),
                p.payment_method.value if hasattr(p.payment_method, "value") else str(p.payment_method),
                p.reference_no or "-",
                _money(p.amount),
            ])
        payments_table = Table(payment_rows, colWidths=[35 * mm, 35 * mm, 60 * mm, 36 * mm])
        payments_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3f2fd")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(payments_table)

    # ── Notes ────────────────────────────────────────────────────────────────
    if invoice.notes:
        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph("Notes", heading_style))
        elements.append(Paragraph(invoice.notes, normal))

    doc.build(elements)
    return buffer.getvalue()
