import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';

/// A single entry from `GET /trucks/{id}/photos` — `id` only; the image bytes
/// are fetched separately via [TruckPhotoRepository.getPhotoBytes].
class TruckPhotoRef {
  const TruckPhotoRef({required this.id, required this.position});

  factory TruckPhotoRef.fromJson(Map<String, dynamic> json) {
    return TruckPhotoRef(
      id: json['id'] as String,
      position: json['position'] as int,
    );
  }

  final String id;
  final int position;
}

/// Read-only access to a truck's photo gallery (up to 6 photos), for the
/// driver app's Vehicle Info screen.
class TruckPhotoRepository {
  TruckPhotoRepository({ApiClient? apiClient}) : _dio = (apiClient ?? ApiClient()).dio;

  final Dio _dio;

  Future<List<TruckPhotoRef>> listPhotos(String truckId) async {
    final response = await _dio.get('/trucks/$truckId/photos');
    final items = response.data as List<dynamic>;
    return items
        .map((e) => TruckPhotoRef.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<int>> getPhotoBytes(String truckId, String photoId) async {
    final response = await _dio.get<List<int>>(
      '/trucks/$truckId/photos/$photoId',
      options: Options(responseType: ResponseType.bytes),
    );
    return response.data!;
  }
}
