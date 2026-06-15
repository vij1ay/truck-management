import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/profile_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/data/mock_data.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/refresh_wrapper.dart';

class VehicleInfoScreen extends ConsumerWidget {
  const VehicleInfoScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final specs = MockData.vehicleSpecs;

    final driver = ref.watch(driverMeProvider).valueOrNull;
    final truck = driver?.currentTruck;

    // Real truck identity (registration/make/model) when available — falls
    // back to the mock spec sheet for everything else (gap #4 in
    // mobile_app_design.md: full vehicle specs aren't yet exposed via the API).
    final truckNumber = truck?.registrationNo ?? specs['Truck Number']!;
    final brandModel = truck != null
        ? truck.displayName
        : '${specs['Brand']} ${specs['Model']}';

    return Scaffold(
      appBar: AppBar(title: Text(l10n.vehicleInfoTitle)),
      body: RefreshWrapper(
        onRefresh: () async {
          if (truck != null) ref.invalidate(truckPhotosProvider(truck.id));
          ref.invalidate(driverMeProvider);
        },
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            AppCard(
              child: Row(
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.local_shipping,
                      color: AppColors.primary,
                      size: 28,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              truckNumber,
                              style: theme.textTheme.titleLarge,
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 3,
                              ),
                              decoration: BoxDecoration(
                                color: AppColors.statusActive.withValues(
                                  alpha: 0.15,
                                ),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                l10n.statusInTransit,
                                style: theme.textTheme.labelSmall?.copyWith(
                                  color: AppColors.statusActive,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ],
                        ),
                        Text(
                          brandModel,
                          style: theme.textTheme.bodyMedium,
                        ),
                        Text(
                          l10n.vehicleInfoLastService('10 May 2026'),
                          style: theme.textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            Text(l10n.vehicleInfoPhotos, style: theme.textTheme.titleSmall),
            const SizedBox(height: 8),
            if (truck == null)
              _PhotoGalleryEmpty(message: l10n.vehicleInfoNoPhotos)
            else
              _PhotoGallery(truckId: truck.id),
            const SizedBox(height: 16),

            AppCard(
              child: Column(
                children: [
                  for (final entry in specs.entries) ...[
                    _SpecRow(label: entry.key, value: entry.value),
                    if (entry.key != specs.keys.last) const Divider(height: 1),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Horizontal scrolling gallery of a truck's photos (up to 6), each fetched
/// lazily via [truckPhotoBytesProvider].
class _PhotoGallery extends ConsumerWidget {
  const _PhotoGallery({required this.truckId});

  final String truckId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final photosAsync = ref.watch(truckPhotosProvider(truckId));

    return photosAsync.when(
      data: (photos) {
        if (photos.isEmpty) {
          return _PhotoGalleryEmpty(message: l10n.vehicleInfoNoPhotos);
        }
        return SizedBox(
          height: 120,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: photos.length,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (context, index) {
              final photo = photos[index];
              return ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: _PhotoThumb(truckId: truckId, photoId: photo.id),
              );
            },
          ),
        );
      },
      loading: () => const SizedBox(
        height: 120,
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      ),
      error: (_, __) => _PhotoGalleryEmpty(message: l10n.vehicleInfoNoPhotos),
    );
  }
}

class _PhotoThumb extends ConsumerWidget {
  const _PhotoThumb({required this.truckId, required this.photoId});

  final String truckId;
  final String photoId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bytesAsync = ref.watch(truckPhotoBytesProvider((truckId, photoId)));

    return bytesAsync.when(
      data: (bytes) => Image.memory(
        Uint8List.fromList(bytes),
        width: 160,
        height: 120,
        fit: BoxFit.cover,
      ),
      loading: () => Container(
        width: 160,
        height: 120,
        color: AppColors.lightSurfaceAlt,
        child: const Center(child: CircularProgressIndicator(strokeWidth: 2)),
      ),
      error: (_, __) => Container(
        width: 160,
        height: 120,
        color: AppColors.lightSurfaceAlt,
        child: const Icon(Icons.broken_image_outlined),
      ),
    );
  }
}

class _PhotoGalleryEmpty extends StatelessWidget {
  const _PhotoGalleryEmpty({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      child: SizedBox(
        height: 88,
        child: Center(
          child: Text(
            message,
            style: theme.textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}

class _SpecRow extends StatelessWidget {
  const _SpecRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: theme.textTheme.bodyMedium),
          Text(value, style: theme.textTheme.titleSmall),
        ],
      ),
    );
  }
}
