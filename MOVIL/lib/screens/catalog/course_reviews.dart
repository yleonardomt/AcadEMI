import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../models/course.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';

/// Resumen de valoraciones, reseña propia (si está inscrito) y lista de reseñas.
class CourseReviews extends StatefulWidget {
  const CourseReviews({super.key, required this.course, required this.onChanged});

  final Course course;
  final Future<void> Function() onChanged;

  @override
  State<CourseReviews> createState() => _CourseReviewsState();
}

class _CourseReviewsState extends State<CourseReviews> {
  late int _rating = widget.course.userReview?.rating ?? 0;
  late final TextEditingController _comment = TextEditingController(text: widget.course.userReview?.comment ?? '');
  bool _saving = false;
  bool _editing = false;

  @override
  void dispose() {
    _comment.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_rating == 0) {
      showToast(context, 'Selecciona una valoración de 1 a 5 estrellas.', error: true);
      return;
    }
    setState(() => _saving = true);
    try {
      final msg = await context.read<AuthProvider>().api.saveReview(widget.course.id, _rating, _comment.text.trim());
      if (mounted) {
        showToast(context, msg, success: true);
        setState(() => _editing = false);
      }
      await widget.onChanged();
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _saving = false);
  }

  Future<void> _delete(Review review) async {
    final ok = await confirmDialog(context,
        title: 'Eliminar reseña', message: '¿Seguro que quieres eliminar tu reseña?', confirmLabel: 'Eliminar', danger: true);
    if (!ok || !mounted) return;
    try {
      await context.read<AuthProvider>().api.deleteReview(review.id);
      _rating = 0;
      _comment.clear();
      await widget.onChanged();
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  Future<void> _report(Review review) async {
    final reason = TextEditingController();
    final send = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Reportar reseña'),
        content: TextField(controller: reason, maxLines: 3, decoration: const InputDecoration(hintText: 'Cuéntanos qué está mal…')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(
            style: FilledButton.styleFrom(minimumSize: const Size(0, 42)),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Reportar'),
          ),
        ],
      ),
    );
    if (send != true || reason.text.trim().isEmpty || !mounted) return;
    try {
      final msg = await context.read<AuthProvider>().api.report('review', review.id, reason.text.trim());
      if (mounted) showToast(context, msg, success: true);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  Widget _stars(int value, {ValueChanged<int>? onTap, double size = 30}) => Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(
          5,
          (i) => GestureDetector(
            onTap: onTap == null ? null : () => onTap(i + 1),
            child: Padding(
              padding: const EdgeInsets.only(right: 6),
              child: FaIcon(i < value ? FontAwesomeIcons.solidStar : FontAwesomeIcons.star, size: size, color: AppColors.secondaryDark),
            ),
          ),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final course = widget.course;
    final user = context.watch<AuthProvider>().user!;
    final mine = course.userReview;
    final canReview = user.isStudent && course.isEnrolled;
    final maxCount = course.ratingDistribution.values.fold<int>(1, (a, b) => b > a ? b : a);

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
        Column(children: [
          Text(course.rating.toStringAsFixed(1), style: const TextStyle(fontSize: 42, fontWeight: FontWeight.w800, height: 1)),
          const SizedBox(height: 6),
          RatingStars(rating: course.rating),
          const SizedBox(height: 4),
          Text('${course.reviewsCount} ${course.reviewsCount == 1 ? 'reseña' : 'reseñas'}', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
        ]),
        const SizedBox(width: 22),
        Expanded(
          child: Column(children: [
            for (var star = 5; star >= 1; star--)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(children: [
                  Text('$star', style: TextStyle(color: p.inkMuted, fontSize: 12, fontWeight: FontWeight.w700)),
                  const SizedBox(width: 4),
                  const FaIcon(FontAwesomeIcons.solidStar, size: 10, color: AppColors.secondaryDark),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: LinearProgressIndicator(
                        value: (course.ratingDistribution[star] ?? 0) / maxCount,
                        minHeight: 7,
                        backgroundColor: p.isDark ? p.border : AppColors.primaryLighter,
                        color: AppColors.secondary,
                      ),
                    ),
                  ),
                  SizedBox(width: 26, child: Text('${course.ratingDistribution[star] ?? 0}', textAlign: TextAlign.right, style: TextStyle(color: p.inkMuted, fontSize: 12))),
                ]),
              ),
          ]),
        ),
      ]),
      const SizedBox(height: 18),
      if (canReview)
        FormCard(
          title: mine == null || _editing ? 'Deja tu reseña' : 'Tu reseña',
          icon: FontAwesomeIcons.penToSquare,
          child: mine != null && !_editing
              ? Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  _stars(mine.rating, size: 18),
                  if (mine.comment.isNotEmpty) ...[const SizedBox(height: 8), Text(mine.comment, style: const TextStyle(height: 1.45))],
                  const SizedBox(height: 12),
                  Row(children: [
                    TextButton.icon(
                        onPressed: () => setState(() => _editing = true),
                        icon: const FaIcon(FontAwesomeIcons.pen, size: 13),
                        label: const Text('Editar')),
                    TextButton.icon(
                        onPressed: () => _delete(mine),
                        style: TextButton.styleFrom(foregroundColor: AppColors.danger),
                        icon: const FaIcon(FontAwesomeIcons.trash, size: 13),
                        label: const Text('Eliminar')),
                  ]),
                ])
              : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  _stars(_rating, onTap: (v) => setState(() => _rating = v)),
                  const SizedBox(height: 14),
                  TextField(controller: _comment, maxLines: 3, decoration: const InputDecoration(hintText: 'Cuéntanos tu experiencia (opcional)')),
                  const SizedBox(height: 14),
                  LoadingButton(label: 'Publicar reseña', icon: FontAwesomeIcons.paperPlane, loading: _saving, onPressed: _save),
                ]),
        ),
      if (course.reviews.isEmpty && mine == null)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: Center(child: Text('Aún no hay reseñas. ¡Sé el primero!', style: TextStyle(color: p.inkMuted))),
        ),
      for (final r in course.reviews)
        Padding(
          padding: const EdgeInsets.only(top: 14),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            UserAvatar(name: r.student, url: r.picture, radius: 20),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(child: Text(r.student, style: const TextStyle(fontWeight: FontWeight.w800))),
                  Text(Fmt.ago(r.createdAt), style: TextStyle(color: p.inkMuted, fontSize: 12)),
                ]),
                const SizedBox(height: 3),
                RatingStars(rating: r.rating.toDouble(), size: 12),
                if (r.comment.isNotEmpty) ...[const SizedBox(height: 6), Text(r.comment, style: const TextStyle(height: 1.45))],
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton.icon(
                    onPressed: () => _report(r),
                    style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 30), foregroundColor: p.inkMuted),
                    icon: const FaIcon(FontAwesomeIcons.flag, size: 11),
                    label: const Text('Reportar', style: TextStyle(fontSize: 12)),
                  ),
                ),
              ]),
            ),
          ]),
        ),
    ]);
  }
}
