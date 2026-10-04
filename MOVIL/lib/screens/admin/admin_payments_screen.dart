import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';

/// RF-47: compras realizadas e ingresos generados.
class AdminPaymentsScreen extends StatelessWidget {
  const AdminPaymentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Compras e ingresos')),
      body: AsyncBody<Map<String, dynamic>>(
        load: api.adminPayments,
        builder: (context, data, reload) {
          final list = asList(data['payments']);
          return ListView(padding: const EdgeInsets.all(16), children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(gradient: AppColors.heroGradient, borderRadius: BorderRadius.circular(20)),
              child: Row(children: [
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Ingresos totales', style: TextStyle(color: Colors.white.withValues(alpha: 0.8))),
                    const SizedBox(height: 4),
                    Text(Fmt.amount(asDouble(data['total_revenue'])), style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 4),
                    Text('Este mes: ${Fmt.amount(asDouble(data['monthly_revenue']))}', style: const TextStyle(color: AppColors.secondary, fontWeight: FontWeight.w700)),
                  ]),
                ),
                Column(children: [
                  Text('${asInt(data['completed_count'])}', style: const TextStyle(color: AppColors.secondary, fontSize: 26, fontWeight: FontWeight.w800)),
                  Text('compras', style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 12)),
                ]),
              ]),
            ),
            const SizedBox(height: 16),
            if (list.isEmpty) const Padding(padding: EdgeInsets.only(top: 40), child: EmptyState(icon: FontAwesomeIcons.receipt, title: 'Sin compras', message: 'Aún no se registraron compras.')),
            for (final pay in list)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        Expanded(child: Text(asStringOrNull(pay['invoice_number']) ?? 'Compra #${asInt(pay['id'])}', style: const TextStyle(fontWeight: FontWeight.w800))),
                        Text(Fmt.amount(asDouble(pay['total'])), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                      ]),
                      const SizedBox(height: 4),
                      Text('${asString(pay['student'])} · ${asString(pay['email'])}', maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                      const SizedBox(height: 6),
                      Text((pay['courses'] as List? ?? []).join(', '), maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13)),
                      const SizedBox(height: 8),
                      Row(children: [
                        SoftTag(label: asString(pay['status_label']), color: asString(pay['status']) == 'completed' ? AppColors.success : AppColors.warning),
                        const SizedBox(width: 8),
                        Text(asString(pay['method_label']), style: TextStyle(color: p.inkMuted, fontSize: 12)),
                        const Spacer(),
                        Text(Fmt.date(asDate(pay['created_at'])), style: TextStyle(color: p.inkMuted, fontSize: 12)),
                      ]),
                    ]),
                  ),
                ),
              ),
          ]);
        },
      ),
    );
  }
}
