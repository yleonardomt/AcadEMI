import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_colors.dart';
import '../../models/course.dart';
import '../../widgets/common.dart';

/// Información del docente del curso (bio, especialidad, estadísticas y enlaces).
Future<void> showTeacherProfile(BuildContext context, Course course) => showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => _TeacherProfile(course: course),
    );

class _TeacherProfile extends StatelessWidget {
  const _TeacherProfile({required this.course});

  final Course course;

  @override
  Widget build(BuildContext context) {
    final t = course.teacherInfo!;
    final p = context.palette;

    Widget stat(FaIconData icon, String value, String label, Color color) => Expanded(
          child: Column(children: [
            FaIcon(icon, size: 18, color: color),
            const SizedBox(height: 6),
            Text(value, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
            Text(label, style: TextStyle(color: p.inkMuted, fontSize: 12)),
          ]),
        );

    Widget link(FaIconData icon, String label, String url) => Padding(
          padding: const EdgeInsets.only(top: 10),
          child: OutlinedButton.icon(
            style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(46)),
            onPressed: () => launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication),
            icon: FaIcon(icon, size: 15),
            label: Text(label),
          ),
        );

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.7,
      maxChildSize: 0.92,
      minChildSize: 0.4,
      builder: (context, scroll) => ListView(controller: scroll, padding: const EdgeInsets.fromLTRB(24, 0, 24, 32), children: [
        Center(child: UserAvatar(name: t.name, url: t.picture, radius: 44)),
        const SizedBox(height: 14),
        Center(child: Text(t.name, textAlign: TextAlign.center, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800))),
        if (t.specialty.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Center(child: Text(t.specialty, style: TextStyle(color: p.primaryText, fontWeight: FontWeight.w700))),
          ),
        if (t.institution.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Center(child: Text(t.institution, style: TextStyle(color: p.inkMuted))),
          ),
        const SizedBox(height: 20),
        Container(
          padding: const EdgeInsets.symmetric(vertical: 16),
          decoration: BoxDecoration(color: p.surfaceSoft, borderRadius: BorderRadius.circular(16)),
          child: Row(children: [
            stat(FontAwesomeIcons.chalkboard, '${t.coursesCount}', 'Cursos', AppColors.primaryLight),
            stat(FontAwesomeIcons.userGroup, '${t.studentsCount}', 'Estudiantes', AppColors.teal),
            stat(FontAwesomeIcons.solidStar, t.rating > 0 ? t.rating.toStringAsFixed(1) : '—', 'Valoración', AppColors.secondaryDark),
          ]),
        ),
        if (t.experienceYears.isNotEmpty) ...[
          const SizedBox(height: 16),
          Row(children: [
            const FaIcon(FontAwesomeIcons.briefcase, size: 15, color: AppColors.orange),
            const SizedBox(width: 10),
            Text('Experiencia: ${t.experienceYears} años', style: const TextStyle(fontWeight: FontWeight.w600)),
          ]),
        ],
        if (t.bio.isNotEmpty) ...[
          const SizedBox(height: 18),
          const Text('Sobre el docente', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Text(t.bio, style: const TextStyle(height: 1.55)),
        ],
        if (t.linkedin.isNotEmpty) link(FontAwesomeIcons.linkedin, 'LinkedIn', t.linkedin),
        if (t.website.isNotEmpty) link(FontAwesomeIcons.globe, 'Sitio web', t.website),
      ]),
    );
  }
}
