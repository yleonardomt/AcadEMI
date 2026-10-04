import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../models/social.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';

/// Estudiantes inscritos: de todos los cursos del docente o de uno específico.
class TeacherStudentsScreen extends StatelessWidget {
  const TeacherStudentsScreen({super.key, this.courseId});

  final int? courseId;

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    return AsyncBody<(String, List<TeacherStudent>)>(
      load: () async {
        if (courseId != null) return api.courseStudents(courseId!);
        return ('Mis estudiantes', await api.teacherStudents());
      },
      builder: (context, data, reload) {
        final (title, list) = data;
        final p = context.palette;
        return Scaffold(
          appBar: AppBar(title: Text(courseId == null ? 'Mis estudiantes' : title, maxLines: 1, overflow: TextOverflow.ellipsis)),
          body: list.isEmpty
              ? const EmptyState(icon: FontAwesomeIcons.userGroup, title: 'Aún no hay estudiantes', message: 'Cuando alguien se inscriba en tus cursos aparecerá aquí.')
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: list.length + 1,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (context, i) {
                    if (i == 0) {
                      return Text('${list.length} estudiantes', style: TextStyle(color: p.inkMuted, fontWeight: FontWeight.w600));
                    }
                    final s = list[i - 1];
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Row(children: [
                          UserAvatar(name: s.student, url: s.picture, radius: 22),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(s.student, style: const TextStyle(fontWeight: FontWeight.w800)),
                              Text(s.course.isNotEmpty ? s.course : s.email, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                              const SizedBox(height: 8),
                              Row(children: [
                                Expanded(child: ProgressBar(value: s.progress, height: 6)),
                                const SizedBox(width: 8),
                                Text('${s.progress}%', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12.5)),
                              ]),
                            ]),
                          ),
                          if (s.averageScore != null) ...[
                            const SizedBox(width: 12),
                            Column(children: [
                              Text('${s.averageScore}%', style: TextStyle(fontWeight: FontWeight.w800, color: s.averageScore! >= 70 ? AppColors.success : AppColors.warning)),
                              Text('nota', style: TextStyle(color: p.inkMuted, fontSize: 11)),
                            ]),
                          ],
                        ]),
                      ),
                    );
                  },
                ),
        );
      },
    );
  }
}
