import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/portal_provider.dart';
import '../../../l10n/app_localizations.dart';

/// A horizontal row of [FilterChip]s — "All" plus one per linked carrier
/// (`GET /portal/me`) — shown above the Shipments/Invoices status tabs.
///
/// Hidden entirely when the account has 0 or 1 linked carriers (the common
/// case), since there's nothing to filter. [selected] is the chosen carrier's
/// `tenant_name`, or `null` for "All".
class CarrierFilterBar extends ConsumerWidget {
  const CarrierFilterBar({super.key, required this.selected, required this.onSelect});

  final String? selected;
  final ValueChanged<String?> onSelect;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final carriers = ref.watch(myCarriersProvider).valueOrNull;

    if (carriers == null || carriers.length <= 1) return const SizedBox.shrink();

    return SizedBox(
      height: 48,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        children: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text(l10n.clientAllCarriers),
              selected: selected == null,
              onSelected: (_) => onSelect(null),
            ),
          ),
          for (final carrier in carriers)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: FilterChip(
                label: Text(carrier.tenantName),
                selected: selected == carrier.tenantName,
                onSelected: (_) => onSelect(carrier.tenantName),
              ),
            ),
        ],
      ),
    );
  }
}
