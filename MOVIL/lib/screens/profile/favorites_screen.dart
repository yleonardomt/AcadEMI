import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/utils/nav.dart';
import '../../models/course.dart';
import '../../providers/auth_provider.dart';
import '../../providers/shell_nav.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../catalog/course_detail_screen.dart';

class FavoritesScreen extends StatelessWidget {
  const FavoritesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    return Scaffold(
      appBar: AppBar(title: const Text('Mis favoritos')),
      body: AsyncBody<List<Course>>(
        load: api.favorites,
        builder: (context, courses, reload) {
          if (courses.isEmpty) {
            return ListView(children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: EmptyState(
                  icon: FontAwesomeIcons.heart,
                  title: 'Aún no tienes favoritos',
                  message: 'Toca el corazón en un curso para guardarlo aquí.',
                  actionLabel: 'Explorar cursos',
                  onAction: () {
                    Navigator.of(context).popUntil((r) => r.isFirst);
                    context.read<ShellNav>().openCatalog(1);
                  },
                ),
              ),
            ]);
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: courses.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final c = courses[i];
              return SizedBox(
                height: 132,
                child: CourseListTile(
                  course: c,
                  onFavorite: () async {
                    try {
                      await api.toggleFavorite(c.id);
                      await reload();
                    } catch (e) {
                      if (context.mounted) showToast(context, errorText(e), error: true);
                    }
                  },
                  onTap: () async {
                    await push(context, CourseDetailScreen(courseId: c.id));
                    reload();
                  },
                ),
              );
            },
          );
        },
      ),
    );
  }
}
