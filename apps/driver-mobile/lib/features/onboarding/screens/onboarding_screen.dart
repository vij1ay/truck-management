import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/onboarding/onboarding_prefs.dart';
import '../../../core/providers/app_mode_provider.dart';
import '../../../core/providers/locale_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/widgets/primary_button.dart';

/// First-launch flow: pick a UI language, then say whether you're a Driver or
/// a Client. Shown once (gated by [OnboardingPrefs.isComplete] in
/// `app_router.dart`'s `redirect`); both choices remain changeable later
/// (language from Profile → Settings).
///
/// - Driver → onboarding completes, app mode = driver, continue to `/login`.
/// - Client → onboarding completes, app mode = client, continue to `/login`.
class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

enum _Step { language, role }

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  _Step _step = _Step.language;
  Locale _selectedLocale = const Locale('en');

  @override
  void initState() {
    super.initState();
    final current = ref.read(localeProvider).valueOrNull;
    if (current != null) _selectedLocale = current;
  }

  Future<void> _confirmLanguage() async {
    await ref.read(localeProvider.notifier).setLocale(_selectedLocale);
    if (mounted) setState(() => _step = _Step.role);
  }

  Future<void> _continueAsDriver() async {
    await OnboardingPrefs().markComplete(AppMode.driver);
    await ref.read(appModeProvider.notifier).setMode(AppMode.driver);
    if (mounted) context.go('/login');
  }

  Future<void> _continueAsClient() async {
    await OnboardingPrefs().markComplete(AppMode.client);
    await ref.read(appModeProvider.notifier).setMode(AppMode.client);
    if (mounted) context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: switch (_step) {
            _Step.language => _LanguageStep(
                selected: _selectedLocale,
                onSelect: (locale) => setState(() => _selectedLocale = locale),
                onContinue: _confirmLanguage,
              ),
            _Step.role => _RoleStep(
                onPickDriver: _continueAsDriver,
                onPickClient: _continueAsClient,
              ),
          },
        ),
      ),
    );
  }
}

class _LanguageStep extends StatelessWidget {
  const _LanguageStep({
    required this.selected,
    required this.onSelect,
    required this.onContinue,
  });

  final Locale selected;
  final ValueChanged<Locale> onSelect;
  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 24),
        Text(l10n.onboardingChooseLanguage, style: theme.textTheme.headlineSmall),
        const SizedBox(height: 6),
        Text(l10n.onboardingChooseLanguageSubtitle, style: theme.textTheme.bodyMedium),
        const SizedBox(height: 24),
        for (final locale in supportedLocales) ...[
          _SelectableTile(
            label: localeDisplayNames[locale.languageCode]!,
            selected: locale == selected,
            onTap: () => onSelect(locale),
          ),
          const SizedBox(height: 12),
        ],
        const Spacer(),
        PrimaryButton(
          label: l10n.onboardingContinue,
          icon: Icons.arrow_forward,
          onPressed: onContinue,
        ),
      ],
    );
  }
}

class _RoleStep extends StatelessWidget {
  const _RoleStep({required this.onPickDriver, required this.onPickClient});

  final VoidCallback onPickDriver;
  final VoidCallback onPickClient;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 24),
        Text(l10n.onboardingWhoAreYou, style: theme.textTheme.headlineSmall),
        const SizedBox(height: 6),
        Text(l10n.onboardingWhoAreYouSubtitle, style: theme.textTheme.bodyMedium),
        const SizedBox(height: 24),
        _RoleCard(
          icon: Icons.local_shipping_outlined,
          title: l10n.onboardingDriver,
          subtitle: l10n.onboardingDriverSubtitle,
          onTap: onPickDriver,
        ),
        const SizedBox(height: 12),
        _RoleCard(
          icon: Icons.storefront_outlined,
          title: l10n.onboardingClient,
          subtitle: l10n.onboardingClientSubtitle,
          onTap: onPickClient,
        ),
      ],
    );
  }
}

class _SelectableTile extends StatelessWidget {
  const _SelectableTile({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? AppColors.primary : theme.dividerTheme.color ?? Colors.transparent,
            width: selected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Expanded(child: Text(label, style: theme.textTheme.titleMedium)),
            if (selected) const Icon(Icons.check_circle, color: AppColors.primary),
          ],
        ),
      ),
    );
  }
}

class _RoleCard extends StatelessWidget {
  const _RoleCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: theme.dividerTheme.color ?? Colors.transparent),
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: AppColors.primary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: theme.textTheme.titleMedium),
                  Text(subtitle, style: theme.textTheme.bodySmall),
                ],
              ),
            ),
            const Icon(Icons.chevron_right),
          ],
        ),
      ),
    );
  }
}
