import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_colors.dart';

/// Inter-based [TextTheme] — the closest free, cross-platform match to SF Pro
/// (clean, geometric, highly legible on both Android and iOS).
class AppTextTheme {
  AppTextTheme._();

  static TextTheme build(Color primaryText, Color secondaryText) {
    final base = GoogleFonts.interTextTheme();

    return base.copyWith(
      // Greeting / large headings, e.g. "Good Morning, Peter Williamson"
      headlineSmall: GoogleFonts.inter(
        fontSize: 22,
        fontWeight: FontWeight.w700,
        color: primaryText,
        height: 1.25,
      ),
      // Section titles, e.g. "Today's Summary", "My Trips"
      titleLarge: GoogleFonts.inter(
        fontSize: 18,
        fontWeight: FontWeight.w700,
        color: primaryText,
      ),
      // Card titles, e.g. "Chemical Delivery"
      titleMedium: GoogleFonts.inter(
        fontSize: 15,
        fontWeight: FontWeight.w600,
        color: primaryText,
      ),
      titleSmall: GoogleFonts.inter(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: primaryText,
      ),
      // Body copy
      bodyLarge: GoogleFonts.inter(
        fontSize: 15,
        fontWeight: FontWeight.w400,
        color: primaryText,
      ),
      bodyMedium: GoogleFonts.inter(
        fontSize: 13,
        fontWeight: FontWeight.w400,
        color: secondaryText,
      ),
      bodySmall: GoogleFonts.inter(
        fontSize: 12,
        fontWeight: FontWeight.w400,
        color: secondaryText,
      ),
      // Labels / buttons / badges
      labelLarge: GoogleFonts.inter(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: primaryText,
      ),
      labelMedium: GoogleFonts.inter(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        color: secondaryText,
      ),
      labelSmall: GoogleFonts.inter(
        fontSize: 11,
        fontWeight: FontWeight.w600,
        color: secondaryText,
        letterSpacing: 0.4,
      ),
    );
  }

  static TextTheme dark() =>
      build(AppColors.darkTextPrimary, AppColors.darkTextSecondary);

  static TextTheme light() =>
      build(AppColors.lightTextPrimary, AppColors.lightTextSecondary);
}
