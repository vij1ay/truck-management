import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/notification_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/models/notification_item.dart';
import '../../../shared/models/shipment_history_entry.dart';
import '../../../shared/models/trip.dart';
import '../../../shared/utils/load_status.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/refresh_wrapper.dart';

/// Maps a (trip, latest-history-entry) pair to a localized [NotificationItem]
/// — a checkpoint (from_status == to_status) shows its `remarks` as the
/// title; a real status transition is mapped to a friendlier title.
NotificationItem _notificationFor(AppLocalizations l10n, Trip trip, ShipmentHistoryEntry entry) {
  final isCheckpoint = entry.fromStatus != null && entry.fromStatus == entry.toStatus;
  NotificationType type;
  String title;

  if (isCheckpoint) {
    type = NotificationType.system;
    title = entry.remarks ?? loadStatusLabel(l10n, entry.toStatus);
  } else {
    switch (entry.toStatus) {
      case 'allocated':
        type = NotificationType.newTrip;
        title = l10n.notifNewTripTitle;
      case 'in_transit':
        type = NotificationType.reminder;
        title = l10n.notifTripStartedTitle;
      case 'delivered':
        type = NotificationType.completed;
        title = l10n.notifTripCompletedTitle;
      case 'cancelled':
        type = NotificationType.tripCancelled;
        title = l10n.notifTripCancelledTitle;
      default:
        type = NotificationType.system;
        title = loadStatusLabel(l10n, entry.toStatus);
    }
  }

  return NotificationItem(
    id: entry.id,
    type: type,
    title: title,
    message: trip.loadNo,
    time: entry.changedAt,
    group: 'recent',
    read: true,
  );
}

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final activityAsync = ref.watch(driverRecentActivityProvider);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.notificationsTitle)),
      body: RefreshWrapper(
        onRefresh: () async => ref.invalidate(driverRecentActivityProvider),
        child: activityAsync.when(
          data: (activity) {
            if (activity.isEmpty) {
              return LayoutBuilder(
                builder: (context, constraints) => ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: [
                    SizedBox(
                      height: constraints.maxHeight,
                      child: Center(
                        child: Text(l10n.notificationsEmpty, style: theme.textTheme.bodyMedium),
                      ),
                    ),
                  ],
                ),
              );
            }
            return ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              children: [
                Text(l10n.notificationsRecentActivity, style: theme.textTheme.titleSmall),
                const SizedBox(height: 8),
                for (final (trip, entry) in activity) ...[
                  _NotificationTile(item: _notificationFor(l10n, trip, entry)),
                  const SizedBox(height: 12),
                ],
              ],
            );
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (_, __) => LayoutBuilder(
            builder: (context, constraints) => ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                SizedBox(
                  height: constraints.maxHeight,
                  child: Center(
                    child: Text(l10n.notificationsEmpty, style: theme.textTheme.bodyMedium),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({required this.item});

  final NotificationItem item;

  (IconData, Color) get _iconAndColor {
    switch (item.type) {
      case NotificationType.newTrip:
        return (Icons.local_shipping_outlined, AppColors.statusAssigned);
      case NotificationType.reminder:
        return (Icons.notifications_active_outlined, AppColors.statusPending);
      case NotificationType.documentExpiry:
        return (Icons.warning_amber_outlined, AppColors.statusCancelled);
      case NotificationType.completed:
        return (Icons.check_circle_outline, AppColors.statusActive);
      case NotificationType.tripCancelled:
        return (Icons.cancel_outlined, AppColors.statusCancelled);
      case NotificationType.system:
        return (Icons.info_outline, AppColors.statusAssigned);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (icon, color) = _iconAndColor;

    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        item.title,
                        style: theme.textTheme.titleSmall,
                      ),
                    ),
                    Text(item.time, style: theme.textTheme.bodySmall),
                  ],
                ),
                const SizedBox(height: 4),
                Text(item.message, style: theme.textTheme.bodyMedium),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
