import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/locale_provider.dart';
import '../../../core/providers/profile_provider.dart';
import '../../../core/providers/theme_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/data/mock_data.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/info_row.dart';
import '../../../shared/widgets/refresh_wrapper.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  Future<void> _pickAndUploadAvatar(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    final picked = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 85,
    );
    if (picked == null) return;

    try {
      final user = await ref.read(currentUserProvider.future);
      await ref.read(profileRepositoryProvider).uploadAvatar(user.id, picked.path);
      ref.invalidate(currentUserProvider);
      ref.invalidate(avatarBytesProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.profileAvatarUpdated)),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.profileAvatarUpdateFailed)),
        );
      }
    }
  }

  Future<void> _refresh(WidgetRef ref) async {
    ref.invalidate(currentUserProvider);
    ref.invalidate(driverMeProvider);
    ref.invalidate(avatarBytesProvider);
  }

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

    final user = ref.watch(currentUserProvider).valueOrNull;
    final driver = ref.watch(driverMeProvider).valueOrNull;
    final avatarBytes = ref.watch(avatarBytesProvider).valueOrNull;
    final currentLocale = ref.watch(localeProvider).valueOrNull ?? const Locale('en');

    final displayName = driver?.fullName ?? (user != null ? user.fullName : MockData.driverName);
    final phone = driver?.phone ?? MockData.driverPhone;
    final email = driver?.email ?? user?.email ?? MockData.driverEmail;
    final licenseNo = driver?.licenseNo ?? MockData.driverLicenseNo;
    final emergencyContact = (driver?.emergencyContactName != null && driver?.emergencyContactPhone != null)
        ? '${driver!.emergencyContactName} (${driver.emergencyContactPhone})'
        : MockData.driverEmergencyContact;
    final address = driver?.address ?? MockData.driverAddress;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.profileTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined),
            onPressed: () => _pickAndUploadAvatar(context, ref),
          ),
        ],
      ),
      body: RefreshWrapper(
        onRefresh: () => _refresh(ref),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            Center(
              child: Column(
                children: [
                  GestureDetector(
                    onTap: () => _pickAndUploadAvatar(context, ref),
                    child: CircleAvatar(
                      radius: 44,
                      backgroundColor: AppColors.primary,
                      backgroundImage: avatarBytes != null
                          ? MemoryImage(Uint8List.fromList(avatarBytes))
                          : null,
                      child: avatarBytes == null
                          ? const Icon(Icons.person, color: Colors.white, size: 44)
                          : null,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(displayName, style: theme.textTheme.headlineSmall),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.star,
                        color: AppColors.statusPending,
                        size: 16,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${MockData.driverRating} (${MockData.driverTrips} trips)',
                        style: theme.textTheme.bodyMedium,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.statusActive.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.verified,
                          color: AppColors.statusActive,
                          size: 14,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          l10n.profileVerified,
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: AppColors.statusActive,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  InfoRow(
                    icon: Icons.phone_outlined,
                    label: l10n.profilePhone,
                    value: phone,
                  ),
                  const Divider(height: 1),
                  InfoRow(
                    icon: Icons.email_outlined,
                    label: l10n.profileEmail,
                    value: email,
                  ),
                  const Divider(height: 1),
                  InfoRow(
                    icon: Icons.badge_outlined,
                    label: l10n.profileLicenseNo,
                    value: licenseNo,
                  ),
                  const Divider(height: 1),
                  InfoRow(
                    icon: Icons.emergency_outlined,
                    label: l10n.profileEmergencyContact,
                    value: emergencyContact,
                  ),
                  const Divider(height: 1),
                  InfoRow(
                    icon: Icons.location_on_outlined,
                    label: l10n.profileAddress,
                    value: address,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            AppCard(
              child: Column(
                children: [
                  _ProfileLink(
                    icon: Icons.local_shipping_outlined,
                    label: l10n.profileVehicleInformation,
                    onTap: () => context.go('/profile/vehicle'),
                  ),
                  const Divider(height: 1),
                  _ProfileLink(
                    icon: Icons.folder_outlined,
                    label: l10n.profileDocuments,
                    onTap: () => context.go('/profile/documents'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

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
                      isDark
                          ? Icons.dark_mode_outlined
                          : Icons.light_mode_outlined,
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
                foregroundColor: AppColors.statusCancelled,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProfileLink extends StatelessWidget {
  const _ProfileLink({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          children: [
            Icon(icon, color: theme.colorScheme.primary, size: 20),
            const SizedBox(width: 12),
            Expanded(child: Text(label, style: theme.textTheme.bodyLarge)),
            const Icon(Icons.chevron_right),
          ],
        ),
      ),
    );
  }
}
