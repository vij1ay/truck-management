import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/portal_provider.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/models/shipment.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/label_badge.dart';
import '../../../shared/widgets/refresh_wrapper.dart';
import '../../../shared/utils/load_status.dart';
import '../utils/portal_error.dart';

String _money(double value) => '₹${value.toStringAsFixed(2)}';

/// Client Portal "Home" tab — a landing summary: company name, a
/// shipment-status breakdown, total outstanding across invoices, and a
/// "Recent Shipments" preview. Mirrors the driver app's `DashboardScreen`,
/// computed client-side from data already fetched by [shipmentsProvider]/
/// [invoicesProvider].
class ClientDashboardScreen extends ConsumerWidget {
  const ClientDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final carriersAsync = ref.watch(myCarriersProvider);
    final shipmentsAsync = ref.watch(shipmentsProvider(null));
    final invoicesAsync = ref.watch(invoicesProvider(null));

    final carriers = carriersAsync.valueOrNull;
    final companyName = (carriers != null && carriers.isNotEmpty)
        ? carriers.first.client.companyName
        : null;

    return Scaffold(
      body: SafeArea(
        child: RefreshWrapper(
          onRefresh: () async {
            ref.invalidate(myCarriersProvider);
            ref.invalidate(shipmentsProvider);
            ref.invalidate(invoicesProvider);
          },
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
            children: [
              Text(l10n.clientDashboardGreeting, style: theme.textTheme.bodyMedium),
              if (companyName != null)
                Text(companyName, style: theme.textTheme.headlineSmall),
              const SizedBox(height: 24),

              Text(l10n.clientShipmentSummary, style: theme.textTheme.titleLarge),
              const SizedBox(height: 12),
              shipmentsAsync.when(
                data: (shipments) => _StatusSummaryGrid(shipments: shipments),
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) =>
                    Text(portalErrorMessage(l10n, err), style: theme.textTheme.bodyMedium),
              ),
              const SizedBox(height: 24),

              invoicesAsync.when(
                data: (invoices) {
                  final totalOutstanding =
                      invoices.fold<double>(0, (sum, inv) => sum + inv.outstandingAmount);
                  return AppCard(
                    onTap: () => context.go('/client/invoices'),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(l10n.clientTotalOutstanding, style: theme.textTheme.bodyMedium),
                            const SizedBox(height: 4),
                            Text(_money(totalOutstanding), style: theme.textTheme.headlineSmall),
                          ],
                        ),
                        const Icon(Icons.chevron_right),
                      ],
                    ),
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) =>
                    Text(portalErrorMessage(l10n, err), style: theme.textTheme.bodyMedium),
              ),
              const SizedBox(height: 24),

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(l10n.clientRecentShipments, style: theme.textTheme.titleLarge),
                  TextButton(
                    onPressed: () => context.go('/client/shipments'),
                    child: Text(l10n.viewAll),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              shipmentsAsync.when(
                data: (shipments) {
                  if (shipments.isEmpty) {
                    return Text(l10n.clientShipmentsEmpty, style: theme.textTheme.bodyMedium);
                  }
                  return Column(
                    children: [
                      for (final shipment in shipments.take(3)) ...[
                        _RecentShipmentTile(
                          shipment: shipment,
                          onTap: () => context.go('/client/shipments/${shipment.id}'),
                        ),
                        const SizedBox(height: 12),
                      ],
                    ],
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) =>
                    Text(portalErrorMessage(l10n, err), style: theme.textTheme.bodyMedium),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// A 2-row, 3-column grid of status counts (Draft/Confirmed/Allocated/In
/// Transit/Delivered/Cancelled), computed client-side from [shipments].
class _StatusSummaryGrid extends StatelessWidget {
  const _StatusSummaryGrid({required this.shipments});

  final List<Shipment> shipments;

  @override
  Widget build(BuildContext context) {
    final counts = <String, int>{for (final status in loadStatuses) status: 0};
    for (final shipment in shipments) {
      counts[shipment.status] = (counts[shipment.status] ?? 0) + 1;
    }
    final l10n = AppLocalizations.of(context);

    Widget tile(String status) => Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: _KpiCard(
              value: '${counts[status] ?? 0}',
              label: loadStatusLabel(l10n, status),
              color: loadStatusColor(status),
            ),
          ),
        );

    return Column(
      children: [
        Row(children: [for (final s in loadStatuses.take(3)) tile(s)]),
        const SizedBox(height: 12),
        Row(children: [for (final s in loadStatuses.skip(3)) tile(s)]),
      ],
    );
  }
}

class _KpiCard extends StatelessWidget {
  const _KpiCard({required this.value, required this.label, required this.color});

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
          Text(value, style: theme.textTheme.headlineSmall?.copyWith(color: color)),
          const SizedBox(height: 4),
          Text(label, style: theme.textTheme.bodySmall, textAlign: TextAlign.center),
        ],
      ),
    );
  }
}

class _RecentShipmentTile extends StatelessWidget {
  const _RecentShipmentTile({required this.shipment, this.onTap});

  final Shipment shipment;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final muted = theme.textTheme.bodySmall?.color;

    return AppCard(
      onTap: onTap,
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(shipment.loadNo, style: theme.textTheme.titleMedium),
                const SizedBox(height: 2),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        shipment.origin,
                        style: theme.textTheme.bodySmall,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Icon(Icons.arrow_forward, size: 12, color: muted),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        shipment.destination,
                        style: theme.textTheme.bodySmall,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          LabelBadge(
            label: loadStatusLabel(l10n, shipment.status),
            color: loadStatusColor(shipment.status),
          ),
        ],
      ),
    );
  }
}
