import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/data/auth_repository.dart';
import '../network/api_client.dart';
import '../network/token_storage.dart';

/// Shared [ApiClient] — one Dio instance (with the auth interceptor) for the
/// whole app.
final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    apiClient: ref.watch(apiClientProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  );
});

/// Whether the app currently holds a session (access token present).
///
/// `null` while the initial check is in progress (splash/login screen should
/// treat this as "not yet known"), then `true`/`false`.
class AuthStateNotifier extends AsyncNotifier<bool> {
  @override
  Future<bool> build() async {
    return ref.read(authRepositoryProvider).hasSession();
  }

  Future<void> login({required String email, required String password}) async {
    await ref.read(authRepositoryProvider).login(email: email, password: password);
    state = const AsyncData(true);
  }

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    state = const AsyncData(false);
  }
}

final authStateProvider = AsyncNotifierProvider<AuthStateNotifier, bool>(
  AuthStateNotifier.new,
);
