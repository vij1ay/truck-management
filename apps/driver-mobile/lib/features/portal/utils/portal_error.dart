import 'package:dio/dio.dart';

import '../../../l10n/app_localizations.dart';

/// A user-facing message for an error surfaced by a `/portal/*` call.
///
/// A 404 here almost always means `get_my_clients()`
/// (`app/api/v1/portal.py:37-47`) found no `Client` record linked to this
/// account — every `/portal/*` endpoint depends on that dependency, so an
/// unlinked account gets a 404 on every call. Anything else is a generic,
/// "try again" error.
String portalErrorMessage(AppLocalizations l10n, Object error) {
  if (error is DioException && error.response?.statusCode == 404) {
    return l10n.clientNotLinked;
  }
  return l10n.clientGenericError;
}
