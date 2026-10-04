import 'dart:async';

import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';
import 'auth_shell.dart';

/// Espera a que el usuario confirme su correo (RF-07). Consulta el estado
/// cada pocos segundos y entra sola a la app cuando ya está verificado.
class VerifyPendingScreen extends StatefulWidget {
  const VerifyPendingScreen({super.key});

  @override
  State<VerifyPendingScreen> createState() => _VerifyPendingScreenState();
}

class _VerifyPendingScreenState extends State<VerifyPendingScreen> with WidgetsBindingObserver {
  Timer? _timer;
  bool _resending = false;
  bool _checking = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _check(silent: true));
  }

  @override
  void dispose() {
    _timer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _check(silent: true);
  }

  Future<void> _check({bool silent = false}) async {
    if (_checking) return;
    _checking = true;
    final auth = context.read<AuthProvider>();
    try {
      if (await auth.api.isEmailVerified()) {
        await auth.refresh();
      } else if (!silent && mounted) {
        showToast(context, 'Aún no confirmaste tu correo. Abre el enlace que te enviamos.');
      }
    } catch (_) {}
    _checking = false;
  }

  Future<void> _resend() async {
    setState(() => _resending = true);
    try {
      final msg = await context.read<AuthProvider>().api.resendVerification();
      if (mounted) showToast(context, msg, success: true);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _resending = false);
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final auth = context.watch<AuthProvider>();
    return AuthShell(
      icon: FontAwesomeIcons.envelopeOpenText,
      title: 'Verifica tu correo',
      subtitle: 'Un último paso para activar tu cuenta.',
      child: Column(children: [
        const SizedBox(height: 4),
        Container(
          width: 76,
          height: 76,
          decoration: BoxDecoration(color: AppColors.secondary.withValues(alpha: 0.2), shape: BoxShape.circle),
          child: const Center(child: FaIcon(FontAwesomeIcons.solidEnvelope, size: 32, color: AppColors.secondaryDark)),
        ),
        const SizedBox(height: 16),
        Text(
          'Enviamos un enlace de confirmación a',
          textAlign: TextAlign.center,
          style: TextStyle(color: p.inkMuted),
        ),
        const SizedBox(height: 4),
        Text(auth.user?.email ?? '', textAlign: TextAlign.center, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
        const SizedBox(height: 10),
        Text(
          'Ábrelo desde tu correo y regresa a la app: entrará automáticamente.',
          textAlign: TextAlign.center,
          style: TextStyle(color: p.inkMuted, height: 1.5),
        ),
        const SizedBox(height: 22),
        LoadingButton(label: 'Ya lo confirmé', icon: FontAwesomeIcons.check, onPressed: () => _check()),
        const SizedBox(height: 10),
        LoadingButton(label: 'Reenviar correo', outlined: true, loading: _resending, icon: FontAwesomeIcons.paperPlane, onPressed: _resend),
        const SizedBox(height: 6),
        TextButton(onPressed: () => context.read<AuthProvider>().logout(), child: const Text('Usar otra cuenta')),
      ]),
    );
  }
}
