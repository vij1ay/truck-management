import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers/auth_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/widgets/primary_button.dart';
import '../data/auth_repository.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _rememberMe = false;
  bool _signingIn = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _signIn() async {
    final l10n = AppLocalizations.of(context);
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    if (email.isEmpty || password.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.loginEnterCredentials)),
      );
      return;
    }

    setState(() => _signingIn = true);
    try {
      await ref.read(authStateProvider.notifier).login(email: email, password: password);
      if (mounted) context.go('/home');
    } on AuthException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
      }
    } finally {
      if (mounted) setState(() => _signingIn = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 24),
              const _Logo(),
              const SizedBox(height: 48),
              Text(l10n.loginWelcomeBack, style: theme.textTheme.headlineSmall),
              const SizedBox(height: 6),
              Text(l10n.loginSignInToContinue, style: theme.textTheme.bodyMedium),
              const SizedBox(height: 32),

              Text(l10n.loginEmailOrPhone, style: theme.textTheme.labelLarge),
              const SizedBox(height: 8),
              TextField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(
                  hintText: l10n.loginEmailHint,
                ),
              ),
              const SizedBox(height: 20),

              Text(l10n.loginPassword, style: theme.textTheme.labelLarge),
              const SizedBox(height: 8),
              TextField(
                controller: _passwordController,
                obscureText: _obscurePassword,
                decoration: InputDecoration(
                  hintText: l10n.loginPasswordHint,
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                    ),
                    onPressed: () =>
                        setState(() => _obscurePassword = !_obscurePassword),
                  ),
                ),
              ),
              const SizedBox(height: 12),

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      SizedBox(
                        height: 24,
                        width: 24,
                        child: Checkbox(
                          value: _rememberMe,
                          onChanged: (v) =>
                              setState(() => _rememberMe = v ?? false),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(l10n.loginRememberMe, style: theme.textTheme.bodyMedium),
                    ],
                  ),
                  TextButton(
                    onPressed: () {
                      // TODO: ties to mobile_app_design.md gap #10
                      // (forgot password has no mobile delivery channel yet).
                    },
                    child: Text(
                      l10n.loginForgotPassword,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              PrimaryButton(label: l10n.loginSignIn, onPressed: _signIn, loading: _signingIn),
              const SizedBox(height: 24),

              Row(
                children: [
                  Expanded(child: Divider(color: theme.dividerTheme.color)),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(l10n.loginOr, style: theme.textTheme.bodySmall),
                  ),
                  Expanded(child: Divider(color: theme.dividerTheme.color)),
                ],
              ),
              const SizedBox(height: 24),

              SecondaryButton(
                label: l10n.loginSignInWithOtp,
                icon: Icons.qr_code_scanner_outlined,
                onPressed: () {
                  // TODO: ties to mobile_app_design.md gap #8 (Phase 13 2FA).
                },
              ),
              const SizedBox(height: 40),

              Center(
                child: Text(l10n.loginVersion('1.0.0'), style: theme.textTheme.bodySmall),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Logo extends StatelessWidget {
  const _Logo();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(14),
          ),
          child: const Icon(
            Icons.local_shipping,
            color: AppColors.primary,
            size: 26,
          ),
        ),
        const SizedBox(width: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.appTitle,
              style: theme.textTheme.titleLarge?.copyWith(fontSize: 20),
            ),
            Text(l10n.loginTagline, style: theme.textTheme.bodySmall),
          ],
        ),
      ],
    );
  }
}
