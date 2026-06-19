import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/utils/datetime_format.dart';
import '../../../l10n/generated/app_localizations.dart';
import '../application/factory_providers.dart';

class DeliveriesScreen extends ConsumerWidget {
  const DeliveriesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final scheduleAsync = ref.watch(scheduleProvider);
    final deliveriesAsync = ref.watch(deliveriesProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.deliveriesTitle),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/factory'),
        ),
        actions: [
          IconButton(
            tooltip: t.generateDeliveries,
            icon: const Icon(Icons.event_repeat),
            onPressed: () async {
              final n = await ref
                  .read(factoryRepositoryProvider)
                  .generateDeliveries();
              ref.invalidate(deliveriesProvider);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(t.generatedCount(n))),
                );
              }
            },
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add),
        label: Text(t.addOneOffDelivery),
        onPressed: () => _addOneOff(context, ref),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          scheduleAsync.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => Text(t.loadError),
            data: (schedule) => _ScheduleCard(
              weekdays: schedule.weekdays,
              timeOfDay: schedule.timeOfDay,
            ),
          ),
          const SizedBox(height: 16),
          Text(t.deliveriesTitle,
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          deliveriesAsync.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => Text(t.loadError),
            data: (deliveries) {
              if (deliveries.isEmpty) {
                return Padding(
                  padding: const EdgeInsets.all(24),
                  child: Center(child: Text(t.noOrdersYet)),
                );
              }
              final locale = Localizations.localeOf(context).languageCode;
              return Column(
                children: [
                  for (final d in deliveries)
                    Card(
                      child: ListTile(
                        leading: const Icon(Icons.local_shipping),
                        title: Text(
                          DateTimeFormat.dateTime(d.deliveryDatetime, locale),
                        ),
                        subtitle: Text(_statusLabel(t, d.status)),
                        trailing: TextButton(
                          onPressed: () =>
                              context.go('/factory/deliveries/${d.id}/summary'),
                          child: Text(t.viewSummary),
                        ),
                      ),
                    ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  String _statusLabel(AppLocalizations t, String status) => switch (status) {
        'locked' => t.statusLocked,
        'completed' => t.statusCompleted,
        _ => t.statusOpen,
      };

  Future<void> _addOneOff(BuildContext context, WidgetRef ref) async {
    final now = DateTime.now();
    final date = await showDatePicker(
      context: context,
      firstDate: now,
      lastDate: now.add(const Duration(days: 365)),
      initialDate: now.add(const Duration(days: 1)),
    );
    if (date == null || !context.mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: const TimeOfDay(hour: 8, minute: 0),
    );
    if (time == null) return;

    // Compose local datetime, send as UTC.
    final local = DateTime(
      date.year,
      date.month,
      date.day,
      time.hour,
      time.minute,
    );
    await ref.read(factoryRepositoryProvider).createDelivery(local.toUtc());
    ref.invalidate(deliveriesProvider);
  }
}

class _ScheduleCard extends ConsumerWidget {
  const _ScheduleCard({required this.weekdays, required this.timeOfDay});

  final List<int> weekdays;
  final String timeOfDay;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    // 0=Mon ... 6=Sun
    final labels = [
      t.weekdayMon,
      t.weekdayTue,
      t.weekdayWed,
      t.weekdayThu,
      t.weekdayFri,
      t.weekdaySat,
      t.weekdaySun,
    ];
    final selected = {...weekdays};

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(t.scheduleTitle,
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: [
                for (var i = 0; i < 7; i++)
                  FilterChip(
                    label: Text(labels[i]),
                    selected: selected.contains(i),
                    onSelected: (v) async {
                      final next = {...selected};
                      if (v) {
                        next.add(i);
                      } else {
                        next.remove(i);
                      }
                      if (next.isEmpty) return; // schedule needs >=1 day
                      await ref
                          .read(factoryRepositoryProvider)
                          .updateSchedule(next.toList()..sort(), timeOfDay);
                      ref.invalidate(scheduleProvider);
                    },
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Text('${t.timeLabel}: $timeOfDay'),
                const Spacer(),
                TextButton.icon(
                  icon: const Icon(Icons.schedule),
                  label: Text(timeOfDay),
                  onPressed: () async {
                    final parts = timeOfDay.split(':');
                    final picked = await showTimePicker(
                      context: context,
                      initialTime: TimeOfDay(
                        hour: int.tryParse(parts.first) ?? 8,
                        minute: int.tryParse(parts.last) ?? 0,
                      ),
                    );
                    if (picked == null) return;
                    final hh = picked.hour.toString().padLeft(2, '0');
                    final mm = picked.minute.toString().padLeft(2, '0');
                    await ref
                        .read(factoryRepositoryProvider)
                        .updateSchedule(weekdays, '$hh:$mm');
                    ref.invalidate(scheduleProvider);
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
