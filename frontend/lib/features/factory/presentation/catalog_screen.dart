import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../l10n/generated/app_localizations.dart';
import '../application/factory_providers.dart';

class CatalogScreen extends ConsumerWidget {
  const CatalogScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final productsAsync = ref.watch(productsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.catalogTitle),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/factory'),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add),
        label: Text(t.addProduct),
        onPressed: () => _showAddDialog(context, ref, t),
      ),
      body: productsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => Center(child: Text(t.loadError)),
        data: (products) {
          if (products.isEmpty) {
            return Center(child: Text(t.noProductsSelected));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(8),
            itemCount: products.length,
            itemBuilder: (context, i) {
              final p = products[i];
              return Card(
                child: ListTile(
                  title: Text(p.name),
                  subtitle: Text(p.unit),
                  trailing: Switch(
                    value: p.active,
                    onChanged: (v) async {
                      await ref
                          .read(factoryRepositoryProvider)
                          .setProductActive(p.id, v);
                      ref.invalidate(productsProvider);
                    },
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Future<void> _showAddDialog(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations t,
  ) async {
    final nameController = TextEditingController();
    final unitController = TextEditingController();

    final created = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(t.addProduct),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: InputDecoration(labelText: t.productName),
              autofocus: true,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: unitController,
              decoration: InputDecoration(labelText: t.productUnit),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(t.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(t.save),
          ),
        ],
      ),
    );

    if (created == true &&
        nameController.text.trim().isNotEmpty &&
        unitController.text.trim().isNotEmpty) {
      await ref.read(factoryRepositoryProvider).createProduct(
          nameController.text.trim(), unitController.text.trim());
      ref.invalidate(productsProvider);
    }
  }
}
