import 'package:dio/dio.dart';

import 'token_storage.dart';

/// Backend API base URL.
///
/// - Android emulator: `10.0.2.2` reaches the host machine's `localhost`.
/// - iOS simulator / desktop: `localhost` works directly.
///
/// Override at build time with `--dart-define=API_BASE_URL=http://<host>:8000/api/v1`
/// when testing against a physical device on the same network as the backend.
const String _defaultBaseUrl = 'http://10.0.2.2:8000/api/v1';

const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: _defaultBaseUrl,
);

/// Shared Dio instance for all backend API calls.
///
/// - Attaches `Authorization: Bearer <accessToken>` to every request.
/// - On a 401 (except for the login/refresh endpoints themselves), attempts a
///   single token refresh via `POST /auth/refresh` and retries the original
///   request once; if the refresh also fails, the tokens are cleared and the
///   401 is rethrown so the UI can route back to `/login`.
class ApiClient {
  ApiClient({TokenStorage? tokenStorage})
      : _tokenStorage = tokenStorage ?? TokenStorage() {
    dio = Dio(
      BaseOptions(
        baseUrl: apiBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
      ),
    );
    // A separate, interceptor-free client for the refresh call itself —
    // avoids recursive 401 handling.
    _refreshDio = Dio(BaseOptions(baseUrl: apiBaseUrl));

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokenStorage.getAccessToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final isAuthEndpoint = error.requestOptions.path.contains('/auth/');
          if (error.response?.statusCode == 401 && !isAuthEndpoint) {
            try {
              final refreshed = await _refreshTokens();
              if (refreshed != null) {
                final retryOptions = error.requestOptions;
                retryOptions.headers['Authorization'] = 'Bearer $refreshed';
                final response = await dio.fetch(retryOptions);
                return handler.resolve(response);
              }
            } catch (_) {
              // fall through to clearing tokens below
            }
            await _tokenStorage.clear();
          }
          handler.next(error);
        },
      ),
    );
  }

  late final Dio dio;
  late final Dio _refreshDio;
  final TokenStorage _tokenStorage;

  /// Attempts a token refresh. Returns the new access token on success, or
  /// `null` if there's no refresh token / the refresh call fails.
  Future<String?> _refreshTokens() async {
    final refreshToken = await _tokenStorage.getRefreshToken();
    if (refreshToken == null) return null;

    final response = await _refreshDio.post(
      '/auth/refresh',
      data: {'refresh_token': refreshToken},
    );
    final accessToken = response.data['access_token'] as String;
    final newRefreshToken = response.data['refresh_token'] as String;
    await _tokenStorage.saveTokens(
      accessToken: accessToken,
      refreshToken: newRefreshToken,
    );
    return accessToken;
  }
}
