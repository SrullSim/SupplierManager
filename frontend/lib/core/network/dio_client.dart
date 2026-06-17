import 'package:dio/dio.dart';

import '../config/app_config.dart';
import '../storage/token_storage.dart';

/// Builds a configured [Dio] instance with an interceptor that attaches
/// the JWT access token to every request.
Dio buildDioClient(TokenStorage tokenStorage) {
  final dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
      // Don't throw on 4xx so the UI layer can read error details.
      validateStatus: (status) => status != null && status < 500,
    ),
  );

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await tokenStorage.readAccess();
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ),
  );

  return dio;
}
