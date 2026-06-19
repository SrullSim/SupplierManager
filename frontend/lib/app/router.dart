import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/application/auth_controller.dart';
import '../features/auth/domain/auth_models.dart';
import '../features/auth/presentation/login_screen.dart';
import '../features/branch/presentation/branch_home_screen.dart';
import '../features/factory/presentation/branches_screen.dart';
import '../features/factory/presentation/catalog_screen.dart';
import '../features/factory/presentation/deliveries_screen.dart';
import '../features/factory/presentation/delivery_summary_screen.dart';
import '../features/factory/presentation/factory_home_screen.dart';

/// Builds the app router with role-based redirects driven by auth state.
GoRouter buildRouter(Ref ref) {
  return GoRouter(
    initialLocation: '/login',
    refreshListenable: _AuthListenable(ref),
    redirect: (context, goState) {
      final auth = ref.read(authControllerProvider);
      final loggingIn = goState.matchedLocation == '/login';

      if (!auth.isAuthenticated) {
        return loggingIn ? null : '/login';
      }

      // Authenticated: send each role to its home, away from /login.
      final home =
          auth.user!.role == UserRole.factoryAdmin ? '/factory' : '/branch';
      if (loggingIn) return home;

      // Guard cross-role access.
      if (goState.matchedLocation.startsWith('/factory') &&
          auth.user!.role != UserRole.factoryAdmin) {
        return '/branch';
      }
      if (goState.matchedLocation.startsWith('/branch') &&
          auth.user!.role != UserRole.branchUser) {
        return '/factory';
      }
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/factory', builder: (_, __) => const FactoryHomeScreen()),
      GoRoute(
        path: '/factory/catalog',
        builder: (_, __) => const CatalogScreen(),
      ),
      GoRoute(
        path: '/factory/branches',
        builder: (_, __) => const BranchesScreen(),
      ),
      GoRoute(
        path: '/factory/deliveries',
        builder: (_, __) => const DeliveriesScreen(),
      ),
      GoRoute(
        path: '/factory/deliveries/:id/summary',
        builder: (_, state) =>
            DeliverySummaryScreen(deliveryId: state.pathParameters['id']!),
      ),
      GoRoute(path: '/branch', builder: (_, __) => const BranchHomeScreen()),
    ],
  );
}

/// Bridges Riverpod auth state changes to go_router's refresh mechanism.
class _AuthListenable extends ChangeNotifier {
  _AuthListenable(Ref ref) {
    ref.listen(authControllerProvider, (_, __) => notifyListeners());
  }
}
