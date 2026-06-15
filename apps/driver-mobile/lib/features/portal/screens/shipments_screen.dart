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
import 'carrier_filter_bar.dart';

/// "My Shipments" — `GET /portal/loads`, with a status filter [TabBar], an
/// optional carrier filter (when linked to more than one carrier), and a "+"
/// action to submit a new booking request.
class ShipmentsScreen extends ConsumerStatefulWidget {
  const ShipmentsScreen({super.key});

  @override
  ConsumerState<ShipmentsScreen> createState() => _ShipmentsScreenState();
}

class _ShipmentsScreenState extends ConsumerState<ShipmentsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  String? _selectedCarrier;

  /// `null` ("All") followed by every [loadStatuses] value.
  static const _filters = <String?>[null, ...loadStatuses];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _filters.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.clientShipmentsTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: l10n.clientNewShipment,
            onPressed: () => context.push('/client/shipments/new'),
          ),
          const SizedBox(width: 8),
        ],
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: [for (final status in _filters) Tab(text: loadStatusLabel(l10n, status))],
        ),
      ),
      body: Column(
        children: [
          CarrierFilterBar(
            selected: _selectedCarrier,
            onSelect: (carrier) => setState(() => _selectedCarrier = carrier),
          ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                for (final status in _filters)
                  _ShipmentList(status: status, carrierFilter: _selectedCarrier),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ShipmentList extends ConsumerWidget {
  const _ShipmentList({required this.status, this.carrierFilter});

  final String? status;
  final String? carrierFilter;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final shipmentsAsync = ref.watch(shipmentsProvider(status));

    return RefreshWrapper(
      onRefresh: () async => ref.invalidate(shipmentsProvider(status)),
      child: shipmentsAsync.when(
        data: (allShipments) {
          final shipments = carrierFilter == null
              ? allShipments
              : allShipments.where((s) => s.carrierName == carrierFilter).toList();

          if (shipments.isEmpty) {
            return _CenteredMessage(message: l10n.clientShipmentsEmpty);
          }
          return ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: shipments.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final shipment = shipments[index];
              return _ShipmentCard(
                shipment: shipment,
                onTap: () => context.push('/client/shipments/${shipment.id}'),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => _CenteredMessage(message: portalErrorMessage(l10n, err)),
      ),
    );
  }
}

class _CenteredMessage extends StatelessWidget {
  const _CenteredMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          SizedBox(
            height: constraints.maxHeight,
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  message,
                  style: Theme.of(context).textTheme.bodyMedium,
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ShipmentCard extends StatelessWidget {
  const _ShipmentCard({required this.shipment, this.onTap});

  final Shipment shipment;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final muted = theme.textTheme.bodySmall?.color;

    return AppCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(shipment.loadNo, style: theme.textTheme.titleMedium),
              LabelBadge(
                label: loadStatusLabel(l10n, shipment.status),
                color: loadStatusColor(shipment.status),
              ),
            ],
          ),
          if (shipment.carrierName != null) ...[
            const SizedBox(height: 2),
            Text(shipment.carrierName!, style: theme.textTheme.bodySmall),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: Text(
                  shipment.origin,
                  style: theme.textTheme.bodyMedium,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Icon(Icons.arrow_forward, size: 16, color: muted),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  shipment.destination,
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
              Text(shipment.pickupDate, style: theme.textTheme.bodySmall),
            ],
          ),
        ],
      ),
    );
  }
}
