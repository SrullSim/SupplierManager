import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../l10n/generated/app_localizations.dart';
import '../../auth/application/auth_controller.dart';

/// Factory dashboard: entry points to branches, catalog, and deliveries.
class FactoryHomeScreen extends ConsumerWidget {
  const FactoryHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(t.factoryHomeTitle),
        actions: [
          IconButton(
            tooltip: t.logoutButton,
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: GridView.count(
            shrinkWrap: true,
            padding: const EdgeInsets.all(24),
            crossAxisCount: 2,
            mainAxisSpacing: 16,
            crossAxisSpacing: 16,
            childAspectRatio: 1.3,
            children: [
              _DashboardCard(
                icon: Icons.store,
                label: t.navBranches,
                onTap: () => context.go('/factory/branches'),
              ),
              _DashboardCard(
                icon: Icons.bakery_dining,
                label: t.navCatalog,
                onTap: () => context.go('/factory/catalog'),
              ),
              _DashboardCard(
                icon: Icons.local_shipping,
                label: t.navDeliveries,
                onTap: () => context.go('/factory/deliveries'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DashboardCard extends StatelessWidget {
  const _DashboardCard({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 48, color: scheme.primary),
            const SizedBox(height: 12),
            Text(label, style: Theme.of(context).textTheme.titleMedium),
          ],
        ),
      ),
    );
  }
}
