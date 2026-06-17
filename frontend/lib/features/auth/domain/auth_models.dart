import 'dart:convert';

/// The role embedded in the JWT.
enum UserRole { factoryAdmin, branchUser, unknown }

UserRole roleFromString(String? value) {
  switch (value) {
    case 'factory_admin':
      return UserRole.factoryAdmin;
    case 'branch_user':
      return UserRole.branchUser;
    default:
      return UserRole.unknown;
  }
}

/// The authenticated user, decoded from the access token payload.
class AuthUser {
  const AuthUser({required this.userId, required this.role, this.branchId});

  final String userId;
  final UserRole role;
  final String? branchId;

  /// Decodes the JWT payload (middle segment) without verifying the signature —
  /// the server is the source of truth; this is only to route the UI.
  static AuthUser? fromAccessToken(String token) {
    try {
      final parts = token.split('.');
      if (parts.length != 3) return null;
      final payload = parts[1];
      final normalized = base64Url.normalize(payload);
      final decoded = jsonDecode(utf8.decode(base64Url.decode(normalized)))
          as Map<String, dynamic>;
      return AuthUser(
        userId: decoded['sub'] as String? ?? '',
        role: roleFromString(decoded['role'] as String?),
        branchId: decoded['branch_id'] as String?,
      );
    } catch (_) {
      return null;
    }
  }
}

/// Tokens returned by the login endpoint.
class TokenPair {
  const TokenPair({required this.access, required this.refresh});

  final String access;
  final String refresh;

  factory TokenPair.fromJson(Map<String, dynamic> json) => TokenPair(
        access: json['access_token'] as String,
        refresh: json['refresh_token'] as String,
      );
}
