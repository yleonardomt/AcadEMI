import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../core/theme/app_colors.dart';
import '../core/utils/format.dart';
import '../core/utils/json_utils.dart';
import 'common.dart';

/// Tarjeta de un cupón con sus datos y acciones (la usan docente y administrador).
class CouponCard extends StatelessWidget {
  const CouponCard({super.key, required this.coupon, required this.onEdit, required this.onToggle, this.onDelete});

  final Map<String, dynamic> coupon;
  final VoidCallback onEdit, onToggle;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final active = asBool(coupon['is_active']);
    final valid = asBool(coupon['is_valid']);
    final isPercent = asString(coupon['type']) == 'percentage';
    final value = asDouble(coupon['value']);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(color: AppColors.secondary.withValues(alpha: 0.25), borderRadius: BorderRadius.circular(10)),
              child: Text(asString(coupon['code']), style: const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1.2)),
            ),
            const SizedBox(width: 10),
            Text(isPercent ? '-${value.toStringAsFixed(0)}%' : '-Bs. ${value.toStringAsFixed(0)}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
            const Spacer(),
            SoftTag(label: !active ? 'Inactivo' : (valid ? 'Vigente' : 'Vencido/agotado'), color: !active ? AppColors.danger : (valid ? AppColors.success : AppColors.warning)),
          ]),
          const SizedBox(height: 10),
          if (asStringOrNull(coupon['course']) != null)
            Row(children: [
              FaIcon(FontAwesomeIcons.chalkboard, size: 12, color: p.inkMuted),
              const SizedBox(width: 8),
              Expanded(child: Text(asString(coupon['course']), maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 13))),
            ])
          else
            Text('Aplica a todos los cursos', style: TextStyle(color: p.inkMuted, fontSize: 13)),
          const SizedBox(height: 4),
          Text('Usos: ${asInt(coupon['used_count'])}/${asInt(coupon['max_uses'])} · vence ${Fmt.date(asDate(coupon['expires_at']))}', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
          const SizedBox(height: 10),
          Row(children: [
            TextButton.icon(onPressed: onEdit, icon: const FaIcon(FontAwesomeIcons.pen, size: 12), label: const Text('Editar')),
            TextButton.icon(onPressed: onToggle, icon: FaIcon(active ? FontAwesomeIcons.toggleOn : FontAwesomeIcons.toggleOff, size: 15), label: Text(active ? 'Desactivar' : 'Activar')),
            const Spacer(),
            if (onDelete != null) IconButton(onPressed: onDelete, icon: const FaIcon(FontAwesomeIcons.trashCan, size: 15, color: AppColors.danger)),
          ]),
        ]),
      ),
    );
  }
}
