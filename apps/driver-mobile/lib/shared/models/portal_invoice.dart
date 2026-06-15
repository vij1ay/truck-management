import 'payment.dart';

/// Pydantic v2 serializes `Decimal` fields (e.g. `subtotal`, `tax_amount`) as
/// JSON *strings* to preserve precision, while computed `float` properties
/// (e.g. `outstanding_amount`) are plain numbers — handle both.
double _decimal(dynamic value) => double.parse(value.toString());

/// Mirrors `PortalInvoiceResponse` (backend `app/schemas/portal.py`, extends
/// `InvoiceResponse` from `app/schemas/invoice.py`) — returned by
/// `GET /portal/invoices`.
///
/// `status` is kept as its raw lowercase wire value (e.g. `"partial"`) —
/// screens map this to a localized label.
class PortalInvoice {
  const PortalInvoice({
    required this.id,
    required this.invoiceNo,
    required this.carrierName,
    required this.status,
    required this.issuedDate,
    this.dueDate,
    required this.subtotal,
    required this.taxRate,
    required this.taxAmount,
    required this.totalAmount,
    required this.paidAmount,
    required this.outstandingAmount,
    this.notes,
    this.loadNo,
    this.payments = const [],
  });

  factory PortalInvoice.fromJson(Map<String, dynamic> json) {
    return PortalInvoice(
      id: json['id'] as String,
      invoiceNo: json['invoice_no'] as String,
      carrierName: json['carrier_name'] as String,
      status: json['status'] as String,
      issuedDate: json['issued_date'] as String,
      dueDate: json['due_date'] as String?,
      subtotal: _decimal(json['subtotal']),
      taxRate: _decimal(json['tax_rate']),
      taxAmount: _decimal(json['tax_amount']),
      totalAmount: _decimal(json['total_amount']),
      paidAmount: _decimal(json['paid_amount']),
      outstandingAmount: _decimal(json['outstanding_amount']),
      notes: json['notes'] as String?,
      loadNo: json['load_no'] as String?,
      payments: (json['payments'] as List<dynamic>? ?? [])
          .map((e) => Payment.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  final String id;
  final String invoiceNo;
  final String carrierName;
  final String status;
  final String issuedDate;
  final String? dueDate;
  final double subtotal;
  final double taxRate;
  final double taxAmount;
  final double totalAmount;
  final double paidAmount;
  final double outstandingAmount;
  final String? notes;
  final String? loadNo;
  final List<Payment> payments;
}
