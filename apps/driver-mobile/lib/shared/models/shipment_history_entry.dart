/// Mirrors `LoadHistoryResponse` (backend `app/schemas/load.py`) — one status
/// transition in a shipment's timeline (`GET /portal/loads/{id}/history`).
class ShipmentHistoryEntry {
  const ShipmentHistoryEntry({
    required this.id,
    this.fromStatus,
    required this.toStatus,
    required this.changedAt,
    this.remarks,
  });

  factory ShipmentHistoryEntry.fromJson(Map<String, dynamic> json) {
    return ShipmentHistoryEntry(
      id: json['id'] as String,
      fromStatus: json['from_status'] as String?,
      toStatus: json['to_status'] as String,
      changedAt: json['changed_at'] as String,
      remarks: json['remarks'] as String?,
    );
  }

  final String id;
  final String? fromStatus;
  final String toStatus;

  /// Already formatted for display (`LocalDateTime`, rendered server-side in
  /// the caller's timezone).
  final String changedAt;
  final String? remarks;
}
