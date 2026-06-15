/// Subset of `UserResponse` (GET /users/me) needed by the driver app —
/// identity, profile picture flag, and the preferred-language setting.
class UserProfile {
  const UserProfile({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.hasAvatar,
    this.preferredLanguage,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as String,
      email: json['email'] as String,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      hasAvatar: json['has_avatar'] as bool? ?? false,
      preferredLanguage: json['preferred_language'] as String?,
    );
  }

  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final bool hasAvatar;
  final String? preferredLanguage;

  String get fullName => '$firstName $lastName';

  UserProfile copyWith({bool? hasAvatar, String? preferredLanguage}) {
    return UserProfile(
      id: id,
      email: email,
      firstName: firstName,
      lastName: lastName,
      hasAvatar: hasAvatar ?? this.hasAvatar,
      preferredLanguage: preferredLanguage ?? this.preferredLanguage,
    );
  }
}
