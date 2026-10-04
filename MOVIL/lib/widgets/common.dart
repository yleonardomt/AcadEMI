import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../core/network/api_client.dart';
import '../core/theme/app_colors.dart';
import '../core/utils/format.dart';

/// Mensaje breve (equivale al `showToast()` del sitio web).
void showToast(BuildContext context, String message, {bool error = false, bool success = false}) {
  final messenger = ScaffoldMessenger.of(context);
  messenger
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(
      content: Row(children: [
        FaIcon(
          error
              ? FontAwesomeIcons.circleExclamation
              : success
                  ? FontAwesomeIcons.circleCheck
                  : FontAwesomeIcons.circleInfo,
          size: 16,
          color: error
              ? AppColors.danger
              : success
                  ? AppColors.success
                  : AppColors.secondary,
        ),
        const SizedBox(width: 10),
        Expanded(child: Text(message)),
      ]),
    ));
}

String errorText(Object e) => e is ApiException ? e.message : 'Ocurrió un error inesperado.';

Future<bool> confirmDialog(
  BuildContext context, {
  required String title,
  required String message,
  String confirmLabel = 'Confirmar',
  bool danger = false,
}) async {
  final result = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
        FilledButton(
          style: FilledButton.styleFrom(
            minimumSize: const Size(0, 42),
            backgroundColor: danger ? AppColors.danger : null,
          ),
          onPressed: () => Navigator.pop(ctx, true),
          child: Text(confirmLabel),
        ),
      ],
    ),
  );
  return result ?? false;
}

/// Logo de la marca: birrete + "AcadEMI".
class BrandLogo extends StatelessWidget {
  const BrandLogo({super.key, this.size = 22, this.light = false});

  final double size;
  final bool light;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final color = light ? Colors.white : p.primaryText;
    return Row(mainAxisSize: MainAxisSize.min, children: [
      FaIcon(FontAwesomeIcons.graduationCap, size: size, color: AppColors.secondary),
      const SizedBox(width: 8),
      Text('Acad', style: TextStyle(fontSize: size, fontWeight: FontWeight.w800, color: color, letterSpacing: -0.5)),
      Text('EMI',
          style: TextStyle(
              fontSize: size, fontWeight: FontWeight.w800, color: AppColors.secondary, letterSpacing: -0.5)),
    ]);
  }
}

/// Foto de perfil con iniciales como respaldo.
class UserAvatar extends StatelessWidget {
  const UserAvatar({super.key, required this.name, this.url, this.radius = 20});

  final String name;
  final String? url;
  final double radius;

  @override
  Widget build(BuildContext context) {
    final fallback = Container(
      width: radius * 2,
      height: radius * 2,
      alignment: Alignment.center,
      decoration: const BoxDecoration(gradient: AppColors.primaryGradient, shape: BoxShape.circle),
      child: Text(Fmt.initials(name),
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: radius * 0.72)),
    );
    if (url == null) return fallback;
    return ClipOval(
      child: CachedNetworkImage(
        imageUrl: url!,
        width: radius * 2,
        height: radius * 2,
        fit: BoxFit.cover,
        placeholder: (_, _) => fallback,
        errorWidget: (_, _, _) => fallback,
      ),
    );
  }
}

/// Título de sección con acción opcional ("Ver todo").
class SectionHeader extends StatelessWidget {
  const SectionHeader({super.key, required this.title, this.subtitle, this.onSeeAll, this.padding});

  final String title;
  final String? subtitle;
  final VoidCallback? onSeeAll;
  final EdgeInsetsGeometry? padding;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Padding(
      padding: padding ?? const EdgeInsets.fromLTRB(20, 24, 20, 12),
      child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800, letterSpacing: -0.3)),
            if (subtitle != null)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(subtitle!, style: TextStyle(color: p.inkMuted, fontSize: 13)),
              ),
          ]),
        ),
        if (onSeeAll != null)
          TextButton(
            onPressed: onSeeAll,
            style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 8), minimumSize: Size.zero),
            child: const Row(mainAxisSize: MainAxisSize.min, children: [
              Text('Ver todo'),
              SizedBox(width: 6),
              FaIcon(FontAwesomeIcons.arrowRight, size: 12),
            ]),
          ),
      ]),
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    this.message,
    this.actionLabel,
    this.onAction,
  });

  final FaIconData icon;
  final String title;
  final String? message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(
            width: 84,
            height: 84,
            decoration: BoxDecoration(
              color: p.isDark ? p.surfaceSoft : AppColors.primaryLighter,
              shape: BoxShape.circle,
            ),
            child: Center(child: FaIcon(icon, size: 32, color: p.primaryText)),
          ),
          const SizedBox(height: 18),
          Text(title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          if (message != null) ...[
            const SizedBox(height: 8),
            Text(message!, textAlign: TextAlign.center, style: TextStyle(color: p.inkMuted, height: 1.45)),
          ],
          if (actionLabel != null) ...[
            const SizedBox(height: 20),
            FilledButton(
              onPressed: onAction,
              style: FilledButton.styleFrom(minimumSize: const Size(180, 46)),
              child: Text(actionLabel!),
            ),
          ],
        ]),
      ),
    );
  }
}

class ErrorState extends StatelessWidget {
  const ErrorState({super.key, required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => EmptyState(
        icon: FontAwesomeIcons.wifi,
        title: 'No pudimos cargar esto',
        message: message,
        actionLabel: onRetry == null ? null : 'Reintentar',
        onAction: onRetry,
      );
}

/// Carga un `Future` y muestra cargando / error con reintento / contenido.
/// El contenido recibe `reload` para refrescar, y admite "tirar para actualizar".
class AsyncBody<T> extends StatefulWidget {
  const AsyncBody({super.key, required this.load, required this.builder, this.pullToRefresh = true});

  final Future<T> Function() load;
  final Widget Function(BuildContext context, T data, Future<void> Function() reload) builder;
  final bool pullToRefresh;

  @override
  State<AsyncBody<T>> createState() => _AsyncBodyState<T>();
}

class _AsyncBodyState<T> extends State<AsyncBody<T>> {
  T? _data;
  Object? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch({bool silent = false}) async {
    if (!silent && mounted) setState(() => _loading = _data == null);
    try {
      final data = await widget.load();
      if (!mounted) return;
      setState(() {
        _data = data;
        _error = null;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_data == null) {
      return ErrorState(
          message: _error == null ? '' : errorText(_error!),
          onRetry: () {
            setState(() => _loading = true);
            _fetch();
          });
    }
    final child = widget.builder(context, _data as T, () => _fetch(silent: true));
    if (!widget.pullToRefresh) return child;
    return RefreshIndicator(onRefresh: () => _fetch(silent: true), child: child);
  }
}

/// Botón principal con estado de carga.
class LoadingButton extends StatelessWidget {
  const LoadingButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.loading = false,
    this.icon,
    this.accent = false,
    this.outlined = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool loading, accent, outlined;
  final FaIconData? icon;

  @override
  Widget build(BuildContext context) {
    final disabled = loading || onPressed == null;
    final content = loading
        ? SizedBox(
            width: 22,
            height: 22,
            child: CircularProgressIndicator(
                strokeWidth: 2.4, color: outlined ? Theme.of(context).colorScheme.primary : Colors.white))
        : Row(mainAxisSize: MainAxisSize.min, children: [
            if (icon != null) ...[FaIcon(icon, size: 15), const SizedBox(width: 10)],
            Flexible(child: Text(label, overflow: TextOverflow.ellipsis)),
          ]);
    if (outlined) {
      return OutlinedButton(onPressed: disabled ? null : onPressed, child: content);
    }
    return FilledButton(
      onPressed: disabled ? null : onPressed,
      style: accent
          ? FilledButton.styleFrom(backgroundColor: AppColors.secondary, foregroundColor: AppColors.primaryDark)
          : null,
      child: content,
    );
  }
}

class ProgressBar extends StatelessWidget {
  const ProgressBar({super.key, required this.value, this.height = 8, this.color});

  final int value;
  final double height;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return ClipRRect(
      borderRadius: BorderRadius.circular(height),
      child: LinearProgressIndicator(
        value: (value.clamp(0, 100)) / 100,
        minHeight: height,
        backgroundColor: p.isDark ? p.border : AppColors.primaryLighter,
        color: color ?? (value >= 100 ? AppColors.success : AppColors.primaryLight),
      ),
    );
  }
}

class RatingStars extends StatelessWidget {
  const RatingStars({super.key, required this.rating, this.size = 14});

  final double rating;
  final double size;

  @override
  Widget build(BuildContext context) => Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(5, (i) {
          final icon = rating >= i + 0.75
              ? FontAwesomeIcons.solidStar
              : rating >= i + 0.25
                  ? FontAwesomeIcons.starHalfStroke
                  : FontAwesomeIcons.star;
          return Padding(
            padding: const EdgeInsets.only(right: 2),
            child: FaIcon(icon, size: size, color: AppColors.secondaryDark),
          );
        }),
      );
}

class LevelBadge extends StatelessWidget {
  const LevelBadge({super.key, required this.level, required this.label});

  final String level, label;

  @override
  Widget build(BuildContext context) {
    final (bg, fg) = switch (level) {
      'beginner' => (AppColors.tealLight, AppColors.teal),
      'intermediate' => (AppColors.secondaryLight, const Color(0xFF8A6A00)),
      'advanced' => (AppColors.orangeLight, AppColors.orange),
      _ => (AppColors.purpleLight, AppColors.purple),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: TextStyle(color: fg, fontSize: 11, fontWeight: FontWeight.w700)),
    );
  }
}

/// Etiqueta de color suave con ícono opcional.
class SoftTag extends StatelessWidget {
  const SoftTag({super.key, required this.label, required this.color, this.icon});

  final String label;
  final Color color;
  final FaIconData? icon;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(color: color.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(999)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          if (icon != null) ...[FaIcon(icon, size: 11, color: color), const SizedBox(width: 5)],
          Text(label, style: TextStyle(color: color, fontSize: 11.5, fontWeight: FontWeight.w700)),
        ]),
      );
}

/// Cabecera con degradado de marca (portadas de dashboard y perfil).
class GradientHeader extends StatelessWidget {
  const GradientHeader({super.key, required this.child, this.padding, this.radius = 28});

  final Widget child;
  final EdgeInsetsGeometry? padding;
  final double radius;

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: padding ?? const EdgeInsets.fromLTRB(20, 12, 20, 24),
        decoration: BoxDecoration(
          gradient: AppColors.heroGradient,
          borderRadius: BorderRadius.vertical(bottom: Radius.circular(radius)),
        ),
        child: child,
      );
}

/// Tarjeta de estadística (ícono + número + etiqueta).
class StatTile extends StatelessWidget {
  const StatTile({super.key, required this.icon, required this.value, required this.label, this.color});

  final FaIconData icon;
  final String value, label;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final c = color ?? p.primaryText;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: p.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: p.border),
        boxShadow: p.shadow,
      ),
      child: Row(children: [
        Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(color: c.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(12)),
          child: Center(child: FaIcon(icon, size: 17, color: c)),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: Text(value, maxLines: 1, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, height: 1.1)),
            ),
            const SizedBox(height: 2),
            Text(label, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted, fontSize: 12)),
          ]),
        ),
      ]),
    );
  }
}

/// Icono según el tipo de lección.
FaIconData lessonIcon(String type) => switch (type) {
      'video' => FontAwesomeIcons.circlePlay,
      'document' => FontAwesomeIcons.fileLines,
      'text' => FontAwesomeIcons.alignLeft,
      'quiz' => FontAwesomeIcons.listCheck,
      'exam' => FontAwesomeIcons.clipboardCheck,
      'assignment' => FontAwesomeIcons.filePen,
      _ => FontAwesomeIcons.book,
    };

String lessonTypeLabel(String type) => switch (type) {
      'video' => 'Video',
      'document' => 'Documento',
      'text' => 'Lectura',
      'quiz' => 'Cuestionario',
      'exam' => 'Examen',
      'assignment' => 'Tarea',
      _ => 'Lección',
    };

/// Ícono de la categoría según su nombre (equivalente a `_category_icon` del sitio).
FaIconData categoryIcon(String? name) {
  final n = (name ?? '').toLowerCase();
  if (n.contains('program') || n.contains('tecnolog') || n.contains('sistem')) return FontAwesomeIcons.code;
  if (n.contains('dise')) return FontAwesomeIcons.penRuler;
  if (n.contains('market')) return FontAwesomeIcons.bullhorn;
  if (n.contains('negocio') || n.contains('empresa') || n.contains('finanz')) return FontAwesomeIcons.chartLine;
  if (n.contains('idioma') || n.contains('ingl')) return FontAwesomeIcons.language;
  if (n.contains('ciencia') || n.contains('matem')) return FontAwesomeIcons.flask;
  if (n.contains('arte')) return FontAwesomeIcons.palette;
  if (n.contains('music') || n.contains('músic')) return FontAwesomeIcons.music;
  if (n.contains('deporte') || n.contains('salud') || n.contains('nutri')) return FontAwesomeIcons.dumbbell;
  if (n.contains('foto')) return FontAwesomeIcons.camera;
  if (n.contains('ingenier')) return FontAwesomeIcons.gears;
  return FontAwesomeIcons.bookOpen;
}
