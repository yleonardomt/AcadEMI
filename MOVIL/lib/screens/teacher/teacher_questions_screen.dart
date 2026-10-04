import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/nav.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';
import '../learning/lesson_screen.dart';

/// Preguntas de estudiantes en los cursos del docente (RF-38).
class TeacherQuestionsScreen extends StatefulWidget {
  const TeacherQuestionsScreen({super.key, this.embedded = false});

  final bool embedded;

  @override
  State<TeacherQuestionsScreen> createState() => _TeacherQuestionsScreenState();
}

class _TeacherQuestionsScreenState extends State<TeacherQuestionsScreen> {
  Key _key = UniqueKey();

  Future<void> _answer(DiscussionItem q) async {
    final text = TextEditingController(text: q.answers.isNotEmpty ? q.answers.first.content : '');
    final send = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.fromLTRB(20, 0, 20, MediaQuery.of(ctx).viewInsets.bottom + 20),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Responder a ${q.author}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Text(q.content, style: TextStyle(color: ctx.palette.inkMuted, height: 1.45)),
          const SizedBox(height: 14),
          TextField(controller: text, maxLines: 5, autofocus: true, decoration: const InputDecoration(hintText: 'Escribe tu respuesta…')),
          const SizedBox(height: 14),
          LoadingButton(label: 'Publicar respuesta', icon: FontAwesomeIcons.paperPlane, onPressed: () => Navigator.pop(ctx, true)),
        ]),
      ),
    );
    if (send != true || text.text.trim().isEmpty || !mounted) return;
    try {
      await context.read<AuthProvider>().api.answerQuestion(q.id, text.text.trim());
      if (mounted) {
        showToast(context, 'Respuesta publicada.', success: true);
        setState(() => _key = UniqueKey());
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Preguntas de estudiantes')),
      body: AsyncBody<List<DiscussionItem>>(
        key: _key,
        load: api.teacherQuestions,
        builder: (context, list, reload) {
          if (list.isEmpty) {
            return ListView(children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: const EmptyState(icon: FontAwesomeIcons.commentDots, title: 'Sin preguntas', message: 'Cuando un estudiante te pregunte algo en una lección, lo verás aquí.'),
              ),
            ]);
          }
          final pending = list.where((q) => !q.isAnswered).length;
          return ListView(padding: const EdgeInsets.all(16), children: [
            if (pending > 0)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: SoftTag(label: '$pending pendiente(s) de responder', color: AppColors.orange, icon: FontAwesomeIcons.hourglassHalf),
              ),
            for (final q in list)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        UserAvatar(name: q.author, url: q.picture, radius: 18),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(q.author, style: const TextStyle(fontWeight: FontWeight.w800)),
                            Text(Fmt.ago(q.createdAt), style: TextStyle(color: p.inkMuted, fontSize: 12)),
                          ]),
                        ),
                        SoftTag(label: q.isAnswered ? 'Respondida' : 'Pendiente', color: q.isAnswered ? AppColors.success : AppColors.orange),
                      ]),
                      const SizedBox(height: 10),
                      Text(q.content, style: const TextStyle(height: 1.45, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 6),
                      Text('${q.course ?? ''} · ${q.lesson ?? ''}', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                      for (final a in q.answers)
                        Container(
                          margin: const EdgeInsets.only(top: 10),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(color: AppColors.primaryLight.withValues(alpha: p.isDark ? 0.22 : 0.10), borderRadius: BorderRadius.circular(12)),
                          child: Text(a.content, style: const TextStyle(height: 1.45)),
                        ),
                      const SizedBox(height: 12),
                      Row(children: [
                        Expanded(
                          child: FilledButton.icon(
                            style: FilledButton.styleFrom(minimumSize: const Size(0, 44)),
                            onPressed: () => _answer(q),
                            icon: FaIcon(q.isAnswered ? FontAwesomeIcons.pen : FontAwesomeIcons.reply, size: 14),
                            label: Text(q.isAnswered ? 'Editar respuesta' : 'Responder'),
                          ),
                        ),
                        if (q.lessonId != null) ...[
                          const SizedBox(width: 10),
                          OutlinedButton(
                            style: OutlinedButton.styleFrom(minimumSize: const Size(52, 44), padding: EdgeInsets.zero),
                            onPressed: () => push(context, LessonScreen(lessonId: q.lessonId!)),
                            child: const FaIcon(FontAwesomeIcons.arrowUpRightFromSquare, size: 14),
                          ),
                        ],
                      ]),
                    ]),
                  ),
                ),
              ),
          ]);
        },
      ),
    );
  }
}
