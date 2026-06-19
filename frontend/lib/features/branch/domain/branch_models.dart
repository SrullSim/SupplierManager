/// A product the branch may order.
class Product {
  const Product({
    required this.id,
    required this.name,
    required this.unit,
    required this.active,
  });

  final String id;
  final String name;
  final String unit;
  final bool active;

  factory Product.fromJson(Map<String, dynamic> json) => Product(
        id: json['id'] as String,
        name: json['name'] as String,
        unit: json['unit'] as String,
        active: json['active'] as bool? ?? true,
      );
}

/// The next delivery for this branch, plus whether ordering is locked.
class UpcomingDelivery {
  const UpcomingDelivery({
    required this.deliveryId,
    required this.deliveryDatetime,
    required this.cutoffDatetime,
    required this.status,
    required this.isLocked,
  });

  final String deliveryId;
  final DateTime deliveryDatetime; // UTC
  final DateTime cutoffDatetime; // UTC
  final String status;
  final bool isLocked;

  /// Parses the `/branch/deliveries/upcoming` response, which wraps the
  /// delivery in a `delivery` key alongside `is_locked`. Returns null when
  /// there is no upcoming delivery.
  static UpcomingDelivery? fromResponse(Map<String, dynamic> json) {
    final delivery = json['delivery'];
    if (delivery == null) return null;
    final d = delivery as Map<String, dynamic>;
    return UpcomingDelivery(
      deliveryId: d['id'] as String,
      deliveryDatetime: DateTime.parse(d['delivery_datetime'] as String),
      cutoffDatetime: DateTime.parse(d['cutoff_datetime'] as String),
      status: d['status'] as String,
      isLocked: json['is_locked'] as bool? ?? false,
    );
  }
}

/// A single line in an order.
class OrderItem {
  const OrderItem({required this.productId, required this.quantity});

  final String productId;
  final int quantity;

  factory OrderItem.fromJson(Map<String, dynamic> json) => OrderItem(
        productId: json['product_id'] as String,
        quantity: json['quantity'] as int,
      );

  Map<String, dynamic> toJson() =>
      {'product_id': productId, 'quantity': quantity};
}

/// The branch's order for a delivery.
class BranchOrder {
  const BranchOrder({
    required this.id,
    required this.deliveryId,
    required this.items,
    required this.status,
    required this.isLocked,
    required this.cutoffDatetime,
    this.confirmedAt,
  });

  final String id;
  final String deliveryId;
  final List<OrderItem> items;
  final String status; // draft | confirmed | locked | empty_finalized
  final bool isLocked;
  final DateTime cutoffDatetime;
  final DateTime? confirmedAt;

  bool get isConfirmed => status == 'confirmed';

  /// Quantity map keyed by product id, for quick lookup in the UI.
  Map<String, int> get quantitiesByProduct => {
        for (final item in items) item.productId: item.quantity,
      };

  factory BranchOrder.fromJson(Map<String, dynamic> json) => BranchOrder(
        id: json['id'] as String,
        deliveryId: json['delivery_id'] as String,
        items: (json['items'] as List<dynamic>)
            .map((e) => OrderItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        status: json['status'] as String,
        isLocked: json['is_locked'] as bool? ?? false,
        cutoffDatetime: DateTime.parse(json['cutoff_datetime'] as String),
        confirmedAt: json['confirmed_at'] == null
            ? null
            : DateTime.parse(json['confirmed_at'] as String),
      );
}
