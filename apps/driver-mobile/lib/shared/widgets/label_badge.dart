import 'package:flutter/material.dart';

/// A small colored pill showing an arbitrary [label] in [color] — the
/// generic version of `status_badge.dart`'s `StatusBadge` (which is tied to
/// the driver app's [TripStatus] enum). Used for shipment/invoice statuses in
/// the Client portal screens.
class LabelBadge extends StatelessWidget {
  const LabelBadge({super.key, required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: color,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
