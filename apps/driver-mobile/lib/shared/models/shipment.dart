/// Pydantic v2 serializes `Decimal` fields (e.g. `weight_kg`,
/// `freight_amount`) as JSON *strings* to preserve precision, while computed
/// `float` properties (e.g. `balance_amount`) are plain numbers — handle both.
double? _decimal(dynamic value) => value == null ? null : double.parse(value.toString());

/// Mirrors `LoadResponse` (backend `app/schemas/load.py`), plus the
/// `carrier_name` field added by `PortalLoadResponse` when returned from
/// `GET /portal/loads` (absent — `null` — from `GET /portal/loads/{id}`).
///
/// Status/goods-type are kept as their raw lowercase wire values (e.g.
/// `"in_transit"`, `"general"`) — screens map these to localized labels.
class Shipment {
  const Shipment({
    required this.id,
    required this.tenantId,
    required this.loadNo,
    required this.status,
    this.carrierName,
    required this.origin,
    required this.destination,
    this.distanceKm,
    required this.pickupDate,
    this.pickupTime,
    this.expectedDeliveryDate,
    this.actualDeliveryDate,
    required this.goodsType,
    this.goodsDescription,
    this.weightKg,
    this.volumeCbm,
    this.quantity,
    this.freightAmount,
    this.advanceAmount,
    required this.balanceAmount,
    this.truckPreference,
    this.specialInstructions,
    this.notes,
    required this.isEditable,
    required this.isDeletable,
  });

  factory Shipment.fromJson(Map<String, dynamic> json) {
    return Shipment(
      id: json['id'] as String,
      tenantId: json['tenant_id'] as String,
      loadNo: json['load_no'] as String,
      status: json['status'] as String,
      carrierName: json['carrier_name'] as String?,
      origin: json['origin'] as String,
      destination: json['destination'] as String,
      distanceKm: _decimal(json['distance_km']),
      pickupDate: json['pickup_date'] as String,
      pickupTime: json['pickup_time'] as String?,
      expectedDeliveryDate: json['expected_delivery_date'] as String?,
      actualDeliveryDate: json['actual_delivery_date'] as String?,
      goodsType: json['goods_type'] as String,
      goodsDescription: json['goods_description'] as String?,
      weightKg: _decimal(json['weight_kg']),
      volumeCbm: _decimal(json['volume_cbm']),
      quantity: json['quantity'] as int?,
      freightAmount: _decimal(json['freight_amount']),
      advanceAmount: _decimal(json['advance_amount']),
      balanceAmount: (json['balance_amount'] as num).toDouble(),
      truckPreference: json['truck_preference'] as String?,
      specialInstructions: json['special_instructions'] as String?,
      notes: json['notes'] as String?,
      isEditable: json['is_editable'] as bool,
      isDeletable: json['is_deletable'] as bool,
    );
  }

  final String id;
  final String tenantId;
  final String loadNo;
  final String status;
  final String? carrierName;
  final String origin;
  final String destination;
  final double? distanceKm;
  final String pickupDate;
  final String? pickupTime;
  final String? expectedDeliveryDate;
  final String? actualDeliveryDate;
  final String goodsType;
  final String? goodsDescription;
  final double? weightKg;
  final double? volumeCbm;
  final int? quantity;
  final double? freightAmount;
  final double? advanceAmount;
  final double balanceAmount;
  final String? truckPreference;
  final String? specialInstructions;
  final String? notes;

  /// Only DRAFT/CONFIRMED shipments can be edited via `PATCH /portal/loads/{id}`.
  final bool isEditable;

  /// Only DRAFT/CANCELLED shipments are deletable (admin-only; not currently
  /// exposed to the Client Portal, but parsed for completeness).
  final bool isDeletable;
}
