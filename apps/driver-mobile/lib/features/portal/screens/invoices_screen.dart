import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/portal_provider.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/models/portal_invoice.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/label_badge.dart';
import '../../../shared/widgets/refresh_wrapper.dart';
import '../utils/invoice_status.dart';
import '../utils/portal_error.dart';
import 'carrier_filter_bar.dart';

String _money(double value) => '₹${value.toStringAsFixed(2)}';

/// "My Invoices" — `GET /portal/invoices`, with a status filter [TabBar] and
/// an optional carrier filter (when linked to more than one carrier).
class InvoicesScreen extends ConsumerStatefulWidget {
  const InvoicesScreen({super.key});

  @override
  ConsumerState<InvoicesScreen> createState() => _InvoicesScreenState();
}

class _InvoicesScreenState extends ConsumerState<InvoicesScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  String? _selectedCarrier;

  /// `null` ("All") followed by every [invoiceStatuses] value.
  static const _filters = <String?>[null, ...invoiceStatuses];

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
        title: Text(l10n.clientInvoicesTitle),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: [for (final status in _filters) Tab(text: invoiceStatusLabel(l10n, status))],
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
                  _InvoiceList(status: status, carrierFilter: _selectedCarrier),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InvoiceList extends ConsumerWidget {
  const _InvoiceList({required this.status, this.carrierFilter});

  final String? status;
  final String? carrierFilter;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final invoicesAsync = ref.watch(invoicesProvider(status));

    return RefreshWrapper(
      onRefresh: () async => ref.invalidate(invoicesProvider(status)),
      child: invoicesAsync.when(
        data: (allInvoices) {
          final invoices = carrierFilter == null
              ? allInvoices
              : allInvoices.where((i) => i.carrierName == carrierFilter).toList();

          if (invoices.isEmpty) {
            return _CenteredMessage(message: l10n.clientInvoicesEmpty);
          }
          return ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: invoices.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final invoice = invoices[index];
              return _InvoiceCard(
                invoice: invoice,
                onTap: () => context.push('/client/invoices/${invoice.id}', extra: invoice),
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

class _InvoiceCard extends StatelessWidget {
  const _InvoiceCard({required this.invoice, this.onTap});

  final PortalInvoice invoice;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    return AppCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(invoice.invoiceNo, style: theme.textTheme.titleMedium),
              LabelBadge(
                label: invoiceStatusLabel(l10n, invoice.status),
                color: invoiceStatusColor(invoice.status),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Text(invoice.carrierName, style: theme.textTheme.bodySmall),
          const SizedBox(height: 10),
          Row(
            children: [
              Icon(Icons.calendar_today_outlined, size: 14, color: theme.textTheme.bodySmall?.color),
              const SizedBox(width: 6),
              Text(invoice.issuedDate, style: theme.textTheme.bodySmall),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.invoiceTotal, style: theme.textTheme.bodySmall),
                  Text(_money(invoice.totalAmount), style: theme.textTheme.titleMedium),
                ],
              ),
              if (invoice.outstandingAmount > 0)
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(l10n.invoiceOutstanding, style: theme.textTheme.bodySmall),
                    Text(_money(invoice.outstandingAmount), style: theme.textTheme.titleMedium),
                  ],
                ),
            ],
          ),
        ],
      ),
    );
  }
}
