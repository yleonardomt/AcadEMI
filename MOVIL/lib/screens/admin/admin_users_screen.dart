import 'dart:async';

import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';
import '../../widgets/form_sheet.dart';

/// RF-43: crear, consultar, modificar, activar/desactivar y eliminar usuarios y roles.
class AdminUsersScreen extends StatefulWidget {
  const AdminUsersScreen({super.key});

  @override
  State<AdminUsersScreen> createState() => _AdminUsersScreenState();
}

class _AdminUsersScreenState extends State<AdminUsersScreen> {
  final _search = TextEditingController();
  Timer? _debounce;
  String? _role;
  Key _key = UniqueKey();

  static const _roles = {'student': 'Estudiante', 'teacher': 'Docente', 'admin': 'Administrador'};

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    super.dispose();
  }

  void _refresh() => setState(() => _key = UniqueKey());

  Future<void> _run(Future<void> Function() action, String ok) async {
    try {
      await action();
      if (mounted) showToast(context, ok, success: true);
      _refresh();
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  Future<void> _form({Map<String, dynamic>? user}) async {
    final api = context.read<AuthProvider>().api;
    final editing = user != null;
    final v = await showFormSheet(context, title: editing ? 'Editar usuario' : 'Nuevo usuario', fields: [
      FieldSpec('username', 'Usuario', initial: user?['username'], required: true, icon: FontAwesomeIcons.user),
      FieldSpec('email', 'Correo', type: FieldType.email, initial: user?['email'], required: true, icon: FontAwesomeIcons.envelope),
      FieldSpec('first_name', 'Nombre', initial: user?['first_name'], icon: FontAwesomeIcons.idCard),
      FieldSpec('phone', 'Teléfono', initial: user?['phone'], icon: FontAwesomeIcons.phone),
      FieldSpec('role', 'Rol', type: FieldType.dropdown, options: _roles, initial: user?['role'] ?? 'student', required: true, icon: FontAwesomeIcons.userShield),
      if (!editing) const FieldSpec('password', 'Contraseña (mín. 8)', type: FieldType.password, required: true, icon: FontAwesomeIcons.lock),
    ]);
    if (v == null) return;
    await _run(() => editing ? api.adminUpdateUser(asInt(user['id']), v) : api.adminCreateUser(v), editing ? 'Usuario actualizado' : 'Usuario creado');
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final me = context.read<AuthProvider>().user!;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Usuarios')),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.secondary,
        foregroundColor: AppColors.primaryDark,
        onPressed: () => _form(),
        icon: const FaIcon(FontAwesomeIcons.userPlus, size: 15),
        label: const Text('Nuevo', style: TextStyle(fontWeight: FontWeight.w800)),
      ),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
          child: TextField(
            controller: _search,
            onChanged: (_) {
              _debounce?.cancel();
              _debounce = Timer(const Duration(milliseconds: 400), _refresh);
            },
            decoration: InputDecoration(
              hintText: 'Buscar por nombre, usuario o correo',
              prefixIcon: Padding(padding: const EdgeInsets.all(14), child: FaIcon(FontAwesomeIcons.magnifyingGlass, size: 15, color: p.inkMuted)),
              prefixIconConstraints: const BoxConstraints(minWidth: 44),
            ),
          ),
        ),
        SizedBox(
          height: 44,
          child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 16), children: [
            for (final e in {null: 'Todos', ..._roles}.entries)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(label: Text(e.value), selected: _role == e.key, onSelected: (_) {
                  _role = e.key;
                  _refresh();
                }),
              ),
          ]),
        ),
        Expanded(
          child: AsyncBody<Map<String, dynamic>>(
            key: _key,
            load: () => api.adminUsers(q: _search.text.trim(), role: _role),
            builder: (context, data, reload) {
              final users = asList(data['users']);
              final t = (data['totals'] as Map?) ?? {};
              return ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 100), children: [
                Text('${asInt(t['all'])} usuarios · ${asInt(t['active'])} activos · ${asInt(t['inactive'])} inactivos', style: TextStyle(color: p.inkMuted, fontWeight: FontWeight.w600, fontSize: 13)),
                const SizedBox(height: 10),
                if (users.isEmpty) Padding(padding: const EdgeInsets.only(top: 50), child: Center(child: Text('Sin resultados', style: TextStyle(color: p.inkMuted)))),
                for (final u in users)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Card(
                      child: ListTile(
                        contentPadding: const EdgeInsets.fromLTRB(14, 6, 4, 6),
                        leading: UserAvatar(name: asString(u['name']), url: asStringOrNull(u['picture']), radius: 22),
                        title: Text(asString(u['name']), maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800)),
                        subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(asString(u['email']), maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                          const SizedBox(height: 4),
                          Wrap(spacing: 6, children: [
                            SoftTag(label: asString(u['role_label']), color: AppColors.primaryLight),
                            SoftTag(label: asBool(u['is_active']) ? 'Activo' : 'Inactivo', color: asBool(u['is_active']) ? AppColors.success : AppColors.danger),
                          ]),
                        ]),
                        trailing: PopupMenuButton<String>(
                          onSelected: (a) async {
                            final id = asInt(u['id']);
                            if (a == 'edit') await _form(user: u);
                            if (a == 'toggle') await _run(() => api.adminToggleUser(id), 'Estado actualizado');
                            if (a == 'password') {
                              final v = await showFormSheet(context, title: 'Restablecer contraseña', subtitle: asString(u['username']), fields: const [
                                FieldSpec('new_password', 'Nueva contraseña (mín. 8)', type: FieldType.password, required: true, icon: FontAwesomeIcons.key),
                              ]);
                              if (v != null) await _run(() => api.adminResetPassword(id, v['new_password']), 'Contraseña restablecida');
                            }
                            if (a == 'delete') {
                              final ok = await confirmDialog(context, title: 'Eliminar usuario', message: 'Se eliminará a ${asString(u['username'])} y sus datos. No se puede deshacer.', confirmLabel: 'Eliminar', danger: true);
                              if (ok) await _run(() => api.adminDeleteUser(id), 'Usuario eliminado');
                            }
                          },
                          itemBuilder: (_) => [
                            const PopupMenuItem(value: 'edit', child: Text('Editar / cambiar rol')),
                            if (asInt(u['id']) != me.id) PopupMenuItem(value: 'toggle', child: Text(asBool(u['is_active']) ? 'Desactivar' : 'Activar')),
                            const PopupMenuItem(value: 'password', child: Text('Restablecer contraseña')),
                            if (asInt(u['id']) != me.id) const PopupMenuItem(value: 'delete', child: Text('Eliminar', style: TextStyle(color: AppColors.danger))),
                          ],
                        ),
                        onTap: () => showToast(context, 'Registrado ${Fmt.date(asDate(u['joined']))}'),
                      ),
                    ),
                  ),
              ]);
            },
          ),
        ),
      ]),
    );
  }
}
