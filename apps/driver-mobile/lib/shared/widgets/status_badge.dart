import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../models/trip.dart';

/// A small colored pill — "ASSIGNED" / "ACTIVE" / "PENDING" / "IN TRANSIT" /
/// "COMPLETED" / "CANCELLED" — matching the reference design's status chips.
class StatusBadge extends StatelessWidget {
  const StatusBadge({super.key, required this.status, this.label});

  final TripStatus status;

  /// Override the default label (e.g. "IN TRANSIT" instead of "ACTIVE").
  final String? label;

  Color get _color {
    switch (status) {
      case TripStatus.assigned:
        return AppColors.statusAssigned;
      case TripStatus.active:
        return AppColors.statusActive;
      case TripStatus.pending:
        return AppColors.statusPending;
      case TripStatus.completed:
        return AppColors.statusCompleted;
      case TripStatus.cancelled:
        return AppColors.statusCancelled;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _color;
    final text = (label ?? status.label).toUpperCase();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        text,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: color,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
