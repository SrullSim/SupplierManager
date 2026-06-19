import 'package:flutter_test/flutter_test.dart';
import 'package:supplier_manager/features/factory/domain/factory_models.dart';

void main() {
  test('CreatedBranch parses branch + one-time password', () {
    final created = CreatedBranch.fromJson({
      'id': 'b1',
      'branch_code': 'jeru01',
      'name': 'Jerusalem',
      'assigned_product_ids': ['p1', 'p2'],
      'active': true,
      'generated_password': 'secret123',
    });
    expect(created.branch.branchCode, 'jeru01');
    expect(created.branch.assignedProductIds, ['p1', 'p2']);
    expect(created.generatedPassword, 'secret123');
  });

  test('DeliverySchedule parses weekdays + time', () {
    final s = DeliverySchedule.fromJson({
      'weekdays': [0, 3],
      'time_of_day': '08:00',
      'active': true,
    });
    expect(s.weekdays, [0, 3]);
    expect(s.timeOfDay, '08:00');
  });

  test('DeliverySummary parses branches + branches without order', () {
    final summary = DeliverySummary.fromJson({
      'delivery_id': 'd1',
      'delivery_datetime': '2026-07-10T08:00:00Z',
      'branches': [
        {
          'branch_name': 'Jerusalem',
          'branch_code': 'jeru01',
          'status': 'confirmed',
          'items': [
            {'product_id': 'p1', 'quantity': 10},
          ],
        },
      ],
      'branches_without_order': ['Tel Aviv'],
    });
    expect(summary.branches, hasLength(1));
    expect(summary.branches.first.items.first.quantity, 10);
    expect(summary.branchesWithoutOrder, ['Tel Aviv']);
  });
}
