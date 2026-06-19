import 'dart:async';

import 'package:flutter/material.dart';

import '../../../../core/utils/datetime_format.dart';
import '../../../../l10n/generated/app_localizations.dart';
import '../../domain/branch_models.dart';

/// Shows the delivery date, lock state, and a live countdown to the cutoff.
class LockStatusBanner extends StatefulWidget {
  const LockStatusBanner({super.key, required this.delivery});

  final UpcomingDelivery delivery;

  @override
  State<LockStatusBanner> createState() => _LockStatusBannerState();
}

class _LockStatusBannerState extends State<LockStatusBanner> {
  Timer? _ticker;

  @override
  void initState() {
    super.initState();
    // Refresh the countdown once a minute.
    _ticker = Timer.periodic(const Duration(minutes: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  String _countdownText(AppLocalizations t) {
    final parts = DateTimeFormat.countdownParts(widget.delivery.cutoffDatetime);
    if (parts.isEmpty) return t.closedAt;
    String unitLabel(CountdownUnit u) => switch (u) {
          CountdownUnit.days => t.daysShort,
          CountdownUnit.hours => t.hoursShort,
          CountdownUnit.minutes => t.minutesShort,
        };
    final joined =
        parts.map((p) => '${p.value} ${unitLabel(p.unit)}').join(' ');
    return '${t.closesIn} $joined';
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final locale = Localizations.localeOf(context).languageCode;
    final locked = widget.delivery.isLocked;
    final scheme = Theme.of(context).colorScheme;
    final color = locked ? scheme.error : scheme.primary;

    return Card(
      color: color.withValues(alpha: 0.08),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(locked ? Icons.lock : Icons.lock_open, color: color),
                const SizedBox(width: 8),
                Text(
                  locked ? t.orderLocked : t.orderEditable,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(color: color, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text('${t.deliveryDateLabel}: '
                '${DateTimeFormat.dateTime(widget.delivery.deliveryDatetime, locale)}'),
            const SizedBox(height: 4),
            Text(
              _countdownText(t),
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: color),
            ),
          ],
        ),
      ),
    );
  }
}
