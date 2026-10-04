import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../core/utils/nav.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../../widgets/header_actions.dart';
import '../catalog/course_detail_screen.dart';
import 'teacher_questions_screen.dart';
import 'teacher_reviews_screen.dart';
import 'teacher_students_screen.dart';

/// Panel del docente (y resumen global para el administrador).
class TeacherDashboardTab extends StatelessWidget {
  const TeacherDashboardTab({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthProvider>();
    final user = auth.user!;
    final p = context.palette;

    return Scaffold(
      body: AsyncBody<Map<String, dynamic>>(
        load: auth.api.teacherDashboard,
        builder: (context, d, reload) {
          final admin = d['admin'] as Map<String, dynamic>?;
          String n(String k) => '${asInt(d[k])}';
          final recent = asList(d['recent_courses']);

          return ListView(padding: EdgeInsets.zero, children: [
            GradientHeader(
              padding: EdgeInsets.fromLTRB(20, MediaQuery.of(context).padding.top + 8, 8, 26),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Row(children: [BrandLogo(light: true), Spacer(), HeaderActions(color: Colors.white)]),
                const SizedBox(height: 18),
                Text(user.isAdmin ? 'Panel de administración' : 'Hola, ${Fmt.firstName(user.name)}',
                    style: const TextStyle(color: Colors.white, fontSize: 25, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
                const SizedBox(height: 4),
                Text(user.isAdmin ? 'Resumen general de la plataforma' : 'Así van tus cursos y estudiantes', style: TextStyle(color: Colors.white.withValues(alpha: 0.82))),
              ]),
            ),
            if (admin != null) ...[
              const SectionHeader(title: 'Plataforma'),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 2.15,
                  children: [
                    StatTile(icon: FontAwesomeIcons.users, value: '${asInt(admin['users'])}', label: 'Usuarios', color: AppColors.primaryLight),
                    StatTile(icon: FontAwesomeIcons.userGraduate, value: '${asInt(admin['students'])}', label: 'Estudiantes', color: AppColors.teal),
                    StatTile(icon: FontAwesomeIcons.chalkboardUser, value: '${asInt(admin['teachers'])}', label: 'Docentes', color: AppColors.purple),
                    StatTile(icon: FontAwesomeIcons.hourglassHalf, value: '${asInt(admin['courses_pending_approval'])}', label: 'Por aprobar', color: AppColors.warning),
                    StatTile(icon: FontAwesomeIcons.coins, value: Fmt.amount(asDouble(admin['revenue'])), label: 'Ingresos', color: AppColors.success),
                    StatTile(icon: FontAwesomeIcons.calendarDay, value: Fmt.amount(asDouble(admin['monthly_revenue'])), label: 'Este mes', color: AppColors.orange),
                    StatTile(icon: FontAwesomeIcons.receipt, value: '${asInt(admin['payments'])}', label: 'Pagos', color: AppColors.pink),
                    StatTile(icon: FontAwesomeIcons.flag, value: '${asInt(admin['open_reports'])}', label: 'Reportes', color: AppColors.danger),
                  ],
                ),
              ),
            ],
            SectionHeader(title: user.isAdmin ? 'Cursos' : 'Mis cursos'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 2.15,
                children: [
                  StatTile(icon: FontAwesomeIcons.chalkboard, value: n('courses'), label: 'Cursos', color: AppColors.primaryLight),
                  StatTile(icon: FontAwesomeIcons.circleCheck, value: n('published'), label: 'Publicados', color: AppColors.success),
                  StatTile(icon: FontAwesomeIcons.pencil, value: n('drafts'), label: 'Borradores', color: AppColors.info),
                  StatTile(icon: FontAwesomeIcons.hourglassHalf, value: n('pending'), label: 'En revisión', color: AppColors.warning),
                ],
              ),
            ),
            const SectionHeader(title: 'Estudiantes y actividad'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 2.15,
                children: [
                  StatTile(icon: FontAwesomeIcons.userGroup, value: n('students'), label: 'Estudiantes', color: AppColors.teal),
                  StatTile(icon: FontAwesomeIcons.bolt, value: n('active_students'), label: 'Activos', color: AppColors.orange),
                  StatTile(icon: FontAwesomeIcons.graduationCap, value: n('completed_students'), label: 'Completaron', color: AppColors.purple),
                  StatTile(icon: FontAwesomeIcons.solidStar, value: asDouble(d['rating']).toStringAsFixed(1), label: '${n('reviews')} reseñas', color: AppColors.secondaryDark),
                ],
              ),
            ),
            if (asInt(d['pending_questions']) > 0 || asInt(d['pending_assignments']) > 0) ...[
              const SectionHeader(title: 'Pendiente de atender'),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(children: [
                  if (asInt(d['pending_questions']) > 0)
                    _Alert(
                      icon: FontAwesomeIcons.commentDots,
                      color: AppColors.orange,
                      text: '${n('pending_questions')} pregunta(s) de estudiantes sin responder',
                      onTap: () => push(context, const TeacherQuestionsScreen()),
                    ),
                  if (asInt(d['pending_assignments']) > 0)
                    _Alert(
                      icon: FontAwesomeIcons.filePen,
                      color: AppColors.info,
                      text: '${n('pending_assignments')} tarea(s) por calificar',
                    ),
                ]),
              ),
            ],
            const SectionHeader(title: 'Accesos rápidos'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Row(children: [
                Expanded(child: _Quick(icon: FontAwesomeIcons.userGroup, label: 'Estudiantes', onTap: () => push(context, const TeacherStudentsScreen()))),
                const SizedBox(width: 12),
                Expanded(child: _Quick(icon: FontAwesomeIcons.comments, label: 'Preguntas', onTap: () => push(context, const TeacherQuestionsScreen()))),
                const SizedBox(width: 12),
                Expanded(child: _Quick(icon: FontAwesomeIcons.solidStar, label: 'Reseñas', onTap: () => push(context, const TeacherReviewsScreen()))),
              ]),
            ),
            if (recent.isNotEmpty) ...[
              const SectionHeader(title: 'Cursos recientes'),
              for (final c in recent)
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 0, 20, 10),
                  child: Card(
                    clipBehavior: Clip.antiAlias,
                    child: ListTile(
                      onTap: () => push(context, CourseDetailScreen(courseId: asInt(c['id']))),
                      contentPadding: const EdgeInsets.all(10),
                      leading: ClipRRect(borderRadius: BorderRadius.circular(10), child: SizedBox(width: 60, height: 60, child: CourseImage(url: asStringOrNull(c['image']), category: null))),
                      title: Text(asString(c['title']), maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800)),
                      subtitle: Text('${asInt(c['students'])} estudiantes', style: TextStyle(color: p.inkMuted)),
                      trailing: FaIcon(FontAwesomeIcons.chevronRight, size: 13, color: p.inkMuted),
                    ),
                  ),
                ),
            ],
            const SizedBox(height: 40),
          ]);
        },
      ),
    );
  }
}

class _Alert extends StatelessWidget {
  const _Alert({required this.icon, required this.color, required this.text, this.onTap});

  final FaIconData icon;
  final Color color;
  final String text;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(14)),
            child: Row(children: [
              FaIcon(icon, size: 18, color: color),
              const SizedBox(width: 12),
              Expanded(child: Text(text, style: const TextStyle(fontWeight: FontWeight.w700, height: 1.35))),
              if (onTap != null) FaIcon(FontAwesomeIcons.chevronRight, size: 12, color: color),
            ]),
          ),
        ),
      );
}

class _Quick extends StatelessWidget {
  const _Quick({required this.icon, required this.label, required this.onTap});

  final FaIconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(16), border: Border.all(color: p.border), boxShadow: p.shadow),
        child: Column(children: [
          FaIcon(icon, size: 22, color: p.primaryText),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5)),
        ]),
      ),
    );
  }
}
