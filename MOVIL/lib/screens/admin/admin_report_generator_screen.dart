import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';

/// RF-49: reportes de usuarios, cursos, ventas y rendimiento académico por rango de fechas.
class AdminReportGeneratorScreen extends StatefulWidget {
  const AdminReportGeneratorScreen({super.key});

  @override
  State<AdminReportGeneratorScreen> createState() => _AdminReportGeneratorScreenState();
}

class _AdminReportGeneratorScreenState extends State<AdminReportGeneratorScreen> {
  final _from = TextEditingController();
  final _to = TextEditingController();
  Map<String, dynamic>? _report;
  bool _loading = false;

  @override
  void dispose() {
    _from.dispose();
    _to.dispose();
    super.dispose();
  }

  Future<void> _pick(TextEditingController c) async {
    final d = await showDatePicker(context: context, initialDate: DateTime.now(), firstDate: DateTime(2020), lastDate: DateTime(2100), locale: const Locale('es'));
    if (d != null) c.text = '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
  }

  Future<void> _generate() async {
    setState(() => _loading = true);
    try {
      final r = await context.read<AuthProvider>().api.adminGenerateReport(_from.text.isEmpty ? null : _from.text, _to.text.isEmpty ? null : _to.text);
      if (mounted) setState(() => _report = r['report'] as Map<String, dynamic>);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final r = _report;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Generar reportes')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        FormCard(
          title: 'Periodo',
          icon: FontAwesomeIcons.calendarDays,
          child: Column(children: [
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(child: GestureDetector(onTap: () => _pick(_from), child: AbsorbPointer(child: AppTextField(controller: _from, label: 'Desde', hint: 'AAAA-MM-DD', icon: FontAwesomeIcons.calendarDay)))),
              const SizedBox(width: 12),
              Expanded(child: GestureDetector(onTap: () => _pick(_to), child: AbsorbPointer(child: AppTextField(controller: _to, label: 'Hasta', hint: 'AAAA-MM-DD', icon: FontAwesomeIcons.calendarDay)))),
            ]),
            const SizedBox(height: 6),
            Align(alignment: Alignment.centerLeft, child: Text('Déjalos vacíos para todo el historial.', style: TextStyle(color: p.inkMuted, fontSize: 12.5))),
            const SizedBox(height: 14),
            LoadingButton(label: 'Generar reporte', icon: FontAwesomeIcons.fileLines, loading: _loading, onPressed: _generate),
          ]),
        ),
        if (r != null) ...[
          const SectionHeader(title: 'Resultado', padding: EdgeInsets.fromLTRB(4, 24, 4, 10)),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 2.15,
            children: [
              StatTile(icon: FontAwesomeIcons.users, value: '${asInt(r['users'])}', label: 'Usuarios nuevos', color: AppColors.primaryLight),
              StatTile(icon: FontAwesomeIcons.userGraduate, value: '${asInt(r['students'])}', label: 'Estudiantes', color: AppColors.teal),
              StatTile(icon: FontAwesomeIcons.chalkboardUser, value: '${asInt(r['teachers'])}', label: 'Docentes', color: AppColors.purple),
              StatTile(icon: FontAwesomeIcons.chalkboard, value: '${asInt(r['courses'])}', label: 'Cursos creados', color: AppColors.orange),
              StatTile(icon: FontAwesomeIcons.cartShopping, value: '${asInt(r['sales'])}', label: 'Ventas', color: AppColors.pink),
              StatTile(icon: FontAwesomeIcons.coins, value: Fmt.amount(asDouble(r['revenue'])), label: 'Ingresos', color: AppColors.success),
              StatTile(icon: FontAwesomeIcons.bookOpenReader, value: '${asInt(r['enrollments'])}', label: 'Inscripciones', color: AppColors.info),
              StatTile(icon: FontAwesomeIcons.graduationCap, value: '${asInt(r['completed_enrollments'])}', label: 'Cursos completados', color: AppColors.success),
              StatTile(icon: FontAwesomeIcons.listCheck, value: '${asInt(r['passed_evaluations'])}/${asInt(r['evaluations'])}', label: 'Evaluaciones aprobadas', color: AppColors.purple),
              StatTile(icon: FontAwesomeIcons.chartLine, value: '${asInt(r['avg_score'])}%', label: 'Nota promedio', color: AppColors.orange),
            ],
          ),
          if (asList(r['top_courses']).isNotEmpty) ...[
            const SectionHeader(title: 'Cursos más vendidos', padding: EdgeInsets.fromLTRB(4, 24, 4, 10)),
            for (final c in asList(r['top_courses']))
              Card(child: ListTile(title: Text(asString(c['title']), style: const TextStyle(fontWeight: FontWeight.w700)), subtitle: Text('${asInt(c['sales'])} ventas'), trailing: Text(Fmt.amount(asDouble(c['revenue'])), style: const TextStyle(fontWeight: FontWeight.w800)))),
          ],
        ],
      ]),
    );
  }
}
