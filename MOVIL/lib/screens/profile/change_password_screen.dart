import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../providers/auth_provider.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';

class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final _form = GlobalKey<FormState>();
  final _old = TextEditingController();
  final _new = TextEditingController();
  final _confirm = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _old.dispose();
    _new.dispose();
    _confirm.dispose();
    super.dispose();
  }

  String? _rules(String? v) {
    final s = v ?? '';
    if (s.length < 8) return 'Debe tener al menos 8 caracteres';
    if (!RegExp(r'[A-Z]').hasMatch(s)) return 'Debe tener al menos una mayúscula';
    if (!RegExp(r'[a-z]').hasMatch(s)) return 'Debe tener al menos una minúscula';
    if (!RegExp(r'[0-9]').hasMatch(s)) return 'Debe tener al menos un número';
    if (!RegExp(r'[!@#$%^&*(),.?":{}|<>]').hasMatch(s)) return 'Debe tener al menos un carácter especial (!@#\$%^&*)';
    return null;
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _saving = true);
    final auth = context.read<AuthProvider>();
    try {
      final token = await auth.api.changePassword(_old.text, _new.text, _confirm.text);
      await auth.replaceToken(token);
      if (mounted) {
        showToast(context, 'Contraseña cambiada correctamente.', success: true);
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Cambiar contraseña')),
        body: GestureDetector(
          onTap: () => FocusScope.of(context).unfocus(),
          child: Form(
            key: _form,
            child: ListView(padding: const EdgeInsets.all(16), children: [
              FormCard(
                title: 'Seguridad',
                icon: FontAwesomeIcons.shieldHalved,
                child: Column(children: [
                  AppTextField(controller: _old, label: 'Contraseña actual', icon: FontAwesomeIcons.lock, obscure: true, validator: (v) => (v ?? '').isEmpty ? 'Ingresa tu contraseña actual' : null),
                  const SizedBox(height: 14),
                  AppTextField(controller: _new, label: 'Nueva contraseña', icon: FontAwesomeIcons.key, obscure: true, validator: _rules),
                  const SizedBox(height: 14),
                  AppTextField(controller: _confirm, label: 'Confirmar nueva contraseña', icon: FontAwesomeIcons.lockOpen, obscure: true, validator: (v) => v == _new.text ? null : 'Las contraseñas no coinciden'),
                ]),
              ),
              const SizedBox(height: 22),
              LoadingButton(label: 'Actualizar contraseña', icon: FontAwesomeIcons.check, loading: _saving, onPressed: _save),
            ]),
          ),
        ),
      );
}
