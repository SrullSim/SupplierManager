import 'package:dio/dio.dart';

import '../../../core/storage/token_storage.dart';
import '../domain/auth_models.dart';

/// Thrown when the backend rejects the credentials (401).
class InvalidCredentialsException implements Exception {}

/// Thrown when the server is unreachable or returns a non-auth error.
class AuthNetworkException implements Exception {}

/// Talks to the backend /auth endpoints and persists tokens.
class AuthRepository {
  AuthRepository({required Dio dio, required TokenStorage tokenStorage})
      : _dio = dio,
        _tokenStorage = tokenStorage;

  final Dio _dio;
  final TokenStorage _tokenStorage;

  Future<AuthUser> login(String branchCode, String password) async {
    try {
      final resp = await _dio.post<Map<String, dynamic>>(
        '/auth/login',
        data: {'branch_code': branchCode, 'password': password},
      );

      if (resp.statusCode == 401) {
        throw InvalidCredentialsException();
      }
      if (resp.statusCode != 200 || resp.data == null) {
        throw AuthNetworkException();
      }

      final tokens = TokenPair.fromJson(resp.data!);
      await _tokenStorage.save(access: tokens.access, refresh: tokens.refresh);

      final user = AuthUser.fromAccessToken(tokens.access);
      if (user == null) throw AuthNetworkException();
      return user;
    } on DioException {
      throw AuthNetworkException();
    }
  }

  Future<void> logout() async {
    final refresh = await _tokenStorage.readRefresh();
    if (refresh != null) {
      try {
        await _dio.post<void>('/auth/logout', data: {'refresh_token': refresh});
      } on DioException {
        // Logout should succeed locally even if the server call fails.
      }
    }
    await _tokenStorage.clear();
  }

  /// Restores the session on app start, if a valid token is stored.
  Future<AuthUser?> currentUser() async {
    final access = await _tokenStorage.readAccess();
    if (access == null || access.isEmpty) return null;
    return AuthUser.fromAccessToken(access);
  }
}
