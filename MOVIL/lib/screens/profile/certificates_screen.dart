import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/nav.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../providers/shell_nav.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';
import 'certificate_detail_screen.dart';

class CertificatesScreen extends StatelessWidget {
  const CertificatesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Mis certificados')),
      body: AsyncBody<List<CertificateItem>>(
        load: api.certificates,
        builder: (context, list, reload) {
          if (list.isEmpty) {
            return ListView(children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: EmptyState(
                  icon: FontAwesomeIcons.certificate,
                  title: 'Todavía no tienes certificados',
                  message: 'Completa un curso al 100% para recibir tu certificado.',
                  actionLabel: 'Ir a mis cursos',
                  onAction: () {
                    Navigator.of(context).popUntil((r) => r.isFirst);
                    context.read<ShellNav>().setTab(2);
                  },
                ),
              ),
            ]);
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final c = list[i];
              return InkWell(
                borderRadius: BorderRadius.circular(20),
                onTap: () => push(context, CertificateDetailScreen(certificate: c)),
                child: Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    gradient: c.isRevoked ? null : AppColors.heroGradient,
                    color: c.isRevoked ? p.surfaceSoft : null,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(children: [
                    Container(
                      width: 54,
                      height: 54,
                      decoration: BoxDecoration(color: AppColors.secondary.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(16)),
                      child: const Center(child: FaIcon(FontAwesomeIcons.award, size: 26, color: AppColors.secondary)),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(c.course, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: c.isRevoked ? null : Colors.white, fontWeight: FontWeight.w800, fontSize: 16, height: 1.25)),
                        const SizedBox(height: 4),
                        Text('Emitido ${Fmt.date(c.issuedAt)}', style: TextStyle(color: c.isRevoked ? p.inkMuted : Colors.white.withValues(alpha: 0.8), fontSize: 12.5)),
                        if (c.isRevoked) ...[const SizedBox(height: 6), const SoftTag(label: 'Revocado', color: AppColors.danger)],
                      ]),
                    ),
                    FaIcon(FontAwesomeIcons.chevronRight, size: 14, color: c.isRevoked ? p.inkMuted : Colors.white70),
                  ]),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

/// Verificación pública de un certificado por su código (RF-67).
class VerifyCertificateScreen extends StatefulWidget {
  const VerifyCertificateScreen({super.key});

  @override
  State<VerifyCertificateScreen> createState() => _VerifyCertificateScreenState();
}

class _VerifyCertificateScreenState extends State<VerifyCertificateScreen> {
  final _code = TextEditingController();
  bool _loading = false;
  bool _checked = false;
  CertificateItem? _found;

  @override
  void dispose() {
    _code.dispose();
    super.dispose();
  }

  Future<void> _verify() async {
    final code = _code.text.trim();
    if (code.isEmpty) return;
    FocusScope.of(context).unfocus();
    setState(() => _loading = true);
    try {
      final c = await context.read<AuthProvider>().api.verifyCertificate(code);
      if (mounted) {
        setState(() {
          _found = c;
          _checked = true;
        });
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Verificar certificado')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        FormCard(
          title: 'Código del certificado',
          icon: FontAwesomeIcons.magnifyingGlass,
          child: Column(children: [
            AppTextField(
              controller: _code,
              label: 'Código',
              icon: FontAwesomeIcons.hashtag,
              hint: 'Ej: AB12CD34EF56',
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => _verify(),
            ),
            const SizedBox(height: 16),
            LoadingButton(label: 'Verificar', icon: FontAwesomeIcons.shieldHalved, loading: _loading, onPressed: _verify),
          ]),
        ),
        if (_checked) ...[
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: (_found != null ? AppColors.success : AppColors.danger).withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(18),
            ),
            child: _found == null
                ? const Row(children: [
                    FaIcon(FontAwesomeIcons.circleXmark, size: 26, color: AppColors.danger),
                    SizedBox(width: 14),
                    Expanded(child: Text('No encontramos un certificado válido con ese código.', style: TextStyle(fontWeight: FontWeight.w700, height: 1.4))),
                  ])
                : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Row(children: [
                      FaIcon(FontAwesomeIcons.circleCheck, size: 26, color: AppColors.success),
                      SizedBox(width: 12),
                      Text('Certificado auténtico', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
                    ]),
                    const SizedBox(height: 14),
                    Text('Otorgado a', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                    Text(_found!.student, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                    const SizedBox(height: 10),
                    Text('Curso', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                    Text(_found!.course, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                    const SizedBox(height: 10),
                    Text('Emitido el ${Fmt.date(_found!.issuedAt)}', style: TextStyle(color: p.inkMuted)),
                  ]),
          ),
        ],
      ]),
    );
  }
}
