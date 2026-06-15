import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/locale_provider.dart';
import '../../../core/providers/portal_provider.dart';
import '../../../core/providers/theme_provider.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/info_row.dart';
import '../../../shared/widgets/refresh_wrapper.dart';
import '../utils/portal_error.dart';

/// Client portal "Profile" tab — company/contact details for every linked
/// carrier relationship (`GET /portal/me`), plus the same language/theme
/// settings and logout as the driver app's Profile screen.
class ClientProfileScreen extends ConsumerWidget {
  const ClientProfileScreen({super.key});

  Future<void> _logOut(BuildContext context, WidgetRef ref) async {
    await ref.read(authStateProvider.notifier).logout();
    if (context.mounted) context.go('/login');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final themeMode = ref.watch(themeModeProvider);
    final isDark = themeMode == ThemeMode.dark;
    final currentLocale = ref.watch(localeProvider).valueOrNull ?? const Locale('en');
    final carriersAsync = ref.watch(myCarriersProvider);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.clientProfileTitle)),
      body: RefreshWrapper(
        onRefresh: () async => ref.invalidate(myCarriersProvider),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            carriersAsync.when(
              data: (carriers) {
                if (carriers.isEmpty) {
                  return AppCard(
                    child: SizedBox(
                      height: 88,
                      child: Center(
                        child: Text(l10n.clientNoCarriers, style: theme.textTheme.bodyMedium),
                      ),
                    ),
                  );
                }
                return Column(
                  children: [
                    for (final carrier in carriers) ...[
                      AppCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                const Icon(Icons.local_shipping_outlined),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(carrier.tenantName, style: theme.textTheme.titleSmall),
                                ),
                              ],
                            ),
                            const Divider(height: 24),
                            InfoRow(
                              icon: Icons.storefront_outlined,
                              label: l10n.clientCompanyName,
                              value: carrier.client.companyName,
                            ),
                            if (carrier.client.contactPerson != null) ...[
                              const Divider(height: 1),
                              InfoRow(
                                icon: Icons.person_outline,
                                label: l10n.clientContactPerson,
                                value: carrier.client.contactPerson!,
                              ),
                            ],
                            const Divider(height: 1),
                            InfoRow(
                              icon: Icons.phone_outlined,
                              label: l10n.profilePhone,
                              value: carrier.client.phone,
                            ),
                            if (carrier.client.email != null) ...[
                              const Divider(height: 1),
                              InfoRow(
                                icon: Icons.email_outlined,
                                label: l10n.profileEmail,
                                value: carrier.client.email!,
                              ),
                            ],
                            if (carrier.client.fullAddress != null) ...[
                              const Divider(height: 1),
                              InfoRow(
                                icon: Icons.location_on_outlined,
                                label: l10n.profileAddress,
                                value: carrier.client.fullAddress!,
                              ),
                            ],
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                  ],
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => AppCard(
                child: SizedBox(
                  height: 88,
                  child: Center(
                    child: Text(portalErrorMessage(l10n, err), style: theme.textTheme.bodyMedium),
                  ),
                ),
              ),
            ),

            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.profileSettings, style: theme.textTheme.titleSmall),
                  const SizedBox(height: 8),
                  SwitchListTile.adaptive(
                    contentPadding: EdgeInsets.zero,
                    title: Text(l10n.profileDarkMode),
                    secondary: Icon(
                      isDark ? Icons.dark_mode_outlined : Icons.light_mode_outlined,
                    ),
                    value: isDark,
                    onChanged: (value) => ref
                        .read(themeModeProvider.notifier)
                        .setThemeMode(value ? ThemeMode.dark : ThemeMode.light),
                  ),
                  const Divider(height: 1),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.language_outlined),
                    title: Text(l10n.profileLanguage),
                    trailing: DropdownButton<Locale>(
                      value: currentLocale,
                      underline: const SizedBox.shrink(),
                      items: supportedLocales
                          .map((locale) => DropdownMenuItem(
                                value: locale,
                                child: Text(localeDisplayNames[locale.languageCode]!),
                              ))
                          .toList(),
                      onChanged: (locale) {
                        if (locale != null) {
                          ref.read(localeProvider.notifier).setLocale(locale);
                        }
                      },
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            OutlinedButton.icon(
              onPressed: () => _logOut(context, ref),
              icon: const Icon(Icons.logout),
              label: Text(l10n.profileLogOut),
              style: OutlinedButton.styleFrom(
                foregroundColor: Theme.of(context).colorScheme.error,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
