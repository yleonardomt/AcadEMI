import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/nav.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import '../../widgets/common.dart';
import '../auth/server_settings_sheet.dart';
import '../chatbot/chatbot_screen.dart';
import '../commerce/purchases_screen.dart';
import '../teacher/teacher_coupons_screen.dart';
import '../teacher/teacher_reviews_screen.dart';
import '../teacher/teacher_students_screen.dart';
import 'certificates_screen.dart';
import 'change_password_screen.dart';
import 'edit_profile_screen.dart';
import 'favorites_screen.dart';
import 'grades_screen.dart';
import 'progress_screen.dart';
import 'notifications_screen.dart';

class ProfileTab extends StatelessWidget {
  const ProfileTab({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final settings = context.watch<SettingsProvider>();
    final user = auth.user!;
    final p = context.palette;

    Widget group(String title, List<Widget> children) => Padding(
          padding: const EdgeInsets.fromLTRB(16, 18, 16, 0),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Padding(
              padding: const EdgeInsets.only(left: 6, bottom: 8),
              child: Text(title.toUpperCase(), style: TextStyle(color: p.inkMuted, fontSize: 12, fontWeight: FontWeight.w800, letterSpacing: 0.8)),
            ),
            Material(
              color: p.surface,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18), side: BorderSide(color: p.border)),
              clipBehavior: Clip.antiAlias,
              child: Column(children: [
                for (var i = 0; i < children.length; i++) ...[
                  if (i > 0) Divider(height: 1, indent: 62, color: p.border),
                  children[i],
                ],
              ]),
            ),
          ]),
        );

    Widget item(FaIconData icon, String label, VoidCallback onTap, {Color? color, String? trailing, int badge = 0}) => ListTile(
          onTap: onTap,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
          leading: Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(color: (color ?? p.primaryText).withValues(alpha: 0.13), borderRadius: BorderRadius.circular(11)),
            child: Center(child: FaIcon(icon, size: 16, color: color ?? p.primaryText)),
          ),
          title: Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
          trailing: badge > 0
              ? Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(color: AppColors.danger, borderRadius: BorderRadius.circular(10)),
                  child: Text('$badge', style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w800)),
                )
              : trailing != null
                  ? Text(trailing, style: TextStyle(color: p.inkMuted, fontSize: 13))
                  : FaIcon(FontAwesomeIcons.chevronRight, size: 12, color: p.inkMuted),
        );

    return Scaffold(
      body: ListView(padding: EdgeInsets.zero, children: [
        GradientHeader(
          padding: EdgeInsets.fromLTRB(20, MediaQuery.of(context).padding.top + 20, 20, 28),
          child: Column(children: [
            Stack(children: [
              Container(
                padding: const EdgeInsets.all(3),
                decoration: const BoxDecoration(color: AppColors.secondary, shape: BoxShape.circle),
                child: UserAvatar(name: user.name, url: user.picture, radius: 46),
              ),
              Positioned(
                right: 0,
                bottom: 0,
                child: InkWell(
                  onTap: () => push(context, const EditProfileScreen()),
                  child: Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(color: p.surface, shape: BoxShape.circle, border: Border.all(color: AppColors.primary, width: 2)),
                    child: Center(child: FaIcon(FontAwesomeIcons.pen, size: 12, color: p.primaryText)),
                  ),
                ),
              ),
            ]),
            const SizedBox(height: 14),
            Text(user.name, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
            const SizedBox(height: 2),
            Text(user.email, style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 13.5)),
            const SizedBox(height: 12),
            SoftTag(label: user.roleLabel, color: AppColors.secondary, icon: user.isTeacher ? FontAwesomeIcons.chalkboardUser : (user.isAdmin ? FontAwesomeIcons.userShield : FontAwesomeIcons.userGraduate)),
          ]),
        ),
        group('Mi cuenta', [
          item(FontAwesomeIcons.userPen, 'Editar perfil', () => push(context, const EditProfileScreen())),
          item(FontAwesomeIcons.key, 'Cambiar contraseña', () => push(context, const ChangePasswordScreen())),
          item(FontAwesomeIcons.bell, 'Notificaciones', () => push(context, const NotificationsScreen()), badge: auth.unreadNotifications),
        ]),
        if (user.isStudent)
          group('Mi aprendizaje', [
            item(FontAwesomeIcons.heart, 'Favoritos', () => push(context, const FavoritesScreen()), color: AppColors.danger),
            item(FontAwesomeIcons.certificate, 'Certificados', () => push(context, const CertificatesScreen()), color: AppColors.secondaryDark),
            item(FontAwesomeIcons.chartLine, 'Mi progreso', () => push(context, const ProgressScreen()), color: AppColors.primaryLight),
            item(FontAwesomeIcons.chartSimple, 'Calificaciones', () => push(context, const GradesScreen()), color: AppColors.teal),
            item(FontAwesomeIcons.receipt, 'Historial de compras', () => push(context, const PurchasesScreen()), color: AppColors.purple),
          ]),
        if (user.isTeacher)
          group('Mi docencia', [
            item(FontAwesomeIcons.userGroup, 'Mis estudiantes', () => push(context, const TeacherStudentsScreen()), color: AppColors.teal),
            item(FontAwesomeIcons.ticket, 'Mis cupones', () => push(context, const TeacherCouponsScreen()), color: AppColors.pink),
            item(FontAwesomeIcons.solidStar, 'Reseñas de mis cursos', () => push(context, const TeacherReviewsScreen()), color: AppColors.secondaryDark),
          ]),
        group('Ayuda', [
          item(FontAwesomeIcons.robot, 'Asistente virtual', () => push(context, const ChatbotScreen()), color: AppColors.info),
          item(FontAwesomeIcons.certificate, 'Verificar un certificado', () => push(context, const VerifyCertificateScreen()), color: AppColors.orange),
        ]),
        group('Apariencia y conexión', [
          item(
            FontAwesomeIcons.circleHalfStroke,
            'Tema',
            () => _pickTheme(context, settings),
            trailing: switch (settings.themeMode) {
              ThemeMode.light => 'Claro',
              ThemeMode.dark => 'Oscuro',
              _ => 'Sistema',
            },
          ),
          item(FontAwesomeIcons.server, 'Servidor', () => showServerSettings(context), trailing: Uri.tryParse(settings.serverUrl)?.host ?? ''),
        ]),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 22, 16, 0),
          child: OutlinedButton.icon(
            style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger, side: const BorderSide(color: AppColors.danger)),
            onPressed: () async {
              final ok = await confirmDialog(context, title: 'Cerrar sesión', message: '¿Seguro que quieres cerrar tu sesión?', confirmLabel: 'Cerrar sesión', danger: true);
              if (ok && context.mounted) context.read<AuthProvider>().logout();
            },
            icon: const FaIcon(FontAwesomeIcons.rightFromBracket, size: 16),
            label: const Text('Cerrar sesión'),
          ),
        ),
        const SizedBox(height: 12),
        Center(child: Text('AcadEMI móvil · v1.0.0', style: TextStyle(color: p.inkMuted, fontSize: 12))),
        const SizedBox(height: 30),
      ]),
    );
  }

  void _pickTheme(BuildContext context, SettingsProvider settings) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Padding(padding: EdgeInsets.all(8), child: Text('Tema de la app', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800))),
          for (final o in const [
            (ThemeMode.system, 'Igual que el sistema', FontAwesomeIcons.mobileScreen),
            (ThemeMode.light, 'Claro', FontAwesomeIcons.sun),
            (ThemeMode.dark, 'Oscuro', FontAwesomeIcons.moon),
          ])
            ListTile(
              leading: FaIcon(o.$3, size: 18),
              title: Text(o.$2, style: const TextStyle(fontWeight: FontWeight.w600)),
              trailing: settings.themeMode == o.$1 ? const FaIcon(FontAwesomeIcons.circleCheck, size: 18, color: AppColors.success) : null,
              onTap: () {
                settings.setThemeMode(o.$1);
                Navigator.pop(ctx);
              },
            ),
          const SizedBox(height: 8),
        ]),
      ),
    );
  }
}
