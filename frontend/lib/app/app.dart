import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/theme/app_theme.dart';
import '../l10n/generated/app_localizations.dart';
import 'router.dart';

/// Router provider so the GoRouter rebuilds with the same ProviderScope.
final routerProvider = Provider((ref) => buildRouter(ref));

class SupplierManagerApp extends ConsumerWidget {
  const SupplierManagerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      onGenerateTitle: (context) => AppLocalizations.of(context)!.appTitle,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: router,
      // i18n / RTL: Hebrew is the default locale; Flutter applies RTL
      // automatically based on the active locale.
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('he'),
    );
  }
}
