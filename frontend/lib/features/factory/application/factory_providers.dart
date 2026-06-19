import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/application/auth_controller.dart';
import '../data/factory_repository.dart';
import '../domain/factory_models.dart';

final factoryRepositoryProvider = Provider<FactoryRepository>((ref) {
  return FactoryRepository(ref.watch(dioProvider));
});

/// Catalog products. Auto-refreshes when invalidated after a mutation.
final productsProvider = FutureProvider<List<FactoryProduct>>((ref) {
  return ref.watch(factoryRepositoryProvider).products();
});

final branchesProvider = FutureProvider<List<FactoryBranch>>((ref) {
  return ref.watch(factoryRepositoryProvider).branches();
});

final scheduleProvider = FutureProvider<DeliverySchedule>((ref) {
  return ref.watch(factoryRepositoryProvider).schedule();
});

final deliveriesProvider = FutureProvider<List<FactoryDelivery>>((ref) {
  return ref.watch(factoryRepositoryProvider).deliveries();
});

/// Order summary for a specific delivery.
final deliverySummaryProvider =
    FutureProvider.family<DeliverySummary, String>((ref, deliveryId) {
  return ref.watch(factoryRepositoryProvider).deliverySummary(deliveryId);
});
