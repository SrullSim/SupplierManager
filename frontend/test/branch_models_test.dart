import 'package:flutter_test/flutter_test.dart';
import 'package:supplier_manager/features/branch/domain/branch_models.dart';

void main() {
  group('Product.fromJson', () {
    test('parses fields', () {
      final p = Product.fromJson({'id': '1', 'name': 'חלה', 'unit': 'loaf', 'active': true});
      expect(p.id, '1');
      expect(p.name, 'חלה');
      expect(p.unit, 'loaf');
      expect(p.active, true);
    });
  });

  group('UpcomingDelivery.fromResponse', () {
    test('null delivery -> null', () {
      expect(UpcomingDelivery.fromResponse({'delivery': null}), isNull);
      expect(UpcomingDelivery.fromResponse({}), isNull);
    });

    test('parses wrapped delivery + lock flag', () {
      final d = UpcomingDelivery.fromResponse({
        'delivery': {
          'id': 'd1',
          'delivery_datetime': '2026-07-10T08:00:00Z',
          'cutoff_datetime': '2026-07-09T20:00:00Z',
          'status': 'open',
        },
        'is_locked': true,
      });
      expect(d, isNotNull);
      expect(d!.deliveryId, 'd1');
      expect(d.isLocked, true);
      expect(d.deliveryDatetime.toUtc().hour, 8);
    });
  });

  group('BranchOrder', () {
    test('parses items and builds quantity map', () {
      final order = BranchOrder.fromJson({
        'id': 'o1',
        'delivery_id': 'd1',
        'items': [
          {'product_id': 'p1', 'quantity': 3},
          {'product_id': 'p2', 'quantity': 5},
        ],
        'status': 'confirmed',
        'is_locked': false,
        'cutoff_datetime': '2026-07-09T20:00:00Z',
        'confirmed_at': '2026-07-08T10:00:00Z',
      });
      expect(order.isConfirmed, true);
      expect(order.quantitiesByProduct, {'p1': 3, 'p2': 5});
      expect(order.confirmedAt, isNotNull);
    });

    test('handles empty items and null confirmed_at', () {
      final order = BranchOrder.fromJson({
        'id': 'o2',
        'delivery_id': 'd1',
        'items': <dynamic>[],
        'status': 'draft',
        'is_locked': false,
        'cutoff_datetime': '2026-07-09T20:00:00Z',
        'confirmed_at': null,
      });
      expect(order.items, isEmpty);
      expect(order.quantitiesByProduct, isEmpty);
      expect(order.confirmedAt, isNull);
      expect(order.isConfirmed, false);
    });
  });
}
