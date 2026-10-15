import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../providers/settings_provider.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';

/// Permite cambiar la dirección del servidor de AcadEMI y probar la conexión
/// (necesario para usar un celular real: ahí la dirección es la IP de la PC).
Future<void> showServerSettings(BuildContext context) => showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => const _ServerSettings(),
    );

class _ServerSettings extends StatefulWidget {
  const _ServerSettings();

  @override
  State<_ServerSettings> createState() => _ServerSettingsState();
}

class _ServerSettingsState extends State<_ServerSettings> {
  late final TextEditingController _url;
  bool _testing = false;
  String? _result;
  bool _ok = false;

  @override
  void initState() {
    super.initState();
    _url = TextEditingController(text: context.read<SettingsProvider>().serverUrl);
  }

  @override
  void dispose() {
    _url.dispose();
    super.dispose();
  }

  Future<void> _test() async {
    setState(() {
      _testing = true;
      _result = null;
    });
    final client = ApiClient(baseUrl: _normalize(_url.text));
    try {
      await client.get('categories/');
      _ok = true;
      _result = 'Conexión exitosa con el servidor.';
    } catch (e) {
      _ok = false;
      _result = errorText(e);
    }
    if (mounted) setState(() => _testing = false);
  }

  String _normalize(String v) {
    var s = v.trim();
    if (!s.startsWith('http')) s = 'http://$s';
    return s.endsWith('/') ? s.substring(0, s.length - 1) : s;
  }

  Future<void> _save() async {
    await context.read<SettingsProvider>().setServerUrl(_url.text);
    if (mounted) {
      Navigator.pop(context);
      showToast(context, 'Servidor guardado', success: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 4, 20, MediaQuery.of(context).viewInsets.bottom + 24),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Servidor de AcadEMI', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text(
          'Dirección donde corre el sitio de AcadEMI. En el emulador de Android usa 10.0.2.2; '
          'en un celular real, la IP de tu PC en la red (ej. 192.168.1.10).',
          style: TextStyle(color: p.inkMuted, height: 1.45, fontSize: 13.5),
        ),
        const SizedBox(height: 18),
        AppTextField(
          controller: _url,
          label: 'Dirección',
          icon: FontAwesomeIcons.server,
          hint: 'http://192.168.1.10',
          keyboardType: TextInputType.url,
        ),
        if (_result != null) ...[
          const SizedBox(height: 12),
          Row(children: [
            FaIcon(_ok ? FontAwesomeIcons.circleCheck : FontAwesomeIcons.circleExclamation,
                size: 15, color: _ok ? AppColors.success : AppColors.danger),
            const SizedBox(width: 8),
            Expanded(child: Text(_result!, style: TextStyle(color: _ok ? AppColors.success : AppColors.danger, fontSize: 13.5))),
          ]),
        ],
        const SizedBox(height: 18),
        Row(children: [
          Expanded(child: LoadingButton(label: 'Probar', outlined: true, loading: _testing, onPressed: _test, icon: FontAwesomeIcons.plug)),
          const SizedBox(width: 12),
          Expanded(child: LoadingButton(label: 'Guardar', onPressed: _save, icon: FontAwesomeIcons.floppyDisk)),
        ]),
      ]),
    );
  }
}
