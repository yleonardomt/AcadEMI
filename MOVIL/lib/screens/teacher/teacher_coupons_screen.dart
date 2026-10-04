import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';
import '../../widgets/coupon_list.dart';
import '../../widgets/form_sheet.dart';

/// RF-36: el docente crea, modifica, activa/desactiva y elimina cupones de sus cursos.
class TeacherCouponsScreen extends StatefulWidget {
  const TeacherCouponsScreen({super.key});

  @override
  State<TeacherCouponsScreen> createState() => _TeacherCouponsScreenState();
}

class _TeacherCouponsScreenState extends State<TeacherCouponsScreen> {
  Key _key = UniqueKey();
  List<Map<String, dynamic>> _courses = [];

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

  Future<void> _form({Map<String, dynamic>? coupon}) async {
    final api = context.read<AuthProvider>().api;
    final editing = coupon != null;
    final v = await showFormSheet(context, title: editing ? 'Editar cupón ${coupon['code']}' : 'Nuevo cupón', fields: [
      if (!editing) FieldSpec('course', 'Curso', type: FieldType.dropdown, options: {for (final c in _courses) '${c['id']}': asString(c['title'])}, required: true, icon: FontAwesomeIcons.chalkboard),
      if (!editing) const FieldSpec('code', 'Código', required: true, icon: FontAwesomeIcons.ticket, hint: 'Ej: PROMO20'),
      FieldSpec('discount_type', 'Tipo de descuento', type: FieldType.dropdown, options: const {'percentage': 'Porcentaje (%)', 'fixed': 'Monto fijo (Bs.)'}, initial: coupon?['type'] ?? 'percentage', required: true),
      FieldSpec('discount_value', 'Valor', type: FieldType.decimal, initial: coupon?['value'], required: true),
      FieldSpec('max_uses', 'Usos máximos', type: FieldType.number, initial: coupon?['max_uses'] ?? 1, required: true),
      FieldSpec('expires_at', 'Vence el', type: FieldType.date, initial: coupon == null ? null : asString(coupon['expires_at']).split('T').first, required: true),
    ]);
    if (v == null) return;
    await _run(() => api.saveTeacherCoupon(v, id: editing ? asInt(coupon['id']) : null), 'Cupón guardado');
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    return Scaffold(
      appBar: AppBar(title: const Text('Mis cupones')),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.secondary,
        foregroundColor: AppColors.primaryDark,
        onPressed: () => _form(),
        icon: const FaIcon(FontAwesomeIcons.plus, size: 15),
        label: const Text('Nuevo cupón', style: TextStyle(fontWeight: FontWeight.w800)),
      ),
      body: AsyncBody<Map<String, dynamic>>(
        key: _key,
        load: api.teacherCoupons,
        builder: (context, data, reload) {
          _courses = asList(data['courses']);
          final list = asList(data['coupons']);
          if (list.isEmpty) {
            return ListView(children: [
              SizedBox(height: MediaQuery.of(context).size.height * 0.6, child: const EmptyState(icon: FontAwesomeIcons.ticket, title: 'Aún no tienes cupones', message: 'Crea un cupón de descuento para uno de tus cursos publicados.')),
            ]);
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final c = list[i];
              return CouponCard(
                coupon: c,
                onEdit: () => _form(coupon: c),
                onToggle: () => _run(() => api.toggleTeacherCoupon(asInt(c['id'])), 'Cupón actualizado'),
                onDelete: () async {
                  final ok = await confirmDialog(context, title: 'Eliminar cupón', message: '¿Eliminar el cupón ${c['code']}?', confirmLabel: 'Eliminar', danger: true);
                  if (ok) await _run(() => api.deleteTeacherCoupon(asInt(c['id'])), 'Cupón eliminado');
                },
              );
            },
          );
        },
      ),
    );
  }
}
