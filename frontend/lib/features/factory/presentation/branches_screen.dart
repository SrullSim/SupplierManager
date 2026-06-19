import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../l10n/generated/app_localizations.dart';
import '../application/factory_providers.dart';
import '../data/factory_repository.dart';
import '../domain/factory_models.dart';

class BranchesScreen extends ConsumerWidget {
  const BranchesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final branchesAsync = ref.watch(branchesProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.branchesTitle),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/factory'),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add),
        label: Text(t.addBranch),
        onPressed: () => _showAddBranchDialog(context, ref, t),
      ),
      body: branchesAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => Center(child: Text(t.loadError)),
        data: (branches) {
          if (branches.isEmpty) {
            return Center(child: Text(t.branchesTitle));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(8),
            itemCount: branches.length,
            itemBuilder: (context, i) {
              final b = branches[i];
              return Card(
                child: ListTile(
                  leading: const Icon(Icons.store),
                  title: Text(b.name),
                  subtitle: Text(
                    '${b.branchCode} · '
                    '${t.assignedProductsCount(b.assignedProductIds.length)}',
                  ),
                  trailing: TextButton.icon(
                    icon: const Icon(Icons.checklist),
                    label: Text(t.assignProducts),
                    onPressed: () => _showAssignDialog(context, ref, t, b),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Future<void> _showAddBranchDialog(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations t,
  ) async {
    final codeController = TextEditingController();
    final nameController = TextEditingController();
    String? errorText;

    final submitted = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: Text(t.addBranch),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: codeController,
                decoration: InputDecoration(labelText: t.branchCode),
                autofocus: true,
              ),
              const SizedBox(height: 12),
              TextField(
                controller: nameController,
                decoration: InputDecoration(labelText: t.branchName),
              ),
              if (errorText != null) ...[
                const SizedBox(height: 8),
                Text(
                  errorText!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text(t.cancel),
            ),
            FilledButton(
              onPressed: () async {
                if (codeController.text.trim().isEmpty ||
                    nameController.text.trim().isEmpty) {
                  return;
                }
                try {
                  final created =
                      await ref.read(factoryRepositoryProvider).createBranch(
                            codeController.text.trim(),
                            nameController.text.trim(),
                          );
                  if (context.mounted) Navigator.pop(context, true);
                  ref.invalidate(branchesProvider);
                  if (context.mounted && created.generatedPassword != null) {
                    await _showPasswordDialog(
                      context,
                      t,
                      created.branch.branchCode,
                      created.generatedPassword!,
                    );
                  }
                } on FactoryApiException catch (e) {
                  setState(() => errorText = e.message);
                }
              },
              child: Text(t.save),
            ),
          ],
        ),
      ),
    );
    if (submitted != true) return;
  }

  Future<void> _showPasswordDialog(
    BuildContext context,
    AppLocalizations t,
    String branchCode,
    String password,
  ) async {
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(t.branchCreatedTitle),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${t.branchCode}: $branchCode'),
            const SizedBox(height: 12),
            Text(t.generatedPasswordLabel),
            const SizedBox(height: 4),
            Row(
              children: [
                Expanded(
                  child: SelectableText(
                    password,
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.copy),
                  onPressed: () async {
                    await Clipboard.setData(ClipboardData(text: password));
                    if (context.mounted) {
                      ScaffoldMessenger.of(
                        context,
                      ).showSnackBar(SnackBar(content: Text(t.copyDone)));
                    }
                  },
                ),
              ],
            ),
          ],
        ),
        actions: [
          FilledButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  Future<void> _showAssignDialog(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations t,
    FactoryBranch branch,
  ) async {
    final products = await ref.read(productsProvider.future);
    if (!context.mounted) return;
    final selected = {...branch.assignedProductIds};

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: Text('${t.assignProducts} · ${branch.name}'),
          content: SizedBox(
            width: 360,
            child: ListView(
              shrinkWrap: true,
              children: [
                for (final p in products)
                  CheckboxListTile(
                    title: Text(p.name),
                    subtitle: Text(p.unit),
                    value: selected.contains(p.id),
                    onChanged: (v) => setState(() {
                      if (v == true) {
                        selected.add(p.id);
                      } else {
                        selected.remove(p.id);
                      }
                    }),
                  ),
              ],
            ),
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
      ),
    );

    if (saved == true) {
      await ref
          .read(factoryRepositoryProvider)
          .assignProducts(branch.id, selected.toList());
      ref.invalidate(branchesProvider);
    }
  }
}
