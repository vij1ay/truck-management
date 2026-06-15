import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/profile_provider.dart';
import '../../../core/providers/trip_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/models/shipment_document.dart';
import '../../../shared/utils/document_type.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/document_image_dialog.dart';
import '../../../shared/widgets/refresh_wrapper.dart';

class DocumentsScreen extends ConsumerStatefulWidget {
  const DocumentsScreen({super.key});

  @override
  ConsumerState<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends ConsumerState<DocumentsScreen>
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.documentsTitle),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(text: l10n.documentsTabVehicle),
            Tab(text: l10n.documentsTabDriver),
            Tab(text: l10n.documentsTabTrip),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _VehicleDocumentsTab(),
          _DriverDocumentsTab(),
          _TripDocumentsTab(),
        ],
      ),
    );
  }
}

class _VehicleDocumentsTab extends ConsumerWidget {
  const _VehicleDocumentsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final driver = ref.watch(driverMeProvider).valueOrNull;
    final truck = driver?.currentTruck;

    if (truck == null) {
      return _CenteredMessage(message: l10n.documentsNoVehicle);
    }

    final docsAsync = ref.watch(truckDocumentsProvider(truck.id));
    return _DocumentListView(
      docsAsync: docsAsync,
      onRefresh: () async => ref.invalidate(truckDocumentsProvider(truck.id)),
    );
  }
}

class _DriverDocumentsTab extends ConsumerWidget {
  const _DriverDocumentsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final driver = ref.watch(driverMeProvider).valueOrNull;

    if (driver == null) {
      return _CenteredMessage(message: l10n.documentsEmpty);
    }

    final docsAsync = ref.watch(driverDocumentsProvider(driver.id));
    return _DocumentListView(
      docsAsync: docsAsync,
      onRefresh: () async => ref.invalidate(driverDocumentsProvider(driver.id)),
    );
  }
}

/// Vehicle/Driver document lists are metadata-only (no upload endpoint yet,
/// so `has_file` is always false) — shown read-only, no tap action.
class _DocumentListView extends StatelessWidget {
  const _DocumentListView({required this.docsAsync, required this.onRefresh});

  final AsyncValue<List<ShipmentDocument>> docsAsync;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    return RefreshWrapper(
      onRefresh: onRefresh,
      child: docsAsync.when(
        data: (docs) {
          if (docs.isEmpty) {
            return _CenteredMessage(message: l10n.documentsEmpty);
          }
          return ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: docs.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final doc = docs[index];
              return AppCard(
                child: Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.description_outlined, color: AppColors.primary),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(documentTypeLabel(doc.documentType), style: theme.textTheme.titleSmall),
                          Text(doc.fileName, style: theme.textTheme.bodySmall),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => _CenteredMessage(message: l10n.documentsEmpty),
      ),
    );
  }
}

class _TripDocumentsTab extends ConsumerWidget {
  const _TripDocumentsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final docsAsync = ref.watch(recentTripDocumentsProvider);

    return RefreshWrapper(
      onRefresh: () async => ref.invalidate(recentTripDocumentsProvider),
      child: docsAsync.when(
        data: (items) {
          if (items.isEmpty) {
            return _CenteredMessage(message: l10n.documentsEmpty);
          }
          return ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final (trip, doc) = items[index];
              return AppCard(
                onTap: doc.hasFile
                    ? () => showDialog(
                          context: context,
                          builder: (context) => DocumentImageDialog(
                            provider: tripDocumentBytesProvider((trip.id, doc.id)),
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
                          Text(documentTypeLabel(doc.documentType), style: theme.textTheme.titleSmall),
                          Text('${trip.loadNo} · ${doc.fileName}', style: theme.textTheme.bodySmall),
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
        error: (_, __) => _CenteredMessage(message: l10n.documentsEmpty),
      ),
    );
  }
}

class _CenteredMessage extends StatelessWidget {
  const _CenteredMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return RefreshWrapper(
      child: LayoutBuilder(
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
      ),
    );
  }
}
