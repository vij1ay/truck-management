import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../shared/models/client_profile.dart';
import '../../../shared/models/portal_invoice.dart';
import '../../../shared/models/shipment.dart';
import '../../../shared/models/shipment_document.dart';
import '../../../shared/models/shipment_history_entry.dart';

/// Wraps the Client Portal endpoints (`/portal/*`,
/// `apps/backend/app/api/v1/portal.py`) — role `Client` only, scoped to the
/// logged-in user's linked `Client` rows across every carrier (tenant).
class PortalRepository {
  PortalRepository({ApiClient? apiClient}) : _dio = (apiClient ?? ApiClient()).dio;

  final Dio _dio;

  /// Every carrier (tenant) relationship linked to this account.
  Future<List<PortalCarrierLink>> getMyProfile() async {
    final response = await _dio.get('/portal/me');
    final carriers = (response.data as Map<String, dynamic>)['carriers'] as List<dynamic>;
    return carriers.map((e) => PortalCarrierLink.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// My Shipments, optionally filtered by [status] (`LoadStatus` wire value).
  Future<List<Shipment>> getMyShipments({String? status}) async {
    final response = await _dio.get('/portal/loads', queryParameters: {
      'size': 100,
      if (status != null) 'status': status,
    });
    final items = (response.data as Map<String, dynamic>)['items'] as List<dynamic>;
    return items.map((e) => Shipment.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Shipment> getShipment(String id) async {
    final response = await _dio.get('/portal/loads/$id');
    return Shipment.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<ShipmentHistoryEntry>> getShipmentHistory(String id) async {
    final response = await _dio.get('/portal/loads/$id/history');
    final items = response.data as List<dynamic>;
    return items.map((e) => ShipmentHistoryEntry.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<ShipmentDocument>> getShipmentDocuments(String id) async {
    final response = await _dio.get('/portal/loads/$id/documents');
    final items = (response.data as Map<String, dynamic>)['items'] as List<dynamic>;
    return items.map((e) => ShipmentDocument.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Attach a photo to a shipment (`POST /portal/loads/{id}/documents`,
  /// multipart, image-only — see `app/core/avatar_storage.py`).
  Future<ShipmentDocument> uploadShipmentDocument(String loadId, String filePath) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath, filename: 'document.jpg'),
    });
    final response = await _dio.post('/portal/loads/$loadId/documents', data: formData);
    return ShipmentDocument.fromJson(response.data as Map<String, dynamic>);
  }

  /// Image bytes for a shipment document
  /// (`GET /portal/loads/{id}/documents/{documentId}/file`).
  Future<List<int>> getShipmentDocumentBytes(String loadId, String documentId) async {
    final response = await _dio.get<List<int>>(
      '/portal/loads/$loadId/documents/$documentId/file',
      options: Options(responseType: ResponseType.bytes),
    );
    return response.data!;
  }

  /// Submit a new booking request — `payload` mirrors `PortalLoadCreate`
  /// (`app/schemas/portal.py`): `tenant_id`, `origin`, `destination`,
  /// `pickup_date`, `goods_type`, plus optional fields.
  Future<Shipment> createShipment(Map<String, dynamic> payload) async {
    final response = await _dio.post('/portal/loads', data: payload);
    return Shipment.fromJson(response.data as Map<String, dynamic>);
  }

  /// Edit a DRAFT/CONFIRMED booking — `payload` mirrors `LoadUpdate`
  /// (`app/schemas/load.py`), e.g. `origin`/`destination`/`pickup_date`/etc.
  /// (no `tenant_id` — the carrier can't change).
  Future<Shipment> updateShipment(String id, Map<String, dynamic> payload) async {
    final response = await _dio.patch('/portal/loads/$id', data: payload);
    return Shipment.fromJson(response.data as Map<String, dynamic>);
  }

  /// Cancel a booking with a mandatory [reason] (>= 5 chars, enforced by
  /// `LoadCancelRequest`). 403 if the shipment is IN_TRANSIT.
  Future<Shipment> cancelShipment(String id, String reason) async {
    final response = await _dio.post('/portal/loads/$id/cancel', data: {'reason': reason});
    return Shipment.fromJson(response.data as Map<String, dynamic>);
  }

  /// My Invoices, optionally filtered by [status] (`InvoiceStatus` wire value).
  Future<List<PortalInvoice>> getMyInvoices({String? status}) async {
    final response = await _dio.get('/portal/invoices', queryParameters: {
      'size': 100,
      if (status != null) 'status': status,
    });
    final items = (response.data as Map<String, dynamic>)['items'] as List<dynamic>;
    return items.map((e) => PortalInvoice.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Raw PDF bytes for an invoice (`GET /portal/invoices/{id}/pdf`).
  Future<List<int>> downloadInvoicePdf(String id) async {
    final response = await _dio.get<List<int>>(
      '/portal/invoices/$id/pdf',
      options: Options(responseType: ResponseType.bytes),
    );
    return response.data!;
  }
}
