import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/portal/data/portal_repository.dart';
import '../../shared/models/client_profile.dart';
import '../../shared/models/portal_invoice.dart';
import '../../shared/models/shipment.dart';
import '../../shared/models/shipment_document.dart';
import '../../shared/models/shipment_history_entry.dart';
import 'auth_provider.dart';

final portalRepositoryProvider = Provider<PortalRepository>((ref) {
  return PortalRepository(apiClient: ref.watch(apiClientProvider));
});

/// Every carrier (tenant) relationship linked to this account
/// (`GET /portal/me`) — used by the Client Profile screen and the "Carrier"
/// dropdown on the New Shipment form.
final myCarriersProvider = FutureProvider<List<PortalCarrierLink>>((ref) async {
  return ref.watch(portalRepositoryProvider).getMyProfile();
});

/// My Shipments, optionally filtered by `LoadStatus` wire value (`null` = all).
final shipmentsProvider = FutureProvider.family<List<Shipment>, String?>((ref, status) async {
  return ref.watch(portalRepositoryProvider).getMyShipments(status: status);
});

final shipmentDetailProvider = FutureProvider.family<Shipment, String>((ref, id) async {
  return ref.watch(portalRepositoryProvider).getShipment(id);
});

final shipmentHistoryProvider = FutureProvider.family<List<ShipmentHistoryEntry>, String>((ref, id) async {
  return ref.watch(portalRepositoryProvider).getShipmentHistory(id);
});

final shipmentDocumentsProvider = FutureProvider.family<List<ShipmentDocument>, String>((ref, id) async {
  return ref.watch(portalRepositoryProvider).getShipmentDocuments(id);
});

/// Image bytes for a single shipment document.
final shipmentDocumentBytesProvider =
    FutureProvider.family<List<int>, (String loadId, String documentId)>((ref, params) async {
  return ref.watch(portalRepositoryProvider).getShipmentDocumentBytes(params.$1, params.$2);
});

/// My Invoices, optionally filtered by `InvoiceStatus` wire value (`null` = all).
final invoicesProvider = FutureProvider.family<List<PortalInvoice>, String?>((ref, status) async {
  return ref.watch(portalRepositoryProvider).getMyInvoices(status: status);
});
