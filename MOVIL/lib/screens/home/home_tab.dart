import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/nav.dart';
import '../../models/course.dart';
import '../../providers/auth_provider.dart';
import '../../providers/shell_nav.dart';
import '../../services/services.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../../widgets/header_actions.dart';
import '../catalog/course_detail_screen.dart';
import '../learning/learn_screen.dart';

/// Portada del estudiante: saludo, progreso, cursos para continuar y catálogo destacado.
class HomeTab extends StatelessWidget {
  const HomeTab({super.key});

  static const catalogTab = 1;

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthProvider>();
    return Scaffold(
      body: AsyncBody<HomeData>(
        load: auth.api.home,
        builder: (context, data, reload) => _HomeContent(data: data, reload: reload),
      ),
    );
  }
}

class _HomeContent extends StatelessWidget {
  const _HomeContent({required this.data, required this.reload});

  final HomeData data;
  final Future<void> Function() reload;

  void _openCourse(BuildContext context, Course c) async {
    await push(context, CourseDetailScreen(courseId: c.id));
    reload();
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user!;
    final p = context.palette;
    final firstName = Fmt.firstName(user.name);
    final stats = data.stats;

    Widget carousel(List<Course> courses) => SizedBox(
          height: 288,
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            scrollDirection: Axis.horizontal,
            itemCount: courses.length,
            separatorBuilder: (_, _) => const SizedBox(width: 14),
            itemBuilder: (_, i) => CourseCard(course: courses[i], onTap: () => _openCourse(context, courses[i])),
          ),
        );

    return ListView(padding: EdgeInsets.zero, children: [
      GradientHeader(
        padding: EdgeInsets.fromLTRB(20, MediaQuery.of(context).padding.top + 8, 8, 26),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const BrandLogo(light: true, size: 22),
            const Spacer(),
            const HeaderActions(color: Colors.white),
          ]),
          const SizedBox(height: 18),
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Hola, $firstName',
                  style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
              const SizedBox(height: 4),
              Text('¿Qué quieres aprender hoy?', style: TextStyle(color: Colors.white.withValues(alpha: 0.82), fontSize: 15)),
              const SizedBox(height: 18),
              GestureDetector(
                onTap: () => context.read<ShellNav>().openCatalog(HomeTab.catalogTab),
                child: Container(
                  height: 50,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(14)),
                  child: Row(children: [
                    FaIcon(FontAwesomeIcons.magnifyingGlass, size: 16, color: p.inkMuted),
                    const SizedBox(width: 12),
                    Text('Buscar cursos, docentes o temas', style: TextStyle(color: p.inkMuted, fontSize: 14.5)),
                  ]),
                ),
              ),
            ]),
          ),
        ]),
      ),

      if (data.emiDiscount != null)
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(gradient: AppColors.accentGradient, borderRadius: BorderRadius.circular(18)),
            child: Row(children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.35), borderRadius: BorderRadius.circular(14)),
                child: const Center(child: FaIcon(FontAwesomeIcons.percent, size: 20, color: AppColors.primaryDark)),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('${data.emiDiscount!.toStringAsFixed(0)}% de descuento EMI',
                      style: const TextStyle(color: AppColors.primaryDark, fontWeight: FontWeight.w800, fontSize: 16)),
                  const SizedBox(height: 2),
                  const Text('En tu primera compra, aplicado automáticamente.',
                      style: TextStyle(color: AppColors.primaryDark, fontSize: 13)),
                ]),
              ),
            ]),
          ),
        ),

      if (stats != null)
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
          child: GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 2.15,
            children: [
              StatTile(icon: FontAwesomeIcons.bookOpenReader, value: '${stats['enrolled']}', label: 'Mis cursos', color: AppColors.primaryLight),
              StatTile(icon: FontAwesomeIcons.circleCheck, value: '${stats['completed']}', label: 'Completados', color: AppColors.success),
              StatTile(icon: FontAwesomeIcons.chartLine, value: '${stats['avg_progress']}%', label: 'Progreso', color: AppColors.orange),
              StatTile(icon: FontAwesomeIcons.certificate, value: '${stats['certificates']}', label: 'Certificados', color: AppColors.purple),
            ],
          ),
        ),

      if (data.continueLearning.isNotEmpty) ...[
        const SectionHeader(title: 'Continúa aprendiendo'),
        SizedBox(
          height: 172,
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            scrollDirection: Axis.horizontal,
            itemCount: data.continueLearning.length,
            separatorBuilder: (_, _) => const SizedBox(width: 14),
            itemBuilder: (context, i) {
              final e = data.continueLearning[i];
              return SizedBox(
                width: 268,
                child: Card(
                  clipBehavior: Clip.antiAlias,
                  child: InkWell(
                    onTap: () async {
                      await push(context, LearnScreen(courseId: e.courseId));
                      reload();
                    },
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Row(children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(12),
                            child: SizedBox(width: 56, height: 56, child: CourseImage(url: e.image, category: e.category)),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(e.title,
                                maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800, height: 1.25)),
                          ),
                        ]),
                        const Spacer(),
                        Row(children: [
                          Text('${e.progress}% completado', style: TextStyle(color: p.inkMuted, fontSize: 12.5, fontWeight: FontWeight.w600)),
                          const Spacer(),
                          Text('Continuar', style: TextStyle(color: p.primaryText, fontWeight: FontWeight.w700, fontSize: 13)),
                          const SizedBox(width: 6),
                          FaIcon(FontAwesomeIcons.circleArrowRight, size: 14, color: p.primaryText),
                        ]),
                        const SizedBox(height: 8),
                        ProgressBar(value: e.progress),
                      ]),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],

      if (data.categories.isNotEmpty) ...[
        const SectionHeader(title: 'Explora por categoría'),
        SizedBox(
          height: 92,
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            scrollDirection: Axis.horizontal,
            itemCount: data.categories.length,
            separatorBuilder: (_, _) => const SizedBox(width: 12),
            itemBuilder: (context, i) {
              final c = data.categories[i];
              final tints = [AppColors.primaryLight, AppColors.teal, AppColors.purple, AppColors.orange, AppColors.pink];
              final color = tints[i % tints.length];
              return InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: () => context.read<ShellNav>().openCatalog(HomeTab.catalogTab, category: c.id),
                child: Container(
                  width: 96,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: p.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: p.border),
                  ),
                  child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                    Container(
                      width: 38,
                      height: 38,
                      decoration: BoxDecoration(color: color.withValues(alpha: 0.14), shape: BoxShape.circle),
                      child: Center(child: FaIcon(categoryIcon(c.name), size: 16, color: color)),
                    ),
                    const SizedBox(height: 6),
                    Text(c.name, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                  ]),
                ),
              );
            },
          ),
        ),
      ],

      if (data.featured.isNotEmpty) ...[
        SectionHeader(
          title: 'Cursos destacados',
          subtitle: 'Seleccionados por nuestro equipo',
          onSeeAll: () => context.read<ShellNav>().openCatalog(HomeTab.catalogTab),
        ),
        carousel(data.featured),
      ],
      if (data.bestsellers.isNotEmpty) ...[
        const SectionHeader(title: 'Más populares', subtitle: 'Lo que más eligen los estudiantes'),
        carousel(data.bestsellers),
      ],
      if (data.newest.isNotEmpty) ...[
        SectionHeader(
          title: 'Recién agregados',
          onSeeAll: () => context.read<ShellNav>().openCatalog(HomeTab.catalogTab),
        ),
        carousel(data.newest),
      ],
      const SizedBox(height: 90),
    ]);
  }
}
