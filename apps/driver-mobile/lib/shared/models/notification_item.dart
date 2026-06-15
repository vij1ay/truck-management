enum NotificationType { newTrip, reminder, documentExpiry, completed, system, tripCancelled }

class NotificationItem {
  const NotificationItem({
    required this.id,
    required this.type,
    required this.title,
    required this.message,
    required this.time,
    required this.group,
    this.read = false,
  });

  final String id;
  final NotificationType type;
  final String title;
  final String message;
  final String time;

  /// "Today" / "Yesterday" / "Older" — used to group the list.
  final String group;
  final bool read;
}
