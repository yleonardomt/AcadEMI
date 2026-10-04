import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/nav.dart';
import '../../widgets/common.dart';
import '../../widgets/header_actions.dart';
import 'admin_categories_screen.dart';
import 'admin_certificates_screen.dart';
import 'admin_coupons_screen.dart';
import 'admin_courses_screen.dart';
import 'admin_payments_screen.dart';
import 'admin_report_generator_screen.dart';
import 'admin_reports_screen.dart';
import 'admin_users_screen.dart';

/// Punto de entrada a todo el módulo de administración (RF-43 a RF-49).
class AdminHubScreen extends StatelessWidget {
  const AdminHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final entries = <(FaIconData, String, String, Color, Widget)>[
      (FontAwesomeIcons.users, 'Usuarios', 'Crear, editar, roles y estado', AppColors.primaryLight, const AdminUsersScreen()),
      (FontAwesomeIcons.chalkboard, 'Cursos', 'Aprobar, rechazar y retirar', AppColors.orange, const AdminCoursesScreen()),
      (FontAwesomeIcons.tags, 'Categorías', 'Organiza el catálogo', AppColors.teal, const AdminCategoriesScreen()),
      (FontAwesomeIcons.flag, 'Reportados', 'Moderar contenido', AppColors.danger, const AdminReportsScreen()),
      (FontAwesomeIcons.ticket, 'Cupones', 'Promociones y descuentos', AppColors.pink, const AdminCouponsScreen()),
      (FontAwesomeIcons.coins, 'Compras', 'Ventas e ingresos', AppColors.success, const AdminPaymentsScreen()),
      (FontAwesomeIcons.certificate, 'Certificados', 'Emitidos y revocación', AppColors.secondaryDark, const AdminCertificatesScreen()),
      (FontAwesomeIcons.fileLines, 'Reportes', 'Genera resúmenes', AppColors.purple, const AdminReportGeneratorScreen()),
    ];
    return Scaffold(
      body: ListView(padding: EdgeInsets.zero, children: [
        GradientHeader(
          padding: EdgeInsets.fromLTRB(20, MediaQuery.of(context).padding.top + 8, 8, 26),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Row(children: [BrandLogo(light: true), Spacer(), HeaderActions(color: Colors.white)]),
            const SizedBox(height: 18),
            const Text('Administración', style: TextStyle(color: Colors.white, fontSize: 25, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
            const SizedBox(height: 4),
            Text('Gestiona usuarios, cursos, ventas y más', style: TextStyle(color: Colors.white.withValues(alpha: 0.82))),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.05,
            children: [
              for (final e in entries)
                InkWell(
                  borderRadius: BorderRadius.circular(18),
                  onTap: () => push(context, e.$5),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(18), border: Border.all(color: p.border), boxShadow: p.shadow),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Container(
                        width: 46,
                        height: 46,
                        decoration: BoxDecoration(color: e.$4.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(14)),
                        child: Center(child: FaIcon(e.$1, size: 19, color: e.$4)),
                      ),
                      const Spacer(),
                      Text(e.$2, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                      const SizedBox(height: 3),
                      Text(e.$3, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12.5, height: 1.3)),
                    ]),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 90),
      ]),
    );
  }
}
