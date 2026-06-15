import 'dart:ui' show PlatformDispatcher;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'auth_provider.dart';
import 'profile_provider.dart';

const _prefsKey = 'preferred_language';

/// Languages selectable in the Profile screen's language picker — mirrors
/// `app.schemas.common.SUPPORTED_LANGUAGES` on the backend.
const supportedLocales = [Locale('en'), Locale('hi'), Locale('ta')];

/// The app's current UI language.
///
/// Resolution order on startup: local `shared_preferences` cache → the logged-in
/// user's `User.preferred_language` (`GET /users/me`) → device locale (if
/// supported) → `en`. [setLocale] updates all three: in-memory state, the local
/// cache, and (best-effort) `PATCH /users/{id}` so the preference follows the
/// driver across devices.
class LocaleNotifier extends AsyncNotifier<Locale> {
  @override
  Future<Locale> build() async {
    final prefs = await SharedPreferences.getInstance();
    final cached = prefs.getString(_prefsKey);
    if (cached != null) {
      return _toLocale(cached);
    }

    // No local preference yet — try the account's saved preference.
    final loggedIn = await ref.read(authRepositoryProvider).hasSession();
    if (loggedIn) {
      try {
        final me = await ref.read(profileRepositoryProvider).getMe();
        if (me.preferredLanguage != null) {
          await prefs.setString(_prefsKey, me.preferredLanguage!);
          return _toLocale(me.preferredLanguage!);
        }
      } catch (_) {
        // ignore — fall through to device/default
      }
    }

    final device = PlatformDispatcher.instance.locale;
    if (supportedLocales.any((l) => l.languageCode == device.languageCode)) {
      return Locale(device.languageCode);
    }
    return const Locale('en');
  }

  Locale _toLocale(String code) {
    return supportedLocales.firstWhere(
      (l) => l.languageCode == code,
      orElse: () => const Locale('en'),
    );
  }

  /// Switch the app language, persist it, and sync it to the backend.
  Future<void> setLocale(Locale locale) async {
    state = AsyncData(locale);

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, locale.languageCode);

    try {
      final loggedIn = await ref.read(authRepositoryProvider).hasSession();
      if (loggedIn) {
        final me = await ref.read(profileRepositoryProvider).getMe();
        await ref
            .read(profileRepositoryProvider)
            .updatePreferredLanguage(me.id, locale.languageCode);
      }
    } catch (_) {
      // Best-effort sync — the local preference still applies even if the
      // backend call fails (e.g. offline).
    }
  }
}

final localeProvider = AsyncNotifierProvider<LocaleNotifier, Locale>(
  LocaleNotifier.new,
);

/// Display names for the language picker.
const localeDisplayNames = {
  'en': 'English',
  'hi': 'हिन्दी',
  'ta': 'தமிழ்',
};
