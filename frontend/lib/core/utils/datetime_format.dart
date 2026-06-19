import 'package:intl/intl.dart';

/// Formatting helpers for delivery dates and the lock countdown.
class DateTimeFormat {
  /// Formats a UTC datetime in the device's local time, e.g. "ראשון, 18 ביוני, 08:00".
  static String dateTime(DateTime utc, String localeCode) {
    final local = utc.toLocal();
    return DateFormat('EEEE, d MMMM, HH:mm', localeCode).format(local);
  }

  /// Short date+time, e.g. "18/06 08:00".
  static String shortDateTime(DateTime utc, String localeCode) {
    final local = utc.toLocal();
    return DateFormat('dd/MM HH:mm', localeCode).format(local);
  }

  /// Builds a countdown string from now until [target].
  /// Returns parts as a list of (value, unitLabel) so the caller localizes units.
  static List<({int value, CountdownUnit unit})> countdownParts(
      DateTime target) {
    final remaining = target.toLocal().difference(DateTime.now());
    if (remaining.isNegative) return const [];
    final days = remaining.inDays;
    final hours = remaining.inHours % 24;
    final minutes = remaining.inMinutes % 60;

    final parts = <({int value, CountdownUnit unit})>[];
    if (days > 0) parts.add((value: days, unit: CountdownUnit.days));
    if (hours > 0) parts.add((value: hours, unit: CountdownUnit.hours));
    // Always show minutes when under a day so it doesn't look frozen.
    if (days == 0) parts.add((value: minutes, unit: CountdownUnit.minutes));
    return parts;
  }
}

enum CountdownUnit { days, hours, minutes }
