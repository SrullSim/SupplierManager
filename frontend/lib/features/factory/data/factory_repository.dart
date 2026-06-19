import 'package:dio/dio.dart';

import '../domain/factory_models.dart';

class FactoryApiException implements Exception {
  FactoryApiException(this.message);
  final String message;
}

/// Talks to all factory-facing backend endpoints.
class FactoryRepository {
  FactoryRepository(this._dio);

  final Dio _dio;

  // ── Catalog ───────────────────────────────────────────────────────────────

  Future<List<FactoryProduct>> products() async {
    final resp = await _dio.get<List<dynamic>>('/factory/products');
    _ok(resp.statusCode);
    return (resp.data ?? [])
        .map((e) => FactoryProduct.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<FactoryProduct> createProduct(String name, String unit) async {
    final resp = await _dio.post<Map<String, dynamic>>(
      '/factory/products',
      data: {'name': name, 'unit': unit},
    );
    _ok(resp.statusCode);
    return FactoryProduct.fromJson(resp.data!);
  }

  Future<FactoryProduct> setProductActive(String id, bool active) async {
    final resp = await _dio.patch<Map<String, dynamic>>(
      '/factory/products/$id',
      data: {'active': active},
    );
    _ok(resp.statusCode);
    return FactoryProduct.fromJson(resp.data!);
  }

  // ── Branches ──────────────────────────────────────────────────────────────

  Future<List<FactoryBranch>> branches() async {
    final resp = await _dio.get<List<dynamic>>('/factory/branches');
    _ok(resp.statusCode);
    return (resp.data ?? [])
        .map((e) => FactoryBranch.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CreatedBranch> createBranch(String branchCode, String name) async {
    final resp = await _dio.post<Map<String, dynamic>>(
      '/factory/branches',
      data: {'branch_code': branchCode, 'name': name},
    );
    if (resp.statusCode == 409) {
      throw FactoryApiException('branch_code already in use');
    }
    _ok(resp.statusCode);
    return CreatedBranch.fromJson(resp.data!);
  }

  Future<FactoryBranch> assignProducts(
    String branchId,
    List<String> productIds,
  ) async {
    final resp = await _dio.put<Map<String, dynamic>>(
      '/factory/branches/$branchId/products',
      data: {'product_ids': productIds},
    );
    _ok(resp.statusCode);
    return FactoryBranch.fromJson(resp.data!);
  }

  // ── Schedule & deliveries ───────────────────────────────────────────────────

  Future<DeliverySchedule> schedule() async {
    final resp = await _dio.get<Map<String, dynamic>>('/factory/schedule');
    _ok(resp.statusCode);
    return DeliverySchedule.fromJson(resp.data!);
  }

  Future<DeliverySchedule> updateSchedule(
    List<int> weekdays,
    String timeOfDay,
  ) async {
    final resp = await _dio.put<Map<String, dynamic>>(
      '/factory/schedule',
      data: {'weekdays': weekdays, 'time_of_day': timeOfDay},
    );
    _ok(resp.statusCode);
    return DeliverySchedule.fromJson(resp.data!);
  }

  Future<List<FactoryDelivery>> deliveries() async {
    final resp = await _dio.get<List<dynamic>>('/factory/deliveries');
    _ok(resp.statusCode);
    return (resp.data ?? [])
        .map((e) => FactoryDelivery.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<FactoryDelivery> createDelivery(DateTime deliveryUtc) async {
    final resp = await _dio.post<Map<String, dynamic>>(
      '/factory/deliveries',
      data: {'delivery_datetime': deliveryUtc.toUtc().toIso8601String()},
    );
    _ok(resp.statusCode);
    return FactoryDelivery.fromJson(resp.data!);
  }

  Future<int> generateDeliveries() async {
    final resp = await _dio.post<Map<String, dynamic>>(
      '/factory/deliveries/generate',
    );
    _ok(resp.statusCode);
    return (resp.data?['generated'] as int?) ?? 0;
  }

  Future<DeliverySummary> deliverySummary(String deliveryId) async {
    final resp = await _dio.get<Map<String, dynamic>>(
      '/factory/deliveries/$deliveryId/summary',
    );
    _ok(resp.statusCode);
    return DeliverySummary.fromJson(resp.data!);
  }

  void _ok(int? status) {
    if (status == null || status >= 400) {
      throw FactoryApiException('Request failed with status $status');
    }
  }
}
