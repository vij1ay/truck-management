import 'package:shared_preferences/shared_preferences.dart';

/// Which kind of account the first-launch onboarding flow asked the user
/// about. Only [driver] has real screens today — [client] shows a "coming
/// soon" placeholder (see `OnboardingScreen`) until the client portal is
/// built into this app.
enum AppMode { driver, client }

const _onboardingCompleteKey = 'onboarding_complete';
const _appModeKey = 'app_mode';

/// Persists the first-launch onboarding state (language is handled by
/// [LocaleNotifier] separately) — whether onboarding has been completed, and
/// which [AppMode] the user picked.
///
/// Read directly (not via Riverpod) from `GoRouter`'s `redirect`, mirroring
/// `TokenStorage`'s usage there.
class OnboardingPrefs {
  Future<bool> isComplete() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_onboardingCompleteKey) ?? false;
  }

  Future<void> markComplete(AppMode mode) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_onboardingCompleteKey, true);
    await prefs.setString(_appModeKey, mode.name);
  }

  Future<AppMode> getAppMode() async {
    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getString(_appModeKey);
    return AppMode.values.firstWhere(
      (m) => m.name == stored,
      orElse: () => AppMode.driver,
    );
  }
}
