import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../l10n/generated/app_localizations.dart';
import '../../auth/application/auth_controller.dart';
import '../application/branch_order_controller.dart';
import 'widgets/lock_status_banner.dart';
import 'widgets/product_order_row.dart';

class BranchHomeScreen extends ConsumerWidget {
  const BranchHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final state = ref.watch(branchOrderControllerProvider);
    final controller = ref.read(branchOrderControllerProvider.notifier);

    // Surface save/confirm results and errors as snackbars.
    ref.listen(branchOrderControllerProvider, (prev, next) {
      final messenger = ScaffoldMessenger.of(context);
      if (next.errorKey != null && next.errorKey != prev?.errorKey) {
        final msg = next.errorKey == 'locked'
            ? t.errorLockedMessage
            : t.errorNetworkMessage;
        messenger.showSnackBar(SnackBar(content: Text(msg)));
      } else if (next.justConfirmed && !(prev?.justConfirmed ?? false)) {
        messenger
            .showSnackBar(SnackBar(content: Text(t.orderConfirmedMessage)));
      }
    });

    return Scaffold(
      appBar: AppBar(
        title: Text(t.branchHomeTitle),
        actions: [
          IconButton(
            tooltip: t.logoutButton,
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      body: _buildBody(context, t, state, controller),
    );
  }

  Widget _buildBody(
    BuildContext context,
    AppLocalizations t,
    BranchOrderState state,
    BranchOrderController controller,
  ) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (!state.hasDelivery) {
      return _EmptyState(
        message: state.errorKey != null
            ? t.errorNetworkMessage
            : t.noUpcomingDelivery,
        onRetry: () => controller.load(),
        retryLabel: t.retryButton,
      );
    }

    final locked = state.isLocked;

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              LockStatusBanner(delivery: state.delivery!),
              const SizedBox(height: 8),
              if (state.isConfirmed)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle, color: Colors.green),
                      const SizedBox(width: 8),
                      Text(
                        t.confirmedBadge,
                        style: const TextStyle(
                          color: Colors.green,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 8),
              Text(
                locked ? t.orderSummaryTitle : t.myOrderTitle,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              ..._buildProductList(context, t, state, controller, locked),
            ],
          ),
        ),
        _BottomBar(state: state, controller: controller, t: t),
      ],
    );
  }

  List<Widget> _buildProductList(
    BuildContext context,
    AppLocalizations t,
    BranchOrderState state,
    BranchOrderController controller,
    bool locked,
  ) {
    // When locked, show only products that were actually ordered (the summary).
    final products = locked
        ? state.products
            .where((p) => (state.quantities[p.id] ?? 0) > 0)
            .toList()
        : state.products;

    if (products.isEmpty) {
      return [
        Padding(
          padding: const EdgeInsets.all(24),
          child: Center(child: Text(t.noProductsSelected)),
        ),
      ];
    }

    return [
      for (final p in products)
        ProductOrderRow(
          product: p,
          quantity: state.quantities[p.id] ?? 0,
          enabled: !locked,
          onIncrement: () => controller.increment(p.id),
          onDecrement: () => controller.decrement(p.id),
          onSet: (q) => controller.setQuantity(p.id, q),
        ),
    ];
  }
}

class _BottomBar extends StatelessWidget {
  const _BottomBar(
      {required this.state, required this.controller, required this.t});

  final BranchOrderState state;
  final BranchOrderController controller;
  final AppLocalizations t;

  @override
  Widget build(BuildContext context) {
    if (state.isLocked) return const SizedBox.shrink();

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('${t.totalItemsLabel}: ${state.totalItems}'),
                if (state.hasUnsavedChanges)
                  Text(t.unsavedChanges,
                      style: TextStyle(
                          color: Theme.of(context).colorScheme.error)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: state.isSaving ? null : () => controller.save(),
                    child: Text(t.saveButton),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: state.isSaving || state.totalItems == 0
                        ? null
                        : () => controller.confirm(),
                    child: state.isSaving
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Text(t.confirmOrderButton),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.message,
    required this.onRetry,
    required this.retryLabel,
  });

  final String message;
  final VoidCallback onRetry;
  final String retryLabel;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.inbox, size: 64),
          const SizedBox(height: 16),
          Text(message, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 16),
          OutlinedButton(onPressed: onRetry, child: Text(retryLabel)),
        ],
      ),
    );
  }
}
