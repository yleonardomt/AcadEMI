import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';
import 'lesson_media.dart';

/// Entrega de una tarea: sube (o reemplaza) el archivo y muestra la calificación.
class AssignmentCard extends StatefulWidget {
  const AssignmentCard({super.key, required this.lesson, required this.onSubmitted});

  final LessonDetail lesson;
  final Future<void> Function() onSubmitted;

  @override
  State<AssignmentCard> createState() => _AssignmentCardState();
}

class _AssignmentCardState extends State<AssignmentCard> {
  final _comment = TextEditingController();
  PlatformFile? _file;
  bool _sending = false;
  bool _replacing = false;

  @override
  void dispose() {
    _comment.dispose();
    super.dispose();
  }

  Future<void> _pick() async {
    final file = await FilePicker.pickFile();
    if (file != null && mounted) setState(() => _file = file);
  }

  Future<void> _submit() async {
    if (_file?.path == null) {
      showToast(context, 'Selecciona un archivo para entregar.', error: true);
      return;
    }
    setState(() => _sending = true);
    try {
      final msg = await context.read<AuthProvider>().api.submitAssignment(widget.lesson.id, _file!.path!, _comment.text.trim());
      if (mounted) {
        showToast(context, msg, success: true);
        setState(() {
          _file = null;
          _replacing = false;
          _comment.clear();
        });
      }
      await widget.onSubmitted();
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _sending = false);
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final lesson = widget.lesson;
    final s = lesson.submission;

    if (lesson.isStaff) {
      return FormCard(
        title: 'Tarea',
        icon: FontAwesomeIcons.filePen,
        child: Text('Los estudiantes entregan aquí su archivo. Las entregas se califican desde el sitio web.', style: TextStyle(color: p.inkMuted, height: 1.5)),
      );
    }
    if (!lesson.isEnrolled) {
      return FormCard(
        title: 'Tarea',
        icon: FontAwesomeIcons.filePen,
        child: Text('Inscríbete en el curso para entregar esta tarea.', style: TextStyle(color: p.inkMuted)),
      );
    }

    final showForm = s == null || _replacing;
    return FormCard(
      title: 'Tu entrega',
      icon: FontAwesomeIcons.cloudArrowUp,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        if (lesson.assignmentDeadlineDays != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(children: [
              const FaIcon(FontAwesomeIcons.calendarDay, size: 14, color: AppColors.orange),
              const SizedBox(width: 8),
              Text('Plazo sugerido: ${lesson.assignmentDeadlineDays} días', style: TextStyle(color: p.inkMuted, fontSize: 13)),
            ]),
          ),
        if (s != null && !showForm) ...[
          FileTile(title: 'Archivo entregado', subtitle: 'Enviado ${Fmt.dateTime(s.submittedAt)}', url: s.file, icon: FontAwesomeIcons.fileCircleCheck),
          if (s.comment.isNotEmpty) ...[const SizedBox(height: 8), Text('Tu comentario: ${s.comment}', style: TextStyle(color: p.inkMuted))],
          const SizedBox(height: 12),
          if (s.grade != null)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: AppColors.success.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(14)),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  const FaIcon(FontAwesomeIcons.circleCheck, size: 16, color: AppColors.success),
                  const SizedBox(width: 8),
                  const Text('Calificada', style: TextStyle(fontWeight: FontWeight.w800)),
                  const Spacer(),
                  Text('${s.grade}', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppColors.success)),
                ]),
                if (s.feedback.isNotEmpty) ...[const SizedBox(height: 8), Text(s.feedback, style: const TextStyle(height: 1.45))],
              ]),
            )
          else
            const SoftTag(label: 'Pendiente de calificación', color: AppColors.warning, icon: FontAwesomeIcons.hourglassHalf),
          const SizedBox(height: 12),
          LoadingButton(label: 'Volver a entregar', outlined: true, icon: FontAwesomeIcons.rotate, onPressed: () => setState(() => _replacing = true)),
        ] else ...[
          InkWell(
            onTap: _pick,
            borderRadius: BorderRadius.circular(14),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 22, horizontal: 16),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: p.primaryText.withValues(alpha: 0.5), width: 1.4),
                color: p.surfaceSoft,
              ),
              child: Column(children: [
                FaIcon(_file == null ? FontAwesomeIcons.cloudArrowUp : FontAwesomeIcons.fileCircleCheck, size: 28, color: p.primaryText),
                const SizedBox(height: 8),
                Text(_file?.name ?? 'Toca para elegir un archivo', textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w700)),
              ]),
            ),
          ),
          const SizedBox(height: 14),
          TextField(controller: _comment, maxLines: 3, decoration: const InputDecoration(hintText: 'Comentario para el docente (opcional)')),
          const SizedBox(height: 14),
          LoadingButton(label: 'Entregar tarea', icon: FontAwesomeIcons.paperPlane, loading: _sending, onPressed: _submit),
          if (_replacing) TextButton(onPressed: () => setState(() => _replacing = false), child: const Text('Cancelar')),
        ],
      ]),
    );
  }
}
