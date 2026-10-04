import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';

/// RF-45: revisar y actuar sobre comentarios, preguntas, reseñas y cursos reportados.
class AdminReportsScreen extends StatefulWidget {
  const AdminReportsScreen({super.key});

  @override
  State<AdminReportsScreen> createState() => _AdminReportsScreenState();
}

class _AdminReportsScreenState extends State<AdminReportsScreen> {
  String? _status = 'pending';
  Key _key = UniqueKey();

  Future<void> _resolve(Map<String, dynamic> r, String action) async {
    try {
      await context.read<AuthProvider>().api.adminResolveReport(asInt(r['id']), action);
      if (mounted) {
        showToast(context, 'Reporte actualizado', success: true);
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
      appBar: AppBar(title: const Text('Contenido reportado')),
      body: Column(children: [
        SizedBox(
          height: 52,
          child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.fromLTRB(16, 6, 16, 6), children: [
            for (final e in const {'pending': 'Pendientes', 'resolved': 'Resueltos', 'dismissed': 'Descartados', null: 'Todos'}.entries)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(label: Text(e.value), selected: _status == e.key, onSelected: (_) => setState(() {
                      _status = e.key;
                      _key = UniqueKey();
                    })),
              ),
          ]),
        ),
        Expanded(
          child: AsyncBody<Map<String, dynamic>>(
            key: _key,
            load: () => api.adminReports(status: _status),
            builder: (context, data, reload) {
              final list = asList(data['reports']);
              if (list.isEmpty) return const EmptyState(icon: FontAwesomeIcons.flag, title: 'Sin reportes', message: 'No hay reportes con este estado.');
              return ListView.separated(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 40),
                itemCount: list.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (context, i) {
                  final r = list[i];
                  final pending = asString(r['status']) == 'pending';
                  final type = asString(r['type']);
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Row(children: [
                          SoftTag(label: asString(r['type_label']), color: AppColors.primaryLight, icon: FontAwesomeIcons.flag),
                          const Spacer(),
                          SoftTag(label: asString(r['status_label']), color: pending ? AppColors.warning : AppColors.success),
                        ]),
                        const SizedBox(height: 10),
                        Text('Motivo: ${asString(r['reason'])}', style: const TextStyle(fontWeight: FontWeight.w700, height: 1.4)),
                        const SizedBox(height: 6),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(color: p.surfaceSoft, borderRadius: BorderRadius.circular(12)),
                          child: Text(asStringOrNull(r['content']) ?? '(contenido ya eliminado)', maxLines: 5, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, height: 1.4)),
                        ),
                        const SizedBox(height: 6),
                        Text('Reportado por ${asString(r['reporter'])} · ${Fmt.ago(asDate(r['created_at']))}', style: TextStyle(color: p.inkMuted, fontSize: 12)),
                        if (pending) ...[
                          const SizedBox(height: 10),
                          Wrap(spacing: 8, children: [
                            if (type != 'course')
                              OutlinedButton.icon(
                                style: OutlinedButton.styleFrom(minimumSize: const Size(0, 42), foregroundColor: AppColors.danger, side: const BorderSide(color: AppColors.danger)),
                                onPressed: () => _resolve(r, 'remove'),
                                icon: const FaIcon(FontAwesomeIcons.trashCan, size: 13),
                                label: const Text('Eliminar contenido'),
                              ),
                            FilledButton.icon(style: FilledButton.styleFrom(minimumSize: const Size(0, 42)), onPressed: () => _resolve(r, 'resolve'), icon: const FaIcon(FontAwesomeIcons.check, size: 13), label: const Text('Resolver')),
                            TextButton(onPressed: () => _resolve(r, 'dismiss'), child: const Text('Descartar')),
                          ]),
                        ],
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
}
