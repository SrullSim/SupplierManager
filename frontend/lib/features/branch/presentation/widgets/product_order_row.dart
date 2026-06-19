import 'package:flutter/material.dart';

import '../../domain/branch_models.dart';

/// A single product line with a quantity stepper.
/// Read-only when [enabled] is false (e.g. order is locked).
class ProductOrderRow extends StatelessWidget {
  const ProductOrderRow({
    super.key,
    required this.product,
    required this.quantity,
    required this.enabled,
    required this.onIncrement,
    required this.onDecrement,
    required this.onSet,
  });

  final Product product;
  final int quantity;
  final bool enabled;
  final VoidCallback onIncrement;
  final VoidCallback onDecrement;
  final ValueChanged<int> onSet;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  Text(
                    product.unit,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            if (enabled) ...[
              IconButton.filledTonal(
                icon: const Icon(Icons.remove),
                onPressed: quantity > 0 ? onDecrement : null,
              ),
              SizedBox(
                width: 48,
                child: Text(
                  '$quantity',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              IconButton.filledTonal(
                icon: const Icon(Icons.add),
                onPressed: onIncrement,
              ),
            ] else
              // Locked: just show the chosen quantity.
              Text(
                '$quantity',
                style: Theme.of(context)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
          ],
        ),
      ),
    );
  }
}
