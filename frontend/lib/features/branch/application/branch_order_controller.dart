import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/application/auth_controller.dart';
import '../data/branch_repository.dart';
import '../domain/branch_models.dart';

final branchRepositoryProvider = Provider<BranchRepository>((ref) {
  return BranchRepository(ref.watch(dioProvider));
});

/// Everything the branch order screen needs, in one cohesive state object.
class BranchOrderState {
  const BranchOrderState({
    this.isLoading = true,
    this.isSaving = false,
    this.products = const [],
    this.delivery,
    this.order,
    this.quantities = const {},
    this.errorKey,
    this.justConfirmed = false,
  });

  final bool isLoading;
  final bool isSaving;
  final List<Product> products;
  final UpcomingDelivery? delivery;
  final BranchOrder? order;

  /// Locally-edited quantities, keyed by product id.
  final Map<String, int> quantities;
  final String? errorKey;
  final bool justConfirmed;

  bool get hasDelivery => delivery != null;
  bool get isLocked => delivery?.isLocked ?? true;
  bool get isConfirmed => order?.isConfirmed ?? false;

  /// True when the local edits differ from what's saved on the server.
  bool get hasUnsavedChanges {
    final saved = order?.quantitiesByProduct ?? const {};
    final localNonZero = {
      for (final e in quantities.entries)
        if (e.value > 0) e.key: e.value,
    };
    return localNonZero.length != saved.length ||
        localNonZero.entries.any((e) => saved[e.key] != e.value);
  }

  int get totalItems => quantities.values.fold(0, (sum, q) => sum + q);

  BranchOrderState copyWith({
    bool? isLoading,
    bool? isSaving,
    List<Product>? products,
    UpcomingDelivery? delivery,
    BranchOrder? order,
    Map<String, int>? quantities,
    String? errorKey,
    bool clearError = false,
    bool? justConfirmed,
  }) {
    return BranchOrderState(
      isLoading: isLoading ?? this.isLoading,
      isSaving: isSaving ?? this.isSaving,
      products: products ?? this.products,
      delivery: delivery ?? this.delivery,
      order: order ?? this.order,
      quantities: quantities ?? this.quantities,
      errorKey: clearError ? null : (errorKey ?? this.errorKey),
      justConfirmed: justConfirmed ?? this.justConfirmed,
    );
  }
}

class BranchOrderController extends StateNotifier<BranchOrderState> {
  BranchOrderController(this._repo) : super(const BranchOrderState()) {
    load();
  }

  final BranchRepository _repo;

  Future<void> load() async {
    state = const BranchOrderState(isLoading: true);
    try {
      final delivery = await _repo.upcomingDelivery();
      if (delivery == null) {
        state = const BranchOrderState(isLoading: false);
        return;
      }
      final products = await _repo.assignedProducts();
      final order = await _repo.getOrder(delivery.deliveryId);
      state = BranchOrderState(
        isLoading: false,
        products: products,
        delivery: delivery,
        order: order,
        quantities: Map<String, int>.from(order.quantitiesByProduct),
      );
    } on Object {
      state = const BranchOrderState(isLoading: false, errorKey: 'network');
    }
  }

  void setQuantity(String productId, int quantity) {
    if (state.isLocked) return;
    final next = Map<String, int>.from(state.quantities);
    if (quantity <= 0) {
      next.remove(productId);
    } else {
      next[productId] = quantity;
    }
    state = state.copyWith(quantities: next, justConfirmed: false);
  }

  void increment(String productId) =>
      setQuantity(productId, (state.quantities[productId] ?? 0) + 1);

  void decrement(String productId) =>
      setQuantity(productId, (state.quantities[productId] ?? 0) - 1);

  Future<void> save() async {
    final delivery = state.delivery;
    if (delivery == null || state.isLocked) return;
    state = state.copyWith(isSaving: true, clearError: true);
    try {
      final order =
          await _repo.saveOrder(delivery.deliveryId, state.quantities);
      state = state.copyWith(
        isSaving: false,
        order: order,
        quantities: Map<String, int>.from(order.quantitiesByProduct),
      );
    } on OrderLockedException {
      state = state.copyWith(isSaving: false, errorKey: 'locked');
    } on Object {
      state = state.copyWith(isSaving: false, errorKey: 'network');
    }
  }

  Future<void> confirm() async {
    final delivery = state.delivery;
    if (delivery == null || state.isLocked) return;
    state = state.copyWith(isSaving: true, clearError: true);
    try {
      // Persist current quantities first, then confirm.
      await _repo.saveOrder(delivery.deliveryId, state.quantities);
      final order = await _repo.confirmOrder(delivery.deliveryId);
      state = state.copyWith(
        isSaving: false,
        order: order,
        quantities: Map<String, int>.from(order.quantitiesByProduct),
        justConfirmed: true,
      );
    } on OrderLockedException {
      state = state.copyWith(isSaving: false, errorKey: 'locked');
    } on Object {
      state = state.copyWith(isSaving: false, errorKey: 'network');
    }
  }
}

final branchOrderControllerProvider =
    StateNotifierProvider<BranchOrderController, BranchOrderState>((ref) {
  return BranchOrderController(ref.watch(branchRepositoryProvider));
});
