import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../l10n/generated/app_localizations.dart';
import '../../auth/application/auth_controller.dart';

/// Placeholder factory home. Real screens (branches, catalog, deliveries,
/// order summaries) arrive in Milestone 7.
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
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.factory, size: 64),
            const SizedBox(height: 16),
            Text(t.welcomeFactory, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(t.comingSoon, style: Theme.of(context).textTheme.bodyMedium),
          ],
        ),
      ),
    );
  }
}
