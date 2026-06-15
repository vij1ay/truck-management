import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers/notification_provider.dart';
import '../../l10n/app_localizations.dart';

/// The persistent Scaffold + bottom navigation bar (Home / Trips / Map /
/// Notifications / Profile) shown around the 5 top-level screens, driven by
/// GoRouter's [StatefulShellRoute].
///
/// The "Notifications" tab carries a small badge counting newly-allocated
/// trips not yet started — this is the only "needs attention" indicator in
/// the app (the Dashboard intentionally has no duplicate bell icon).
class AppShell extends ConsumerWidget {
  const AppShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  static const _notificationsIndex = 3;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final items = [
      (icon: Icons.home_outlined, activeIcon: Icons.home, label: l10n.navHome),
      (
        icon: Icons.local_shipping_outlined,
        activeIcon: Icons.local_shipping,
        label: l10n.navTrips,
      ),
      (icon: Icons.map_outlined, activeIcon: Icons.map, label: l10n.navMap),
      (
        icon: Icons.notifications_outlined,
        activeIcon: Icons.notifications,
        label: l10n.navNotifications,
      ),
      (icon: Icons.person_outline, activeIcon: Icons.person, label: l10n.navProfile),
    ];

    final activity = ref.watch(driverRecentActivityProvider).valueOrNull ?? const [];
    final unreadCount = activity.where((a) => a.$2.toStatus == 'allocated' && a.$2.fromStatus != a.$2.toStatus).length;

    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: navigationShell.currentIndex,
        onTap: (index) => navigationShell.goBranch(
          index,
          initialLocation: index == navigationShell.currentIndex,
        ),
        items: [
          for (final (index, item) in items.indexed)
            BottomNavigationBarItem(
              icon: index == _notificationsIndex && unreadCount > 0
                  ? Badge.count(count: unreadCount, child: Icon(item.icon))
                  : Icon(item.icon),
              activeIcon: index == _notificationsIndex && unreadCount > 0
                  ? Badge.count(
                      count: unreadCount,
                      child: Icon(item.activeIcon),
                    )
                  : Icon(item.activeIcon),
              label: item.label,
            ),
        ],
      ),
    );
  }
}
