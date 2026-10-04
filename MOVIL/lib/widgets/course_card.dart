import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../core/theme/app_colors.dart';
import '../core/utils/format.dart';
import '../models/course.dart';
import 'common.dart';

/// Imagen del curso; si no tiene, un degradado de marca con el ícono de su categoría.
class CourseImage extends StatelessWidget {
  const CourseImage({super.key, required this.url, this.category, this.height, this.radius = 0});

  final String? url;
  final String? category;
  final double? height;
  final double radius;

  static const _gradients = [
    [AppColors.primaryDark, AppColors.primaryVivid],
    [AppColors.primary, AppColors.teal],
    [AppColors.primaryLight, AppColors.purple],
    [AppColors.primaryDark, AppColors.pink],
  ];

  @override
  Widget build(BuildContext context) {
    final colors = _gradients[(category ?? '').length % _gradients.length];
    final placeholder = Container(
      height: height,
      width: double.infinity,
      decoration: BoxDecoration(gradient: LinearGradient(colors: colors, begin: Alignment.topLeft, end: Alignment.bottomRight)),
      child: Center(child: FaIcon(categoryIcon(category), size: 34, color: Colors.white.withValues(alpha: 0.85))),
    );
    final Widget image = url == null
        ? placeholder
        : CachedNetworkImage(
            imageUrl: url!,
            height: height,
            width: double.infinity,
            fit: BoxFit.cover,
            placeholder: (_, _) => placeholder,
            errorWidget: (_, _, _) => placeholder,
          );
    return radius == 0 ? image : ClipRRect(borderRadius: BorderRadius.circular(radius), child: image);
  }
}

/// Tarjeta vertical (carruseles de la portada y del catálogo).
class CourseCard extends StatelessWidget {
  const CourseCard({super.key, required this.course, required this.onTap, this.width = 250});

  final Course course;
  final VoidCallback onTap;
  final double width;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return SizedBox(
      width: width,
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Stack(children: [
              CourseImage(url: course.image, category: course.category, height: 128),
              if (course.coupon != null)
                Positioned(
                  top: 10,
                  left: 10,
                  child: SoftTag(label: 'Oferta ${course.coupon!.label}', color: AppColors.pink, icon: FontAwesomeIcons.tag),
                ),
              if (course.isFeatured && course.coupon == null)
                const Positioned(
                  top: 10,
                  left: 10,
                  child: SoftTag(label: 'Destacado', color: AppColors.secondaryDark, icon: FontAwesomeIcons.solidStar),
                ),
            ]),
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                LevelBadge(level: course.level, label: course.levelLabel),
                const SizedBox(height: 8),
                Text(course.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15, height: 1.25)),
                const SizedBox(height: 4),
                Text(course.teacher, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                const SizedBox(height: 8),
                Row(children: [
                  if (course.reviewsCount > 0) ...[
                    const FaIcon(FontAwesomeIcons.solidStar, size: 12, color: AppColors.secondaryDark),
                    const SizedBox(width: 4),
                    Text(course.rating.toStringAsFixed(1), style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5)),
                    Text(' (${course.reviewsCount})', style: TextStyle(color: p.inkMuted, fontSize: 12)),
                  ] else
                    Text('Nuevo', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                  const Spacer(),
                  if (course.isEnrolled)
                    const SoftTag(label: 'Inscrito', color: AppColors.success, icon: FontAwesomeIcons.check)
                  else
                    Text(course.isFree ? 'Gratis' : Fmt.amount(course.price),
                        style: TextStyle(
                            fontWeight: FontWeight.w800,
                            fontSize: 15,
                            color: course.isFree ? AppColors.success : p.primaryText)),
                ]),
              ]),
            ),
          ]),
        ),
      ),
    );
  }
}

/// Tarjeta horizontal (listas: catálogo, favoritos, resultados de búsqueda).
class CourseListTile extends StatelessWidget {
  const CourseListTile({super.key, required this.course, required this.onTap, this.onFavorite, this.trailing});

  final Course course;
  final VoidCallback onTap;
  final VoidCallback? onFavorite;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: IntrinsicHeight(
          child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            SizedBox(
              width: 118,
              child: Stack(fit: StackFit.expand, children: [
                CourseImage(url: course.image, category: course.category),
                if (course.coupon != null)
                  Positioned(
                    top: 8,
                    left: 8,
                    child: SoftTag(label: course.coupon!.label, color: AppColors.pink, icon: FontAwesomeIcons.tag),
                  ),
              ]),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 12, 8, 12),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    LevelBadge(level: course.level, label: course.levelLabel),
                    const Spacer(),
                    if (trailing != null) trailing!,
                    if (onFavorite != null)
                      InkWell(
                        onTap: onFavorite,
                        borderRadius: BorderRadius.circular(20),
                        child: Padding(
                          padding: const EdgeInsets.all(4),
                          child: FaIcon(
                            course.isFavorite ? FontAwesomeIcons.solidHeart : FontAwesomeIcons.heart,
                            size: 16,
                            color: course.isFavorite ? AppColors.danger : p.inkMuted,
                          ),
                        ),
                      ),
                  ]),
                  const SizedBox(height: 6),
                  Text(course.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14.5, height: 1.25)),
                  const SizedBox(height: 3),
                  Text(course.teacher, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                  const Spacer(),
                  Row(children: [
                    if (course.reviewsCount > 0) ...[
                      const FaIcon(FontAwesomeIcons.solidStar, size: 11, color: AppColors.secondaryDark),
                      const SizedBox(width: 4),
                      Text(course.rating.toStringAsFixed(1), style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                      const SizedBox(width: 10),
                    ],
                    FaIcon(FontAwesomeIcons.userGroup, size: 11, color: p.inkMuted),
                    const SizedBox(width: 4),
                    Text('${course.studentsCount}', style: TextStyle(color: p.inkMuted, fontSize: 12)),
                    const Spacer(),
                    if (course.isEnrolled)
                      const SoftTag(label: 'Inscrito', color: AppColors.success)
                    else
                      Text(course.isFree ? 'Gratis' : Fmt.amount(course.price),
                          style: TextStyle(
                              fontWeight: FontWeight.w800,
                              fontSize: 14.5,
                              color: course.isFree ? AppColors.success : p.primaryText)),
                  ]),
                ]),
              ),
            ),
          ]),
        ),
      ),
    );
  }
}
