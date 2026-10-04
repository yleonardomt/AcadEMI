import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/nav.dart';
import '../../models/course.dart';
import '../catalog/course_detail_screen.dart';
import '../learning/learn_screen.dart';
import 'course_stats_screen.dart';
import 'manage_course_screen.dart';
import 'teacher_students_screen.dart';

/// Acciones del docente sobre uno de sus cursos.
Future<void> showTeacherCourseSheet(BuildContext context, Course course) => showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) {
        final published = course.status == 'published';
        Widget action(FaIconData icon, String label, String subtitle, Color color, VoidCallback onTap) => ListTile(
              leading: Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(color: color.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(13)),
                child: Center(child: FaIcon(icon, size: 17, color: color)),
              ),
              title: Text(label, style: const TextStyle(fontWeight: FontWeight.w800)),
              subtitle: Text(subtitle, style: TextStyle(color: ctx.palette.inkMuted, fontSize: 12.5)),
              onTap: () {
                Navigator.pop(ctx);
                onTap();
              },
            );
        return SafeArea(
          child: SingleChildScrollView(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
                child: Text(course.title, maxLines: 2, overflow: TextOverflow.ellipsis, textAlign: TextAlign.center, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
              ),
              action(FontAwesomeIcons.penRuler, 'Editar y gestionar', 'Datos del curso, módulos y lecciones', AppColors.primaryLight, () => push(context, ManageCourseScreen(courseId: course.id))),
              action(FontAwesomeIcons.chartColumn, 'Estadísticas', 'Estudiantes, progreso, valoraciones y ventas', AppColors.orange, () => push(context, CourseStatsScreen(courseId: course.id))),
              action(FontAwesomeIcons.userGroup, 'Estudiantes inscritos', '${course.studentsCount} inscritos y su progreso', AppColors.teal, () => push(context, TeacherStudentsScreen(courseId: course.id))),
              action(FontAwesomeIcons.clipboardCheck, 'Resultados e incidencias', 'Evaluaciones realizadas por los estudiantes', AppColors.danger, () => push(context, CourseResultsScreen(courseId: course.id))),
              if (published) ...[
                action(FontAwesomeIcons.layerGroup, 'Ver contenido', 'Recorre el curso como docente', AppColors.info, () => push(context, LearnScreen(courseId: course.id))),
                action(FontAwesomeIcons.eye, 'Vista del estudiante', 'Cómo lo ve el catálogo', AppColors.purple, () => push(context, CourseDetailScreen(courseId: course.id))),
              ],
              const SizedBox(height: 8),
            ]),
          ),
        );
      },
    );
