import 'package:flutter/material.dart';

/// Central palette for the TransTrack driver app.
///
/// Both a dark theme (default for the operational screens — dashboard, trips,
/// map, trip details, proof of delivery) and a light theme (profile, vehicle
/// info, documents, notifications) are supported app-wide via [ThemeMode] —
/// every screen renders correctly in either, the split in the original
/// reference mockup was illustrative, not a per-screen restriction.
class AppColors {
  AppColors._();

  /// Brand orange — primary actions, active nav state, highlights.
  static const Color primary = Color(0xFFF5A623);
  static const Color primaryDark = Color(0xFFD98C12);

  // ── Status colors (shared by both themes) ──────────────────────────────────
  static const Color statusAssigned = Color(0xFF3B82F6); // blue
  static const Color statusActive = Color(0xFF22C55E); // green
  static const Color statusPending = Color(0xFFF59E0B); // amber
  static const Color statusCompleted = Color(0xFF22C55E); // green
  static const Color statusCancelled = Color(0xFFEF4444); // red
  static const Color statusInTransit = Color(0xFF22C55E); // green
  static const Color statusDraft = Color(0xFF94A3B8); // grey — load/invoice "draft"

  // ── Dark theme ──────────────────────────────────────────────────────────────
  static const Color darkBackground = Color(0xFF0B1220);
  static const Color darkSurface = Color(0xFF161D2E);
  static const Color darkSurfaceAlt = Color(0xFF1E2740);
  static const Color darkBorder = Color(0xFF26304A);
  static const Color darkTextPrimary = Color(0xFFF5F7FA);
  static const Color darkTextSecondary = Color(0xFF94A3B8);

  // ── Light theme ─────────────────────────────────────────────────────────────
  static const Color lightBackground = Color(0xFFF4F6F9);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightSurfaceAlt = Color(0xFFF0F2F6);
  static const Color lightBorder = Color(0xFFE6E9EF);
  static const Color lightTextPrimary = Color(0xFF11151D);
  static const Color lightTextSecondary = Color(0xFF6B7785);
}
