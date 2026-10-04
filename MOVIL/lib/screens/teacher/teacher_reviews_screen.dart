import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../models/course.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';

class TeacherReviewsScreen extends StatelessWidget {
  const TeacherReviewsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Reseñas de mis cursos')),
      body: AsyncBody<List<Review>>(
        load: api.teacherReviews,
        builder: (context, list, reload) {
          if (list.isEmpty) {
            return ListView(children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: const EmptyState(icon: FontAwesomeIcons.solidStar, title: 'Sin reseñas todavía', message: 'Las valoraciones de tus estudiantes aparecerán aquí.'),
              ),
            ]);
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final r = list[i];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    UserAvatar(name: r.student, url: r.picture, radius: 21),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Row(children: [
                          Expanded(child: Text(r.student, style: const TextStyle(fontWeight: FontWeight.w800))),
                          Text(Fmt.ago(r.createdAt), style: TextStyle(color: p.inkMuted, fontSize: 12)),
                        ]),
                        const SizedBox(height: 3),
                        RatingStars(rating: r.rating.toDouble(), size: 13),
                        if (r.comment.isNotEmpty) ...[const SizedBox(height: 8), Text(r.comment, style: const TextStyle(height: 1.45))],
                        const SizedBox(height: 8),
                        Text(r.course ?? '', style: TextStyle(color: p.primaryText, fontSize: 12.5, fontWeight: FontWeight.w700)),
                      ]),
                    ),
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
