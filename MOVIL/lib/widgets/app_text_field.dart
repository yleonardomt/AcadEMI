import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../core/theme/app_colors.dart';

/// Campo de texto de formulario con etiqueta, ícono y ojo para contraseñas.
class AppTextField extends StatefulWidget {
  const AppTextField({
    super.key,
    required this.controller,
    required this.label,
    this.icon,
    this.hint,
    this.obscure = false,
    this.keyboardType,
    this.validator,
    this.maxLines = 1,
    this.textInputAction,
    this.onSubmitted,
    this.autofillHints,
    this.inputFormatters,
    this.enabled = true,
    this.errorText,
    this.onChanged,
  });

  final TextEditingController controller;
  final String label;
  final FaIconData? icon;
  final String? hint;
  final bool obscure, enabled;
  final TextInputType? keyboardType;
  final String? Function(String?)? validator;
  final int maxLines;
  final TextInputAction? textInputAction;
  final ValueChanged<String>? onSubmitted, onChanged;
  final Iterable<String>? autofillHints;
  final List<TextInputFormatter>? inputFormatters;
  final String? errorText;

  @override
  State<AppTextField> createState() => _AppTextFieldState();
}

class _AppTextFieldState extends State<AppTextField> {
  late bool _hidden = widget.obscure;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Padding(
        padding: const EdgeInsets.only(bottom: 6, left: 2),
        child: Text(widget.label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
      ),
      TextFormField(
        controller: widget.controller,
        obscureText: _hidden,
        keyboardType: widget.keyboardType,
        validator: widget.validator,
        maxLines: widget.obscure ? 1 : widget.maxLines,
        textInputAction: widget.textInputAction,
        onFieldSubmitted: widget.onSubmitted,
        onChanged: widget.onChanged,
        autofillHints: widget.autofillHints,
        inputFormatters: widget.inputFormatters,
        enabled: widget.enabled,
        decoration: InputDecoration(
          hintText: widget.hint,
          errorText: widget.errorText,
          prefixIcon: widget.icon == null
              ? null
              : Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  child: FaIcon(widget.icon, size: 16, color: p.inkMuted),
                ),
          prefixIconConstraints: const BoxConstraints(minWidth: 44, minHeight: 20),
          suffixIcon: widget.obscure
              ? IconButton(
                  splashRadius: 20,
                  icon: FaIcon(_hidden ? FontAwesomeIcons.eye : FontAwesomeIcons.eyeSlash, size: 16, color: p.inkMuted),
                  onPressed: () => setState(() => _hidden = !_hidden),
                )
              : null,
        ),
      ),
    ]);
  }
}

/// Selector desplegable con la misma apariencia que [AppTextField].
class AppDropdown<T> extends StatelessWidget {
  const AppDropdown({
    super.key,
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
    this.icon,
    this.validator,
  });

  final String label;
  final T? value;
  final Map<T, String> items;
  final ValueChanged<T?> onChanged;
  final FaIconData? icon;
  final String? Function(T?)? validator;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Padding(
        padding: const EdgeInsets.only(bottom: 6, left: 2),
        child: Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
      ),
      DropdownButtonFormField<T>(
        initialValue: value,
        isExpanded: true,
        validator: validator,
        onChanged: onChanged,
        icon: FaIcon(FontAwesomeIcons.chevronDown, size: 13, color: p.inkMuted),
        decoration: InputDecoration(
          prefixIcon: icon == null
              ? null
              : Padding(padding: const EdgeInsets.symmetric(horizontal: 14), child: FaIcon(icon, size: 16, color: p.inkMuted)),
          prefixIconConstraints: const BoxConstraints(minWidth: 44, minHeight: 20),
        ),
        items: items.entries.map((e) => DropdownMenuItem<T>(value: e.key, child: Text(e.value))).toList(),
      ),
    ]);
  }
}

/// Contenedor de sección tipo tarjeta para formularios.
class FormCard extends StatelessWidget {
  const FormCard({super.key, required this.child, this.title, this.icon});

  final Widget child;
  final String? title;
  final FaIconData? icon;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: p.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: p.border),
        boxShadow: p.shadow,
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (title != null) ...[
          Row(children: [
            if (icon != null) ...[FaIcon(icon, size: 16, color: AppColors.secondaryDark), const SizedBox(width: 10)],
            Text(title!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
          ]),
          const SizedBox(height: 16),
        ],
        Material(type: MaterialType.transparency, child: child),
      ]),
    );
  }
}
