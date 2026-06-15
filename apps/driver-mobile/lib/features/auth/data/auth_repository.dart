import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/token_storage.dart';

/// Thrown when login fails (invalid credentials, locked account, etc.) — the
/// [message] is suitable for direct display in a snackbar.
class AuthException implements Exception {
  AuthException(this.message);
  final String message;

  @override
  String toString() => message;
}

/// Wraps `POST /auth/login` and `POST /auth/logout` (best-effort), persisting
/// tokens via [TokenStorage].
class AuthRepository {
  AuthRepository({ApiClient? apiClient, TokenStorage? tokenStorage})
      : _apiClient = apiClient ?? ApiClient(),
        _tokenStorage = tokenStorage ?? TokenStorage();

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;

  /// Logs in and persists the returned access/refresh tokens.
  Future<void> login({required String email, required String password}) async {
    try {
      final response = await _apiClient.dio.post(
        '/auth/login',
        data: {'email': email, 'password': password},
      );
      final data = response.data as Map<String, dynamic>;
      await _tokenStorage.saveTokens(
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      );
    } on DioException catch (e) {
      throw AuthException(_messageFor(e));
    }
  }

  Future<void> logout() async {
    await _tokenStorage.clear();
  }

  Future<bool> hasSession() => _tokenStorage.hasSession();

  String _messageFor(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['message'] is String) {
      return data['message'] as String;
    }
    switch (e.response?.statusCode) {
      case 401:
        return 'Incorrect email or password.';
      case 423:
        return 'Account locked due to too many failed attempts. Try again later.';
      default:
        return 'Unable to sign in. Please check your connection and try again.';
    }
  }
}
