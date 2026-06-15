import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';

/// The persistent Scaffold + bottom navigation bar (Home / Shipments /
/// Invoices / Profile) shown around the 4 top-level screens for
/// [AppMode.client], driven by GoRouter's [StatefulShellRoute] — mirrors
/// `app_shell.dart`'s driver-mode shell.
class ClientShell extends StatelessWidget {
  const ClientShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final items = [
      (icon: Icons.home_outlined, activeIcon: Icons.home, label: l10n.navHome),
      (
        icon: Icons.local_shipping_outlined,
        activeIcon: Icons.local_shipping,
        label: l10n.navShipments,
      ),
      (
        icon: Icons.receipt_long_outlined,
        activeIcon: Icons.receipt_long,
        label: l10n.navInvoices,
      ),
      (icon: Icons.person_outline, activeIcon: Icons.person, label: l10n.navProfile),
    ];

    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: navigationShell.currentIndex,
        onTap: (index) => navigationShell.goBranch(
          index,
          initialLocation: index == navigationShell.currentIndex,
        ),
        items: [
          for (final item in items)
            BottomNavigationBarItem(
              icon: Icon(item.icon),
              activeIcon: Icon(item.activeIcon),
              label: item.label,
            ),
        ],
      ),
    );
  }
}
