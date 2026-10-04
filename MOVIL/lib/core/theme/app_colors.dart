import 'package:flutter/material.dart';

/// Paleta de marca de AcadEMI. Los valores salen de `static/css/base.css`
/// del sitio web (única fuente de verdad de colores): primario #02167f,
/// acento #ffd014 y los colores de estado/acento.
class AppColors {
  AppColors._();

  // Marca
  static const primary = Color(0xFF02167F);
  static const primaryDark = Color(0xFF010E53);
  static const primaryLight = Color(0xFF2F3FAE);
  static const primaryLighter = Color(0xFFE8EAF6);
  static const primaryVivid = Color(0xFF3F57D6);

  static const secondary = Color(0xFFFFD014);
  static const secondaryDark = Color(0xFFE0AC00);
  static const secondaryLight = Color(0xFFFFE985);

  // Estado
  static const dark = Color(0xFF1A202C);

  static const success = Color(0xFF10B981);
  static const danger = Color(0xFFEF4444);
  static const warning = Color(0xFFF59E0B);
  static const info = Color(0xFF3B82F6);

  // Acentos (etiquetas, niveles, íconos de estadísticas)
  static const teal = Color(0xFF0D9488);
  static const tealLight = Color(0xFFCCFBF1);
  static const purple = Color(0xFF7C3AED);
  static const purpleLight = Color(0xFFEDE9FE);
  static const pink = Color(0xFFDB2777);
  static const pinkLight = Color(0xFFFCE7F3);
  static const orange = Color(0xFFEA580C);
  static const orangeLight = Color(0xFFFFEDD5);

  static const primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [primary, primaryLight],
  );

  /// Degradado de 3 tramos de las cabeceras de dashboard/portada.
  static const heroGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [primaryDark, primary, primaryVivid],
  );

  static const accentGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [secondary, Color(0xFFF5A800)],
  );
}

/// Tokens que cambian entre modo claro y oscuro (equivalen a los tokens
/// "conscientes del tema" de base.css: --surface, --ink, --primary-text...).
class Palette {
  const Palette({
    required this.background,
    required this.surface,
    required this.surfaceSoft,
    required this.border,
    required this.ink,
    required this.inkMuted,
    required this.primaryText,
    required this.isDark,
  });

  final Color background;
  final Color surface;
  final Color surfaceSoft;
  final Color border;
  final Color ink;
  final Color inkMuted;
  final Color primaryText;
  final bool isDark;

  /// Sombra suave azulada de las tarjetas (--shadow del sitio); en oscuro no lleva.
  List<BoxShadow> get shadow => isDark
      ? const []
      : [BoxShadow(color: AppColors.primary.withValues(alpha: 0.08), blurRadius: 20, offset: const Offset(0, 4))];

  static const light = Palette(
    background: Colors.white, // igual que el sitio: body #ffffff
    surface: Colors.white,
    surfaceSoft: Color(0xFFF5F7FA),
    border: Color(0xFFE2E8F0),
    ink: Color(0xFF1A202C),
    inkMuted: Color(0xFF718096),
    primaryText: AppColors.primary,
    isDark: false,
  );

  static const dark = Palette(
    background: Color(0xFF0F172A),
    surface: Color(0xFF1E293B),
    surfaceSoft: Color(0xFF16213A),
    border: Color(0xFF33415C),
    ink: Color(0xFFE8EDF5),
    inkMuted: Color(0xFF94A3B8),
    primaryText: Color(0xFF7DB8FF),
    isDark: true,
  );
}

extension PaletteContext on BuildContext {
  Palette get palette => Theme.of(this).brightness == Brightness.dark ? Palette.dark : Palette.light;
}
