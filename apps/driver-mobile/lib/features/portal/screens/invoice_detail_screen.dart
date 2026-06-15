import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../../../core/providers/portal_provider.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/models/portal_invoice.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/info_row.dart';
import '../../../shared/widgets/label_badge.dart';
import '../../../shared/widgets/primary_button.dart';
import '../utils/invoice_status.dart';

String _money(double value) => '₹${value.toStringAsFixed(2)}';

/// Invoice detail — `GET /portal/invoices` already returns every field needed
/// here, so the [invoice] is passed via `state.extra` (no separate detail
/// endpoint exists). "Download PDF" fetches
/// `GET /portal/invoices/{id}/pdf` and shares/opens the resulting file.
class InvoiceDetailScreen extends ConsumerStatefulWidget {
  const InvoiceDetailScreen({super.key, required this.invoice});

  final PortalInvoice invoice;

  @override
  ConsumerState<InvoiceDetailScreen> createState() => _InvoiceDetailScreenState();
}

class _InvoiceDetailScreenState extends ConsumerState<InvoiceDetailScreen> {
  bool _downloading = false;

  Future<void> _downloadPdf() async {
    final l10n = AppLocalizations.of(context);
    setState(() => _downloading = true);
    try {
      final bytes = await ref.read(portalRepositoryProvider).downloadInvoicePdf(widget.invoice.id);
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/${widget.invoice.invoiceNo}.pdf');
      await file.writeAsBytes(bytes, flush: true);
      await Share.shareXFiles(
        [XFile(file.path, mimeType: 'application/pdf')],
        fileNameOverrides: ['${widget.invoice.invoiceNo}.pdf'],
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.invoiceDownloaded)));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.invoiceDownloadFailed)));
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final invoice = widget.invoice;

    return Scaffold(
      appBar: AppBar(title: Text(invoice.invoiceNo)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          AppCard(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(invoice.invoiceNo, style: theme.textTheme.titleLarge),
                      Text(invoice.carrierName, style: theme.textTheme.bodyMedium),
                      if (invoice.loadNo != null)
                        Text(invoice.loadNo!, style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
                LabelBadge(
                  label: invoiceStatusLabel(l10n, invoice.status),
                  color: invoiceStatusColor(invoice.status),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                InfoRow(label: l10n.invoiceIssuedDate, value: invoice.issuedDate),
                if (invoice.dueDate != null) ...[
                  const Divider(height: 24),
                  InfoRow(label: l10n.invoiceDueDate, value: invoice.dueDate!),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                InfoRow(label: l10n.invoiceSubtotal, value: _money(invoice.subtotal)),
                const Divider(height: 24),
                InfoRow(
                  label: '${l10n.invoiceTax} (${invoice.taxRate}%)',
                  value: _money(invoice.taxAmount),
                ),
                const Divider(height: 24),
                InfoRow(label: l10n.invoiceTotal, value: _money(invoice.totalAmount)),
                const Divider(height: 24),
                InfoRow(label: l10n.invoicePaid, value: _money(invoice.paidAmount)),
                const Divider(height: 24),
                InfoRow(
                  label: l10n.invoiceOutstanding,
                  value: _money(invoice.outstandingAmount),
                  valueColor: invoiceStatusColor(invoice.status),
                ),
              ],
            ),
          ),
          if (invoice.notes?.isNotEmpty ?? false) ...[
            const SizedBox(height: 16),
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.notesLabel, style: theme.textTheme.titleSmall),
                  const SizedBox(height: 8),
                  Text(invoice.notes!, style: theme.textTheme.bodyMedium),
                ],
              ),
            ),
          ],
          const SizedBox(height: 16),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.invoicePaymentHistory, style: theme.textTheme.titleSmall),
                const SizedBox(height: 8),
                if (invoice.payments.isEmpty)
                  Text(l10n.invoiceNoPayments, style: theme.textTheme.bodyMedium)
                else
                  for (final payment in invoice.payments) ...[
                    InfoRow(
                      label: payment.paymentDate,
                      value: _money(payment.amount),
                    ),
                    if (payment.referenceNo?.isNotEmpty ?? false)
                      Padding(
                        padding: const EdgeInsets.only(top: 2, bottom: 4),
                        child: Text(
                          l10n.invoicePaymentReference(payment.referenceNo!),
                          style: theme.textTheme.bodySmall,
                        ),
                      ),
                    if (payment != invoice.payments.last) const Divider(height: 16),
                  ],
              ],
            ),
          ),
          const SizedBox(height: 24),
          PrimaryButton(
            label: l10n.invoiceDownloadPdf,
            icon: Icons.download_outlined,
            loading: _downloading,
            onPressed: _downloadPdf,
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}
