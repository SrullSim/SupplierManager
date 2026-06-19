/// A product in the factory catalog.
class FactoryProduct {
  const FactoryProduct({
    required this.id,
    required this.name,
    required this.unit,
    required this.active,
  });

  final String id;
  final String name;
  final String unit;
  final bool active;

  factory FactoryProduct.fromJson(Map<String, dynamic> json) => FactoryProduct(
        id: json['id'] as String,
        name: json['name'] as String,
        unit: json['unit'] as String,
        active: json['active'] as bool? ?? true,
      );
}

/// A branch as seen by the factory.
class FactoryBranch {
  const FactoryBranch({
    required this.id,
    required this.branchCode,
    required this.name,
    required this.assignedProductIds,
    required this.active,
  });

  final String id;
  final String branchCode;
  final String name;
  final List<String> assignedProductIds;
  final bool active;

  factory FactoryBranch.fromJson(Map<String, dynamic> json) => FactoryBranch(
        id: json['id'] as String,
        branchCode: json['branch_code'] as String,
        name: json['name'] as String,
        assignedProductIds:
            (json['assigned_product_ids'] as List<dynamic>? ?? [])
                .map((e) => e as String)
                .toList(),
        active: json['active'] as bool? ?? true,
      );
}

/// Result of creating a branch — includes the one-time generated password.
class CreatedBranch {
  const CreatedBranch({required this.branch, this.generatedPassword});

  final FactoryBranch branch;
  final String? generatedPassword;

  factory CreatedBranch.fromJson(Map<String, dynamic> json) => CreatedBranch(
        branch: FactoryBranch.fromJson(json),
        generatedPassword: json['generated_password'] as String?,
      );
}

/// The recurring weekly delivery schedule.
class DeliverySchedule {
  const DeliverySchedule({
    required this.weekdays,
    required this.timeOfDay,
    required this.active,
  });

  /// 0 = Monday ... 6 = Sunday (Python weekday convention).
  final List<int> weekdays;
  final String timeOfDay; // "HH:MM"
  final bool active;

  factory DeliverySchedule.fromJson(Map<String, dynamic> json) =>
      DeliverySchedule(
        weekdays: (json['weekdays'] as List<dynamic>? ?? [])
            .map((e) => e as int)
            .toList(),
        timeOfDay: json['time_of_day'] as String? ?? '08:00',
        active: json['active'] as bool? ?? true,
      );
}

/// A delivery event.
class FactoryDelivery {
  const FactoryDelivery({
    required this.id,
    required this.deliveryDatetime,
    required this.cutoffDatetime,
    required this.source,
    required this.status,
  });

  final String id;
  final DateTime deliveryDatetime;
  final DateTime cutoffDatetime;
  final String source; // scheduled | one_off
  final String status; // open | locked | completed

  factory FactoryDelivery.fromJson(Map<String, dynamic> json) =>
      FactoryDelivery(
        id: json['id'] as String,
        deliveryDatetime: DateTime.parse(json['delivery_datetime'] as String),
        cutoffDatetime: DateTime.parse(json['cutoff_datetime'] as String),
        source: json['source'] as String,
        status: json['status'] as String,
      );
}

/// One branch's order within a delivery summary.
class BranchOrderSummary {
  const BranchOrderSummary({
    required this.branchName,
    required this.branchCode,
    required this.status,
    required this.items,
  });

  final String branchName;
  final String branchCode;
  final String status;
  final List<({String productId, int quantity})> items;

  factory BranchOrderSummary.fromJson(Map<String, dynamic> json) =>
      BranchOrderSummary(
        branchName: json['branch_name'] as String,
        branchCode: json['branch_code'] as String,
        status: json['status'] as String,
        items: (json['items'] as List<dynamic>)
            .map(
              (e) => (
                productId: (e as Map<String, dynamic>)['product_id'] as String,
                quantity: e['quantity'] as int,
              ),
            )
            .toList(),
      );
}

/// Full order summary for a delivery, across all branches.
class DeliverySummary {
  const DeliverySummary({
    required this.deliveryId,
    required this.deliveryDatetime,
    required this.branches,
    required this.branchesWithoutOrder,
  });

  final String deliveryId;
  final DateTime deliveryDatetime;
  final List<BranchOrderSummary> branches;
  final List<String> branchesWithoutOrder;

  factory DeliverySummary.fromJson(Map<String, dynamic> json) =>
      DeliverySummary(
        deliveryId: json['delivery_id'] as String,
        deliveryDatetime: DateTime.parse(json['delivery_datetime'] as String),
        branches: (json['branches'] as List<dynamic>)
            .map((e) => BranchOrderSummary.fromJson(e as Map<String, dynamic>))
            .toList(),
        branchesWithoutOrder:
            (json['branches_without_order'] as List<dynamic>? ?? [])
                .map((e) => e as String)
                .toList(),
      );
}
