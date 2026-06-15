import 'package:flutter/material.dart';

/// Shows a simple Yes/No confirmation dialog and returns `true` if the user
/// confirmed. Uses [MaterialLocalizations] for the button labels (OK/Cancel)
/// so no extra i18n strings are needed.
Future<bool> showConfirmDialog(
  BuildContext context, {
  required String title,
  required String message,
}) async {
  final l10n = MaterialLocalizations.of(context);
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: Text(l10n.cancelButtonLabel),
        ),
        TextButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: Text(l10n.okButtonLabel),
        ),
      ],
    ),
  );
  return confirmed ?? false;
}
