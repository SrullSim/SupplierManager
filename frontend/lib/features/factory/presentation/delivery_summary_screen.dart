import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../l10n/generated/app_localizations.dart';
import '../application/factory_providers.dart';

/// Shows every branch's order for one delivery, plus branches that ordered
/// nothing. Product ids are resolved to names via the catalog.
class DeliverySummaryScreen extends ConsumerWidget {
  const DeliverySummaryScreen({super.key, required this.deliveryId});

  final String deliveryId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final summaryAsync = ref.watch(deliverySummaryProvider(deliveryId));
    final productsAsync = ref.watch(productsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.summaryTitle),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/factory/deliveries'),
        ),
      ),
      body: summaryAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => Center(child: Text(t.loadError)),
        data: (summary) {
          // Build product id -> name map (fallback to id if not loaded).
          final names = <String, String>{};
          productsAsync.whenData((products) {
            for (final p in products) {
              names[p.id] = p.name;
            }
          });

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (summary.branches.isEmpty)
                Padding(
                  padding: const EdgeInsets.all(24),
                  child: Center(child: Text(t.noOrdersYet)),
                ),
              for (final branch in summary.branches)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.store, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              branch.branchName,
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const Spacer(),
                            _StatusChip(status: branch.status),
                          ],
                        ),
                        const Divider(),
                        for (final item in branch.items)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(names[item.productId] ?? item.productId),
                                Text(
                                  '${item.quantity}',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              if (summary.branchesWithoutOrder.isNotEmpty) ...[
                const SizedBox(height: 16),
                Text(
                  t.branchesWithoutOrderTitle,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Card(
                  color: Theme.of(
                    context,
                  ).colorScheme.errorContainer.withValues(alpha: 0.4),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        for (final name in summary.branchesWithoutOrder)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2),
                            child: Text('• $name'),
                          ),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final (label, color) = switch (status) {
      'confirmed' => (t.confirmedBadge, Colors.green),
      'empty_finalized' => (t.statusLocked, Colors.grey),
      _ => (status, Colors.blueGrey),
    };
    return Chip(
      label: Text(label),
      labelStyle: TextStyle(color: color, fontSize: 12),
      visualDensity: VisualDensity.compact,
    );
  }
}
