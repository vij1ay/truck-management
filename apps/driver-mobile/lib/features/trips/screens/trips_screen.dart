import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/trip_provider.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/models/trip.dart';
import '../../../shared/widgets/refresh_wrapper.dart';
import '../../../shared/widgets/trip_card.dart';

class TripsScreen extends StatefulWidget {
  const TripsScreen({super.key});

  @override
  State<TripsScreen> createState() => _TripsScreenState();
}

class _TripsScreenState extends State<TripsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  static const _statuses = [
    TripStatus.assigned,
    TripStatus.active,
    TripStatus.completed,
    TripStatus.cancelled,
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _statuses.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final tabLabels = {
      TripStatus.assigned: l10n.statusAssigned,
      TripStatus.active: l10n.statusActive,
      TripStatus.completed: l10n.statusCompleted,
      TripStatus.cancelled: l10n.statusCancelled,
    };

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.tripsTitle),
        actions: [
          IconButton(icon: const Icon(Icons.search), onPressed: () {}),
          IconButton(icon: const Icon(Icons.tune), onPressed: () {}),
          const SizedBox(width: 8),
        ],
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: [for (final status in _statuses) Tab(text: tabLabels[status])],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          for (final status in _statuses)
            _TripList(status: status, statusLabel: tabLabels[status]!),
        ],
      ),
    );
  }
}

class _TripList extends ConsumerWidget {
  const _TripList({required this.status, required this.statusLabel});

  final TripStatus status;
  final String statusLabel;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final tripsAsync = ref.watch(tripsProvider);

    return RefreshWrapper(
      onRefresh: () async => ref.invalidate(tripsProvider),
      child: tripsAsync.when(
        data: (allTrips) {
          final trips = allTrips.where((t) => t.status == status).toList();

          if (trips.isEmpty) {
            final emptyMessages = {
              TripStatus.assigned: l10n.tripsNoAssigned,
              TripStatus.active: l10n.tripsNoActive,
              TripStatus.completed: l10n.tripsNoCompleted,
              TripStatus.cancelled: l10n.tripsNoCancelled,
            };
            return _CenteredMessage(message: emptyMessages[status]!);
          }

          return ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: trips.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final trip = trips[index];
              return TripCard(
                trip: trip,
                statusLabel: statusLabel,
                onTap: () => context.go('/trips/${trip.id}'),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, __) => _CenteredMessage(message: l10n.tripsLoadError),
      ),
    );
  }
}

class _CenteredMessage extends StatelessWidget {
  const _CenteredMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          SizedBox(
            height: constraints.maxHeight,
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  message,
                  style: Theme.of(context).textTheme.bodyMedium,
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
