import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../core/theme/app_colors.dart';
import 'app_text_field.dart';
import 'common.dart';

enum FieldType { text, multiline, number, decimal, password, email, dropdown, switcher, date }

/// Describe un campo de un formulario emergente.
class FieldSpec {
  const FieldSpec(
    this.key,
    this.label, {
    this.type = FieldType.text,
    this.initial,
    this.options = const {},
    this.required = false,
    this.hint,
    this.icon,
    this.enabled = true,
  });

  final String key, label;
  final FieldType type;
  final dynamic initial;
  final Map<String, String> options;
  final bool required, enabled;
  final String? hint;
  final FaIconData? icon;
}

/// Muestra un formulario en una hoja inferior y devuelve los valores (o null si se cancela).
/// Los interruptores devuelven `bool`; el resto, `String` (fechas como AAAA-MM-DD).
Future<Map<String, dynamic>?> showFormSheet(
  BuildContext context, {
  required String title,
  required List<FieldSpec> fields,
  String submitLabel = 'Guardar',
  String? subtitle,
}) =>
    showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _FormSheet(title: title, fields: fields, submitLabel: submitLabel, subtitle: subtitle),
    );

class _FormSheet extends StatefulWidget {
  const _FormSheet({required this.title, required this.fields, required this.submitLabel, this.subtitle});

  final String title, submitLabel;
  final String? subtitle;
  final List<FieldSpec> fields;

  @override
  State<_FormSheet> createState() => _FormSheetState();
}

class _FormSheetState extends State<_FormSheet> {
  final _form = GlobalKey<FormState>();
  late final Map<String, TextEditingController> _controllers = {
    for (final f in widget.fields)
      if (f.type != FieldType.dropdown && f.type != FieldType.switcher) f.key: TextEditingController(text: f.initial == null ? '' : '${f.initial}'),
  };
  late final Map<String, dynamic> _values = {
    for (final f in widget.fields)
      if (f.type == FieldType.dropdown) f.key: f.initial == null ? null : '${f.initial}',
    for (final f in widget.fields)
      if (f.type == FieldType.switcher) f.key: f.initial == true,
  };

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _pickDate(FieldSpec f) async {
    final current = DateTime.tryParse(_controllers[f.key]!.text) ?? DateTime.now().add(const Duration(days: 30));
    final picked = await showDatePicker(
      context: context,
      initialDate: current,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
      locale: const Locale('es'),
    );
    if (picked != null) {
      _controllers[f.key]!.text =
          '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
    }
  }

  void _submit() {
    if (!_form.currentState!.validate()) return;
    final result = <String, dynamic>{..._values};
    for (final f in widget.fields) {
      final c = _controllers[f.key];
      if (c != null) result[f.key] = c.text.trim();
    }
    Navigator.pop(context, result);
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 0, 20, MediaQuery.of(context).viewInsets.bottom + 20),
      child: SingleChildScrollView(
        child: Form(
          key: _form,
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text(widget.title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            if (widget.subtitle != null)
              Padding(padding: const EdgeInsets.only(top: 6), child: Text(widget.subtitle!, style: TextStyle(color: p.inkMuted, height: 1.4))),
            const SizedBox(height: 18),
            for (final f in widget.fields) ...[_field(f), const SizedBox(height: 14)],
            const SizedBox(height: 4),
            LoadingButton(label: widget.submitLabel, icon: FontAwesomeIcons.floppyDisk, onPressed: _submit),
          ]),
        ),
      ),
    );
  }

  Widget _field(FieldSpec f) {
    String? required(String? v) => f.required && (v ?? '').trim().isEmpty ? 'Este campo es obligatorio' : null;
    switch (f.type) {
      case FieldType.dropdown:
        return AppDropdown<String>(
          label: f.label,
          icon: f.icon,
          value: _values[f.key] as String?,
          items: f.options,
          validator: f.required ? (v) => v == null ? 'Selecciona una opción' : null : null,
          onChanged: (v) => setState(() => _values[f.key] = v),
        );
      case FieldType.switcher:
        return SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: Text(f.label, style: const TextStyle(fontWeight: FontWeight.w700)),
          activeThumbColor: AppColors.primary,
          value: _values[f.key] as bool,
          onChanged: (v) => setState(() => _values[f.key] = v),
        );
      case FieldType.date:
        return GestureDetector(
          onTap: () => _pickDate(f),
          child: AbsorbPointer(
            child: AppTextField(controller: _controllers[f.key]!, label: f.label, icon: f.icon ?? FontAwesomeIcons.calendarDay, hint: 'AAAA-MM-DD', validator: required),
          ),
        );
      default:
        return AppTextField(
          controller: _controllers[f.key]!,
          label: f.label,
          icon: f.icon,
          hint: f.hint,
          enabled: f.enabled,
          obscure: f.type == FieldType.password,
          maxLines: f.type == FieldType.multiline ? 4 : 1,
          keyboardType: switch (f.type) {
            FieldType.number => TextInputType.number,
            FieldType.decimal => const TextInputType.numberWithOptions(decimal: true),
            FieldType.email => TextInputType.emailAddress,
            _ => f.type == FieldType.multiline ? TextInputType.multiline : TextInputType.text,
          },
          inputFormatters: f.type == FieldType.number ? [FilteringTextInputFormatter.digitsOnly] : null,
          validator: required,
        );
    }
  }
}
