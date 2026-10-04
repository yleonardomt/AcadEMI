import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/captcha_field.dart';
import '../../core/network/api_client.dart';
import '../../widgets/common.dart';
import 'auth_shell.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _captcha = CaptchaController();
  bool _loading = false;
  bool _sent = false;

  @override
  void initState() {
    super.initState();
    _captcha.load(context.read<AuthProvider>().api);
  }

  @override
  void dispose() {
    _email.dispose();
    _captcha.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await context.read<AuthProvider>().api.requestPasswordReset(_email.text.trim(), _captcha.payload);
      if (mounted) setState(() => _sent = true);
    } catch (e) {
      if (e is ApiException) _captcha.set(e.data?['captcha'] as Map<String, dynamic>?);
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return AuthShell(
      showBack: true,
      icon: FontAwesomeIcons.key,
      title: 'Recupera tu contraseña',
      subtitle: 'Te enviaremos un enlace a tu correo para crear una nueva.',
      child: _sent
          ? Column(children: [
              const SizedBox(height: 8),
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(color: AppColors.success.withValues(alpha: 0.14), shape: BoxShape.circle),
                child: const Center(child: FaIcon(FontAwesomeIcons.envelopeCircleCheck, size: 30, color: AppColors.success)),
              ),
              const SizedBox(height: 16),
              const Text('¡Revisa tu correo!', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              Text(
                'Si ${_email.text.trim()} está registrado, recibirás un enlace de recuperación en unos minutos. Revisa también la carpeta de spam.',
                textAlign: TextAlign.center,
                style: TextStyle(color: p.inkMuted, height: 1.5),
              ),
              const SizedBox(height: 20),
              LoadingButton(label: 'Volver a iniciar sesión', onPressed: () => Navigator.of(context).maybePop()),
            ])
          : Form(
              key: _form,
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                AppTextField(
                  controller: _email,
                  label: 'Correo registrado',
                  icon: FontAwesomeIcons.envelope,
                  hint: 'ejemplo@correo.com',
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _submit(),
                  validator: (v) => RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch((v ?? '').trim()) ? null : 'Ingresa un correo válido',
                ),
                const SizedBox(height: 16),
                CaptchaField(controller: _captcha, onRefresh: () => _captcha.load(context.read<AuthProvider>().api)),
                const SizedBox(height: 20),
                LoadingButton(label: 'Enviar enlace', icon: FontAwesomeIcons.paperPlane, loading: _loading, onPressed: _submit),
              ]),
            ),
    );
  }
}
