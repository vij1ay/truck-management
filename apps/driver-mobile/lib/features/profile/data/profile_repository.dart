import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../shared/models/driver_profile.dart';
import '../../../shared/models/shipment_document.dart';
import '../../../shared/models/user_profile.dart';

/// Wraps the profile-related endpoints used by the mobile app:
/// - `GET /users/me`, `PATCH /users/{id}` (preferred_language)
/// - `POST/DELETE/GET /users/{id}/avatar` (profile picture — self-service)
/// - `GET /drivers/me` (license/vehicle info)
/// - `GET /trucks/{id}/documents`, `GET /drivers/{id}/documents` (Documents tab)
/// - `PATCH /drivers/{id}/location` (GPS location polling)
class ProfileRepository {
  ProfileRepository({ApiClient? apiClient}) : _dio = (apiClient ?? ApiClient()).dio;

  final Dio _dio;

  Future<UserProfile> getMe() async {
    final response = await _dio.get('/users/me');
    return UserProfile.fromJson(response.data as Map<String, dynamic>);
  }

  /// Returns null if this account has no linked Driver record (404).
  Future<DriverProfile?> getDriverMe() async {
    try {
      final response = await _dio.get('/drivers/me');
      return DriverProfile.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }

  Future<void> updatePreferredLanguage(String userId, String languageCode) async {
    await _dio.patch(
      '/users/$userId',
      data: {'preferred_language': languageCode},
    );
  }

  /// Returns the avatar image bytes, or null if the user has no avatar (404).
  Future<List<int>?> getAvatarBytes(String userId) async {
    try {
      final response = await _dio.get<List<int>>(
        '/users/$userId/avatar',
        options: Options(responseType: ResponseType.bytes),
      );
      return response.data;
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }

  Future<void> uploadAvatar(String userId, String filePath) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath, filename: 'avatar.jpg'),
    });
    await _dio.post('/users/$userId/avatar', data: formData);
  }

  Future<void> removeAvatar(String userId) async {
    await _dio.delete('/users/$userId/avatar');
  }

  /// Documents for the truck currently assigned to this driver
  /// (`GET /trucks/{id}/documents` — Driver-permitted for their own truck).
  Future<List<ShipmentDocument>> getTruckDocuments(String truckId) async {
    final response = await _dio.get('/trucks/$truckId/documents');
    final items = (response.data as Map<String, dynamic>)['items'] as List<dynamic>;
    return items.map((e) => ShipmentDocument.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Documents for this driver's own `Driver` record
  /// (`GET /drivers/{id}/documents` — Driver-permitted for themselves).
  Future<List<ShipmentDocument>> getDriverDocuments(String driverId) async {
    final response = await _dio.get('/drivers/$driverId/documents');
    final items = (response.data as Map<String, dynamic>)['items'] as List<dynamic>;
    return items.map((e) => ShipmentDocument.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Reports the driver's current GPS position (`PATCH /drivers/{id}/location`,
  /// Driver-permitted for themselves).
  Future<void> updateLocation(String driverId, double lat, double lon) async {
    await _dio.patch('/drivers/$driverId/location', data: {
      'current_lat': lat,
      'current_lon': lon,
    });
  }
}
