import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../l10n/app_localizations.dart';

/// `LoadStatus` (backend `app/models/load.py`) wire values, in display order.
const loadStatuses = [
  'draft',
  'confirmed',
  'allocated',
  'in_transit',
  'delivered',
  'cancelled',
];

/// Localized label for a [Shipment.status] (or `null` for the "All" filter).
String loadStatusLabel(AppLocalizations l10n, String? status) {
  switch (status) {
    case 'draft':
      return l10n.loadStatusDraft;
    case 'confirmed':
      return l10n.loadStatusConfirmed;
    case 'allocated':
      return l10n.loadStatusAllocated;
    case 'in_transit':
      return l10n.loadStatusInTransit;
    case 'delivered':
      return l10n.loadStatusDelivered;
    case 'cancelled':
      return l10n.loadStatusCancelled;
    default:
      return l10n.loadStatusAll;
  }
}

/// Badge color for a [Shipment.status] — mirrors the admin-frontend's
/// `getStatusColor()` (`shipment-list.component.ts`).
Color loadStatusColor(String status) {
  switch (status) {
    case 'draft':
      return AppColors.statusDraft;
    case 'confirmed':
      return AppColors.statusAssigned;
    case 'allocated':
      return AppColors.statusPending;
    case 'in_transit':
      return AppColors.statusInTransit;
    case 'delivered':
      return AppColors.statusCompleted;
    case 'cancelled':
      return AppColors.statusCancelled;
    default:
      return AppColors.statusDraft;
  }
}
