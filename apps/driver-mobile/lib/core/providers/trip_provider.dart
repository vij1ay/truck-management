import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/trips/data/trip_repository.dart';
import '../../shared/models/shipment_document.dart';
import '../../shared/models/shipment_history_entry.dart';
import '../../shared/models/trip.dart';
import 'auth_provider.dart';

final tripRepositoryProvider = Provider<TripRepository>((ref) {
  return TripRepository(apiClient: ref.watch(apiClientProvider));
});

/// My Trips (`GET /loads`, auto-scoped to the Driver's allocated loads).
final tripsProvider = FutureProvider<List<Trip>>((ref) async {
  return ref.watch(tripRepositoryProvider).getMyTrips();
});

final tripDetailProvider = FutureProvider.family<Trip, String>((ref, id) async {
  return ref.watch(tripRepositoryProvider).getTrip(id);
});

final tripHistoryProvider = FutureProvider.family<List<ShipmentHistoryEntry>, String>((ref, id) async {
  return ref.watch(tripRepositoryProvider).getTripHistory(id);
});

final tripDocumentsProvider = FutureProvider.family<List<ShipmentDocument>, String>((ref, id) async {
  return ref.watch(tripRepositoryProvider).getTripDocuments(id);
});

/// Image bytes for a single trip document (e.g. a POD photo).
final tripDocumentBytesProvider =
    FutureProvider.family<List<int>, (String tripId, String documentId)>((ref, params) async {
  return ref.watch(tripRepositoryProvider).getTripDocumentBytes(params.$1, params.$2);
});

/// Documents across the driver's most recent trips (last 5), each paired with
/// its trip for display (e.g. prefixed with `load_no`) — used by the
/// Documents screen's "Trip" tab.
final recentTripDocumentsProvider = FutureProvider<List<(Trip, ShipmentDocument)>>((ref) async {
  final trips = await ref.watch(tripsProvider.future);
  final repo = ref.watch(tripRepositoryProvider);

  final result = <(Trip, ShipmentDocument)>[];
  for (final trip in trips.take(5)) {
    final docs = await repo.getTripDocuments(trip.id);
    for (final doc in docs) {
      result.add((trip, doc));
    }
  }
  return result;
});
