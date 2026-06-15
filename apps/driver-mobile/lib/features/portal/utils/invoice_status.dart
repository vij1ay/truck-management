import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';

/// `InvoiceStatus` (backend `app/models/invoice.py`) wire values, in display
/// order.
const invoiceStatuses = [
  'draft',
  'sent',
  'partial',
  'paid',
  'overdue',
  'cancelled',
];

/// Localized label for a [PortalInvoice.status] (or `null` for the "All" filter).
String invoiceStatusLabel(AppLocalizations l10n, String? status) {
  switch (status) {
    case 'draft':
      return l10n.loadStatusDraft;
    case 'sent':
      return l10n.invoiceStatusSent;
    case 'partial':
      return l10n.invoiceStatusPartial;
    case 'paid':
      return l10n.invoiceStatusPaid;
    case 'overdue':
      return l10n.invoiceStatusOverdue;
    case 'cancelled':
      return l10n.loadStatusCancelled;
    default:
      return l10n.invoiceStatusAll;
  }
}

/// Badge color for a [PortalInvoice.status].
Color invoiceStatusColor(String status) {
  switch (status) {
    case 'draft':
      return AppColors.statusDraft;
    case 'sent':
      return AppColors.statusAssigned;
    case 'partial':
      return AppColors.statusPending;
    case 'paid':
      return AppColors.statusCompleted;
    case 'overdue':
      return AppColors.statusCancelled;
    case 'cancelled':
      return AppColors.statusCancelled;
    default:
      return AppColors.statusDraft;
  }
}
