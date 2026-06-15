/// Mirrors `PaymentResponse` (backend `app/schemas/invoice.py`) — one payment
/// recorded against an invoice, included in `PortalInvoiceResponse.payments`.
class Payment {
  const Payment({
    required this.id,
    required this.amount,
    required this.paymentDate,
    required this.paymentMethod,
    this.referenceNo,
    this.notes,
  });

  factory Payment.fromJson(Map<String, dynamic> json) {
    return Payment(
      id: json['id'] as String,
      // `amount` is a Decimal, serialized as a JSON string — see
      // `shipment.dart`'s `_decimal()` helper for why.
      amount: double.parse(json['amount'].toString()),
      paymentDate: json['payment_date'] as String,
      paymentMethod: json['payment_method'] as String,
      referenceNo: json['reference_no'] as String?,
      notes: json['notes'] as String?,
    );
  }

  final String id;
  final double amount;
  final String paymentDate;
  final String paymentMethod;
  final String? referenceNo;
  final String? notes;
}
