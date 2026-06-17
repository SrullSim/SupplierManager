import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../../../core/storage/token_storage.dart';
import '../data/auth_repository.dart';
import '../domain/auth_models.dart';

// ── Infrastructure providers ─────────────────────────────────────────────────

final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());

final dioProvider = Provider<Dio>((ref) {
  return buildDioClient(ref.watch(tokenStorageProvider));
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    dio: ref.watch(dioProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  );
});

// ── Auth state ───────────────────────────────────────────────────────────────

/// Represents who is logged in (or nobody). null user = signed out.
class AuthState {
  const AuthState({this.user, this.isLoading = false, this.errorKey});

  final AuthUser? user;
  final bool isLoading;

  /// A translation key for an error to show, or null. Decouples the
  /// controller from the UI's localized strings.
  final String? errorKey;

  bool get isAuthenticated => user != null;

  AuthState copyWith({
    AuthUser? user,
    bool? isLoading,
    String? errorKey,
    bool clearUser = false,
    bool clearError = false,
  }) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      isLoading: isLoading ?? this.isLoading,
      errorKey: clearError ? null : (errorKey ?? this.errorKey),
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._repository) : super(const AuthState()) {
    _restore();
  }

  final AuthRepository _repository;

  Future<void> _restore() async {
    final user = await _repository.currentUser();
    if (user != null) state = state.copyWith(user: user);
  }

  Future<void> login(String branchCode, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final user = await _repository.login(branchCode.trim(), password);
      state = AuthState(user: user);
    } on InvalidCredentialsException {
      state = const AuthState(errorKey: 'invalid');
    } on AuthNetworkException {
      state = const AuthState(errorKey: 'network');
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    state = const AuthState();
  }
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref.watch(authRepositoryProvider));
});
