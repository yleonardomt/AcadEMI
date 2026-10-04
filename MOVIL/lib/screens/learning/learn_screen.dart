import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/nav.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../profile/certificate_detail_screen.dart';
import 'lesson_screen.dart';

/// Ruta de aprendizaje del curso: progreso, próxima lección y módulos.
class LearnScreen extends StatefulWidget {
  const LearnScreen({super.key, required this.courseId});

  final int courseId;

  @override
  State<LearnScreen> createState() => _LearnScreenState();
}

class _LearnScreenState extends State<LearnScreen> {
  final Key _key = UniqueKey();

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthProvider>();
    return Scaffold(
      body: AsyncBody<LearnData>(
        key: _key,
        load: () => auth.api.learn(widget.courseId),
        builder: (context, data, reload) => _LearnContent(
          data: data,
          openLesson: (id) async {
            await push(context, LessonScreen(lessonId: id));
            await reload();
          },
        ),
      ),
    );
  }
}

class _LearnContent extends StatelessWidget {
  const _LearnContent({required this.data, required this.openLesson});

  final LearnData data;
  final void Function(int lessonId) openLesson;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final done = data.progress >= 100;
    return CustomScrollView(slivers: [
      SliverAppBar(
        pinned: true,
        expandedHeight: 210,
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        flexibleSpace: FlexibleSpaceBar(
          titlePadding: const EdgeInsetsDirectional.only(start: 56, end: 16, bottom: 14),
          title: Text(data.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: Colors.white)),
          background: Stack(fit: StackFit.expand, children: [
            CourseImage(url: data.image, category: data.title),
            const DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [Colors.black26, Colors.black87]),
              ),
            ),
          ]),
        ),
      ),
      SliverToBoxAdapter(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            if (data.preview)
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: AppColors.info.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(14)),
                child: const Row(children: [
                  FaIcon(FontAwesomeIcons.eye, size: 16, color: AppColors.info),
                  SizedBox(width: 10),
                  Expanded(child: Text('Estás viendo el contenido como docente. Tu progreso no se registra.')),
                ]),
              )
            else ...[
              Row(children: [
                Text('${data.progress}%', style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w800, letterSpacing: -1)),
                const SizedBox(width: 10),
                Expanded(
                  child: Text('${data.completedCount} de ${data.totalLessons} lecciones completadas', style: TextStyle(color: p.inkMuted)),
                ),
              ]),
              const SizedBox(height: 10),
              ProgressBar(value: data.progress, height: 10),
              const SizedBox(height: 18),
              if (data.certificate != null)
                Container(
                  margin: const EdgeInsets.only(bottom: 14),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(gradient: AppColors.accentGradient, borderRadius: BorderRadius.circular(18)),
                  child: Row(children: [
                    const FaIcon(FontAwesomeIcons.award, size: 30, color: AppColors.primaryDark),
                    const SizedBox(width: 14),
                    const Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text('¡Curso completado!', style: TextStyle(color: AppColors.primaryDark, fontWeight: FontWeight.w800, fontSize: 16)),
                        Text('Tu certificado ya está disponible.', style: TextStyle(color: AppColors.primaryDark)),
                      ]),
                    ),
                    FilledButton(
                      style: FilledButton.styleFrom(minimumSize: const Size(0, 40), backgroundColor: AppColors.primaryDark),
                      onPressed: () => push(context, CertificateDetailScreen(certificate: data.certificate!)),
                      child: const Text('Ver'),
                    ),
                  ]),
                ),
              if (data.nextLessonId != null)
                LoadingButton(
                  label: data.completedCount == 0 ? 'Empezar el curso' : (done ? 'Repasar' : 'Continuar donde lo dejaste'),
                  icon: FontAwesomeIcons.circlePlay,
                  accent: true,
                  onPressed: () => openLesson(data.nextLessonId!),
                ),
            ],
            const SizedBox(height: 22),
            const Text('Contenido', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800)),
          ]),
        ),
      ),
      SliverList.builder(
        itemCount: data.modules.length,
        itemBuilder: (context, mi) {
          final m = data.modules[mi];
          final completed = m.lessons.where((l) => l.completed).length;
          return Container(
            margin: const EdgeInsets.fromLTRB(20, 10, 20, 0),
            decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(16), border: Border.all(color: p.border), boxShadow: p.shadow),
            clipBehavior: Clip.antiAlias,
            child: Theme(
              data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                initiallyExpanded: m.lessons.any((l) => l.id == data.nextLessonId) || mi == 0,
                shape: const Border(),
                collapsedShape: const Border(),
                tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                leading: Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(color: p.isDark ? p.surfaceSoft : AppColors.primaryLighter, shape: BoxShape.circle),
                  child: Center(child: Text('${mi + 1}', style: TextStyle(fontWeight: FontWeight.w800, color: p.primaryText))),
                ),
                title: Text(m.title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                subtitle: Text('$completed/${m.lessons.length} completadas', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                children: [
                  for (final l in m.lessons)
                    ListTile(
                      dense: true,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                      leading: l.completed
                          ? const FaIcon(FontAwesomeIcons.circleCheck, size: 20, color: AppColors.success)
                          : FaIcon(lessonIcon(l.type), size: 19, color: p.primaryText),
                      title: Text(l.title,
                          style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 14,
                              decoration: l.completed ? TextDecoration.none : null,
                              color: l.id == data.nextLessonId ? p.primaryText : null)),
                      subtitle: Text([lessonTypeLabel(l.type), if (l.durationMinutes > 0) Fmt.duration(l.durationMinutes)].join(' · '),
                          style: TextStyle(color: p.inkMuted, fontSize: 12)),
                      trailing: l.id == data.nextLessonId && !data.preview
                          ? const SoftTag(label: 'Siguiente', color: AppColors.primaryLight)
                          : FaIcon(FontAwesomeIcons.chevronRight, size: 12, color: p.inkMuted),
                      onTap: () => openLesson(l.id),
                    ),
                ],
              ),
            ),
          );
        },
      ),
      const SliverToBoxAdapter(child: SizedBox(height: 40)),
    ]);
  }
}
