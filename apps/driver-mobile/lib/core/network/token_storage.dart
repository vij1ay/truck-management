import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Persists the JWT access/refresh tokens issued by `POST /auth/login`
/// (and rotated by `POST /auth/refresh`) in the platform secure storage
/// (Keychain on iOS, Keystore-backed EncryptedSharedPreferences on Android).
class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';

  final FlutterSecureStorage _storage;

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
  }

  Future<String?> getAccessToken() => _read(_accessTokenKey);

  Future<String?> getRefreshToken() => _read(_refreshTokenKey);

  Future<void> clear() async {
    try {
      await _storage.delete(key: _accessTokenKey);
      await _storage.delete(key: _refreshTokenKey);
    } catch (_) {
      // No secure storage available (e.g. widget tests with no platform
      // channel) — nothing to clear.
    }
  }

  Future<bool> hasSession() async => (await getAccessToken()) != null;

  /// Reads a key, treating "secure storage unavailable" (e.g. the platform
  /// channel isn't mocked in widget tests) the same as "not set" rather than
  /// throwing — callers (notably the router's `redirect`) should never crash
  /// because of this.
  Future<String?> _read(String key) async {
    try {
      return await _storage.read(key: key);
    } catch (_) {
      return null;
    }
  }
}
