// Smoke test: the app boots and shows the login screen in Hebrew.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:supplier_manager/app/app.dart';

void main() {
  testWidgets('boots to the login screen', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: SupplierManagerApp()),
    );
    // Let the router settle on /login.
    await tester.pumpAndSettle();

    // The sign-in button label (Hebrew) should be present.
    expect(find.text('התחבר'), findsOneWidget);
    // The branch-code field label should be present.
    expect(find.text('קוד סניף'), findsWidgets);
  });
}
