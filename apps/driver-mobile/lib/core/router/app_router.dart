import 'package:go_router/go_router.dart';

import '../network/token_storage.dart';
import '../onboarding/onboarding_prefs.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/dashboard/screens/dashboard_screen.dart';
import '../../features/notifications/screens/notifications_screen.dart';
import '../../features/onboarding/screens/onboarding_screen.dart';
import '../../features/portal/screens/client_dashboard_screen.dart';
import '../../features/portal/screens/client_profile_screen.dart';
import '../../features/portal/screens/invoice_detail_screen.dart';
import '../../features/portal/screens/invoices_screen.dart';
import '../../features/portal/screens/new_shipment_screen.dart';
import '../../features/portal/screens/shipment_detail_screen.dart';
import '../../features/portal/screens/shipments_screen.dart';
import '../../features/profile/screens/documents_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../features/profile/screens/vehicle_info_screen.dart';
import '../../features/trips/screens/active_trip_map_screen.dart';
import '../../features/trips/screens/proof_of_delivery_screen.dart';
import '../../features/trips/screens/trip_details_screen.dart';
import '../../features/trips/screens/trips_screen.dart';
import '../../shared/models/portal_invoice.dart';
import '../../shared/models/shipment.dart';
import '../../shared/widgets/app_shell.dart';
import '../../shared/widgets/client_shell.dart';

/// Paths that belong to the Driver-mode shell — used by `redirect` to bounce
/// a [AppMode.client] user back to their own shell if they somehow land here
/// (and vice versa for `/client/*`).
const _driverPaths = ['/home', '/trips', '/map', '/notifications', '/profile'];

/// App-wide [GoRouter] — `/onboarding` and `/login` are standalone; the
/// top-level tabs live in one of two [StatefulShellRoute]s depending on the
/// [AppMode] chosen during onboarding:
/// - [AppMode.driver]: Home/Trips/Map/Notifications/Profile ([AppShell]).
/// - [AppMode.client]: Shipments/Invoices/Profile ([ClientShell]), backed by
///   the `/portal/*` Client Portal API.
///
/// Each branch keeps its own navigation stack (e.g. pushing Trip Details from
/// "Trips" doesn't affect the "Home" tab).
///
/// `redirect` guards every route:
/// - First launch (onboarding not yet completed) → `/onboarding`, regardless
///   of session state.
/// - Otherwise, signed-out users are sent to `/login`; a signed-in user
///   landing on `/login` (e.g. after a hot restart) is sent to their mode's
///   home (`/home` for Driver, `/client/shipments` for Client).
/// - A signed-in user is also bounced back to their own mode's shell if they
///   end up on a route belonging to the other mode.
final appRouter = GoRouter(
  initialLocation: '/onboarding',
  redirect: (context, state) async {
    final onOnboarding = state.matchedLocation == '/onboarding';

    final onboardingDone = await OnboardingPrefs().isComplete();
    if (!onboardingDone) {
      return onOnboarding ? null : '/onboarding';
    }
    if (onOnboarding) return '/login';

    // Bounded so a slow/unavailable secure-storage platform channel (e.g. in
    // widget tests, or a misbehaving device) can never block navigation
    // indefinitely — treated the same as "no session".
    final loggedIn = await TokenStorage()
        .hasSession()
        .timeout(const Duration(seconds: 3), onTimeout: () => false);
    final onLoginScreen = state.matchedLocation == '/login';

    if (!loggedIn && !onLoginScreen) return '/login';

    final appMode = await OnboardingPrefs().getAppMode();
    final isClientMode = appMode == AppMode.client;

    if (loggedIn && onLoginScreen) {
      return isClientMode ? '/client/home' : '/home';
    }

    if (loggedIn) {
      final onClientPath = state.matchedLocation.startsWith('/client');
      final onDriverPath = _driverPaths.any((p) => state.matchedLocation.startsWith(p));
      if (isClientMode && onDriverPath) return '/client/shipments';
      if (!isClientMode && onClientPath) return '/home';
    }

    return null;
  },
  routes: [
    GoRoute(path: '/onboarding', builder: (context, state) => const OnboardingScreen()),
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) =>
          AppShell(navigationShell: navigationShell),
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/home',
              builder: (context, state) => const DashboardScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/trips',
              builder: (context, state) => const TripsScreen(),
              routes: [
                GoRoute(
                  path: ':id',
                  builder: (context, state) =>
                      TripDetailsScreen(tripId: state.pathParameters['id']!),
                  routes: [
                    GoRoute(
                      path: 'pod',
                      builder: (context, state) => ProofOfDeliveryScreen(
                        tripId: state.pathParameters['id']!,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/map',
              builder: (context, state) => const ActiveTripMapScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/notifications',
              builder: (context, state) => const NotificationsScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/profile',
              builder: (context, state) => const ProfileScreen(),
              routes: [
                GoRoute(
                  path: 'vehicle',
                  builder: (context, state) => const VehicleInfoScreen(),
                ),
                GoRoute(
                  path: 'documents',
                  builder: (context, state) => const DocumentsScreen(),
                ),
              ],
            ),
          ],
        ),
      ],
    ),
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) =>
          ClientShell(navigationShell: navigationShell),
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/client/home',
              builder: (context, state) => const ClientDashboardScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/client/shipments',
              builder: (context, state) => const ShipmentsScreen(),
              routes: [
                GoRoute(
                  path: 'new',
                  builder: (context, state) => const NewShipmentScreen(),
                ),
                GoRoute(
                  path: ':id',
                  builder: (context, state) =>
                      ShipmentDetailScreen(shipmentId: state.pathParameters['id']!),
                  routes: [
                    GoRoute(
                      path: 'edit',
                      builder: (context, state) =>
                          NewShipmentScreen(editing: state.extra as Shipment),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/client/invoices',
              builder: (context, state) => const InvoicesScreen(),
              routes: [
                GoRoute(
                  path: ':id',
                  builder: (context, state) =>
                      InvoiceDetailScreen(invoice: state.extra as PortalInvoice),
                ),
              ],
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/client/profile',
              builder: (context, state) => const ClientProfileScreen(),
            ),
          ],
        ),
      ],
    ),
  ],
);
