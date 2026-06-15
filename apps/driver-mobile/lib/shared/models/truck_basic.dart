/// Mirrors `TruckBasic` (backend `app/schemas/truck.py`) — minimal truck info
/// nested in `DriverMeResponse.current_truck`.
class TruckBasic {
  const TruckBasic({
    required this.id,
    required this.registrationNo,
    this.make,
    this.model,
    required this.hasAvatar,
  });

  factory TruckBasic.fromJson(Map<String, dynamic> json) {
    return TruckBasic(
      id: json['id'] as String,
      registrationNo: json['registration_no'] as String,
      make: json['make'] as String?,
      model: json['model'] as String?,
      hasAvatar: json['has_avatar'] as bool? ?? false,
    );
  }

  final String id;
  final String registrationNo;
  final String? make;
  final String? model;
  final bool hasAvatar;

  /// e.g. "Tata LPT 2518", or just the registration number if make/model are unset.
  String get displayName {
    final parts = [make, model].where((p) => p != null && p.isNotEmpty);
    return parts.isEmpty ? registrationNo : parts.join(' ');
  }
}
