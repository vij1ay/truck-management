import 'package:flutter/material.dart';

import '../models/trip.dart';
import 'app_card.dart';
import 'status_badge.dart';

/// A trip summary card — used on the Dashboard ("Upcoming Assignments") and
/// My Trips screens. Tapping navigates to Trip Details.
class TripCard extends StatelessWidget {
  const TripCard({super.key, required this.trip, this.onTap, this.statusLabel});

  final Trip trip;
  final VoidCallback? onTap;

  /// Override the badge text (e.g. "IN TRANSIT" on the active trip card).
  final String? statusLabel;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.color;

    return AppCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              StatusBadge(status: trip.status, label: statusLabel),
              CircleAvatar(
                radius: 16,
                backgroundColor: theme.colorScheme.primary.withValues(
                  alpha: 0.12,
                ),
                child: Icon(
                  Icons.local_shipping_outlined,
                  size: 16,
                  color: theme.colorScheme.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(trip.loadNo, style: theme.textTheme.bodySmall),
          const SizedBox(height: 2),
          Text(trip.title, style: theme.textTheme.titleMedium),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: Text(
                  trip.origin,
                  style: theme.textTheme.bodyMedium,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Icon(Icons.arrow_forward, size: 16, color: muted),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  trip.destination,
                  textAlign: TextAlign.end,
                  style: theme.textTheme.bodyMedium,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Icon(Icons.calendar_today_outlined, size: 14, color: muted),
              const SizedBox(width: 6),
              Text(trip.pickupDate, style: theme.textTheme.bodySmall),
              const SizedBox(width: 16),
              Icon(Icons.access_time, size: 14, color: muted),
              const SizedBox(width: 6),
              Text(trip.pickupTime, style: theme.textTheme.bodySmall),
            ],
          ),
        ],
      ),
    );
  }
}
