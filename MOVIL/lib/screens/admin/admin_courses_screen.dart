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
import '../catalog/course_detail_screen.dart';
import '../teacher/manage_course_screen.dart';

/// RF-44: consultar, aprobar, rechazar, modificar y retirar cursos.
class AdminCoursesScreen extends StatefulWidget {
  const AdminCoursesScreen({super.key});

  @override
  State<AdminCoursesScreen> createState() => _AdminCoursesScreenState();
}

class _AdminCoursesScreenState extends State<AdminCoursesScreen> {
  String? _status;
  Key _key = UniqueKey();

  static const _filters = {null: 'Todos', 'pending': 'Pendientes', 'published': 'Publicados', 'draft': 'Borradores', 'rejected': 'Rechazados', 'archived': 'Retirados'};

  void _refresh() => setState(() => _key = UniqueKey());

  Future<void> _moderate(Map<String, dynamic> c, String action) async {
    final api = context.read<AuthProvider>().api;
    var reason = '';
    if (action == 'reject') {
      final v = await showFormSheet(context, title: 'Rechazar curso', subtitle: asString(c['title']), fields: const [
        FieldSpec('reason', 'Motivo (se lo mostramos al docente)', type: FieldType.multiline, required: true),
      ], submitLabel: 'Rechazar');
      if (v == null) return;
      reason = v['reason'];
    } else if (action == 'retire') {
      final ok = await confirmDialog(context, title: 'Retirar curso', message: 'Dejará de mostrarse en el catálogo.', confirmLabel: 'Retirar', danger: true);
      if (!ok) return;
    }
    try {
      await api.adminModerateCourse(asInt(c['id']), action, reason: reason);
      if (mounted) showToast(context, 'Curso actualizado', success: true);
      _refresh();
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Cursos')),
      body: Column(children: [
        SizedBox(
          height: 52,
          child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.fromLTRB(16, 6, 16, 6), children: [
            for (final e in _filters.entries)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(label: Text(e.value), selected: _status == e.key, onSelected: (_) {
                  _status = e.key;
                  _refresh();
                }),
              ),
          ]),
        ),
        Expanded(
          child: AsyncBody<Map<String, dynamic>>(
            key: _key,
            load: () => api.adminCourses(status: _status),
            builder: (context, data, reload) {
              final list = asList(data['courses']);
              if (list.isEmpty) return const EmptyState(icon: FontAwesomeIcons.chalkboard, title: 'Sin cursos', message: 'No hay cursos con este estado.');
              return ListView.separated(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 40),
                itemCount: list.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (context, i) {
                  final c = list[i];
                  final status = asString(c['status']);
                  final color = switch (status) { 'published' => AppColors.success, 'pending' => AppColors.warning, 'rejected' || 'archived' => AppColors.danger, _ => AppColors.info };
                  return Card(
                    clipBehavior: Clip.antiAlias,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Row(children: [
                          ClipRRect(borderRadius: BorderRadius.circular(12), child: SizedBox(width: 68, height: 68, child: CourseImage(url: asStringOrNull(c['image']), category: asStringOrNull(c['category'])))),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(asString(c['title']), maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800, height: 1.25)),
                              const SizedBox(height: 3),
                              Text('${asString(c['teacher'])} · ${asBool(c['is_free']) ? 'Gratis' : Fmt.amount(asDouble(c['price']))}', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                              const SizedBox(height: 6),
                              Wrap(spacing: 6, children: [
                                SoftTag(label: asString(c['status_label']), color: color),
                                if (asBool(c['is_reported'])) const SoftTag(label: 'Reportado', color: AppColors.danger, icon: FontAwesomeIcons.flag),
                              ]),
                            ]),
                          ),
                        ]),
                        if (asString(c['rejection_reason']).isNotEmpty)
                          Padding(padding: const EdgeInsets.only(top: 8), child: Text('Motivo: ${asString(c['rejection_reason'])}', style: TextStyle(color: p.inkMuted, fontSize: 12.5))),
                        const SizedBox(height: 10),
                        Wrap(spacing: 8, runSpacing: 4, children: [
                          if (status != 'published') _act(FontAwesomeIcons.check, 'Aprobar', AppColors.success, () => _moderate(c, 'approve')),
                          if (status != 'rejected') _act(FontAwesomeIcons.xmark, 'Rechazar', AppColors.warning, () => _moderate(c, 'reject')),
                          if (status == 'published') _act(FontAwesomeIcons.boxArchive, 'Retirar', AppColors.danger, () => _moderate(c, 'retire')),
                          _act(FontAwesomeIcons.penRuler, 'Gestionar', AppColors.primaryLight, () async {
                            await push(context, ManageCourseScreen(courseId: asInt(c['id'])));
                            _refresh();
                          }),
                          if (status == 'published') _act(FontAwesomeIcons.eye, 'Ver', AppColors.info, () => push(context, CourseDetailScreen(courseId: asInt(c['id'])))),
                        ]),
                      ]),
                    ),
                  );
                },
              );
            },
          ),
        ),
      ]),
    );
  }

  Widget _act(FaIconData icon, String label, Color color, VoidCallback onTap) => TextButton.icon(
        style: TextButton.styleFrom(foregroundColor: color, padding: const EdgeInsets.symmetric(horizontal: 10), minimumSize: const Size(0, 36)),
        onPressed: onTap,
        icon: FaIcon(icon, size: 13),
        label: Text(label),
      );
}
