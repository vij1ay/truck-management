import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:intl/intl.dart';

import '../../../core/providers/profile_provider.dart';
import '../../../core/providers/trip_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/data/mock_data.dart';
import '../../../shared/models/trip.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/primary_button.dart';
import '../../../shared/widgets/refresh_wrapper.dart';
import '../../../shared/widgets/status_badge.dart';

/// "Active Trip (Map View)" — the map itself is a stylized placeholder
/// (gradient + grid + drawn route) so this base app has no
/// `google_maps_flutter`/API-key dependency. Swap [_MapPlaceholder] for a
/// real map widget once map tiles + live driver location (gap #9 in
/// mobile_app_design.md) are wired up.
class ActiveTripMapScreen extends ConsumerStatefulWidget {
  const ActiveTripMapScreen({super.key});

  @override
  ConsumerState<ActiveTripMapScreen> createState() => _ActiveTripMapScreenState();
}

class _ActiveTripMapScreenState extends ConsumerState<ActiveTripMapScreen> {
  bool _refreshing = false;
  bool _recordingCheckpoint = false;

  Timer? _locationTimer;
  bool _sharingLocation = false;
  DateTime? _lastLocationUpdate;

  @override
  void dispose() {
    _locationTimer?.cancel();
    super.dispose();
  }

  /// Starts/stops the periodic `PATCH /drivers/{id}/location` polling
  /// (Phase 15 MVP, gap #9) based on whether there's a real in-transit trip —
  /// called once per frame from [build], idempotent.
  void _syncLocationTimer(Trip? activeTrip) {
    if (activeTrip != null && _locationTimer == null) {
      _locationTimer = Timer.periodic(const Duration(seconds: 30), (_) => _sendLocation());
      _sendLocation();
    } else if (activeTrip == null && _locationTimer != null) {
      _locationTimer?.cancel();
      _locationTimer = null;
      if (mounted) setState(() => _sharingLocation = false);
    }
  }

  Future<void> _sendLocation() async {
    try {
      if (!await Geolocator.isLocationServiceEnabled()) {
        _stopSharing();
        return;
      }
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied || permission == LocationPermission.deniedForever) {
        _stopSharing();
        return;
      }

      final position = await Geolocator.getCurrentPosition();
      final driver = await ref.read(driverMeProvider.future);
      if (driver == null) return;

      await ref.read(profileRepositoryProvider).updateLocation(
            driver.id,
            position.latitude,
            position.longitude,
          );
      if (mounted) {
        setState(() {
          _sharingLocation = true;
          _lastLocationUpdate = DateTime.now();
        });
      }
    } catch (_) {
      // Location services unavailable/denied (common on desktop test
      // builds) — stop quietly rather than retrying every 30s.
      _stopSharing();
    }
  }

  void _stopSharing() {
    _locationTimer?.cancel();
    _locationTimer = null;
    if (mounted) setState(() => _sharingLocation = false);
  }

  Future<void> _refresh() async {
    setState(() => _refreshing = true);
    ref.invalidate(tripsProvider);
    // Stands in for re-polling the driver's location/ETA — see gap #9 in
    // mobile_app_design.md (live GPS broadcast is Phase 15).
    await RefreshWrapper.simulateRefresh();
    if (mounted) setState(() => _refreshing = false);
  }

  Future<void> _reachedPickup(Trip trip) async {
    final l10n = AppLocalizations.of(context);
    setState(() => _recordingCheckpoint = true);
    try {
      await ref.read(tripRepositoryProvider).addCheckpoint(trip.id, l10n.activeTripReachedPickup);
      ref.invalidate(tripDetailProvider(trip.id));
      ref.invalidate(tripHistoryProvider(trip.id));
      ref.invalidate(tripsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.tripDetailsCheckpointRecorded)),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.clientUpdateFailed)),
        );
      }
    } finally {
      if (mounted) setState(() => _recordingCheckpoint = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    Trip? realActiveTrip;
    for (final t in ref.watch(tripsProvider).valueOrNull ?? const <Trip>[]) {
      if (t.status == TripStatus.active) {
        realActiveTrip = t;
        break;
      }
    }
    final trip = realActiveTrip ?? MockData.activeTrip;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _syncLocationTimer(realActiveTrip);
    });

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.activeTripTitle),
        actions: [
          IconButton(
            icon: _refreshing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
            tooltip: l10n.activeTripRefreshTooltip,
            onPressed: _refreshing ? null : _refresh,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      StatusBadge(
                        status: TripStatus.active,
                        label: l10n.statusInTransit,
                      ),
                      const Icon(Icons.expand_more),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(trip.loadNo, style: theme.textTheme.bodySmall),
                  Text(trip.title, style: theme.textTheme.titleLarge),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _Metric(
                          value: trip.distanceKm == null ? '-' : '${trip.distanceKm!.toStringAsFixed(0)} km',
                          label: l10n.metricRemaining,
                        ),
                      ),
                      Expanded(
                        child: _Metric(
                          value: trip.etaLabel ?? '-',
                          label: l10n.metricEta,
                        ),
                      ),
                    ],
                  ),
                  if (_sharingLocation) ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(Icons.my_location, size: 14, color: AppColors.statusActive),
                        const SizedBox(width: 6),
                        Text(
                          _lastLocationUpdate == null
                              ? l10n.activeTripSharingLocation
                              : '${l10n.activeTripSharingLocation} · ${DateFormat('h:mm a').format(_lastLocationUpdate!)}',
                          style: theme.textTheme.bodySmall?.copyWith(color: AppColors.statusActive),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: const _MapPlaceholder(),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.activeTripNextStep, style: theme.textTheme.bodySmall),
                  const SizedBox(height: 4),
                  Text(
                    l10n.activeTripReachPickupLocation,
                    style: theme.textTheme.titleMedium,
                  ),
                  const SizedBox(height: 12),
                  PrimaryButton(
                    label: l10n.activeTripReachedPickup,
                    loading: _recordingCheckpoint,
                    onPressed: realActiveTrip == null ? null : () => _reachedPickup(realActiveTrip!),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(value, style: theme.textTheme.titleMedium),
        Text(label, style: theme.textTheme.bodySmall),
      ],
    );
  }
}

/// Stylized "map" — gradient background + grid lines + a curved route from a
/// start marker (origin, green) to a destination pin (orange).
class _MapPlaceholder extends StatelessWidget {
  const _MapPlaceholder();

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isDark
              ? [const Color(0xFF1B2333), const Color(0xFF0E1524)]
              : [const Color(0xFFE9EDF4), const Color(0xFFD7DEE9)],
        ),
      ),
      child: CustomPaint(
        painter: _RoutePainter(
          gridColor: (isDark ? Colors.white : Colors.black).withValues(
            alpha: 0.04,
          ),
          routeColor: AppColors.primary,
        ),
        child: const SizedBox.expand(),
      ),
    );
  }
}

class _RoutePainter extends CustomPainter {
  _RoutePainter({required this.gridColor, required this.routeColor});

  final Color gridColor;
  final Color routeColor;

  @override
  void paint(Canvas canvas, Size size) {
    // Subtle grid, evoking a map without real tiles.
    final gridPaint = Paint()
      ..color = gridColor
      ..strokeWidth = 1;
    const step = 32.0;
    for (double x = 0; x < size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), gridPaint);
    }
    for (double y = 0; y < size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    // Route from bottom-left (current location) to top-right (destination).
    final start = Offset(size.width * 0.15, size.height * 0.8);
    final end = Offset(size.width * 0.8, size.height * 0.18);
    final control1 = Offset(size.width * 0.35, size.height * 0.85);
    final control2 = Offset(size.width * 0.55, size.height * 0.35);

    final path = Path()
      ..moveTo(start.dx, start.dy)
      ..cubicTo(
        control1.dx,
        control1.dy,
        control2.dx,
        control2.dy,
        end.dx,
        end.dy,
      );

    final routePaint = Paint()
      ..color = routeColor
      ..strokeWidth = 4
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawPath(path, routePaint);

    // Start marker (current location).
    canvas.drawCircle(start, 8, Paint()..color = AppColors.statusActive);
    canvas.drawCircle(
      start,
      8,
      Paint()
        ..color = Colors.white
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2,
    );

    // Destination pin.
    final pinPaint = Paint()..color = AppColors.statusCancelled;
    canvas.drawCircle(end, 8, pinPaint);
    canvas.drawCircle(
      end,
      8,
      Paint()
        ..color = Colors.white
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2,
    );
  }

  @override
  bool shouldRepaint(covariant _RoutePainter oldDelegate) =>
      oldDelegate.gridColor != gridColor ||
      oldDelegate.routeColor != routeColor;
}
