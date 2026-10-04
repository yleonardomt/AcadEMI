import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/common.dart';

/// RF-48: certificados emitidos, con opción de revocarlos o reactivarlos.
class AdminCertificatesScreen extends StatefulWidget {
  const AdminCertificatesScreen({super.key});

  @override
  State<AdminCertificatesScreen> createState() => _AdminCertificatesScreenState();
}

class _AdminCertificatesScreenState extends State<AdminCertificatesScreen> {
  Key _key = UniqueKey();

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Certificados emitidos')),
      body: AsyncBody<Map<String, dynamic>>(
        key: _key,
        load: api.adminCertificates,
        builder: (context, data, reload) {
          final list = asList(data['certificates']);
          if (list.isEmpty) return const EmptyState(icon: FontAwesomeIcons.certificate, title: 'Sin certificados', message: 'Aún no se emitió ningún certificado.');
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final c = list[i];
              final revoked = asBool(c['is_revoked']);
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Expanded(child: Text(asString(c['student']), style: const TextStyle(fontWeight: FontWeight.w800))),
                      SoftTag(label: revoked ? 'Revocado' : 'Válido', color: revoked ? AppColors.danger : AppColors.success),
                    ]),
                    const SizedBox(height: 4),
                    Text(asString(c['course']), maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.inkMuted)),
                    const SizedBox(height: 6),
                    Text('${asString(c['code'])} · ${Fmt.date(asDate(c['issued_at']))} · verificado ${asInt(c['verification_count'])} veces', style: TextStyle(color: p.inkMuted, fontSize: 12)),
                    const SizedBox(height: 6),
                    Row(children: [
                      if (asStringOrNull(c['pdf']) != null)
                        TextButton.icon(onPressed: () => launchUrl(Uri.parse(asString(c['pdf'])), mode: LaunchMode.externalApplication), icon: const FaIcon(FontAwesomeIcons.filePdf, size: 13), label: const Text('PDF')),
                      const Spacer(),
                      TextButton.icon(
                        style: TextButton.styleFrom(foregroundColor: revoked ? AppColors.success : AppColors.danger),
                        onPressed: () async {
                          final ok = await confirmDialog(context, title: revoked ? 'Reactivar certificado' : 'Revocar certificado', message: revoked ? '¿Reactivar este certificado?' : 'El certificado dejará de ser válido al verificarlo.', confirmLabel: revoked ? 'Reactivar' : 'Revocar', danger: !revoked);
                          if (!ok) return;
                          try {
                            await api.adminToggleCertificate(asInt(c['id']));
                            if (mounted) setState(() => _key = UniqueKey());
                          } catch (e) {
                            if (mounted) showToast(context, errorText(e), error: true);
                          }
                        },
                        icon: FaIcon(revoked ? FontAwesomeIcons.rotateLeft : FontAwesomeIcons.ban, size: 13),
                        label: Text(revoked ? 'Reactivar' : 'Revocar'),
                      ),
                    ]),
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
