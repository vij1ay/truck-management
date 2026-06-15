// Widget tests for the real-data-backed Trips/Trip Details screens —
// overrides `tripRepositoryProvider` with a fake (no HTTP), bypassing
// GoRouter by pumping the screens directly inside a plain `MaterialApp`.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:driver_mobile/core/providers/profile_provider.dart';
import 'package:driver_mobile/core/providers/trip_provider.dart';
import 'package:driver_mobile/features/trips/data/trip_repository.dart';
import 'package:driver_mobile/features/trips/screens/trip_details_screen.dart';
import 'package:driver_mobile/features/trips/screens/trips_screen.dart';
import 'package:driver_mobile/l10n/app_localizations.dart';
import 'package:driver_mobile/shared/models/shipment_document.dart';
import 'package:driver_mobile/shared/models/shipment_history_entry.dart';
import 'package:driver_mobile/shared/models/trip.dart';

/// A `TripRepository` backed by canned data — no Dio/HTTP involved.
class FakeTripRepository implements TripRepository {
  FakeTripRepository({required this.trips, this.history = const []});

  final List<Trip> trips;
  final List<ShipmentHistoryEntry> history;

  @override
  Future<List<Trip>> getMyTrips({String? status}) async => trips;

  @override
  Future<Trip> getTrip(String id) async => trips.firstWhere((t) => t.id == id);

  @override
  Future<List<ShipmentHistoryEntry>> getTripHistory(String id) async => history;

  @override
  Future<List<ShipmentDocument>> getTripDocuments(String id) async => [];

  @override
  Future<List<int>> getTripDocumentBytes(String id, String documentId) async => [];

  @override
  Future<Trip> startTrip(String id) async => trips.first;

  @override
  Future<Trip> addCheckpoint(String id, String label) async => trips.first;

  @override
  Future<ShipmentDocument> uploadPodPhoto(String id, String filePath) =>
      throw UnimplementedError();

  @override
  Future<Trip> deliverTrip(String id) async => trips.first;
}

Widget _wrap(Widget child, List<Override> overrides) {
  return ProviderScope(
    overrides: overrides,
    child: MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    ),
  );
}

void main() {
  final assignedTrip = Trip.fromJson({
    'id': 'load-1',
    'tenant_id': 'tenant-1',
    'load_no': 'LD-2026-000001',
    'status': 'allocated',
    'client_name': 'Acme Corp',
    'origin': 'Mumbai',
    'destination': 'Pune',
    'pickup_date': '2026-06-20',
    'pickup_time': null,
    'goods_type': 'general',
    'goods_description': null,
    'weight_kg': null,
    'distance_km': null,
    'balance_amount': 0,
    'is_editable': true,
    'is_deletable': true,
  });

  testWidgets('Trips screen lists fake trips by status tab', (tester) async {
    await tester.pumpWidget(_wrap(
      const TripsScreen(),
      [tripRepositoryProvider.overrideWithValue(FakeTripRepository(trips: [assignedTrip]))],
    ));
    await tester.pumpAndSettle();

    // "Assigned" is the first tab — the allocated trip shows there.
    expect(find.text('LD-2026-000001'), findsOneWidget);
  });

  testWidgets('Trip Details shows client name and a timeline checkpoint', (tester) async {
    final inTransitTrip = Trip.fromJson({
      'id': 'load-2',
      'tenant_id': 'tenant-1',
      'load_no': 'LD-2026-000002',
      'status': 'in_transit',
      'client_name': 'Acme Corp',
      'origin': 'Mumbai',
      'destination': 'Pune',
      'pickup_date': '2026-06-20',
      'pickup_time': null,
      'goods_type': 'general',
      'goods_description': null,
      'weight_kg': null,
      'distance_km': null,
      'balance_amount': 0,
      'is_editable': false,
      'is_deletable': false,
    });

    final checkpoint = ShipmentHistoryEntry.fromJson({
      'id': 'h1',
      'from_status': 'in_transit',
      'to_status': 'in_transit',
      'changed_at': '14 Jun 2026, 10:00 AM IST',
      'remarks': 'Reached Pickup',
    });

    await tester.pumpWidget(_wrap(
      const TripDetailsScreen(tripId: 'load-2'),
      [
        tripRepositoryProvider.overrideWithValue(
          FakeTripRepository(trips: [inTransitTrip], history: [checkpoint]),
        ),
        driverMeProvider.overrideWith((ref) async => null),
      ],
    ));
    await tester.pumpAndSettle();

    expect(find.text('Client: Acme Corp'), findsOneWidget);

    await tester.tap(find.text('Timeline'));
    await tester.pumpAndSettle();

    expect(find.text('Reached Pickup'), findsOneWidget);
  });
}
