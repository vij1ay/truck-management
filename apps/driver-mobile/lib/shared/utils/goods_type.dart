/// `GoodsType` (backend `app/models/load.py`) wire values, in the order shown
/// in the booking form's dropdown.
const goodsTypes = [
  'general',
  'hazardous',
  'perishable',
  'fragile',
  'machinery',
  'chemicals',
  'other',
];

/// "general" -> "General" — these are short, widely-understood logistics
/// terms shown as-is (matching the admin-frontend's booking form, which lists
/// the raw enum values too).
String goodsTypeLabel(String value) {
  if (value.isEmpty) return value;
  return value[0].toUpperCase() + value.substring(1);
}
