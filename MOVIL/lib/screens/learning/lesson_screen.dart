import 'package:flutter/material.dart';
import 'package:flutter_widget_from_html_core/flutter_widget_from_html_core.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/nav.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';
import '../catalog/course_detail_screen.dart';
import '../profile/certificates_screen.dart';
import 'assignment_card.dart';
import 'lesson_discussion.dart';
import 'lesson_media.dart';
import 'quiz_screen.dart';

/// Vista de una lección: video, lectura, documento, cuestionario o tarea,
/// con recursos, comentarios y preguntas.
class LessonScreen extends StatefulWidget {
  const LessonScreen({super.key, required this.lessonId});

  final int lessonId;

  @override
  State<LessonScreen> createState() => _LessonScreenState();
}

class _LessonScreenState extends State<LessonScreen> {
  LessonDetail? _lesson;
  String? _error;
  bool _loading = true;
  bool _completing = false;
  final Key _discussionKey = UniqueKey();

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent) setState(() => _loading = true);
    try {
      final l = await context.read<AuthProvider>().api.lesson(widget.lessonId);
      if (mounted) {
        setState(() {
          _lesson = l;
          _error = null;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = errorText(e);
          _loading = false;
        });
      }
    }
  }

  void _goToLesson(int id) => Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => LessonScreen(lessonId: id)));

  Future<void> _complete() async {
    final lesson = _lesson!;
    setState(() => _completing = true);
    try {
      final r = await context.read<AuthProvider>().api.completeLesson(lesson.id);
      if (!mounted) return;
      await _load(silent: true);
      if (r['course_completed'] == true && mounted) {
        await _celebrate();
      } else if (mounted) {
        showToast(context, 'Lección completada · ${r['progress']}% del curso', success: true);
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _completing = false);
  }

  Future<void> _celebrate() async {
    final lesson = _lesson!;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Column(children: [
          FaIcon(FontAwesomeIcons.award, size: 44, color: AppColors.secondaryDark),
          SizedBox(height: 12),
          Text('¡Curso completado!', textAlign: TextAlign.center),
        ]),
        content: Text('Terminaste "${lesson.courseTitle}". Tu certificado ya está listo en la sección Certificados.', textAlign: TextAlign.center),
        actionsAlignment: MainAxisAlignment.center,
        actions: [
          FilledButton(
            style: FilledButton.styleFrom(minimumSize: const Size(160, 44)),
            onPressed: () => Navigator.pop(ctx),
            child: const Text('¡Genial!'),
          ),
        ],
      ),
    );
  }

  Future<void> _openQuiz() async {
    final lesson = _lesson!;
    final result = await push<QuizResult>(context, QuizScreen(lessonId: lesson.id, title: lesson.title));
    if (!mounted) return;
    await _load(silent: true);
    if (result != null && result.courseCompleted && mounted) await _celebrate();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return Scaffold(appBar: AppBar(), body: const Center(child: CircularProgressIndicator()));
    if (_lesson == null) {
      return Scaffold(appBar: AppBar(), body: ErrorState(message: _error ?? '', onRetry: () => _load()));
    }
    final lesson = _lesson!;
    final p = context.palette;
    final user = context.watch<AuthProvider>().user!;
    final isPreview = !lesson.isEnrolled && !lesson.isStaff;

    Widget media;
    if (lesson.type == 'video') {
      if (lesson.youtubeId != null) {
        media = YoutubeLesson(key: ValueKey(lesson.id), videoId: lesson.youtubeId!);
      } else if (lesson.videoFile != null) {
        media = FileVideoLesson(key: ValueKey(lesson.id), url: lesson.videoFile!);
      } else if (lesson.videoUrl != null) {
        media = ExternalVideoLesson(url: lesson.videoUrl!);
      } else {
        media = const SizedBox.shrink();
      }
    } else {
      media = const SizedBox.shrink();
    }

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Text(lesson.courseTitle, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 16)),
        actions: [
          if (lesson.isEnrolled)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Center(child: SoftTag(label: '${lesson.progress}%', color: AppColors.primaryLight, icon: FontAwesomeIcons.chartLine)),
            ),
        ],
      ),
      bottomNavigationBar: _NavBar(lesson: lesson, onGo: _goToLesson),
      body: RefreshIndicator(
        onRefresh: () => _load(silent: true),
        child: ListView(padding: const EdgeInsets.fromLTRB(16, 16, 16, 40), children: [
          if (isPreview)
            Container(
              margin: const EdgeInsets.only(bottom: 14),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: AppColors.info.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(14)),
              child: Row(children: [
                const FaIcon(FontAwesomeIcons.eye, size: 16, color: AppColors.info),
                const SizedBox(width: 10),
                const Expanded(child: Text('Vista previa gratuita de esta lección.', style: TextStyle(fontWeight: FontWeight.w600))),
                TextButton(
                  onPressed: () => push(context, CourseDetailScreen(courseId: lesson.courseId)),
                  child: const Text('Ver curso'),
                ),
              ]),
            ),
          media,
          if (lesson.type == 'video') const SizedBox(height: 16),
          Row(children: [
            SoftTag(label: lessonTypeLabel(lesson.type), color: AppColors.primaryLight, icon: lessonIcon(lesson.type)),
            const SizedBox(width: 8),
            if (lesson.durationMinutes > 0) SoftTag(label: Fmt.duration(lesson.durationMinutes), color: AppColors.orange, icon: FontAwesomeIcons.clock),
            if (lesson.completed) ...[const SizedBox(width: 8), const SoftTag(label: 'Completada', color: AppColors.success, icon: FontAwesomeIcons.check)],
          ]),
          const SizedBox(height: 12),
          Text(lesson.title, style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w800, letterSpacing: -0.4, height: 1.2)),
          if (lesson.module.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(lesson.module, style: TextStyle(color: p.inkMuted, fontSize: 13.5)),
            ),
          if (lesson.description.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(lesson.description, style: TextStyle(color: p.ink.withValues(alpha: 0.9), height: 1.55)),
          ],
          if (lesson.type == 'document' && lesson.documentFile != null) ...[
            const SizedBox(height: 18),
            FileTile(title: 'Abrir documento de la lección', subtitle: 'Se abrirá en tu visor de documentos', url: lesson.documentFile),
          ],
          if (lesson.content.trim().isNotEmpty) ...[
            const SizedBox(height: 18),
            HtmlWidget(
              lesson.content,
              textStyle: TextStyle(color: p.ink, height: 1.6, fontSize: 15.5),
              onTapUrl: (url) => launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication),
            ),
          ],
          if (lesson.isQuiz && lesson.quiz != null) ...[
            const SizedBox(height: 18),
            _QuizCard(lesson: lesson, onStart: _openQuiz),
          ],
          if (lesson.type == 'assignment') ...[
            const SizedBox(height: 18),
            AssignmentCard(lesson: lesson, onSubmitted: () => _load(silent: true)),
          ],
          if (lesson.resources.isNotEmpty) ...[
            const SizedBox(height: 22),
            const Text('Recursos', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            for (final r in lesson.resources)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: FileTile(title: r.title, subtitle: r.type.toUpperCase(), url: r.url, icon: FontAwesomeIcons.paperclip),
              ),
          ],
          if (lesson.isEnrolled && !lesson.isQuiz && lesson.type != 'assignment' && !lesson.completed) ...[
            const SizedBox(height: 22),
            LoadingButton(label: 'Marcar como completada', icon: FontAwesomeIcons.circleCheck, accent: true, loading: _completing, onPressed: _complete),
          ] else if (lesson.isEnrolled && lesson.type == 'assignment' && !lesson.completed) ...[
            const SizedBox(height: 22),
            LoadingButton(label: 'Marcar como completada', icon: FontAwesomeIcons.circleCheck, accent: true, loading: _completing, onPressed: _complete),
          ],
          if (lesson.isEnrolled && lesson.progress >= 100 && user.isStudent) ...[
            const SizedBox(height: 12),
            LoadingButton(
              label: 'Ver mis certificados',
              outlined: true,
              icon: FontAwesomeIcons.certificate,
              onPressed: () => push(context, const CertificatesScreen()),
            ),
          ],
          const SizedBox(height: 28),
          const Text('Comunidad', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800)),
          const SizedBox(height: 12),
          LessonDiscussion(key: _discussionKey, lesson: lesson),
        ]),
      ),
    );
  }
}

class _QuizCard extends StatelessWidget {
  const _QuizCard({required this.lesson, required this.onStart});

  final LessonDetail lesson;
  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) {
    final q = lesson.quiz!;
    final p = context.palette;
    final blocked = q.attemptsLeft == 0;

    Widget row(FaIconData icon, String label, String value) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(children: [
            FaIcon(icon, size: 15, color: p.primaryText),
            const SizedBox(width: 12),
            Expanded(child: Text(label, style: TextStyle(color: p.inkMuted))),
            Text(value, style: const TextStyle(fontWeight: FontWeight.w800)),
          ]),
        );

    return FormCard(
      title: q.title.isEmpty ? 'Cuestionario' : q.title,
      icon: FontAwesomeIcons.listCheck,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        if (q.description.isNotEmpty) Padding(padding: const EdgeInsets.only(bottom: 10), child: Text(q.description, style: TextStyle(color: p.inkMuted, height: 1.5))),
        row(FontAwesomeIcons.circleQuestion, 'Preguntas', '${q.questionsCount}'),
        row(FontAwesomeIcons.stopwatch, 'Tiempo límite', '${q.timeLimitMinutes} min'),
        row(FontAwesomeIcons.bullseye, 'Puntaje para aprobar', '${q.passingScore}%'),
        row(FontAwesomeIcons.repeat, 'Intentos', '${q.attempts}/${q.maxAttempts}'),
        if (q.bestScore != null) row(FontAwesomeIcons.trophy, 'Tu mejor puntaje', '${q.bestScore}%'),
        const SizedBox(height: 14),
        if (!lesson.isEnrolled)
          Text('Inscríbete en el curso para realizar este cuestionario.', style: TextStyle(color: p.inkMuted))
        else if (lesson.isStaff)
          Text('Los docentes no realizan el cuestionario.', style: TextStyle(color: p.inkMuted))
        else if (blocked)
          const SoftTag(label: 'Sin intentos disponibles', color: AppColors.danger, icon: FontAwesomeIcons.ban)
        else
          LoadingButton(
            label: q.attempts == 0 ? 'Comenzar cuestionario' : 'Reintentar cuestionario',
            icon: FontAwesomeIcons.play,
            accent: true,
            onPressed: onStart,
          ),
      ]),
    );
  }
}

class _NavBar extends StatelessWidget {
  const _NavBar({required this.lesson, required this.onGo});

  final LessonDetail lesson;
  final void Function(int) onGo;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    if (lesson.prevLessonId == null && lesson.nextLessonId == null) return const SizedBox.shrink();
    return Container(
      padding: EdgeInsets.fromLTRB(16, 10, 16, MediaQuery.of(context).padding.bottom + 10),
      decoration: BoxDecoration(color: p.surface, border: Border(top: BorderSide(color: p.border))),
      child: Row(children: [
        if (lesson.prevLessonId != null)
          SizedBox(
            width: 54,
            child: OutlinedButton(
              onPressed: () => onGo(lesson.prevLessonId!),
              style: OutlinedButton.styleFrom(padding: EdgeInsets.zero),
              child: const FaIcon(FontAwesomeIcons.arrowLeft, size: 16),
            ),
          ),
        if (lesson.prevLessonId != null && lesson.nextLessonId != null) const SizedBox(width: 12),
        if (lesson.nextLessonId != null)
          Expanded(
            flex: 2,
            child: FilledButton.icon(
              onPressed: () => onGo(lesson.nextLessonId!),
              icon: const FaIcon(FontAwesomeIcons.arrowRight, size: 14),
              iconAlignment: IconAlignment.end,
              label: Text(lesson.nextLessonTitle ?? 'Siguiente', maxLines: 1, overflow: TextOverflow.ellipsis),
            ),
          ),
      ]),
    );
  }
}
