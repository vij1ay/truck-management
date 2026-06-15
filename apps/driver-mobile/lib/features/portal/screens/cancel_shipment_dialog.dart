import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

/// Prompts for a cancellation reason (>= 5 chars, enforced by the backend's
/// `LoadCancelRequest`) and returns it, or `null` if the user backed out.
Future<String?> showCancelShipmentDialog(BuildContext context) {
  final l10n = AppLocalizations.of(context);
  final controller = TextEditingController();

  return showDialog<String>(
    context: context,
    builder: (context) {
      String? errorText;
      return StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: Text(l10n.clientCancelShipment),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.clientCancelConfirmMessage),
              const SizedBox(height: 12),
              TextField(
                controller: controller,
                autofocus: true,
                maxLines: 2,
                decoration: InputDecoration(
                  labelText: l10n.clientCancelReason,
                  hintText: l10n.clientCancelReasonHint,
                  errorText: errorText,
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(MaterialLocalizations.of(context).cancelButtonLabel),
            ),
            TextButton(
              onPressed: () {
                final reason = controller.text.trim();
                if (reason.length < 5) {
                  setState(() => errorText = l10n.clientCancelReasonHint);
                  return;
                }
                Navigator.of(context).pop(reason);
              },
              child: Text(MaterialLocalizations.of(context).okButtonLabel),
            ),
          ],
        ),
      );
    },
  ).whenComplete(controller.dispose);
}
