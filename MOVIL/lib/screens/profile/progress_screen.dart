import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../core/utils/nav.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../learning/learn_screen.dart';

/// RF-09: avance por curso e historial de actividad de aprendizaje.
class ProgressScreen extends StatelessWidget {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Mi progreso')),
      body: AsyncBody<Map<String, dynamic>>(
        load: api.progress,
        builder: (context, data, reload) {
          final courses = asList(data['courses']);
          final activity = asList(data['activity']);
          activity.sort((a, b) => asString(b['at']).compareTo(asString(a['at'])));
          if (courses.isEmpty) {
            return ListView(children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: const EmptyState(icon: FontAwesomeIcons.chartLine, title: 'Aún no hay progreso', message: 'Inscríbete en un curso y empieza a completar lecciones.'),
              ),
            ]);
          }
          final done = courses.fold<int>(0, (a, c) => a + asInt(c['completed_lessons']));
          final total = courses.fold<int>(0, (a, c) => a + asInt(c['total_lessons']));
          return ListView(padding: const EdgeInsets.all(16), children: [
            Row(children: [
              Expanded(child: StatTile(icon: FontAwesomeIcons.circleCheck, value: '$done/$total', label: 'Lecciones', color: AppColors.success)),
              const SizedBox(width: 12),
              Expanded(child: StatTile(icon: FontAwesomeIcons.graduationCap, value: '${courses.where((c) => asString(c['status']) == 'completed').length}', label: 'Cursos listos', color: AppColors.purple)),
            ]),
            const SectionHeader(title: 'Mis cursos', padding: EdgeInsets.fromLTRB(4, 22, 4, 10)),
            for (final c in courses)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Builder(builder: (context) {
                  final e = EnrollmentItem.fromJson(c);
                  return Card(
                    clipBehavior: Clip.antiAlias,
                    child: InkWell(
                      onTap: () => push(context, LearnScreen(courseId: e.courseId)),
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Row(children: [
                          ClipRRect(borderRadius: BorderRadius.circular(12), child: SizedBox(width: 60, height: 60, child: CourseImage(url: e.image, category: e.category))),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(e.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800)),
                              const SizedBox(height: 6),
                              ProgressBar(value: e.progress, height: 7),
                              const SizedBox(height: 6),
                              Text('${asInt(c['completed_lessons'])} de ${asInt(c['total_lessons'])} lecciones · ${e.progress}%${e.lastAccessed != null ? ' · ${Fmt.ago(e.lastAccessed)}' : ''}',
                                  style: TextStyle(color: p.inkMuted, fontSize: 12)),
                            ]),
                          ),
                        ]),
                      ),
                    ),
                  );
                }),
              ),
            if (activity.isNotEmpty) ...[
              const SectionHeader(title: 'Actividad reciente', padding: EdgeInsets.fromLTRB(4, 22, 4, 10)),
              for (final a in activity.take(25))
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      color: (asString(a['type']) == 'lesson' ? AppColors.success : (a['passed'] == true ? AppColors.primaryLight : AppColors.warning)).withValues(alpha: 0.14),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: FaIcon(asString(a['type']) == 'lesson' ? FontAwesomeIcons.check : FontAwesomeIcons.listCheck, size: 15,
                          color: asString(a['type']) == 'lesson' ? AppColors.success : (a['passed'] == true ? AppColors.primaryLight : AppColors.warning)),
                    ),
                  ),
                  title: Text(asString(a['title']), maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                  subtitle: Text('${asString(a['type']) == 'lesson' ? 'Lección completada' : (a['passed'] == true ? 'Evaluación aprobada' : 'Evaluación realizada')} · ${asString(a['course'])}',
                      maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12)),
                  trailing: Text(Fmt.ago(asDate(a['at'])), style: TextStyle(color: p.inkMuted, fontSize: 11.5)),
                ),
            ],
          ]);
        },
      ),
    );
  }
}
