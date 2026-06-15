/// `DocumentType` (backend `app/models/document.py`) wire values -> display
/// labels, mirroring `goods_type.dart`'s pattern.
const Map<String, String> _documentTypeLabels = {
  'rc_book': 'RC Book',
  'insurance': 'Insurance',
  'fitness': 'Fitness Certificate',
  'pollution': 'Pollution Certificate',
  'permit': 'Permit',
  'driver_license': "Driver's License",
  'medical': 'Medical Certificate',
  'contract': 'Contract',
  'pod': 'Proof of Delivery',
  'other': 'Other',
};

/// "rc_book" -> "RC Book".
String documentTypeLabel(String value) => _documentTypeLabels[value] ?? value;
