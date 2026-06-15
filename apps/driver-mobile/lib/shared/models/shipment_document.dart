/// Subset of `DocumentResponse` (backend `app/schemas/document.py`) shown on
/// a shipment's Documents tab (`GET /portal/loads/{id}/documents`).
class ShipmentDocument {
  const ShipmentDocument({
    required this.id,
    required this.documentType,
    required this.fileName,
    required this.hasFile,
    required this.createdAt,
  });

  factory ShipmentDocument.fromJson(Map<String, dynamic> json) {
    return ShipmentDocument(
      id: json['id'] as String,
      documentType: json['document_type'] as String,
      fileName: json['file_name'] as String,
      hasFile: json['has_file'] as bool? ?? false,
      createdAt: json['created_at'] as String,
    );
  }

  final String id;
  final String documentType;
  final String fileName;

  /// Whether an image was uploaded for this document (via the Client Portal's
  /// "Upload Document") — if true, fetch bytes via
  /// `GET /portal/loads/{id}/documents/{id}/file`.
  final bool hasFile;

  /// Already formatted for display (`LocalDateTime`).
  final String createdAt;
}
