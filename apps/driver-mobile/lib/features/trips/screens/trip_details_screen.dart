import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/profile_provider.dart';
import '../../../core/providers/trip_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/models/trip.dart';
import '../../../shared/utils/load_status.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/document_image_dialog.dart';
import '../../../shared/widgets/info_row.dart';
import '../../../shared/widgets/primary_button.dart';
import '../../../shared/widgets/refresh_wrapper.dart';
import '../../../shared/widgets/status_badge.dart';

class TripDetailsScreen extends ConsumerStatefulWidget {
  const TripDetailsScreen({super.key, required this.tripId});

  final String tripId;

  @override
  ConsumerState<TripDetailsScreen> createState() => _TripDetailsScreenState();
}

class _TripDetailsScreenState extends ConsumerState<TripDetailsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final tripAsync = ref.watch(tripDetailProvider(widget.tripId));

    return tripAsync.when(
      data: (rawTrip) {
        final driver = ref.watch(driverMeProvider).valueOrNull;
        final truck = driver?.currentTruck;
        final trip = rawTrip.copyWith(
          truckNumber: truck?.registrationNo,
          truckModel: truck?.displayName,
          driverName: driver?.fullName,
        );

        return Scaffold(
          appBar: AppBar(
            title: Text(l10n.tripDetailsTitle),
            actions: [
              IconButton(icon: const Icon(Icons.more_vert), onPressed: () {}),
            ],
          ),
          body: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                child: AppCard(
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(
                                  trip.loadNo,
                                  style: theme.textTheme.titleLarge,
                                ),
                                const SizedBox(width: 8),
                                StatusBadge(
                                  status: trip.status,
                                  label: trip.status == TripStatus.active
                                      ? l10n.statusInTransit
                                      : null,
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(trip.title, style: theme.textTheme.bodyMedium),
                            if (trip.clientName != null)
                              Text(
                                l10n.tripDetailsClientLabel(trip.clientName!),
                                style: theme.textTheme.bodySmall,
                              ),
                            const SizedBox(height: 8),
                            Text(
                              l10n.tripDetailsTruckInfo(trip.truckNumber ?? '-', trip.truckModel ?? '-'),
                              style: theme.textTheme.bodySmall,
                            ),
                            Text(
                              l10n.tripDetailsDriverInfo(trip.driverName ?? '-'),
                              style: theme.textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                      Container(
                        width: 44,
                        height: 44,
                        decoration: const BoxDecoration(
                          color: AppColors.primary,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.call,
                          color: Colors.white,
                          size: 20,
                        ),
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
                  Tab(text: l10n.tripDetailsTabNotes),
                ],
              ),
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _OverviewTab(trip: trip),
                    _TimelineTab(tripId: widget.tripId),
                    _DocumentsTab(tripId: widget.tripId),
                    const _NotesTab(),
                  ],
                ),
              ),
            ],
          ),
        );
      },
      loading: () => Scaffold(
        appBar: AppBar(title: Text(l10n.tripDetailsTitle)),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (_, __) => Scaffold(
        appBar: AppBar(title: Text(l10n.tripDetailsTitle)),
        body: Center(child: Text(l10n.tripsLoadError, style: theme.textTheme.bodyMedium)),
      ),
    );
  }
}

class _OverviewTab extends ConsumerStatefulWidget {
  const _OverviewTab({required this.trip});

  final Trip trip;

  @override
  ConsumerState<_OverviewTab> createState() => _OverviewTabState();
}

class _OverviewTabState extends ConsumerState<_OverviewTab> {
  bool _actionInProgress = false;

  Future<void> _runAction(Future<void> Function() action, {String? successMessage}) async {
    final l10n = AppLocalizations.of(context);
    setState(() => _actionInProgress = true);
    try {
      await action();
      ref.invalidate(tripDetailProvider(widget.trip.id));
      ref.invalidate(tripsProvider);
      ref.invalidate(tripHistoryProvider(widget.trip.id));
      if (mounted && successMessage != null) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(successMessage)));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.clientUpdateFailed)),
        );
      }
    } finally {
      if (mounted) setState(() => _actionInProgress = false);
    }
  }

  Future<void> _startTrip() async {
    final repo = ref.read(tripRepositoryProvider);
    await _runAction(() => repo.startTrip(widget.trip.id));
  }

  Future<void> _checkpoint(String label) async {
    final repo = ref.read(tripRepositoryProvider);
    final l10n = AppLocalizations.of(context);
    await _runAction(
      () => repo.addCheckpoint(widget.trip.id, label),
      successMessage: l10n.tripDetailsCheckpointRecorded,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final trip = widget.trip;

    return RefreshWrapper(
      onRefresh: () async {
        ref.invalidate(tripDetailProvider(trip.id));
        ref.invalidate(tripsProvider);
      },
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
                  value: trip.pickupAddress ?? trip.origin,
                ),
                const Divider(height: 24),
                InfoRow(
                  icon: Icons.flag_outlined,
                  label: l10n.tripDetailsDeliveryLocation,
                  value: trip.deliveryAddress ?? trip.destination,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppCard(
            child: Row(
              children: [
                Expanded(
                  child: InfoTile(
                    label: l10n.tripDetailsDistance,
                    value: trip.distanceKm == null ? '-' : '${trip.distanceKm!.toStringAsFixed(0)} km',
                  ),
                ),
                Expanded(
                  child: InfoTile(
                    label: l10n.tripDetailsLoadWeight,
                    value: trip.weightTonnes == null ? '-' : '${trip.weightTonnes} Tonnes',
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppCard(
            child: InfoTile(
              label: l10n.tripDetailsDeparture,
              value: trip.departure ?? '${trip.pickupDate}, ${trip.pickupTime}',
            ),
          ),
          const SizedBox(height: 24),

          if (trip.canStart)
            PrimaryButton(
              label: l10n.tripDetailsStartTrip,
              icon: Icons.play_arrow,
              loading: _actionInProgress,
              onPressed: _startTrip,
            ),

          if (trip.isInTransit) ...[
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _actionInProgress ? null : () => _checkpoint(l10n.tripDetailsCheckpointLoaded),
                    child: Text(l10n.tripDetailsCheckpointLoaded),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton(
                    onPressed: _actionInProgress
                        ? null
                        : () => _checkpoint(l10n.tripDetailsCheckpointReachedDestination),
                    child: Text(l10n.tripDetailsCheckpointReachedDestination),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            PrimaryButton(
              label: l10n.tripDetailsMarkDelivered,
              icon: Icons.local_shipping_outlined,
              onPressed: _actionInProgress ? null : () => context.push('/trips/${trip.id}/pod'),
            ),
            const SizedBox(height: 12),
          ],

          OutlinedButton.icon(
            onPressed: () => context.go('/map'),
            icon: const Icon(Icons.alt_route),
            label: Text(l10n.tripDetailsViewRoute),
          ),
          const SizedBox(height: 8),
          Text(
            l10n.tripDetailsMapPreviewNote,
            style: theme.textTheme.bodySmall,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _TimelineTab extends ConsumerWidget {
  const _TimelineTab({required this.tripId});

  final String tripId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final historyAsync = ref.watch(tripHistoryProvider(tripId));

    return RefreshWrapper(
      onRefresh: () async => ref.invalidate(tripHistoryProvider(tripId)),
      child: historyAsync.when(
        data: (history) {
          if (history.isEmpty) {
            return _CenteredMessage(message: l10n.shipmentNoHistory);
          }
          return ListView.builder(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: history.length,
            itemBuilder: (context, index) {
              final entry = history[index];
              final isLast = index == history.length - 1;
              // A checkpoint (e.g. "Reached Pickup") has from_status ==
              // to_status — show its remarks as the title rather than "X → X".
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
        error: (_, __) => _CenteredMessage(message: l10n.shipmentNoHistory),
      ),
    );
  }
}

class _DocumentsTab extends ConsumerWidget {
  const _DocumentsTab({required this.tripId});

  final String tripId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final docsAsync = ref.watch(tripDocumentsProvider(tripId));

    return RefreshWrapper(
      onRefresh: () async => ref.invalidate(tripDocumentsProvider(tripId)),
      child: docsAsync.when(
        data: (docs) {
          if (docs.isEmpty) {
            return _CenteredMessage(message: l10n.tripDetailsNoDocuments);
          }
          return ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: docs.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final doc = docs[index];
              return AppCard(
                onTap: doc.hasFile
                    ? () => showDialog(
                          context: context,
                          builder: (context) => DocumentImageDialog(
                            provider: tripDocumentBytesProvider((tripId, doc.id)),
                          ),
                        )
                    : null,
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
        error: (_, __) => _CenteredMessage(message: l10n.tripDetailsNoDocuments),
      ),
    );
  }
}

class _NotesTab extends StatelessWidget {
  const _NotesTab();

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
                Text(l10n.tripDetailsSpecialInstructions, style: theme.textTheme.titleSmall),
                const SizedBox(height: 8),
                Text(
                  l10n.tripDetailsHazardousNote,
                  style: theme.textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ],
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
