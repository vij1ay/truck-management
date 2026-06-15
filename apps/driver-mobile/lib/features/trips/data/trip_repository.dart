import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../shared/models/shipment_document.dart';
import '../../../shared/models/shipment_history_entry.dart';
import '../../../shared/models/trip.dart';

/// Wraps the Driver-facing `/loads/*` endpoints
/// (`apps/backend/app/api/v1/loads.py`) — `GET /loads` is auto-scoped
/// server-side to the loads allocated to the calling Driver
/// (`LoadService.get_loads`, `app/services/load_service.py:107-114`).
class TripRepository {
  TripRepository({ApiClient? apiClient}) : _dio = (apiClient ?? ApiClient()).dio;

  final Dio _dio;

  /// My Trips, optionally filtered by `LoadStatus` wire value.
  Future<List<Trip>> getMyTrips({String? status}) async {
    final response = await _dio.get('/loads', queryParameters: {
      'size': 100,
      if (status != null) 'status': status,
    });
    final items = (response.data as Map<String, dynamic>)['items'] as List<dynamic>;
    return items.map((e) => Trip.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Trip> getTrip(String id) async {
    final response = await _dio.get('/loads/$id');
    return Trip.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<ShipmentHistoryEntry>> getTripHistory(String id) async {
    final response = await _dio.get('/loads/$id/history');
    final items = response.data as List<dynamic>;
    return items.map((e) => ShipmentHistoryEntry.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<ShipmentDocument>> getTripDocuments(String id) async {
    final response = await _dio.get('/loads/$id/documents');
    final items = (response.data as Map<String, dynamic>)['items'] as List<dynamic>;
    return items.map((e) => ShipmentDocument.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<int>> getTripDocumentBytes(String id, String documentId) async {
    final response = await _dio.get<List<int>>(
      '/loads/$id/documents/$documentId/file',
      options: Options(responseType: ResponseType.bytes),
    );
    return response.data!;
  }

  /// ALLOCATED -> IN_TRANSIT.
  Future<Trip> startTrip(String id) async {
    final response = await _dio.post('/loads/$id/start-trip');
    return Trip.fromJson(response.data as Map<String, dynamic>);
  }

  /// Record an informational checkpoint (e.g. "Reached Pickup") without
  /// changing status.
  Future<Trip> addCheckpoint(String id, String label) async {
    final response = await _dio.post('/loads/$id/checkpoints', data: {'label': label});
    return Trip.fromJson(response.data as Map<String, dynamic>);
  }

  /// Upload a Proof-of-Delivery photo.
  Future<ShipmentDocument> uploadPodPhoto(String id, String filePath) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath, filename: 'pod.jpg'),
    });
    final response = await _dio.post('/loads/$id/documents/pod', data: formData);
    return ShipmentDocument.fromJson(response.data as Map<String, dynamic>);
  }

  /// IN_TRANSIT -> DELIVERED.
  Future<Trip> deliverTrip(String id) async {
    final response = await _dio.post('/loads/$id/deliver');
    return Trip.fromJson(response.data as Map<String, dynamic>);
  }
}
