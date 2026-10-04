import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';

/// RF-16: estadísticas de estudiantes, progreso, evaluaciones, valoraciones y ventas.
class CourseStatsScreen extends StatelessWidget {
  const CourseStatsScreen({super.key, required this.courseId});

  final int courseId;

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Estadísticas del curso')),
      body: AsyncBody<Map<String, dynamic>>(
        load: () => api.courseStats(courseId),
        builder: (context, data, reload) {
          final s = data['stats'] as Map<String, dynamic>;
          final dist = (s['rating_distribution'] as Map?) ?? {};
          final reviews = asInt(s['reviews']);
          Widget tile(FaIconData i, String v, String l, Color c) => StatTile(icon: i, value: v, label: l, color: c);
          return ListView(padding: const EdgeInsets.all(16), children: [
            Text((data['course'] as Map)['title'] as String, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800)),
            const SizedBox(height: 14),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 2.15,
              children: [
                tile(FontAwesomeIcons.userGroup, '${asInt(s['total_students'])}', 'Estudiantes', AppColors.teal),
                tile(FontAwesomeIcons.graduationCap, '${asInt(s['completed'])}', 'Completaron (${asInt(s['completion_rate'])}%)', AppColors.success),
                tile(FontAwesomeIcons.personRunning, '${asInt(s['in_progress'])}', 'En progreso', AppColors.warning),
                tile(FontAwesomeIcons.chartLine, '${asInt(s['avg_progress'])}%', 'Progreso medio', AppColors.orange),
                tile(FontAwesomeIcons.listCheck, '${asInt(s['evaluations_taken'])}', 'Evaluaciones', AppColors.purple),
                tile(FontAwesomeIcons.circleCheck, '${asInt(s['pass_rate'])}%', 'Aprobación', AppColors.success),
                tile(FontAwesomeIcons.triangleExclamation, '${asInt(s['incidents'])}', 'Incidencias', AppColors.danger),
                tile(FontAwesomeIcons.cartShopping, '${asInt(s['sales'])}', 'Ventas', AppColors.primaryLight),
              ],
            ),
            const SizedBox(height: 12),
            StatTile(icon: FontAwesomeIcons.coins, value: Fmt.amount(asDouble(s['revenue'])), label: 'Ingresos del curso', color: AppColors.success),
            const SectionHeader(title: 'Valoraciones', padding: EdgeInsets.fromLTRB(4, 24, 4, 10)),
            FormCard2(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Text('${asDouble(s['avg_rating'])}', style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w800)),
                  const SizedBox(width: 12),
                  RatingStars(rating: asDouble(s['avg_rating']), size: 16),
                  const Spacer(),
                  Text('$reviews reseñas', style: TextStyle(color: p.inkMuted)),
                ]),
                const SizedBox(height: 12),
                for (var star = 5; star >= 1; star--)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 3),
                    child: Row(children: [
                      SizedBox(width: 14, child: Text('$star', style: TextStyle(color: p.inkMuted, fontWeight: FontWeight.w700))),
                      const FaIcon(FontAwesomeIcons.solidStar, size: 11, color: AppColors.secondaryDark),
                      const SizedBox(width: 8),
                      Expanded(child: ProgressBar(value: reviews == 0 ? 0 : (asInt(dist['$star']) * 100 / reviews).round(), height: 7, color: AppColors.secondary)),
                      SizedBox(width: 28, child: Text('${asInt(dist['$star'])}', textAlign: TextAlign.right, style: TextStyle(color: p.inkMuted, fontSize: 12))),
                    ]),
                  ),
              ]),
            ),
          ]);
        },
      ),
    );
  }
}

/// Tarjeta simple con borde y sombra suave.
class FormCard2 extends StatelessWidget {
  const FormCard2({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(18), border: Border.all(color: p.border), boxShadow: p.shadow),
      child: child,
    );
  }
}

/// RF-32: resultados, calificaciones e incidencias registradas en las evaluaciones.
class CourseResultsScreen extends StatelessWidget {
  const CourseResultsScreen({super.key, required this.courseId});

  final int courseId;

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Resultados e incidencias')),
      body: AsyncBody<Map<String, dynamic>>(
        load: () => api.courseResults(courseId),
        builder: (context, data, reload) {
          final results = asList(data['results']);
          if (results.isEmpty) {
            return ListView(children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: const EmptyState(icon: FontAwesomeIcons.clipboardCheck, title: 'Sin evaluaciones realizadas', message: 'Cuando los estudiantes rindan cuestionarios o exámenes, verás sus resultados aquí.'),
              ),
            ]);
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: results.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final r = results[i];
              final incidents = asList(r['incidents']);
              final passed = asBool(r['passed']);
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Expanded(child: Text(asString(r['student']), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15))),
                      SoftTag(label: passed ? 'Aprobado' : 'Reprobado', color: passed ? AppColors.success : AppColors.danger),
                    ]),
                    const SizedBox(height: 4),
                    Text(asString(r['evaluation']), style: TextStyle(color: p.inkMuted)),
                    const SizedBox(height: 10),
                    Text('${asInt(r['score'])}/${asInt(r['total_points'])} pts (${asInt(r['percentage'])}%) · intento ${asInt(r['attempt'])} · ${asInt(r['time_spent']) ~/ 60} min · ${Fmt.dateTime(asDate(r['completed_at']))}',
                        style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                    if (incidents.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      for (final inc in incidents)
                        Container(
                          margin: const EdgeInsets.only(top: 6),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(color: AppColors.warning.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(10)),
                          child: Row(children: [
                            const FaIcon(FontAwesomeIcons.triangleExclamation, size: 13, color: AppColors.warning),
                            const SizedBox(width: 8),
                            Expanded(child: Text('${asString(inc['type_label'])}: ${asString(inc['description'])}', style: const TextStyle(fontSize: 12.5, height: 1.35))),
                          ]),
                        ),
                    ],
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
