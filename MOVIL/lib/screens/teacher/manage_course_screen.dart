import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../core/utils/nav.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../../widgets/form_sheet.dart';
import 'course_form_screen.dart';
import 'course_stats_screen.dart';
import 'lesson_form_screen.dart';
import 'submissions_screen.dart';
import 'teacher_students_screen.dart';

/// RF-14: estructura del curso. Permite crear, editar, ordenar y eliminar módulos y lecciones.
class ManageCourseScreen extends StatefulWidget {
  const ManageCourseScreen({super.key, required this.courseId});

  final int courseId;

  @override
  State<ManageCourseScreen> createState() => _ManageCourseScreenState();
}

class _ManageCourseScreenState extends State<ManageCourseScreen> {
  Key _key = UniqueKey();

  void _refresh() => setState(() => _key = UniqueKey());

  Future<void> _run(Future<void> Function() action, {String? ok}) async {
    try {
      await action();
      if (ok != null && mounted) showToast(context, ok, success: true);
      _refresh();
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  Future<void> _moduleForm({Map<String, dynamic>? module}) async {
    final api = context.read<AuthProvider>().api;
    final v = await showFormSheet(context, title: module == null ? 'Nuevo módulo' : 'Editar módulo', fields: [
      FieldSpec('title', 'Título del módulo', initial: module?['title'], required: true, icon: FontAwesomeIcons.heading),
      FieldSpec('description', 'Descripción (opcional)', type: FieldType.multiline, initial: module?['description']),
    ]);
    if (v == null) return;
    await _run(() => api.saveModule(courseId: widget.courseId, moduleId: module == null ? null : asInt(module['id']), title: v['title'], description: v['description']),
        ok: 'Módulo guardado');
  }

  Future<void> _pickLessonType(int moduleId) async {
    const types = [
      ('text', 'Lectura', 'Texto o contenido en HTML', FontAwesomeIcons.alignLeft),
      ('video', 'Video', 'YouTube o archivo de video', FontAwesomeIcons.circlePlay),
      ('document', 'Documento', 'PDF, presentación u otro archivo', FontAwesomeIcons.fileLines),
      ('assignment', 'Tarea', 'El estudiante sube un archivo', FontAwesomeIcons.filePen),
      ('quiz', 'Cuestionario', 'Preguntas con opciones', FontAwesomeIcons.listCheck),
      ('exam', 'Examen', 'Evaluación más extensa', FontAwesomeIcons.clipboardCheck),
    ];
    final type = await showModalBottomSheet<String>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Padding(padding: EdgeInsets.all(8), child: Text('¿Qué tipo de lección?', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800))),
          for (final t in types)
            ListTile(
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(color: AppColors.primaryLight.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(12)),
                child: Center(child: FaIcon(t.$4, size: 16, color: ctx.palette.primaryText)),
              ),
              title: Text(t.$2, style: const TextStyle(fontWeight: FontWeight.w800)),
              subtitle: Text(t.$3, style: TextStyle(color: ctx.palette.inkMuted, fontSize: 12.5)),
              onTap: () => Navigator.pop(ctx, t.$1),
            ),
          const SizedBox(height: 8),
        ]),
      ),
    );
    if (type == null || !mounted) return;
    final saved = await push<bool>(context, LessonFormScreen(moduleId: moduleId, type: type));
    if (saved == true) _refresh();
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Gestionar curso')),
      body: AsyncBody<Map<String, dynamic>>(
        key: _key,
        load: () => api.manageCourse(widget.courseId),
        builder: (context, c, reload) {
          final modules = asList(c['modules']);
          final status = asString(c['status']);
          final statusColor = switch (status) {
            'published' => AppColors.success,
            'pending' => AppColors.warning,
            'rejected' => AppColors.danger,
            _ => AppColors.info,
          };
          return ListView(padding: const EdgeInsets.fromLTRB(16, 16, 16, 100), children: [
            Card(
              clipBehavior: Clip.antiAlias,
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                SizedBox(height: 130, width: double.infinity, child: CourseImage(url: asStringOrNull(c['image']), category: asStringOrNull(c['category']))),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      SoftTag(label: asString(c['status_label']), color: statusColor),
                      const SizedBox(width: 8),
                      Text(asBool(c['is_free']) ? 'Gratis' : Fmt.amount(asDouble(c['price'])), style: const TextStyle(fontWeight: FontWeight.w800)),
                    ]),
                    const SizedBox(height: 10),
                    Text(asString(c['title']), style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800, height: 1.25)),
                    if (asString(c['rejection_reason']).isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Text('Motivo del rechazo: ${asString(c['rejection_reason'])}', style: const TextStyle(color: AppColors.danger, height: 1.4)),
                    ],
                    const SizedBox(height: 14),
                    Wrap(spacing: 8, runSpacing: 8, children: [
                      _chip(FontAwesomeIcons.pen, 'Editar', () async {
                        await push(context, CourseFormScreen(courseId: widget.courseId));
                        _refresh();
                      }),
                      _chip(FontAwesomeIcons.chartColumn, 'Estadísticas', () => push(context, CourseStatsScreen(courseId: widget.courseId))),
                      _chip(FontAwesomeIcons.userGroup, 'Estudiantes', () => push(context, TeacherStudentsScreen(courseId: widget.courseId))),
                      _chip(FontAwesomeIcons.clipboardCheck, 'Resultados', () => push(context, CourseResultsScreen(courseId: widget.courseId))),
                    ]),
                  ]),
                ),
              ]),
            ),
            if (status != 'published') ...[
              const SizedBox(height: 14),
              LoadingButton(
                label: 'Publicar curso',
                icon: FontAwesomeIcons.rocket,
                accent: true,
                onPressed: () => _run(() async => showToast(context, await api.publishCourse(widget.courseId), success: true)),
              ),
            ],
            SectionHeader(title: 'Contenido', subtitle: '${modules.length} módulos', padding: const EdgeInsets.fromLTRB(4, 24, 4, 10)),
            if (modules.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 30),
                child: Center(child: Text('Aún no hay módulos. Crea el primero.', style: TextStyle(color: p.inkMuted))),
              ),
            for (final m in modules)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(16), border: Border.all(color: p.border), boxShadow: p.shadow),
                child: Column(children: [
                  ListTile(
                    contentPadding: const EdgeInsets.fromLTRB(16, 4, 4, 0),
                    title: Text(asString(m['title']), style: const TextStyle(fontWeight: FontWeight.w800)),
                    subtitle: Text('${asList(m['lessons']).length} lecciones', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                    trailing: PopupMenuButton<String>(
                      onSelected: (a) async {
                        final id = asInt(m['id']);
                        if (a == 'edit') await _moduleForm(module: m);
                        if (a == 'up') await _run(() => api.moveModule(id, 'up'));
                        if (a == 'down') await _run(() => api.moveModule(id, 'down'));
                        if (a == 'delete') {
                          final ok = await confirmDialog(context, title: 'Eliminar módulo', message: 'Se eliminarán también sus lecciones.', confirmLabel: 'Eliminar', danger: true);
                          if (ok) await _run(() => api.deleteModule(id), ok: 'Módulo eliminado');
                        }
                      },
                      itemBuilder: (_) => const [
                        PopupMenuItem(value: 'edit', child: Text('Editar módulo')),
                        PopupMenuItem(value: 'up', child: Text('Subir')),
                        PopupMenuItem(value: 'down', child: Text('Bajar')),
                        PopupMenuItem(value: 'delete', child: Text('Eliminar', style: TextStyle(color: AppColors.danger))),
                      ],
                    ),
                  ),
                  for (final l in asList(m['lessons']))
                    ListTile(
                      dense: true,
                      contentPadding: const EdgeInsets.fromLTRB(16, 0, 4, 0),
                      leading: FaIcon(lessonIcon(asString(l['type'])), size: 17, color: p.primaryText),
                      title: Text(asString(l['title']), style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                      subtitle: Text([lessonTypeLabel(asString(l['type'])), if (asInt(l['duration_minutes']) > 0) Fmt.duration(asInt(l['duration_minutes'])), if (asBool(l['is_free'])) 'Vista previa'].join(' · '),
                          style: TextStyle(color: p.inkMuted, fontSize: 12)),
                      trailing: PopupMenuButton<String>(
                        onSelected: (a) async {
                          final id = asInt(l['id']);
                          if (a == 'edit') {
                            final saved = await push<bool>(context, LessonFormScreen(lessonId: id, type: asString(l['type'])));
                            if (saved == true) _refresh();
                          }
                          if (a == 'submissions') push(context, SubmissionsScreen(lessonId: id));
                          if (a == 'up') await _run(() => api.moveLesson(id, 'up'));
                          if (a == 'down') await _run(() => api.moveLesson(id, 'down'));
                          if (a == 'delete') {
                            final ok = await confirmDialog(context, title: 'Eliminar lección', message: '¿Eliminar "${asString(l['title'])}"?', confirmLabel: 'Eliminar', danger: true);
                            if (ok) await _run(() => api.deleteLesson(id), ok: 'Lección eliminada');
                          }
                        },
                        itemBuilder: (_) => [
                          const PopupMenuItem(value: 'edit', child: Text('Editar')),
                          if (asString(l['type']) == 'assignment') const PopupMenuItem(value: 'submissions', child: Text('Ver entregas')),
                          const PopupMenuItem(value: 'up', child: Text('Subir')),
                          const PopupMenuItem(value: 'down', child: Text('Bajar')),
                          const PopupMenuItem(value: 'delete', child: Text('Eliminar', style: TextStyle(color: AppColors.danger))),
                        ],
                      ),
                    ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
                    child: TextButton.icon(
                      onPressed: () => _pickLessonType(asInt(m['id'])),
                      icon: const FaIcon(FontAwesomeIcons.plus, size: 12),
                      label: const Text('Agregar lección'),
                    ),
                  ),
                ]),
              ),
            const SizedBox(height: 4),
            OutlinedButton.icon(onPressed: () => _moduleForm(), icon: const FaIcon(FontAwesomeIcons.folderPlus, size: 16), label: const Text('Agregar módulo')),
            const SizedBox(height: 22),
            TextButton.icon(
              style: TextButton.styleFrom(foregroundColor: AppColors.danger),
              onPressed: () async {
                final ok = await confirmDialog(context, title: 'Eliminar curso', message: 'Se eliminará el curso completo con sus módulos, lecciones y avances. Esta acción no se puede deshacer.', confirmLabel: 'Eliminar curso', danger: true);
                if (!ok || !mounted) return;
                try {
                  final msg = await api.deleteCourse(widget.courseId);
                  if (mounted) {
                    showToast(context, msg, success: true);
                    Navigator.pop(context, true);
                  }
                } catch (e) {
                  if (mounted) showToast(context, errorText(e), error: true);
                }
              },
              icon: const FaIcon(FontAwesomeIcons.trashCan, size: 15),
              label: const Text('Eliminar curso'),
            ),
          ]);
        },
      ),
    );
  }

  Widget _chip(FaIconData icon, String label, VoidCallback onTap) => ActionChip(
        avatar: FaIcon(icon, size: 13),
        label: Text(label),
        onPressed: onTap,
      );
}
