import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';
import '../../widgets/form_sheet.dart';

/// Entregas de una tarea: el docente descarga el archivo y la califica.
class SubmissionsScreen extends StatefulWidget {
  const SubmissionsScreen({super.key, required this.lessonId});

  final int lessonId;

  @override
  State<SubmissionsScreen> createState() => _SubmissionsScreenState();
}

class _SubmissionsScreenState extends State<SubmissionsScreen> {
  Key _key = UniqueKey();

  Future<void> _grade(Map<String, dynamic> s) async {
    final v = await showFormSheet(context, title: 'Calificar entrega', subtitle: asString(s['student']), fields: [
      FieldSpec('grade', 'Nota (0 a 100)', type: FieldType.number, initial: s['grade'], required: true, icon: FontAwesomeIcons.star),
      FieldSpec('feedback', 'Comentarios para el estudiante', type: FieldType.multiline, initial: s['feedback']),
    ], submitLabel: 'Guardar nota');
    if (v == null || !mounted) return;
    try {
      await context.read<AuthProvider>().api.gradeSubmission(asInt(s['id']), int.tryParse(v['grade']) ?? -1, v['feedback']);
      if (mounted) {
        showToast(context, 'Tarea calificada.', success: true);
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
      appBar: AppBar(title: const Text('Entregas de la tarea')),
      body: AsyncBody<Map<String, dynamic>>(
        key: _key,
        load: () => api.submissions(widget.lessonId),
        builder: (context, data, reload) {
          final list = asList(data['submissions']);
          if (list.isEmpty) {
            return ListView(children: [
              SizedBox(height: MediaQuery.of(context).size.height * 0.6, child: const EmptyState(icon: FontAwesomeIcons.inbox, title: 'Sin entregas', message: 'Aún no hay estudiantes que hayan entregado esta tarea.')),
            ]);
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final s = list[i];
              final graded = s['grade'] != null;
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Expanded(child: Text(asString(s['student']), style: const TextStyle(fontWeight: FontWeight.w800))),
                      if (graded) SoftTag(label: 'Nota ${asInt(s['grade'])}', color: AppColors.success) else const SoftTag(label: 'Sin calificar', color: AppColors.warning),
                    ]),
                    const SizedBox(height: 4),
                    Text('Entregada ${Fmt.dateTime(asDate(s['submitted_at']))}', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                    if (asString(s['comment']).isNotEmpty) ...[const SizedBox(height: 8), Text(asString(s['comment']), style: const TextStyle(height: 1.4))],
                    const SizedBox(height: 12),
                    Row(children: [
                      if (asStringOrNull(s['file']) != null)
                        Expanded(child: OutlinedButton.icon(style: OutlinedButton.styleFrom(minimumSize: const Size(0, 44)), onPressed: () => launchUrl(Uri.parse(asString(s['file'])), mode: LaunchMode.externalApplication), icon: const FaIcon(FontAwesomeIcons.download, size: 14), label: const Text('Archivo'))),
                      if (asStringOrNull(s['file']) != null) const SizedBox(width: 10),
                      Expanded(child: FilledButton.icon(style: FilledButton.styleFrom(minimumSize: const Size(0, 44)), onPressed: () => _grade(s), icon: const FaIcon(FontAwesomeIcons.star, size: 14), label: Text(graded ? 'Cambiar nota' : 'Calificar'))),
                    ]),
                  ]),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
