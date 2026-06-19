import 'package:dio/dio.dart';

import '../domain/branch_models.dart';

/// Thrown when an order edit is rejected because the 12-hour cutoff passed.
class OrderLockedException implements Exception {}

/// Thrown for unexpected network/server failures.
class BranchApiException implements Exception {
  BranchApiException(this.message);
  final String message;
}

/// Talks to the branch-facing backend endpoints.
class BranchRepository {
  BranchRepository(this._dio);

  final Dio _dio;

  Future<List<Product>> assignedProducts() async {
    final resp = await _dio.get<List<dynamic>>('/branch/products');
    _ensureOk(resp.statusCode);
    return (resp.data ?? [])
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<UpcomingDelivery?> upcomingDelivery() async {
    final resp =
        await _dio.get<Map<String, dynamic>>('/branch/deliveries/upcoming');
    _ensureOk(resp.statusCode);
    return UpcomingDelivery.fromResponse(resp.data ?? {});
  }

  Future<BranchOrder> getOrder(String deliveryId) async {
    final resp =
        await _dio.get<Map<String, dynamic>>('/branch/orders/$deliveryId');
    _ensureOk(resp.statusCode);
    return BranchOrder.fromJson(resp.data!);
  }

  Future<BranchOrder> saveOrder(
      String deliveryId, Map<String, int> quantities) async {
    final items = quantities.entries
        .where((e) => e.value > 0)
        .map((e) => {'product_id': e.key, 'quantity': e.value})
        .toList();
    final resp = await _dio.put<Map<String, dynamic>>(
      '/branch/orders/$deliveryId',
      data: {'items': items},
    );
    if (resp.statusCode == 403) throw OrderLockedException();
    _ensureOk(resp.statusCode);
    return BranchOrder.fromJson(resp.data!);
  }

  Future<BranchOrder> confirmOrder(String deliveryId) async {
    final resp = await _dio
        .post<Map<String, dynamic>>('/branch/orders/$deliveryId/confirm');
    if (resp.statusCode == 403) throw OrderLockedException();
    _ensureOk(resp.statusCode);
    return BranchOrder.fromJson(resp.data!);
  }

  void _ensureOk(int? status) {
    if (status == null || status >= 400) {
      throw BranchApiException('Request failed with status $status');
    }
  }
}
