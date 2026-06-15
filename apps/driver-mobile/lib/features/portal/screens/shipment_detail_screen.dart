import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/providers/portal_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/models/shipment.dart';
import '../../../shared/models/shipment_document.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/document_image_dialog.dart';
import '../../../shared/widgets/info_row.dart';
import '../../../shared/widgets/label_badge.dart';
import '../../../shared/widgets/refresh_wrapper.dart';
import '../../../shared/utils/goods_type.dart';
import '../../../shared/utils/load_status.dart';
import '../utils/portal_error.dart';
import 'cancel_shipment_dialog.dart';

String _money(double? value) => value == null ? '-' : '₹${value.toStringAsFixed(2)}';

/// Opens [address] in the device's default Maps app (or browser fallback)
/// via a universal Google Maps search URL.
Future<void> _openInMaps(String address) {
  final uri = Uri.parse(
    'https://www.google.com/maps/search/?api=1&query=${Uri.encodeComponent(address)}',
  );
  return launchUrl(uri, mode: LaunchMode.externalApplication);
}

/// Shipment detail (`GET /portal/loads/{id}`) — Overview / Timeline /
/// Documents tabs, mirroring the admin-frontend's shipment-detail page and
/// `trip_details_screen.dart`'s tab layout.
class ShipmentDetailScreen extends ConsumerStatefulWidget {
  const ShipmentDetailScreen({super.key, required this.shipmentId});

  final String shipmentId;

  @override
  ConsumerState<ShipmentDetailScreen> createState() => _ShipmentDetailScreenState();
}

class _ShipmentDetailScreenState extends ConsumerState<ShipmentDetailScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _edit(Shipment shipment) async {
    await context.push('/client/shipments/${shipment.id}/edit', extra: shipment);
    // The edit screen invalidates shipmentDetailProvider/shipmentsProvider on
    // success, so this just needs to rebuild once we're back.
    if (mounted) setState(() {});
  }

  Future<void> _cancel(Shipment shipment) async {
    final l10n = AppLocalizations.of(context);
    final reason = await showCancelShipmentDialog(context);
    if (reason == null) return;

    try {
      await ref.read(portalRepositoryProvider).cancelShipment(shipment.id, reason);
      ref.invalidate(shipmentDetailProvider(shipment.id));
      ref.invalidate(shipmentsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.clientShipmentCancelled)),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.clientUpdateFailed)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final shipmentAsync = ref.watch(shipmentDetailProvider(widget.shipmentId));
    final shipment = shipmentAsync.valueOrNull;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.clientShipmentDetailsTitle),
        actions: [
          if (shipment != null && shipment.isEditable) ...[
            IconButton(
              icon: const Icon(Icons.edit_outlined),
              tooltip: l10n.clientEditShipment,
              onPressed: () => _edit(shipment),
            ),
            IconButton(
              icon: const Icon(Icons.cancel_outlined),
              tooltip: l10n.clientCancelShipment,
              onPressed: () => _cancel(shipment),
            ),
          ],
        ],
      ),
      body: shipmentAsync.when(
        data: (shipment) => Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              child: AppCard(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(shipment.loadNo, style: theme.textTheme.titleLarge),
                          if (shipment.carrierName != null)
                            Text(shipment.carrierName!, style: theme.textTheme.bodyMedium),
                        ],
                      ),
                    ),
                    LabelBadge(
                      label: loadStatusLabel(l10n, shipment.status),
                      color: loadStatusColor(shipment.status),
                    ),
                  ],
                ),
              ),
            ),
            TabBar(
              controller: _tabController,
              isScrollable: true,
              tabAlignment: TabAlignment.start,
              tabs: [
                Tab(text: l10n.tripDetailsTabOverview),
                Tab(text: l10n.tripDetailsTabTimeline),
                Tab(text: l10n.documentsTitle),
              ],
            ),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _OverviewTab(shipment: shipment),
                  _TimelineTab(shipmentId: widget.shipmentId),
                  _DocumentsTab(shipmentId: widget.shipmentId),
                ],
              ),
            ),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => Center(
          child: Text(l10n.clientShipmentsEmpty, style: theme.textTheme.bodyMedium),
        ),
      ),
    );
  }
}

class _OverviewTab extends StatelessWidget {
  const _OverviewTab({required this.shipment});

  final Shipment shipment;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    return RefreshWrapper(
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        children: [
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                InfoRow(
                  icon: Icons.trip_origin,
                  label: l10n.tripDetailsPickupLocation,
                  value: shipment.origin,
                  trailing: Tooltip(
                    message: l10n.shipmentOpenInMaps,
                    child: const Icon(Icons.map_outlined),
                  ),
                  onTap: () => _openInMaps(shipment.origin),
                ),
                const Divider(height: 24),
                InfoRow(
                  icon: Icons.flag_outlined,
                  label: l10n.tripDetailsDeliveryLocation,
                  value: shipment.destination,
                  trailing: Tooltip(
                    message: l10n.shipmentOpenInMaps,
                    child: const Icon(Icons.map_outlined),
                  ),
                  onTap: () => _openInMaps(shipment.destination),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                InfoRow(label: l10n.bookingPickupDate, value: shipment.pickupDate),
                if (shipment.expectedDeliveryDate != null) ...[
                  const Divider(height: 24),
                  InfoRow(
                    label: l10n.shipmentExpectedDelivery,
                    value: shipment.expectedDeliveryDate!,
                  ),
                ],
                if (shipment.actualDeliveryDate != null) ...[
                  const Divider(height: 24),
                  InfoRow(
                    label: l10n.shipmentActualDelivery,
                    value: shipment.actualDeliveryDate!,
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppCard(
            child: Row(
              children: [
                Expanded(
                  child: InfoTile(
                    label: l10n.shipmentGoodsType,
                    value: goodsTypeLabel(shipment.goodsType),
                  ),
                ),
                if (shipment.distanceKm != null)
                  Expanded(
                    child: InfoTile(
                      label: l10n.tripDetailsDistance,
                      value: '${shipment.distanceKm!.toStringAsFixed(0)} km',
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppCard(
            child: Row(
              children: [
                if (shipment.weightKg != null)
                  Expanded(
                    child: InfoTile(
                      label: l10n.shipmentWeight,
                      value: '${shipment.weightKg} kg',
                    ),
                  ),
                if (shipment.volumeCbm != null)
                  Expanded(
                    child: InfoTile(
                      label: l10n.shipmentVolume,
                      value: '${shipment.volumeCbm} m³',
                    ),
                  ),
                if (shipment.quantity != null)
                  Expanded(
                    child: InfoTile(
                      label: l10n.shipmentQuantity,
                      value: '${shipment.quantity}',
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                InfoRow(
                  label: l10n.shipmentFreightAmount,
                  value: _money(shipment.freightAmount),
                ),
                const Divider(height: 24),
                InfoRow(
                  label: l10n.shipmentAdvanceAmount,
                  value: _money(shipment.advanceAmount),
                ),
                const Divider(height: 24),
                InfoRow(
                  label: l10n.shipmentBalanceAmount,
                  value: _money(shipment.balanceAmount),
                  valueColor: AppColors.statusPending,
                ),
              ],
            ),
          ),
          if (shipment.specialInstructions?.isNotEmpty ?? false) ...[
            const SizedBox(height: 16),
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.tripDetailsSpecialInstructions, style: theme.textTheme.titleSmall),
                  const SizedBox(height: 8),
                  Text(shipment.specialInstructions!, style: theme.textTheme.bodyMedium),
                ],
              ),
            ),
          ],
          if (shipment.notes?.isNotEmpty ?? false) ...[
            const SizedBox(height: 16),
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.notesLabel, style: theme.textTheme.titleSmall),
                  const SizedBox(height: 8),
                  Text(shipment.notes!, style: theme.textTheme.bodyMedium),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _TimelineTab extends ConsumerWidget {
  const _TimelineTab({required this.shipmentId});

  final String shipmentId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final historyAsync = ref.watch(shipmentHistoryProvider(shipmentId));

    return RefreshWrapper(
      onRefresh: () async => ref.invalidate(shipmentHistoryProvider(shipmentId)),
      child: historyAsync.when(
        data: (history) {
          if (history.isEmpty) {
            return LayoutBuilder(
              builder: (context, constraints) => ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                children: [
                  SizedBox(
                    height: constraints.maxHeight,
                    child: Center(
                      child: Text(l10n.shipmentNoHistory, style: theme.textTheme.bodyMedium),
                    ),
                  ),
                ],
              ),
            );
          }
          return ListView.builder(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: history.length,
            itemBuilder: (context, index) {
              final entry = history[index];
              final isLast = index == history.length - 1;
              // A checkpoint (e.g. "Reached Pickup", added via
              // POST /loads/{id}/checkpoints) has from_status == to_status —
              // show its remarks as the title rather than "X → X", and don't
              // repeat it as a subtitle below.
              final isCheckpoint = entry.fromStatus != null && entry.fromStatus == entry.toStatus;
              final title = entry.fromStatus == null
                  ? loadStatusLabel(l10n, entry.toStatus)
                  : isCheckpoint
                      ? (entry.remarks ?? loadStatusLabel(l10n, entry.toStatus))
                      : '${loadStatusLabel(l10n, entry.fromStatus)} → ${loadStatusLabel(l10n, entry.toStatus)}';
              final showRemarksSubtitle =
                  !isCheckpoint && entry.remarks != null && entry.remarks!.isNotEmpty;

              return IntrinsicHeight(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Column(
                      children: [
                        Container(
                          width: 12,
                          height: 12,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: loadStatusColor(entry.toStatus),
                          ),
                        ),
                        if (!isLast)
                          Expanded(
                            child: Container(width: 2, color: theme.dividerTheme.color),
                          ),
                      ],
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.only(bottom: 24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(title, style: theme.textTheme.titleSmall),
                            const SizedBox(height: 2),
                            Text(entry.changedAt, style: theme.textTheme.bodySmall),
                            if (showRemarksSubtitle) ...[
                              const SizedBox(height: 2),
                              Text(entry.remarks!, style: theme.textTheme.bodySmall),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
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
                  child: Text(l10n.shipmentNoHistory, style: theme.textTheme.bodyMedium),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DocumentsTab extends ConsumerStatefulWidget {
  const _DocumentsTab({required this.shipmentId});

  final String shipmentId;

  @override
  ConsumerState<_DocumentsTab> createState() => _DocumentsTabState();
}

class _DocumentsTabState extends ConsumerState<_DocumentsTab> {
  bool _uploading = false;

  Future<void> _upload() async {
    final l10n = AppLocalizations.of(context);
    final picked = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      maxWidth: 1600,
      imageQuality: 85,
    );
    if (picked == null) return;

    setState(() => _uploading = true);
    try {
      await ref.read(portalRepositoryProvider).uploadShipmentDocument(widget.shipmentId, picked.path);
      ref.invalidate(shipmentDocumentsProvider(widget.shipmentId));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.clientDocumentUploaded)),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.clientDocumentUploadFailed)),
        );
      }
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  void _view(ShipmentDocument doc) {
    showDialog(
      context: context,
      builder: (context) => DocumentImageDialog(
        provider: shipmentDocumentBytesProvider((widget.shipmentId, doc.id)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final docsAsync = ref.watch(shipmentDocumentsProvider(widget.shipmentId));

    return Column(
      children: [
        Expanded(
          child: RefreshWrapper(
            onRefresh: () async => ref.invalidate(shipmentDocumentsProvider(widget.shipmentId)),
            child: docsAsync.when(
              data: (docs) {
                if (docs.isEmpty) {
                  return LayoutBuilder(
                    builder: (context, constraints) => ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: [
                        SizedBox(
                          height: constraints.maxHeight,
                          child: Center(
                            child: Text(l10n.shipmentNoDocuments, style: theme.textTheme.bodyMedium),
                          ),
                        ),
                      ],
                    ),
                  );
                }
                return ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  itemCount: docs.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final doc = docs[index];
                    return AppCard(
                      onTap: doc.hasFile ? () => _view(doc) : null,
                      child: Row(
                        children: [
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: AppColors.primary.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Icon(
                              doc.hasFile ? Icons.image_outlined : Icons.description_outlined,
                              color: AppColors.primary,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(doc.fileName, style: theme.textTheme.titleSmall),
                                Text(doc.documentType, style: theme.textTheme.bodySmall),
                              ],
                            ),
                          ),
                          if (doc.hasFile) const Icon(Icons.chevron_right),
                        ],
                      ),
                    );
                  },
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => LayoutBuilder(
                builder: (context, constraints) => ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: [
                    SizedBox(
                      height: constraints.maxHeight,
                      child: Center(
                        child: Text(portalErrorMessage(l10n, err), style: theme.textTheme.bodyMedium),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: OutlinedButton.icon(
              onPressed: _uploading ? null : _upload,
              icon: _uploading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.add_photo_alternate_outlined),
              label: Text(l10n.clientUploadDocument),
            ),
          ),
        ),
      ],
    );
  }
}
