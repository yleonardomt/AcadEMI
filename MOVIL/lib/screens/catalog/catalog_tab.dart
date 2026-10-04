import 'dart:async';

import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/nav.dart';
import '../../models/course.dart';
import '../../providers/auth_provider.dart';
import '../../providers/shell_nav.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../../widgets/header_actions.dart';
import 'course_detail_screen.dart';

/// Catálogo con búsqueda, categorías, filtros y paginación infinita.
class CatalogTab extends StatefulWidget {
  const CatalogTab({super.key});

  @override
  State<CatalogTab> createState() => _CatalogTabState();
}

class _CatalogTabState extends State<CatalogTab> {
  final _search = TextEditingController();
  final _scroll = ScrollController();
  Timer? _debounce;

  List<CategoryItem> _categories = [];
  final List<Course> _courses = [];
  int? _category;
  String? _level;
  String? _price;
  String _sort = 'featured';
  int _page = 1;
  int _total = 0;
  bool _hasMore = false;
  bool _loading = true;
  bool _loadingMore = false;
  String? _error;
  int _lastRequest = -1;

  @override
  void initState() {
    super.initState();
    _scroll.addListener(() {
      if (_scroll.position.pixels > _scroll.position.maxScrollExtent - 300 && _hasMore && !_loadingMore && !_loading) {
        _loadMore();
      }
    });
    _loadCategories();
    _reload();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _loadCategories() async {
    try {
      final cats = await context.read<AuthProvider>().api.categories();
      if (mounted) setState(() => _categories = cats.where((c) => c.coursesCount > 0).toList());
    } catch (_) {}
  }

  Future<void> _reload({bool silent = false}) async {
    setState(() {
      _loading = !silent;
      _error = null;
      _page = 1;
    });
    try {
      final res = await context.read<AuthProvider>().api.courses(
            q: _search.text.trim(),
            category: _category,
            level: _level,
            price: _price,
            sort: _sort,
          );
      if (!mounted) return;
      setState(() {
        _courses
          ..clear()
          ..addAll(res.courses);
        _total = res.total;
        _hasMore = res.hasMore;
        _loading = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = errorText(e);
          _loading = false;
        });
      }
    }
  }

  Future<void> _loadMore() async {
    setState(() => _loadingMore = true);
    try {
      final res = await context.read<AuthProvider>().api.courses(
            q: _search.text.trim(),
            category: _category,
            level: _level,
            price: _price,
            sort: _sort,
            page: _page + 1,
          );
      if (!mounted) return;
      setState(() {
        _page = res.page;
        _courses.addAll(res.courses);
        _hasMore = res.hasMore;
      });
    } catch (_) {}
    if (mounted) setState(() => _loadingMore = false);
  }

  void _onSearchChanged(String _) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 450), _reload);
  }

  Future<void> _toggleFavorite(int index) async {
    final user = context.read<AuthProvider>().user!;
    if (!user.isStudent) return;
    final course = _courses[index];
    try {
      final fav = await context.read<AuthProvider>().api.toggleFavorite(course.id);
      if (mounted) setState(() => _courses[index] = course.copyWith(isFavorite: fav));
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  int get _activeFilters => (_level != null ? 1 : 0) + (_price != null ? 1 : 0) + (_sort != 'featured' ? 1 : 0);

  Future<void> _openFilters() async {
    var level = _level, price = _price, sort = _sort;
    final applied = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(builder: (ctx, setSheet) {
        Widget group(String title, Map<String?, String> options, String? current, void Function(String?) onPick) =>
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Padding(
                padding: const EdgeInsets.only(top: 14, bottom: 8),
                child: Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
              ),
              Wrap(spacing: 8, runSpacing: 8, children: [
                for (final e in options.entries)
                  ChoiceChip(
                    label: Text(e.value),
                    selected: current == e.key,
                    onSelected: (_) => setSheet(() => onPick(e.key)),
                  ),
              ]),
            ]);
        return Padding(
          padding: EdgeInsets.fromLTRB(20, 0, 20, MediaQuery.of(ctx).viewInsets.bottom + 20),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Filtros', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            group('Nivel', {
              null: 'Todos',
              'beginner': 'Principiante',
              'intermediate': 'Intermedio',
              'advanced': 'Avanzado',
              'expert': 'Experto',
            }, level, (v) => level = v),
            group('Precio', {null: 'Todos', 'free': 'Gratis', 'paid': 'De pago'}, price, (v) => price = v),
            group('Ordenar por', {
              'featured': 'Destacados',
              'recent': 'Más recientes',
              'popular': 'Más populares',
              'rating': 'Mejor valorados',
              'price_asc': 'Precio: menor a mayor',
              'price_desc': 'Precio: mayor a menor',
            }, sort, (v) => sort = v ?? 'featured'),
            const SizedBox(height: 22),
            Row(children: [
              Expanded(
                child: LoadingButton(
                  label: 'Limpiar',
                  outlined: true,
                  onPressed: () {
                    level = null;
                    price = null;
                    sort = 'featured';
                    Navigator.pop(ctx, true);
                  },
                ),
              ),
              const SizedBox(width: 12),
              Expanded(child: LoadingButton(label: 'Aplicar', onPressed: () => Navigator.pop(ctx, true))),
            ]),
          ]),
        );
      }),
    );
    if (applied == true) {
      setState(() {
        _level = level;
        _price = price;
        _sort = sort;
      });
      _reload();
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final nav = context.watch<ShellNav>();

    // Otra pantalla pidió abrir el catálogo con una búsqueda o categoría.
    if (nav.catalogRequest != _lastRequest) {
      _lastRequest = nav.catalogRequest;
      if (nav.catalogRequest > 0) {
        _search.text = nav.catalogQuery;
        _category = nav.catalogCategory;
        WidgetsBinding.instance.addPostFrameCallback((_) => _reload());
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Catálogo'),
        actions: const [HeaderActions()],
      ),
      body: Column(children: [
        Container(
          color: p.surface,
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
          child: Row(children: [
            Expanded(
              child: TextField(
                controller: _search,
                onChanged: _onSearchChanged,
                textInputAction: TextInputAction.search,
                decoration: InputDecoration(
                  hintText: 'Buscar cursos o docentes',
                  isDense: true,
                  filled: true,
                  fillColor: p.background,
                  prefixIcon: Padding(padding: const EdgeInsets.all(14), child: FaIcon(FontAwesomeIcons.magnifyingGlass, size: 15, color: p.inkMuted)),
                  prefixIconConstraints: const BoxConstraints(minWidth: 44),
                  suffixIcon: _search.text.isEmpty
                      ? null
                      : IconButton(
                          icon: FaIcon(FontAwesomeIcons.circleXmark, size: 15, color: p.inkMuted),
                          onPressed: () {
                            _search.clear();
                            _reload();
                          },
                        ),
                ),
              ),
            ),
            const SizedBox(width: 10),
            InkWell(
              onTap: _openFilters,
              borderRadius: BorderRadius.circular(12),
              child: Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  color: _activeFilters > 0 ? AppColors.primary : p.background,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: p.border),
                ),
                child: Center(
                  child: BadgeIcon(
                    icon: FontAwesomeIcons.sliders,
                    count: _activeFilters,
                    size: 17,
                    color: _activeFilters > 0 ? Colors.white : p.ink,
                  ),
                ),
              ),
            ),
          ]),
        ),
        if (_categories.isNotEmpty)
          Container(
            color: p.surface,
            height: 52,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
              children: [
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: const Text('Todos'),
                    selected: _category == null,
                    onSelected: (_) {
                      setState(() => _category = null);
                      _reload();
                    },
                  ),
                ),
                for (final c in _categories)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      avatar: FaIcon(categoryIcon(c.name), size: 12, color: _category == c.id ? p.primaryText : p.inkMuted),
                      label: Text(c.name),
                      selected: _category == c.id,
                      onSelected: (_) {
                        setState(() => _category = _category == c.id ? null : c.id);
                        _reload();
                      },
                    ),
                  ),
              ],
            ),
          ),
        Divider(height: 1, color: p.border),
        Expanded(child: _body(p)),
      ]),
    );
  }

  Widget _body(Palette p) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return ErrorState(message: _error!, onRetry: _reload);
    if (_courses.isEmpty) {
      return const EmptyState(
        icon: FontAwesomeIcons.magnifyingGlass,
        title: 'Sin resultados',
        message: 'No encontramos cursos con esos filtros. Prueba con otra búsqueda o categoría.',
      );
    }
    return RefreshIndicator(
      onRefresh: () => _reload(silent: true),
      child: ListView.separated(
        controller: _scroll,
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 100),
        itemCount: _courses.length + 1,
        separatorBuilder: (_, _) => const SizedBox(height: 12),
        itemBuilder: (context, i) {
          if (i == 0) {
            return Text('$_total ${_total == 1 ? 'curso' : 'cursos'}',
                style: TextStyle(color: p.inkMuted, fontWeight: FontWeight.w600, fontSize: 13));
          }
          final index = i - 1;
          final course = _courses[index];
          return Column(children: [
            SizedBox(
              height: 132,
              child: CourseListTile(
                course: course,
                onFavorite: context.read<AuthProvider>().user!.isStudent ? () => _toggleFavorite(index) : null,
                onTap: () async {
                  await push(context, CourseDetailScreen(courseId: course.id));
                  if (mounted) _reload(silent: true);
                },
              ),
            ),
            if (index == _courses.length - 1 && _loadingMore)
              const Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()),
          ]);
        },
      ),
    );
  }
}
