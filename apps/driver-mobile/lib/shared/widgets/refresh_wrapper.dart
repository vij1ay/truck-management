import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

/// Wraps a scrollable [child] in a [RefreshIndicator] so every list-style
/// screen (Dashboard, My Trips, Trip Details tabs, Notifications, Documents,
/// Vehicle Information, Profile) supports the standard pull-to-refresh
/// gesture.
///
/// The [child] should set `physics: const AlwaysScrollableScrollPhysics()` so
/// the gesture still works when the content is shorter than the viewport
/// (e.g. an empty list).
///
/// [onRefresh] defaults to [simulateRefresh] — until the screens are wired to
/// the real API (see `mobile_app_design.md`'s "Backend Readiness" gaps), a
/// pull just re-renders the (static) mock data after a brief delay so the
/// gesture feels real.
class RefreshWrapper extends StatelessWidget {
  const RefreshWrapper({super.key, required this.child, this.onRefresh});

  final Widget child;
  final Future<void> Function()? onRefresh;

  /// Brief artificial delay standing in for a network round-trip.
  static Future<void> simulateRefresh() =>
      Future.delayed(const Duration(milliseconds: 700));

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh ?? simulateRefresh,
      color: AppColors.primary,
      child: child,
    );
  }
}
