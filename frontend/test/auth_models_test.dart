import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:supplier_manager/features/auth/domain/auth_models.dart';

/// Builds an unsigned JWT-shaped string with the given payload.
String _fakeJwt(Map<String, dynamic> payload) {
  String seg(Map<String, dynamic> m) =>
      base64Url.encode(utf8.encode(jsonEncode(m))).replaceAll('=', '');
  final header = seg({'alg': 'HS256', 'typ': 'JWT'});
  final body = seg(payload);
  return '$header.$body.signature';
}

void main() {
  group('roleFromString', () {
    test('maps known roles', () {
      expect(roleFromString('factory_admin'), UserRole.factoryAdmin);
      expect(roleFromString('branch_user'), UserRole.branchUser);
    });

    test('unknown / null -> unknown', () {
      expect(roleFromString('something'), UserRole.unknown);
      expect(roleFromString(null), UserRole.unknown);
    });
  });

  group('AuthUser.fromAccessToken', () {
    test('decodes a factory admin token', () {
      final token =
          _fakeJwt({'sub': 'u1', 'role': 'factory_admin', 'branch_id': null});
      final user = AuthUser.fromAccessToken(token);
      expect(user, isNotNull);
      expect(user!.role, UserRole.factoryAdmin);
      expect(user.userId, 'u1');
      expect(user.branchId, isNull);
    });

    test('decodes a branch user token with branch_id', () {
      final token =
          _fakeJwt({'sub': 'u2', 'role': 'branch_user', 'branch_id': 'b9'});
      final user = AuthUser.fromAccessToken(token);
      expect(user!.role, UserRole.branchUser);
      expect(user.branchId, 'b9');
    });

    test('malformed token -> null', () {
      expect(AuthUser.fromAccessToken('not-a-jwt'), isNull);
      expect(AuthUser.fromAccessToken('only.two'), isNull);
    });
  });

  group('TokenPair.fromJson', () {
    test('parses access + refresh', () {
      final pair =
          TokenPair.fromJson({'access_token': 'a', 'refresh_token': 'r'});
      expect(pair.access, 'a');
      expect(pair.refresh, 'r');
    });
  });
}
