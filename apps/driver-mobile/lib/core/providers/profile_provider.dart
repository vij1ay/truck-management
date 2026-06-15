import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/profile/data/profile_repository.dart';
import '../../features/trucks/data/truck_photo_repository.dart';
import '../../shared/models/driver_profile.dart';
import '../../shared/models/shipment_document.dart';
import '../../shared/models/user_profile.dart';
import 'auth_provider.dart';

export '../../features/trucks/data/truck_photo_repository.dart' show TruckPhotoRef;

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepository(apiClient: ref.watch(apiClientProvider));
});

final truckPhotoRepositoryProvider = Provider<TruckPhotoRepository>((ref) {
  return TruckPhotoRepository(apiClient: ref.watch(apiClientProvider));
});

/// The logged-in user's profile (`GET /users/me`). Call `ref.invalidate
/// (currentUserProvider)` after updating the avatar/language to refresh.
final currentUserProvider = FutureProvider<UserProfile>((ref) async {
  return ref.watch(profileRepositoryProvider).getMe();
});

/// The logged-in user's Driver record + currently-assigned truck
/// (`GET /drivers/me`), or `null` if this account has no linked driver.
final driverMeProvider = FutureProvider<DriverProfile?>((ref) async {
  return ref.watch(profileRepositoryProvider).getDriverMe();
});

/// The logged-in user's profile picture bytes, or `null` if they have none set.
/// Depends on [currentUserProvider] so `ref.invalidate(currentUserProvider)`
/// after an upload/removal also refreshes this.
final avatarBytesProvider = FutureProvider<List<int>?>((ref) async {
  final user = await ref.watch(currentUserProvider.future);
  if (!user.hasAvatar) return null;
  return ref.watch(profileRepositoryProvider).getAvatarBytes(user.id);
});

/// A truck's photo gallery (`GET /trucks/{id}/photos`) — up to 6 entries.
final truckPhotosProvider = FutureProvider.family<List<TruckPhotoRef>, String>((ref, truckId) async {
  return ref.watch(truckPhotoRepositoryProvider).listPhotos(truckId);
});

/// Image bytes for a single gallery photo.
final truckPhotoBytesProvider =
    FutureProvider.family<List<int>, (String truckId, String photoId)>((ref, params) async {
  return ref.watch(truckPhotoRepositoryProvider).getPhotoBytes(params.$1, params.$2);
});

/// Documents for the truck currently assigned to this driver
/// (`GET /trucks/{id}/documents`).
final truckDocumentsProvider = FutureProvider.family<List<ShipmentDocument>, String>((ref, truckId) async {
  return ref.watch(profileRepositoryProvider).getTruckDocuments(truckId);
});

/// Documents for this driver's own `Driver` record (`GET /drivers/{id}/documents`).
final driverDocumentsProvider = FutureProvider.family<List<ShipmentDocument>, String>((ref, driverId) async {
  return ref.watch(profileRepositoryProvider).getDriverDocuments(driverId);
});
