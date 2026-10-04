import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/captcha_field.dart';
import '../../widgets/common.dart';
import 'auth_shell.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _form = GlobalKey<FormState>();
  final _c = {
    for (final k in [
      'full_name', 'email', 'password', 'confirm', 'phone', 'city', 'university', 'career', 'semester',
      'specialty', 'institution',
    ])
      k: TextEditingController(),
  };

  String _role = 'student';
  String? _education;
  String? _experience;
  final _captcha = CaptchaController();
  bool _terms = false;
  bool _loading = false;
  Map<String, dynamic> _serverErrors = {};

  @override
  void initState() {
    super.initState();
    _captcha.load(context.read<AuthProvider>().api);
  }

  @override
  void dispose() {
    for (final c in _c.values) {
      c.dispose();
    }
    _captcha.dispose();
    super.dispose();
  }

  String? _required(String? v, String message) => (v ?? '').trim().isEmpty ? message : null;

  String? _password(String? v) {
    final s = v ?? '';
    if (s.length < 8) return 'Debe tener al menos 8 caracteres';
    if (!RegExp(r'[A-Z]').hasMatch(s)) return 'Debe tener al menos una mayúscula';
    if (!RegExp(r'[a-z]').hasMatch(s)) return 'Debe tener al menos una minúscula';
    if (!RegExp(r'[0-9]').hasMatch(s)) return 'Debe tener al menos un número';
    if (!RegExp(r'[!@#$%^&*(),.?":{}|<>]').hasMatch(s)) return 'Debe tener al menos un carácter especial (!@#\$%^&*)';
    return null;
  }

  Future<void> _submit() async {
    setState(() => _serverErrors = {});
    if (!_form.currentState!.validate()) return;
    if (!_terms) {
      showToast(context, 'Debes aceptar los términos y condiciones para registrarte.', error: true);
      return;
    }
    setState(() => _loading = true);
    final body = <String, dynamic>{
      'role': _role,
      'email': _c['email']!.text.trim(),
      'password': _c['password']!.text,
      'full_name': _c['full_name']!.text.trim(),
      'phone': _c['phone']!.text.trim(),
      'accept_terms': true,
      ..._captcha.payload,
      if (_role == 'student') ...{
        'university': _c['university']!.text.trim(),
        'career': _c['career']!.text.trim(),
        'city': _c['city']!.text.trim(),
        'semester': _c['semester']!.text.trim(),
        'education_level': _education ?? '',
      } else ...{
        'specialty': _c['specialty']!.text.trim(),
        'experience_years': _experience ?? '',
        'institution': _c['institution']!.text.trim(),
      },
    };
    try {
      final sent = await context.read<AuthProvider>().register(body);
      if (!mounted) return;
      // Volvemos a la raíz: el gate de la app mostrará la pantalla de verificación.
      Navigator.of(context).popUntil((r) => r.isFirst);
      if (!sent) {
        showToast(context, 'Registro exitoso, pero no pudimos enviar el correo. Puedes reenviarlo desde la siguiente pantalla.');
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() => _serverErrors = e.errors ?? {});
        _captcha.set(e.data?['captcha'] as Map<String, dynamic>?);
        showToast(context, e.message, error: true);
      }
    }
    if (mounted) setState(() => _loading = false);
  }

  Widget _gap() => const SizedBox(height: 14);

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final isStudent = _role == 'student';
    return AuthShell(
      showBack: true,
      icon: FontAwesomeIcons.userPlus,
      title: 'Crea tu cuenta',
      subtitle: 'Únete a AcadEMI y empieza a aprender hoy.',
      child: Form(
        key: _form,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          SegmentedButton<String>(
            showSelectedIcon: false,
            style: SegmentedButton.styleFrom(
              minimumSize: const Size.fromHeight(46),
              selectedBackgroundColor: AppColors.primary,
              selectedForegroundColor: Colors.white,
            ),
            segments: const [
              ButtonSegment(value: 'student', label: Text('Estudiante'), icon: FaIcon(FontAwesomeIcons.userGraduate, size: 14)),
              ButtonSegment(value: 'teacher', label: Text('Docente'), icon: FaIcon(FontAwesomeIcons.chalkboardUser, size: 14)),
            ],
            selected: {_role},
            onSelectionChanged: (s) => setState(() => _role = s.first),
          ),
          const SizedBox(height: 20),
          AppTextField(
            controller: _c['full_name']!,
            label: 'Nombre completo',
            icon: FontAwesomeIcons.idCard,
            hint: 'Tu nombre completo',
            textInputAction: TextInputAction.next,
            errorText: _serverErrors['full_name'] as String?,
            validator: (v) => _required(v, 'El nombre completo es requerido'),
          ),
          _gap(),
          AppTextField(
            controller: _c['email']!,
            label: 'Correo electrónico',
            icon: FontAwesomeIcons.envelope,
            hint: 'ejemplo@correo.com',
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            errorText: _serverErrors['email'] as String?,
            validator: (v) => RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch((v ?? '').trim()) ? null : 'Ingresa un correo válido',
          ),
          _gap(),
          AppTextField(
            controller: _c['phone']!,
            label: 'Teléfono (opcional)',
            icon: FontAwesomeIcons.phone,
            hint: 'Ej: 79123456',
            keyboardType: TextInputType.phone,
            textInputAction: TextInputAction.next,
          ),
          _gap(),
          if (isStudent) ...[
            AppTextField(
              controller: _c['university']!,
              label: 'Universidad o institución',
              icon: FontAwesomeIcons.buildingColumns,
              textInputAction: TextInputAction.next,
              errorText: _serverErrors['university'] as String?,
              validator: (v) => _required(v, 'La universidad/institución es requerida'),
            ),
            _gap(),
            AppTextField(
              controller: _c['career']!,
              label: 'Carrera',
              icon: FontAwesomeIcons.book,
              textInputAction: TextInputAction.next,
              errorText: _serverErrors['career'] as String?,
              validator: (v) => _required(v, 'La carrera es requerida'),
            ),
            _gap(),
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(
                child: AppTextField(controller: _c['city']!, label: 'Ciudad', icon: FontAwesomeIcons.locationDot, textInputAction: TextInputAction.next),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: AppTextField(controller: _c['semester']!, label: 'Semestre', icon: FontAwesomeIcons.hashtag, textInputAction: TextInputAction.next),
              ),
            ]),
            _gap(),
            AppDropdown<String>(
              label: 'Nivel de estudios',
              icon: FontAwesomeIcons.graduationCap,
              value: _education,
              items: const {
                'secundaria': 'Secundaria',
                'tecnico': 'Técnico Superior',
                'universitario': 'Universitario',
                'posgrado': 'Posgrado/Maestría',
                'doctorado': 'Doctorado',
              },
              onChanged: (v) => setState(() => _education = v),
            ),
          ] else ...[
            AppTextField(
              controller: _c['specialty']!,
              label: 'Especialidad',
              icon: FontAwesomeIcons.award,
              hint: 'Tu área de expertise',
              textInputAction: TextInputAction.next,
              errorText: _serverErrors['specialty'] as String?,
              validator: (v) => _required(v, 'La especialidad es requerida'),
            ),
            _gap(),
            AppDropdown<String>(
              label: 'Años de experiencia',
              icon: FontAwesomeIcons.clockRotateLeft,
              value: _experience,
              validator: (v) => v == null ? 'Los años de experiencia son requeridos' : null,
              items: const {
                '0-1': 'Menos de 1 año',
                '1-3': '1-3 años',
                '3-5': '3-5 años',
                '5-10': '5-10 años',
                '10+': 'Más de 10 años',
              },
              onChanged: (v) => setState(() => _experience = v),
            ),
            _gap(),
            AppTextField(
              controller: _c['institution']!,
              label: 'Institución donde enseñas (opcional)',
              icon: FontAwesomeIcons.buildingColumns,
              textInputAction: TextInputAction.next,
            ),
          ],
          _gap(),
          AppTextField(
            controller: _c['password']!,
            label: 'Contraseña',
            icon: FontAwesomeIcons.lock,
            hint: 'Mínimo 8 caracteres',
            obscure: true,
            textInputAction: TextInputAction.next,
            errorText: _serverErrors['password'] as String?,
            validator: _password,
          ),
          const SizedBox(height: 6),
          Text('Usa mayúscula, minúscula, número y un carácter especial.', style: TextStyle(color: p.inkMuted, fontSize: 12)),
          _gap(),
          AppTextField(
            controller: _c['confirm']!,
            label: 'Confirmar contraseña',
            icon: FontAwesomeIcons.lockOpen,
            obscure: true,
            textInputAction: TextInputAction.done,
            validator: (v) => v == _c['password']!.text ? null : 'Las contraseñas no coinciden',
          ),
          const SizedBox(height: 10),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: _terms,
            onChanged: (v) => setState(() => _terms = v ?? false),
            title: Text.rich(TextSpan(style: const TextStyle(fontSize: 13.5), children: [
              const TextSpan(text: 'Acepto los '),
              TextSpan(
                text: 'términos y condiciones',
                style: TextStyle(color: p.primaryText, fontWeight: FontWeight.w700, decoration: TextDecoration.underline),
              ),
            ])),
            secondary: IconButton(
              icon: const FaIcon(FontAwesomeIcons.arrowUpRightFromSquare, size: 14),
              onPressed: () => launchUrl(
                Uri.parse('${context.read<SettingsProvider>().serverUrl}/terminos/'),
                mode: LaunchMode.externalApplication,
              ),
            ),
          ),
          const SizedBox(height: 8),
          CaptchaField(controller: _captcha, onRefresh: () => _captcha.load(context.read<AuthProvider>().api)),
          const SizedBox(height: 16),
          LoadingButton(label: 'Crear cuenta', icon: FontAwesomeIcons.userCheck, loading: _loading, onPressed: _submit),
          const SizedBox(height: 6),
          TextButton(onPressed: () => Navigator.of(context).maybePop(), child: const Text('¿Ya tienes cuenta? Inicia sesión')),
        ]),
      ),
    );
  }
}
