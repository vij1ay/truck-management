import '../utils/goods_type.dart';

/// Trip status — mirrors the backend's `LoadStatus` enum
/// (`apps/backend/app/models/load.py`): draft/confirmed/allocated/in_transit/
/// delivered/cancelled. The driver app only ever sees allocated/in_transit/
/// delivered/cancelled (see mobile_app_design.md "My Trips" tab mapping).
enum TripStatus { assigned, active, completed, cancelled, pending }

extension TripStatusLabel on TripStatus {
  String get label {
    switch (this) {
      case TripStatus.assigned:
        return 'Assigned';
      case TripStatus.active:
        return 'Active';
      case TripStatus.completed:
        return 'Completed';
      case TripStatus.cancelled:
        return 'Cancelled';
      case TripStatus.pending:
        return 'Pending';
    }
  }
}

/// `LoadStatus` (backend wire value) -> [TripStatus] (driver UI grouping).
TripStatus _tripStatusFromLoadStatus(String loadStatus) {
  switch (loadStatus) {
    case 'allocated':
      return TripStatus.assigned;
    case 'in_transit':
      return TripStatus.active;
    case 'delivered':
      return TripStatus.completed;
    case 'cancelled':
      return TripStatus.cancelled;
    default:
      // draft/confirmed shouldn't be visible to a Driver (get_loads only
      // returns loads allocated to them) — fall back defensively.
      return TripStatus.assigned;
  }
}

/// Pydantic v2 serializes `Decimal` fields (e.g. `weight_kg`, `distance_km`) as
/// JSON *strings* — see `shipment.dart`'s `_decimal()` for details.
double? _decimal(dynamic value) => value == null ? null : double.parse(value.toString());

/// A single load/booking, as seen by the driver. Field names intentionally
/// mirror `LoadResponse` (`apps/backend/app/schemas/load.py`) — `loadNo` ~
/// `load_no`, `pickupDate` ~ `pickup_date`, etc.
class Trip {
  const Trip({
    required this.id,
    required this.loadNo,
    required this.title,
    required this.origin,
    required this.destination,
    required this.pickupDate,
    required this.pickupTime,
    required this.status,
    this.loadStatus,
    this.clientName,
    this.distanceKm,
    this.etaLabel,
    this.weightTonnes,
    this.truckNumber,
    this.truckModel,
    this.driverName,
    this.pickupAddress,
    this.deliveryAddress,
    this.departure,
  });

  /// Maps a `GET /loads` / `GET /loads/{id}` `LoadResponse` JSON object to a
  /// [Trip]. Truck/driver info isn't carried by `LoadResponse` — those fields
  /// are populated separately from `driverMeProvider.currentTruck`.
  factory Trip.fromJson(Map<String, dynamic> json) {
    final goodsType = json['goods_type'] as String;
    final goodsDescription = json['goods_description'] as String?;
    final pickupDate = json['pickup_date'] as String;
    final pickupTime = json['pickup_time'] as String?;
    final weightKg = _decimal(json['weight_kg']);
    final loadStatus = json['status'] as String;

    return Trip(
      id: json['id'] as String,
      loadNo: json['load_no'] as String,
      title: (goodsDescription?.isNotEmpty ?? false) ? goodsDescription! : goodsTypeLabel(goodsType),
      origin: json['origin'] as String,
      destination: json['destination'] as String,
      pickupDate: pickupDate,
      pickupTime: pickupTime ?? '',
      status: _tripStatusFromLoadStatus(loadStatus),
      loadStatus: loadStatus,
      clientName: json['client_name'] as String?,
      distanceKm: _decimal(json['distance_km']),
      weightTonnes: weightKg == null ? null : weightKg / 1000,
      pickupAddress: json['origin'] as String,
      deliveryAddress: json['destination'] as String,
      departure: pickupTime == null || pickupTime.isEmpty ? pickupDate : '$pickupDate, $pickupTime',
    );
  }

  final String id;
  final String loadNo;
  final String title;
  final String origin;
  final String destination;
  final String pickupDate;
  final String pickupTime;
  final TripStatus status;

  /// Raw `LoadStatus` wire value (e.g. `"in_transit"`) — used to decide which
  /// driver actions (Start Trip / checkpoints / Mark Delivered) apply, with
  /// finer granularity than [status]/[TripStatus].
  final String? loadStatus;

  /// The shipper's company name (`LoadResponse.client_name`).
  final String? clientName;
  final double? distanceKm;
  final String? etaLabel;
  final double? weightTonnes;
  final String? truckNumber;
  final String? truckModel;
  final String? driverName;
  final String? pickupAddress;
  final String? deliveryAddress;
  final String? departure;

  /// `true` once ALLOCATED — "Start Trip" transitions to IN_TRANSIT.
  bool get canStart => loadStatus == 'allocated';

  /// `true` while IN_TRANSIT — checkpoints + "Mark Delivered" apply.
  bool get isInTransit => loadStatus == 'in_transit';

  Trip copyWith({String? truckNumber, String? truckModel, String? driverName}) {
    return Trip(
      id: id,
      loadNo: loadNo,
      title: title,
      origin: origin,
      destination: destination,
      pickupDate: pickupDate,
      pickupTime: pickupTime,
      status: status,
      loadStatus: loadStatus,
      clientName: clientName,
      distanceKm: distanceKm,
      etaLabel: etaLabel,
      weightTonnes: weightTonnes,
      truckNumber: truckNumber ?? this.truckNumber,
      truckModel: truckModel ?? this.truckModel,
      driverName: driverName ?? this.driverName,
      pickupAddress: pickupAddress,
      deliveryAddress: deliveryAddress,
      departure: departure,
    );
  }
}
