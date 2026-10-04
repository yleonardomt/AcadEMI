import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';

/// Comentarios y preguntas al docente de una lección (RF-35 a RF-39).
class LessonDiscussion extends StatefulWidget {
  const LessonDiscussion({super.key, required this.lesson});

  final LessonDetail lesson;

  @override
  State<LessonDiscussion> createState() => _LessonDiscussionState();
}

class _LessonDiscussionState extends State<LessonDiscussion> {
  bool _questions = false;
  final _text = TextEditingController();
  bool _sending = false;
  late final List<DiscussionItem> _comments = [...widget.lesson.comments];
  late final List<DiscussionItem> _qs = [...widget.lesson.questions];

  @override
  void dispose() {
    _text.dispose();
    super.dispose();
  }

  bool get _canPost => widget.lesson.isEnrolled || widget.lesson.isStaff;

  Future<void> _send() async {
    final content = _text.text.trim();
    if (content.isEmpty) return;
    setState(() => _sending = true);
    final api = context.read<AuthProvider>().api;
    try {
      if (_questions) {
        final q = await api.addQuestion(widget.lesson.id, content);
        setState(() => _qs.insert(0, q));
      } else {
        final c = await api.addComment(widget.lesson.id, content);
        setState(() => _comments.insert(0, c));
      }
      _text.clear();
      if (mounted) FocusScope.of(context).unfocus();
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _sending = false);
  }

  Future<void> _deleteComment(DiscussionItem c) async {
    final ok = await confirmDialog(context,
        title: 'Eliminar comentario', message: '¿Quieres eliminar este comentario?', confirmLabel: 'Eliminar', danger: true);
    if (!ok || !mounted) return;
    try {
      await context.read<AuthProvider>().api.deleteComment(c.id);
      setState(() => _comments.removeWhere((x) => x.id == c.id));
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  /// RF-25: el autor edita su comentario.
  Future<void> _editComment(DiscussionItem c) async {
    final text = TextEditingController(text: c.content);
    final save = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Editar comentario'),
        content: TextField(controller: text, maxLines: 4, autofocus: true),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(style: FilledButton.styleFrom(minimumSize: const Size(0, 42)), onPressed: () => Navigator.pop(ctx, true), child: const Text('Guardar')),
        ],
      ),
    );
    if (save != true || text.text.trim().isEmpty || !mounted) return;
    try {
      final updated = await context.read<AuthProvider>().api.editComment(c.id, text.text.trim());
      if (mounted) {
        setState(() {
          final i = _comments.indexWhere((x) => x.id == c.id);
          if (i >= 0) _comments[i] = updated;
        });
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  Future<void> _report(String type, DiscussionItem item) async {
    final reason = TextEditingController();
    final send = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Reportar contenido'),
        content: TextField(controller: reason, maxLines: 3, decoration: const InputDecoration(hintText: 'Motivo del reporte…')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(style: FilledButton.styleFrom(minimumSize: const Size(0, 42)), onPressed: () => Navigator.pop(ctx, true), child: const Text('Reportar')),
        ],
      ),
    );
    if (send != true || reason.text.trim().isEmpty || !mounted) return;
    try {
      final msg = await context.read<AuthProvider>().api.report(type, item.id, reason.text.trim());
      if (mounted) showToast(context, msg, success: true);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final items = _questions ? _qs : _comments;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      SegmentedButton<bool>(
        showSelectedIcon: false,
        style: SegmentedButton.styleFrom(
          selectedBackgroundColor: AppColors.primary,
          selectedForegroundColor: Colors.white,
        ),
        segments: [
          ButtonSegment(value: false, label: Text('Comentarios (${_comments.length})'), icon: const FaIcon(FontAwesomeIcons.comment, size: 14)),
          ButtonSegment(value: true, label: Text('Preguntas (${_qs.length})'), icon: const FaIcon(FontAwesomeIcons.circleQuestion, size: 14)),
        ],
        selected: {_questions},
        onSelectionChanged: (s) => setState(() {
          _questions = s.first;
          _text.clear();
        }),
      ),
      const SizedBox(height: 14),
      if (_canPost)
        Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Expanded(
            child: TextField(
              controller: _text,
              minLines: 1,
              maxLines: 4,
              textCapitalization: TextCapitalization.sentences,
              decoration: InputDecoration(hintText: _questions ? 'Haz una pregunta al docente…' : 'Escribe un comentario…'),
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            width: 50,
            height: 50,
            child: FilledButton(
              onPressed: _sending ? null : _send,
              style: FilledButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(50, 50)),
              child: _sending
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2.2, color: Colors.white))
                  : const FaIcon(FontAwesomeIcons.paperPlane, size: 16),
            ),
          ),
        ])
      else
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: p.surfaceSoft, borderRadius: BorderRadius.circular(12)),
          child: Row(children: [
            FaIcon(FontAwesomeIcons.lock, size: 14, color: p.inkMuted),
            const SizedBox(width: 10),
            Expanded(child: Text('Inscríbete en el curso para participar.', style: TextStyle(color: p.inkMuted))),
          ]),
        ),
      const SizedBox(height: 8),
      if (items.isEmpty)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 26),
          child: Center(
            child: Text(_questions ? 'Todavía no hay preguntas.' : 'Todavía no hay comentarios.', style: TextStyle(color: p.inkMuted)),
          ),
        ),
      for (final item in items)
        Padding(
          padding: const EdgeInsets.only(top: 14),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            UserAvatar(name: item.author, url: item.picture, radius: 19),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Flexible(child: Text(item.author, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800))),
                  const SizedBox(width: 8),
                  Text(Fmt.ago(item.createdAt), style: TextStyle(color: p.inkMuted, fontSize: 12)),
                  if (item.isEdited) Text(' · editado', style: TextStyle(color: p.inkMuted, fontSize: 12)),
                  if (_questions && item.isAnswered) ...[const SizedBox(width: 8), const SoftTag(label: 'Respondida', color: AppColors.success)],
                ]),
                const SizedBox(height: 4),
                Text(item.content, style: const TextStyle(height: 1.45)),
                Row(children: [
                  if (!item.isMine)
                    TextButton.icon(
                      onPressed: () => _report(_questions ? 'question' : 'comment', item),
                      style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 30), foregroundColor: p.inkMuted),
                      icon: const FaIcon(FontAwesomeIcons.flag, size: 11),
                      label: const Text('Reportar', style: TextStyle(fontSize: 12)),
                    ),
                  if (!_questions && item.isMine)
                    TextButton.icon(
                      onPressed: () => _editComment(item),
                      style: TextButton.styleFrom(padding: const EdgeInsets.only(right: 12), minimumSize: const Size(0, 30), foregroundColor: p.primaryText),
                      icon: const FaIcon(FontAwesomeIcons.pen, size: 11),
                      label: const Text('Editar', style: TextStyle(fontSize: 12)),
                    ),
                  if (!_questions && (item.isMine || widget.lesson.isStaff))
                    TextButton.icon(
                      onPressed: () => _deleteComment(item),
                      style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 30), foregroundColor: AppColors.danger),
                      icon: const FaIcon(FontAwesomeIcons.trash, size: 11),
                      label: const Text('Eliminar', style: TextStyle(fontSize: 12)),
                    ),
                ]),
                for (final a in item.answers)
                  Container(
                    margin: const EdgeInsets.only(top: 6),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.primaryLight.withValues(alpha: p.isDark ? 0.22 : 0.10),
                      borderRadius: BorderRadius.circular(12),
                      border: Border(left: BorderSide(color: p.primaryText, width: 3)),
                    ),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        FaIcon(FontAwesomeIcons.chalkboardUser, size: 12, color: p.primaryText),
                        const SizedBox(width: 6),
                        Text('${a.teacher} · Docente', style: TextStyle(color: p.primaryText, fontWeight: FontWeight.w800, fontSize: 12.5)),
                      ]),
                      const SizedBox(height: 4),
                      Text(a.content, style: const TextStyle(height: 1.45)),
                    ]),
                  ),
              ]),
            ),
          ]),
        ),
    ]);
  }
}
