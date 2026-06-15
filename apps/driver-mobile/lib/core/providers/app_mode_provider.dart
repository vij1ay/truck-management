import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../onboarding/onboarding_prefs.dart';

export '../onboarding/onboarding_prefs.dart' show AppMode;

/// The [AppMode] (driver/client) chosen during first-launch onboarding.
///
/// Currently only [AppMode.driver] has real screens — this provider exists so
/// future client-portal screens/routing can branch on it without another
/// onboarding pass. [OnboardingScreen] calls [setMode] when the user finishes
/// onboarding.
class AppModeNotifier extends AsyncNotifier<AppMode> {
  @override
  Future<AppMode> build() => OnboardingPrefs().getAppMode();

  Future<void> setMode(AppMode mode) async {
    state = AsyncData(mode);
  }
}

final appModeProvider = AsyncNotifierProvider<AppModeNotifier, AppMode>(
  AppModeNotifier.new,
);
