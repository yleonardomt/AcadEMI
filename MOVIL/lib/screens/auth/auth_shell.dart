import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/nav.dart';
import 'server_settings_sheet.dart';

/// Marco común de login/registro/recuperación: cabecera con degradado de
/// marca y una tarjeta con el formulario encima.
class AuthShell extends StatelessWidget {
  const AuthShell({
    super.key,
    required this.title,
    required this.subtitle,
    required this.child,
    this.showBack = false,
    this.icon = FontAwesomeIcons.graduationCap,
  });

  final String title, subtitle;
  final Widget child;
  final bool showBack;
  final FaIconData icon;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Scaffold(
      backgroundColor: p.background,
      body: GestureDetector(
        onTap: () => FocusScope.of(context).unfocus(),
        child: SingleChildScrollView(
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Container(
              decoration: const BoxDecoration(
                gradient: AppColors.heroGradient,
                borderRadius: BorderRadius.vertical(bottom: Radius.circular(36)),
              ),
              child: SafeArea(
                bottom: false,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(12, 6, 12, 44),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      if (showBack)
                        IconButton(
                          onPressed: () => Navigator.of(context).maybePop(),
                          icon: const FaIcon(FontAwesomeIcons.arrowLeft, size: 18, color: Colors.white),
                        )
                      else
                        const SizedBox(width: 12),
                      const Spacer(),
                      IconButton(
                        tooltip: 'Servidor',
                        onPressed: () => showServerSettings(context),
                        icon: FaIcon(FontAwesomeIcons.gear, size: 17, color: Colors.white.withValues(alpha: 0.85)),
                      ),
                    ]),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Container(
                          width: 58,
                          height: 58,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.14),
                            borderRadius: BorderRadius.circular(18),
                          ),
                          child: Center(child: FaIcon(icon, size: 26, color: AppColors.secondary)),
                        ),
                        const SizedBox(height: 18),
                        Text(title,
                            style: const TextStyle(
                                color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800, letterSpacing: -0.6)),
                        const SizedBox(height: 6),
                        Text(subtitle,
                            style: TextStyle(color: Colors.white.withValues(alpha: 0.82), fontSize: 15, height: 1.4)),
                      ]),
                    ),
                  ]),
                ),
              ),
            ),
            // La tarjeta sube sobre la cabecera (los hijos posteriores se pintan encima).
            Transform.translate(
              offset: const Offset(0, -24),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: p.surface,
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: p.border),
                    boxShadow: [
                      BoxShadow(color: AppColors.primary.withValues(alpha: 0.10), blurRadius: 30, offset: const Offset(0, 12)),
                    ],
                  ),
                  child: Material(type: MaterialType.transparency, child: child),
                ),
              ),
            ),
            Transform.translate(
              offset: const Offset(0, -8),
              child: Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: SafeArea(
                  top: false,
                  child: Text('© AcadEMI · Escuela Militar de Ingeniería',
                      textAlign: TextAlign.center, style: TextStyle(color: p.inkMuted, fontSize: 12)),
                ),
              ),
            ),
          ]),
        ),
      ),
    );
  }
}

/// Navega a una pantalla de autenticación.
void goAuth(BuildContext context, Widget page) => push(context, page);
