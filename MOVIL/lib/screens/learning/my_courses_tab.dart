import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/nav.dart';
import '../../models/course.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../providers/shell_nav.dart';
import '../../core/utils/json_utils.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../../widgets/header_actions.dart';
import '../catalog/course_detail_screen.dart';
import '../teacher/course_form_screen.dart';
import '../teacher/teacher_course_sheet.dart';
import 'learn_screen.dart';

/// "Mis cursos": inscripciones del estudiante o cursos creados por el docente.
class MyCoursesTab extends StatefulWidget {
  const MyCoursesTab({super.key});

  @override
  State<MyCoursesTab> createState() => _MyCoursesTabState();
}

class _MyCoursesTabState extends State<MyCoursesTab> {
  String _filter = 'all';
  Key _reloadKey = UniqueKey();

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthProvider>();
    final isTeacher = auth.user!.isTeacher;
    return Scaffold(
      appBar: AppBar(
        title: Text(isTeacher ? 'Mis cursos' : 'Mis cursos'),
        actions: const [HeaderActions()],
      ),
      floatingActionButton: isTeacher
          ? FloatingActionButton.extended(
              backgroundColor: AppColors.secondary,
              foregroundColor: AppColors.primaryDark,
              onPressed: () async {
                final id = await push<int>(context, const CourseFormScreen());
                if (id != null && context.mounted) {
                  await showTeacherCourseSheet(context, Course.fromJson({'id': id, 'title': 'Curso nuevo', 'status': 'draft'}));
                }
                setState(() => _reloadKey = UniqueKey());
              },
              icon: const FaIcon(FontAwesomeIcons.plus, size: 15),
              label: const Text('Nuevo curso', style: TextStyle(fontWeight: FontWeight.w800)),
            )
          : null,
      body: AsyncBody<Map<String, dynamic>>(
        key: _reloadKey,
        load: auth.api.myCoursesRaw,
        builder: (context, data, reload) {
          if (asString(data['role']) == 'teacher') return _teacherList(context, asList(data['courses']), reload);
          final list = asList(data['enrollments']).map(EnrollmentItem.fromJson).toList();
          return _studentList(context, list, reload);
        },
      ),
    );
  }

  Widget _studentList(BuildContext context, List<EnrollmentItem> all, Future<void> Function() reload) {
    final p = context.palette;
    final list = all.where((e) {
      if (_filter == 'progress') return !e.isCompleted;
      if (_filter == 'done') return e.isCompleted;
      return true;
    }).toList();

    if (all.isEmpty) {
      return ListView(children: [
        SizedBox(
          height: MediaQuery.of(context).size.height * 0.6,
          child: EmptyState(
            icon: FontAwesomeIcons.bookOpenReader,
            title: 'Aún no tienes cursos',
            message: 'Explora el catálogo y empieza a aprender hoy mismo.',
            actionLabel: 'Explorar cursos',
            onAction: () => context.read<ShellNav>().openCatalog(1),
          ),
        ),
      ]);
    }

    return ListView(padding: const EdgeInsets.fromLTRB(16, 14, 16, 100), children: [
      Wrap(spacing: 8, children: [
        for (final f in const [('all', 'Todos'), ('progress', 'En progreso'), ('done', 'Completados')])
          ChoiceChip(label: Text(f.$2), selected: _filter == f.$1, onSelected: (_) => setState(() => _filter = f.$1)),
      ]),
      const SizedBox(height: 14),
      if (list.isEmpty)
        Padding(padding: const EdgeInsets.only(top: 60), child: Center(child: Text('No hay cursos en esta categoría.', style: TextStyle(color: p.inkMuted)))),
      for (final e in list)
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Card(
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: () async {
                await push(context, LearnScreen(courseId: e.courseId));
                reload();
              },
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(14),
                    child: SizedBox(width: 92, height: 92, child: CourseImage(url: e.image, category: e.category)),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(e.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800, height: 1.25)),
                      const SizedBox(height: 3),
                      Text(e.teacher, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                      const SizedBox(height: 10),
                      Row(children: [
                        Expanded(child: ProgressBar(value: e.progress, height: 7)),
                        const SizedBox(width: 10),
                        Text('${e.progress}%', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13)),
                      ]),
                      const SizedBox(height: 8),
                      Row(children: [
                        if (e.isCompleted)
                          const SoftTag(label: 'Completado', color: AppColors.success, icon: FontAwesomeIcons.check)
                        else if (e.status == 'pending')
                          const SoftTag(label: 'Pago pendiente', color: AppColors.warning)
                        else
                          SoftTag(label: e.progress > 0 ? 'En progreso' : 'Por empezar', color: AppColors.primaryLight),
                        const Spacer(),
                        if (e.certificateId != null) const FaIcon(FontAwesomeIcons.certificate, size: 16, color: AppColors.secondaryDark),
                      ]),
                    ]),
                  ),
                ]),
              ),
            ),
          ),
        ),
    ]);
  }

  Widget _teacherList(BuildContext context, List<Map<String, dynamic>> raw, Future<void> Function() reload) {
    final courses = raw.map(Course.fromJson).toList();
    if (courses.isEmpty) {
      return ListView(children: [
        SizedBox(
          height: MediaQuery.of(context).size.height * 0.6,
          child: EmptyState(
            icon: FontAwesomeIcons.chalkboard,
            title: 'Aún no tienes cursos',
            message: 'Crea tu primer curso: agrega módulos, lecciones y cuestionarios desde tu celular.',
            actionLabel: 'Crear curso',
            onAction: () async {
              await push(context, const CourseFormScreen());
              reload();
            },
          ),
        ),
      ]);
    }
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 100),
      itemCount: courses.length,
      separatorBuilder: (_, _) => const SizedBox(height: 12),
      itemBuilder: (context, i) {
        final c = courses[i];
        final color = switch (c.status) {
          'published' => AppColors.success,
          'pending' => AppColors.warning,
          'rejected' => AppColors.danger,
          _ => AppColors.info,
        };
        return SizedBox(
          height: 132,
          child: CourseListTile(
            course: c,
            trailing: SoftTag(label: c.statusLabel ?? '', color: color),
            onTap: () async {
              await showTeacherCourseSheet(context, c);
              reload();
            },
          ),
        );
      },
    );
  }
}

/// Atajo usado por otras pantallas para abrir un curso en modo estudiante.
void openCourse(BuildContext context, int id) => push(context, CourseDetailScreen(courseId: id));
