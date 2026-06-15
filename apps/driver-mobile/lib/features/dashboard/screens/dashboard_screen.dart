import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/trip_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/data/mock_data.dart';
import '../../../shared/models/trip.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/primary_button.dart';
import '../../../shared/widgets/refresh_wrapper.dart';
import '../../../shared/widgets/status_badge.dart';
import '../../../shared/widgets/trip_card.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final trips = ref.watch(tripsProvider).valueOrNull;

    Trip? realActiveTrip;
    if (trips != null) {
      for (final trip in trips) {
        if (trip.status == TripStatus.active) {
          realActiveTrip = trip;
          break;
        }
      }
    }
    final activeTrip = realActiveTrip ?? MockData.activeTrip;
    final upcoming = (trips ?? MockData.trips)
        .where((t) => t.id != activeTrip.id && t.status == TripStatus.assigned)
        .take(2)
        .toList();

    return Scaffold(
      // No app bar chrome here — the bottom-nav "Notifications" tab already
      // covers the bell icon (with its own unread badge, see AppShell), and
      // there's no drawer for a menu icon to open. SafeArea keeps the
      // greeting clear of the status bar.
      body: SafeArea(
        child: RefreshWrapper(
          onRefresh: () async => ref.invalidate(tripsProvider),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          l10n.dashboardGoodMorning,
                          style: theme.textTheme.bodyMedium,
                        ),
                        Text(
                          MockData.driverName,
                          style: theme.textTheme.headlineSmall,
                        ),
                      ],
                    ),
                  ),
                  const CircleAvatar(
                    radius: 24,
                    backgroundColor: AppColors.primary,
                    child: Icon(Icons.person, color: Colors.white),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              _SectionHeader(title: l10n.dashboardTodaysSummary, onViewAll: () {}),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _KpiCard(
                      value: '3',
                      label: l10n.statusAssigned,
                      color: AppColors.statusAssigned,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _KpiCard(
                      value: '1',
                      label: l10n.statusActive,
                      color: AppColors.statusActive,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _KpiCard(
                      value: '2',
                      label: l10n.statusPending,
                      color: AppColors.statusPending,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _KpiCard(
                      value: '8',
                      label: l10n.statusCompleted,
                      color: const Color(0xFF64748B),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              Text(l10n.dashboardActiveTrip, style: theme.textTheme.titleLarge),
              const SizedBox(height: 12),
              AppCard(
                onTap: () => context.go('/trips/${activeTrip.id}'),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Icon(
                          Icons.local_shipping_outlined,
                          color: AppColors.primary,
                        ),
                        StatusBadge(
                          status: TripStatus.active,
                          label: l10n.statusInTransit,
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(activeTrip.title, style: theme.textTheme.titleMedium),
                    const SizedBox(height: 2),
                    Text(activeTrip.loadNo, style: theme.textTheme.bodySmall),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            activeTrip.origin,
                            style: theme.textTheme.bodyMedium,
                          ),
                        ),
                        const Icon(Icons.arrow_forward, size: 16),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            activeTrip.destination,
                            textAlign: TextAlign.end,
                            style: theme.textTheme.bodyMedium,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: _MetricLabel(
                            value: activeTrip.distanceKm == null
                                ? '-'
                                : '${activeTrip.distanceKm!.toStringAsFixed(0)} km',
                            label: l10n.metricRemaining,
                          ),
                        ),
                        Expanded(
                          child: _MetricLabel(
                            value: activeTrip.etaLabel ?? '-',
                            label: l10n.metricEta,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    PrimaryButton(
                      label: l10n.dashboardContinueTrip,
                      icon: Icons.arrow_forward,
                      onPressed: () => context.go('/trips/${activeTrip.id}'),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              _SectionHeader(
                title: l10n.dashboardUpcomingAssignments,
                onViewAll: () => context.go('/trips'),
              ),
              const SizedBox(height: 12),
              for (final trip in upcoming) ...[
                TripCard(
                  trip: trip,
                  onTap: () => context.go('/trips/${trip.id}'),
                ),
                const SizedBox(height: 12),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, this.onViewAll});

  final String title;
  final VoidCallback? onViewAll;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title, style: theme.textTheme.titleLarge),
        if (onViewAll != null)
          TextButton(onPressed: onViewAll, child: Text(l10n.viewAll)),
      ],
    );
  }
}

class _KpiCard extends StatelessWidget {
  const _KpiCard({
    required this.value,
    required this.label,
    required this.color,
  });

  final String value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
      color: color.withValues(alpha: 0.12),
      child: Column(
        children: [
          Text(
            value,
            style: theme.textTheme.headlineSmall?.copyWith(color: color),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: theme.textTheme.bodySmall,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _MetricLabel extends StatelessWidget {
  const _MetricLabel({required this.value, required this.label});

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
