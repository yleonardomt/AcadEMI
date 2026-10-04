import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';

class GradesScreen extends StatelessWidget {
  const GradesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Mis calificaciones')),
      body: AsyncBody<List<GradeResult>>(
        load: api.grades,
        builder: (context, list, reload) {
          if (list.isEmpty) {
            return ListView(children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: const EmptyState(icon: FontAwesomeIcons.chartSimple, title: 'Sin calificaciones', message: 'Tus resultados de cuestionarios y exámenes aparecerán aquí.'),
              ),
            ]);
          }
          final avg = (list.map((g) => g.percentage).reduce((a, b) => a + b) / list.length).round();
          final passed = list.where((g) => g.passed).length;
          return ListView(padding: const EdgeInsets.all(16), children: [
            Row(children: [
              Expanded(child: StatTile(icon: FontAwesomeIcons.chartLine, value: '$avg%', label: 'Promedio', color: AppColors.primaryLight)),
              const SizedBox(width: 12),
              Expanded(child: StatTile(icon: FontAwesomeIcons.circleCheck, value: '$passed/${list.length}', label: 'Aprobadas', color: AppColors.success)),
            ]),
            const SizedBox(height: 16),
            for (final g in list)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(children: [
                      SizedBox(
                        width: 58,
                        height: 58,
                        child: Stack(alignment: Alignment.center, children: [
                          CircularProgressIndicator(
                            value: g.percentage / 100,
                            strokeWidth: 6,
                            backgroundColor: p.border,
                            color: g.passed ? AppColors.success : AppColors.danger,
                          ),
                          Text('${g.percentage}%', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13)),
                        ]),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(g.evaluation, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800)),
                          const SizedBox(height: 2),
                          Text(g.course, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                          const SizedBox(height: 6),
                          Text('${g.score}/${g.totalPoints} pts · intento ${g.attempt} · ${Fmt.date(g.completedAt)}', style: TextStyle(color: p.inkMuted, fontSize: 12)),
                        ]),
                      ),
                      SoftTag(label: g.passed ? 'Aprobado' : 'Reprobado', color: g.passed ? AppColors.success : AppColors.danger),
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
