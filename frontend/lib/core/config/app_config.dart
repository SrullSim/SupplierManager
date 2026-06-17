/// App-wide configuration and feature flags.
///
/// Values can be overridden at build time with --dart-define, e.g.:
///   flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
class AppConfig {
  /// Backend base URL. Defaults to the local dev server.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  /// Feature flag: when false, only Hebrew is active and NO language
  /// selector is shown. Set to true to enable the language switcher.
  static const bool multiLanguageEnabled = bool.fromEnvironment(
    'MULTI_LANGUAGE_ENABLED',
    defaultValue: false,
  );

  /// Supported locales. Hebrew is the default and first.
  static const List<String> supportedLocaleCodes = ['he', 'en'];
}
