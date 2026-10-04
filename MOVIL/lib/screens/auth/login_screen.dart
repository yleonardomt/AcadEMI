import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/nav.dart';
import '../../providers/auth_provider.dart';
import '../../core/network/api_client.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/captcha_field.dart';
import '../../widgets/common.dart';
import 'auth_shell.dart';
import 'forgot_password_screen.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _identifier = TextEditingController();
  final _password = TextEditingController();
  final _captcha = CaptchaController();
  bool _needsCaptcha = false;
  bool _loading = false;

  @override
  void dispose() {
    _identifier.dispose();
    _password.dispose();
    _captcha.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await context.read<AuthProvider>().login(_identifier.text.trim(), _password.text,
          captcha: _needsCaptcha ? _captcha.payload : null);
    } catch (e) {
      // RF-06: tras varios intentos fallidos el servidor exige un CAPTCHA.
      if (e is ApiException && e.code == 'CAPTCHA_REQUIRED') {
        _captcha.set(e.data?['captcha'] as Map<String, dynamic>?);
        if (mounted) setState(() => _needsCaptcha = true);
      }
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return AuthShell(
      title: 'Bienvenido de vuelta',
      subtitle: 'Inicia sesión para continuar aprendiendo.',
      child: Form(
        key: _form,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          AppTextField(
            controller: _identifier,
            label: 'Usuario o correo',
            icon: FontAwesomeIcons.user,
            hint: 'tucorreo@ejemplo.com',
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            autofillHints: const [AutofillHints.username, AutofillHints.email],
            validator: (v) => (v ?? '').trim().isEmpty ? 'Ingresa tu usuario o correo' : null,
          ),
          const SizedBox(height: 16),
          AppTextField(
            controller: _password,
            label: 'Contraseña',
            icon: FontAwesomeIcons.lock,
            hint: '••••••••',
            obscure: true,
            textInputAction: TextInputAction.done,
            autofillHints: const [AutofillHints.password],
            onSubmitted: (_) => _submit(),
            validator: (v) => (v ?? '').isEmpty ? 'Ingresa tu contraseña' : null,
          ),
          if (_needsCaptcha) ...[
            const SizedBox(height: 16),
            CaptchaField(controller: _captcha, onRefresh: () => _captcha.load(context.read<AuthProvider>().api)),
          ],
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: () => push(context, const ForgotPasswordScreen()),
              child: const Text('¿Olvidaste tu contraseña?'),
            ),
          ),
          const SizedBox(height: 4),
          LoadingButton(label: 'Iniciar sesión', icon: FontAwesomeIcons.rightToBracket, loading: _loading, onPressed: _submit),
          const SizedBox(height: 22),
          Row(children: [
            Expanded(child: Divider(color: p.border)),
            Padding(padding: const EdgeInsets.symmetric(horizontal: 12), child: Text('o', style: TextStyle(color: p.inkMuted))),
            Expanded(child: Divider(color: p.border)),
          ]),
          const SizedBox(height: 18),
          LoadingButton(
            label: 'Crear una cuenta',
            outlined: true,
            icon: FontAwesomeIcons.userPlus,
            onPressed: () => push(context, const RegisterScreen()),
          ),
          const SizedBox(height: 14),
          Center(
            child: TextButton.icon(
              onPressed: () => push(context, const _PublicCatalogHint()),
              icon: const FaIcon(FontAwesomeIcons.circleQuestion, size: 14),
              label: const Text('¿Qué es AcadEMI?'),
            ),
          ),
        ]),
      ),
    );
  }
}

/// Breve presentación de la plataforma (equivale a la portada pública del sitio).
class _PublicCatalogHint extends StatelessWidget {
  const _PublicCatalogHint();

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    const items = [
      (FontAwesomeIcons.bookOpen, 'Cursos de calidad', 'Aprende con video, lecturas, cuestionarios y tareas.'),
      (FontAwesomeIcons.certificate, 'Certificados', 'Al terminar un curso recibes un certificado verificable.'),
      (FontAwesomeIcons.robot, 'Asistente virtual', 'Resuelve dudas y recibe recomendaciones de cursos.'),
      (FontAwesomeIcons.percent, 'Descuento EMI', '15% en tu primera compra con tu correo est.emi.edu.bo.'),
    ];
    return Scaffold(
      appBar: AppBar(title: const BrandLogo()),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        const Text('Aprende a tu ritmo, donde estés.',
            style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: -0.5, height: 1.2)),
        const SizedBox(height: 10),
        Text('AcadEMI es la plataforma educativa de la Escuela Militar de Ingeniería.',
            style: TextStyle(color: p.inkMuted, fontSize: 15, height: 1.5)),
        const SizedBox(height: 22),
        for (final it in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                        color: AppColors.secondary.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(14)),
                    child: Center(child: FaIcon(it.$1, size: 20, color: AppColors.secondaryDark)),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(it.$2, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5)),
                      const SizedBox(height: 3),
                      Text(it.$3, style: TextStyle(color: p.inkMuted, height: 1.4)),
                    ]),
                  ),
                ]),
              ),
            ),
          ),
      ]),
    );
  }
}
