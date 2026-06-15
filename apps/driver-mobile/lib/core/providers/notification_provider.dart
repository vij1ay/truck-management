import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/shipment_history_entry.dart';
import '../../shared/models/trip.dart';
import 'trip_provider.dart';

/// A lightweight "Recent Activity" feed derived from `LoadHistory`
/// (gap #7 — no backend notification model exists yet). For each of the
/// driver's trips (most recent first, capped at 5), pairs the trip with its
/// **latest** history entry. `notifications_screen.dart` maps each pair to a
/// localized [NotificationItem] at render time (providers can't access
/// `BuildContext`/`l10n`).
final driverRecentActivityProvider = FutureProvider<List<(Trip, ShipmentHistoryEntry)>>((ref) async {
  final trips = await ref.watch(tripsProvider.future);
  final repo = ref.watch(tripRepositoryProvider);

  final items = <(Trip, ShipmentHistoryEntry)>[];
  for (final trip in trips.take(5)) {
    final history = await repo.getTripHistory(trip.id);
    if (history.isNotEmpty) items.add((trip, history.last));
  }
  return items;
});
