import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';
import '../../widgets/form_sheet.dart';

/// RF-44: gestionar las categorías de cursos.
class AdminCategoriesScreen extends StatefulWidget {
  const AdminCategoriesScreen({super.key});

  @override
  State<AdminCategoriesScreen> createState() => _AdminCategoriesScreenState();
}

class _AdminCategoriesScreenState extends State<AdminCategoriesScreen> {
  Key _key = UniqueKey();

  Future<void> _run(Future<void> Function() action, String ok) async {
    try {
      await action();
      if (mounted) {
        showToast(context, ok, success: true);
        setState(() => _key = UniqueKey());
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  Future<void> _form({Map<String, dynamic>? cat}) async {
    final api = context.read<AuthProvider>().api;
    final v = await showFormSheet(context, title: cat == null ? 'Nueva categoría' : 'Editar categoría', fields: [
      FieldSpec('name', 'Nombre', initial: cat?['name'], required: true, icon: FontAwesomeIcons.tag),
      FieldSpec('description', 'Descripción', type: FieldType.multiline, initial: cat?['description']),
    ]);
    if (v == null) return;
    await _run(() => api.adminSaveCategory(v, id: cat == null ? null : asInt(cat['id'])), 'Categoría guardada');
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Categorías')),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.secondary,
        foregroundColor: AppColors.primaryDark,
        onPressed: () => _form(),
        icon: const FaIcon(FontAwesomeIcons.plus, size: 15),
        label: const Text('Nueva', style: TextStyle(fontWeight: FontWeight.w800)),
      ),
      body: AsyncBody<Map<String, dynamic>>(
        key: _key,
        load: api.adminCategories,
        builder: (context, data, reload) {
          final list = asList(data['categories']);
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final c = list[i];
              return Card(
                child: ListTile(
                  contentPadding: const EdgeInsets.fromLTRB(14, 6, 4, 6),
                  leading: Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(color: AppColors.primaryLight.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(12)),
                    child: Center(child: FaIcon(categoryIcon(asString(c['name'])), size: 17, color: p.primaryText)),
                  ),
                  title: Text(asString(c['name']), style: const TextStyle(fontWeight: FontWeight.w800)),
                  subtitle: Text('${asInt(c['courses_count'])} cursos${asString(c['description']).isNotEmpty ? ' · ${asString(c['description'])}' : ''}', maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                  trailing: PopupMenuButton<String>(
                    onSelected: (a) async {
                      if (a == 'edit') await _form(cat: c);
                      if (a == 'delete') {
                        final ok = await confirmDialog(context, title: 'Eliminar categoría', message: '¿Eliminar "${asString(c['name'])}"? Solo se puede si no tiene cursos.', confirmLabel: 'Eliminar', danger: true);
                        if (ok) await _run(() => api.adminDeleteCategory(asInt(c['id'])), 'Categoría eliminada');
                      }
                    },
                    itemBuilder: (_) => const [
                      PopupMenuItem(value: 'edit', child: Text('Editar')),
                      PopupMenuItem(value: 'delete', child: Text('Eliminar', style: TextStyle(color: AppColors.danger))),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
