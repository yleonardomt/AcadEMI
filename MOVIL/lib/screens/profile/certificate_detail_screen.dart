import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';

/// Certificado de finalización con su código de verificación y descarga del PDF.
class CertificateDetailScreen extends StatefulWidget {
  const CertificateDetailScreen({super.key, required this.certificate});

  final CertificateItem certificate;

  @override
  State<CertificateDetailScreen> createState() => _CertificateDetailScreenState();
}

class _CertificateDetailScreenState extends State<CertificateDetailScreen> {
  bool _sending = false;

  /// RF-41: el estudiante pide que le enviemos el certificado a su correo.
  Future<void> _sendEmail() async {
    setState(() => _sending = true);
    try {
      final msg = await context.read<AuthProvider>().api.emailCertificate(widget.certificate.id);
      if (mounted) showToast(context, msg, success: true);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _sending = false);
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final c = widget.certificate;
    return Scaffold(
      appBar: AppBar(title: const Text('Certificado')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Container(
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(gradient: AppColors.accentGradient, borderRadius: BorderRadius.circular(24)),
          child: Container(
            padding: const EdgeInsets.fromLTRB(22, 28, 22, 28),
            decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(19)),
            child: Column(children: [
              const BrandLogo(size: 24),
              const SizedBox(height: 22),
              const FaIcon(FontAwesomeIcons.award, size: 56, color: AppColors.secondaryDark),
              const SizedBox(height: 16),
              Text('CERTIFICADO DE FINALIZACIÓN', textAlign: TextAlign.center, style: TextStyle(color: p.inkMuted, fontWeight: FontWeight.w800, letterSpacing: 1.4, fontSize: 12)),
              const SizedBox(height: 18),
              Text('Se otorga a', style: TextStyle(color: p.inkMuted)),
              const SizedBox(height: 4),
              Text(c.student, textAlign: TextAlign.center, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
              const SizedBox(height: 16),
              Text('por completar satisfactoriamente el curso', textAlign: TextAlign.center, style: TextStyle(color: p.inkMuted)),
              const SizedBox(height: 6),
              Text(c.course, textAlign: TextAlign.center, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: p.primaryText, height: 1.25)),
              const SizedBox(height: 20),
              Text('Emitido el ${Fmt.date(c.issuedAt)}', style: TextStyle(color: p.inkMuted)),
              const SizedBox(height: 16),
              InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: () {
                  Clipboard.setData(ClipboardData(text: c.code));
                  showToast(context, 'Código copiado');
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: BoxDecoration(color: p.surfaceSoft, borderRadius: BorderRadius.circular(12)),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [
                    Text(c.code, style: const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 2)),
                    const SizedBox(width: 10),
                    FaIcon(FontAwesomeIcons.copy, size: 14, color: p.inkMuted),
                  ]),
                ),
              ),
              if (c.isRevoked) ...[const SizedBox(height: 14), const SoftTag(label: 'Este certificado fue revocado', color: AppColors.danger, icon: FontAwesomeIcons.ban)],
            ]),
          ),
        ),
        const SizedBox(height: 20),
        if (c.pdf != null)
          LoadingButton(
            label: 'Descargar PDF',
            icon: FontAwesomeIcons.filePdf,
            accent: true,
            onPressed: () => launchUrl(Uri.parse(c.pdf!), mode: LaunchMode.externalApplication),
          ),
        if (!c.isRevoked) ...[
          const SizedBox(height: 10),
          LoadingButton(label: 'Enviar a mi correo', outlined: true, loading: _sending, icon: FontAwesomeIcons.envelope, onPressed: _sendEmail),
        ],
        const SizedBox(height: 10),
        Text('Cualquier persona puede verificar su autenticidad con el código en la sección "Verificar certificado".',
            textAlign: TextAlign.center, style: TextStyle(color: p.inkMuted, fontSize: 12.5, height: 1.45)),
      ]),
    );
  }
}
