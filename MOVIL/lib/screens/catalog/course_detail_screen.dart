import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/nav.dart';
import '../../models/course.dart';
import '../../providers/auth_provider.dart';
import '../../providers/cart_provider.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../commerce/cart_screen.dart';
import '../learning/learn_screen.dart';
import '../learning/lesson_screen.dart';
import 'course_reviews.dart';
import 'teacher_profile_sheet.dart';

class CourseDetailScreen extends StatefulWidget {
  const CourseDetailScreen({super.key, required this.courseId});

  final int courseId;

  @override
  State<CourseDetailScreen> createState() => _CourseDetailScreenState();
}

class _CourseDetailScreenState extends State<CourseDetailScreen> {
  Course? _course;
  String? _error;
  bool _loading = true;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final c = await context.read<AuthProvider>().api.courseDetail(widget.courseId);
      if (mounted) {
        setState(() {
          _course = c;
          _error = null;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = errorText(e);
          _loading = false;
        });
      }
    }
  }

  Future<void> _toggleFavorite() async {
    final c = _course!;
    try {
      final fav = await context.read<AuthProvider>().api.toggleFavorite(c.id);
      if (mounted) {
        setState(() => _course = c.copyWith(isFavorite: fav));
        showToast(context, fav ? 'Agregado a favoritos' : 'Quitado de favoritos', success: fav);
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  Future<void> _addToCart({bool goToCart = false}) async {
    setState(() => _busy = true);
    try {
      await context.read<CartProvider>().add(_course!.id);
      if (!mounted) return;
      setState(() => _course = _course!.copyWith(inCart: true));
      if (goToCart) {
        await push(context, const CartScreen());
        _load();
      } else {
        showToast(context, 'Curso agregado al carrito', success: true);
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _busy = false);
  }

  Future<void> _reportCourse() async {
    final reason = TextEditingController();
    final send = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Reportar curso'),
        content: TextField(controller: reason, maxLines: 3, decoration: const InputDecoration(hintText: 'Describe el problema…')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(style: FilledButton.styleFrom(minimumSize: const Size(0, 42)), onPressed: () => Navigator.pop(ctx, true), child: const Text('Reportar')),
        ],
      ),
    );
    if (send != true || reason.text.trim().isEmpty || !mounted) return;
    try {
      final msg = await context.read<AuthProvider>().api.report('course', _course!.id, reason.text.trim());
      if (mounted) showToast(context, msg, success: true);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return Scaffold(appBar: AppBar(), body: const Center(child: CircularProgressIndicator()));
    if (_course == null) {
      return Scaffold(appBar: AppBar(), body: ErrorState(message: _error ?? '', onRetry: () {
        setState(() => _loading = true);
        _load();
      }));
    }
    final c = _course!;
    final user = context.watch<AuthProvider>().user!;
    final p = context.palette;

    return Scaffold(
      bottomNavigationBar: _BottomBar(course: c, busy: _busy, onAdd: _addToCart, onBuyNow: () => _addToCart(goToCart: true)),
      body: RefreshIndicator(
        onRefresh: _load,
        edgeOffset: 90,
        child: CustomScrollView(slivers: [
          SliverAppBar(
            pinned: true,
            expandedHeight: 240,
            backgroundColor: AppColors.primary,
            foregroundColor: Colors.white,
            leading: Padding(
              padding: const EdgeInsets.all(8),
              child: CircleAvatar(
                backgroundColor: Colors.black.withValues(alpha: 0.35),
                child: IconButton(
                  onPressed: () => Navigator.of(context).maybePop(),
                  icon: const FaIcon(FontAwesomeIcons.arrowLeft, size: 16, color: Colors.white),
                ),
              ),
            ),
            actions: [
              if (user.isStudent)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: CircleAvatar(
                    backgroundColor: Colors.black.withValues(alpha: 0.35),
                    child: IconButton(
                      onPressed: _toggleFavorite,
                      icon: FaIcon(c.isFavorite ? FontAwesomeIcons.solidHeart : FontAwesomeIcons.heart,
                          size: 16, color: c.isFavorite ? AppColors.danger : Colors.white),
                    ),
                  ),
                ),
              PopupMenuButton<String>(
                icon: const FaIcon(FontAwesomeIcons.ellipsisVertical, size: 18, color: Colors.white),
                onSelected: (v) {
                  if (v == 'report') _reportCourse();
                },
                itemBuilder: (_) => const [
                  PopupMenuItem(value: 'report', child: Row(children: [FaIcon(FontAwesomeIcons.flag, size: 14), SizedBox(width: 12), Text('Reportar curso')])),
                ],
              ),
              const SizedBox(width: 4),
            ],
            flexibleSpace: FlexibleSpaceBar(
              background: Stack(fit: StackFit.expand, children: [
                CourseImage(url: c.image, category: c.category),
                const DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [Colors.black26, Colors.transparent, Colors.black54]),
                  ),
                ),
              ]),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Wrap(spacing: 8, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
                  LevelBadge(level: c.level, label: c.levelLabel),
                  if (c.category != null) SoftTag(label: c.category!, color: AppColors.primaryLight, icon: categoryIcon(c.category)),
                  if (c.isFeatured) const SoftTag(label: 'Destacado', color: AppColors.secondaryDark, icon: FontAwesomeIcons.solidStar),
                ]),
                const SizedBox(height: 12),
                Text(c.title, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, letterSpacing: -0.5, height: 1.2)),
                const SizedBox(height: 12),
                InkWell(
                  onTap: c.teacherInfo == null ? null : () => showTeacherProfile(context, c),
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(children: [
                      UserAvatar(name: c.teacher, url: c.teacherInfo?.picture, radius: 18),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text('Docente', style: TextStyle(color: p.inkMuted, fontSize: 11.5)),
                          Text(c.teacher, style: const TextStyle(fontWeight: FontWeight.w800)),
                        ]),
                      ),
                      FaIcon(FontAwesomeIcons.chevronRight, size: 13, color: p.inkMuted),
                    ]),
                  ),
                ),
                const SizedBox(height: 16),
                Row(children: [
                  _Fact(icon: FontAwesomeIcons.solidStar, color: AppColors.secondaryDark, value: c.reviewsCount > 0 ? c.rating.toStringAsFixed(1) : '—', label: '${c.reviewsCount} reseñas'),
                  _Fact(icon: FontAwesomeIcons.userGroup, color: AppColors.primaryLight, value: '${c.studentsCount}', label: 'Estudiantes'),
                  _Fact(icon: FontAwesomeIcons.layerGroup, color: AppColors.teal, value: '${c.lessonsCount}', label: 'Lecciones'),
                  _Fact(icon: FontAwesomeIcons.clock, color: AppColors.orange, value: c.durationMinutes > 0 ? Fmt.duration(c.durationMinutes) : '—', label: 'Duración'),
                ]),
                if (c.isEnrolled && c.progress != null) ...[
                  const SizedBox(height: 18),
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(color: AppColors.success.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(14)),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        const FaIcon(FontAwesomeIcons.circleCheck, size: 15, color: AppColors.success),
                        const SizedBox(width: 8),
                        const Text('Ya estás inscrito', style: TextStyle(fontWeight: FontWeight.w800)),
                        const Spacer(),
                        Text('${c.progress}%', style: const TextStyle(fontWeight: FontWeight.w800)),
                      ]),
                      const SizedBox(height: 8),
                      ProgressBar(value: c.progress!),
                    ]),
                  ),
                ],
                _sectionTitle('Acerca de este curso'),
                Text(c.description, style: TextStyle(height: 1.6, color: p.ink.withValues(alpha: 0.9))),
                _sectionTitle('Contenido del curso', trailing: '${c.modules.length} módulos · ${c.lessonsCount} lecciones'),
                for (final m in c.modules) _ModuleTile(module: m, course: c, user: user),
                if (c.teacherInfo != null && c.teacherCourses.isNotEmpty) ...[
                  _sectionTitle('Más cursos de ${c.teacher}'),
                ],
              ]),
            ),
          ),
          if (c.teacherCourses.isNotEmpty)
            SliverToBoxAdapter(
              child: SizedBox(
                height: 288,
                child: ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  scrollDirection: Axis.horizontal,
                  itemCount: c.teacherCourses.length,
                  separatorBuilder: (_, _) => const SizedBox(width: 14),
                  itemBuilder: (_, i) => CourseCard(
                    course: c.teacherCourses[i],
                    onTap: () => push(context, CourseDetailScreen(courseId: c.teacherCourses[i].id)),
                  ),
                ),
              ),
            ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 40),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _sectionTitle('Valoraciones'),
                CourseReviews(course: c, onChanged: _load),
              ]),
            ),
          ),
        ]),
      ),
    );
  }

  Widget _sectionTitle(String text, {String? trailing}) => Padding(
        padding: const EdgeInsets.only(top: 28, bottom: 12),
        child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Expanded(child: Text(text, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800, letterSpacing: -0.3))),
          if (trailing != null) Text(trailing, style: TextStyle(color: context.palette.inkMuted, fontSize: 12.5)),
        ]),
      );
}

class _Fact extends StatelessWidget {
  const _Fact({required this.icon, required this.color, required this.value, required this.label});

  final FaIconData icon;
  final Color color;
  final String value, label;

  @override
  Widget build(BuildContext context) => Expanded(
        child: Column(children: [
          FaIcon(icon, size: 17, color: color),
          const SizedBox(height: 6),
          Text(value, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
          const SizedBox(height: 2),
          Text(label, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: context.palette.inkMuted, fontSize: 11.5)),
        ]),
      );
}

class _ModuleTile extends StatelessWidget {
  const _ModuleTile({required this.module, required this.course, required this.user});

  final ModuleOutline module;
  final Course course;
  final dynamic user;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final staff = !(user.isStudent as bool);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(16), border: Border.all(color: p.border), boxShadow: p.shadow),
      clipBehavior: Clip.antiAlias,
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          shape: const Border(),
          collapsedShape: const Border(),
          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
          title: Text(module.title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
          subtitle: Text('${module.lessons.length} lecciones', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
          children: [
            for (final l in module.lessons)
              ListTile(
                dense: true,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                leading: FaIcon(lessonIcon(l.type), size: 17, color: p.primaryText),
                title: Text(l.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                subtitle: Text([lessonTypeLabel(l.type), if (l.durationMinutes > 0) Fmt.duration(l.durationMinutes)].join(' · '),
                    style: TextStyle(color: p.inkMuted, fontSize: 12)),
                trailing: course.isEnrolled || staff
                    ? (l.completed ? const FaIcon(FontAwesomeIcons.circleCheck, size: 16, color: AppColors.success) : null)
                    : l.isFree
                        ? const SoftTag(label: 'Vista previa', color: AppColors.success, icon: FontAwesomeIcons.eye)
                        : FaIcon(FontAwesomeIcons.lock, size: 13, color: p.inkMuted),
                onTap: (course.isEnrolled || staff || l.isFree)
                    ? () => push(context, LessonScreen(lessonId: l.id))
                    : () => showToast(context, 'Inscríbete en el curso para ver esta lección.'),
              ),
          ],
        ),
      ),
    );
  }
}

class _BottomBar extends StatelessWidget {
  const _BottomBar({required this.course, required this.busy, required this.onAdd, required this.onBuyNow});

  final Course course;
  final bool busy;
  final VoidCallback onAdd, onBuyNow;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final user = context.watch<AuthProvider>().user!;
    final cart = context.watch<CartProvider>();
    final c = course;

    Widget action;
    if (!user.isStudent) {
      action = LoadingButton(
        label: 'Ver contenido del curso',
        icon: FontAwesomeIcons.eye,
        onPressed: () => push(context, LearnScreen(courseId: c.id)),
      );
    } else if (c.isEnrolled) {
      action = LoadingButton(
        label: (c.progress ?? 0) >= 100 ? 'Repasar curso' : ((c.progress ?? 0) > 0 ? 'Continuar curso' : 'Empezar curso'),
        icon: FontAwesomeIcons.circlePlay,
        accent: true,
        onPressed: () => push(context, LearnScreen(courseId: c.id)),
      );
    } else if (c.inCart || cart.contains(c.id)) {
      action = LoadingButton(label: 'Ir al carrito', icon: FontAwesomeIcons.cartShopping, onPressed: () => push(context, const CartScreen()));
    } else {
      action = Row(children: [
        SizedBox(
          width: 54,
          child: OutlinedButton(
            onPressed: busy ? null : onAdd,
            style: OutlinedButton.styleFrom(padding: EdgeInsets.zero),
            child: const FaIcon(FontAwesomeIcons.cartPlus, size: 18),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: LoadingButton(
            label: c.isFree ? 'Inscribirme' : 'Comprar',
            icon: FontAwesomeIcons.bolt,
            accent: true,
            loading: busy,
            onPressed: onBuyNow,
          ),
        ),
      ]);
    }

    final showPrice = user.isStudent && !c.isEnrolled;
    return Container(
      padding: EdgeInsets.fromLTRB(20, 12, 20, MediaQuery.of(context).padding.bottom + 12),
      decoration: BoxDecoration(color: p.surface, border: Border(top: BorderSide(color: p.border))),
      child: Row(children: [
        if (showPrice)
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(c.isFree ? 'Gratis' : Fmt.amount(c.price),
                  style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800, color: c.isFree ? AppColors.success : p.primaryText)),
              if (c.coupon != null)
                Text('Cupón ${c.coupon!.code} ${c.coupon!.label}', style: const TextStyle(color: AppColors.pink, fontSize: 11.5, fontWeight: FontWeight.w700))
              else if (c.emiDiscount != null && !c.isFree)
                Text('-${c.emiDiscount!.toStringAsFixed(0)}% EMI', style: const TextStyle(color: AppColors.pink, fontSize: 11.5, fontWeight: FontWeight.w700)),
            ]),
          ),
        Expanded(child: action),
      ]),
    );
  }
}
