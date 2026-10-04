import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../core/theme/app_colors.dart';
import '../services/services.dart';
import 'app_text_field.dart';

/// Estado de un CAPTCHA (RF-06): clave + imagen + respuesta escrita por el usuario.
class CaptchaController extends ChangeNotifier {
  String? key;
  String? imageUrl;
  final answer = TextEditingController();
  bool loading = false;

  bool get ready => key != null;

  /// Campos que se envían al servidor junto con el formulario.
  Map<String, dynamic> get payload => {'captcha_key': key, 'captcha_answer': answer.text.trim()};

  Future<void> load(AppServices api) async {
    loading = true;
    notifyListeners();
    try {
      set(await api.captcha());
    } catch (_) {}
    loading = false;
    notifyListeners();
  }

  /// Usa un captcha nuevo entregado por el servidor (tras un error).
  void set(Map<String, dynamic>? data) {
    if (data == null) return;
    key = data['key'] as String?;
    imageUrl = data['image'] as String?;
    answer.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    answer.dispose();
    super.dispose();
  }
}

/// Imagen del CAPTCHA con botón para cambiarla y campo para escribir el código.
class CaptchaField extends StatelessWidget {
  const CaptchaField({super.key, required this.controller, required this.onRefresh});

  final CaptchaController controller;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Padding(
          padding: EdgeInsets.only(bottom: 6, left: 2),
          child: Text('Código de seguridad', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
        ),
        Row(children: [
          Expanded(
            child: Container(
              height: 60,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: p.border),
              ),
              clipBehavior: Clip.antiAlias,
              child: controller.imageUrl == null
                  ? Center(child: controller.loading ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.2)) : Text('Sin imagen', style: TextStyle(color: p.inkMuted)))
                  : Image.network(controller.imageUrl!, fit: BoxFit.contain,
                      errorBuilder: (_, _, _) => Center(child: Text('No se pudo cargar', style: TextStyle(color: p.inkMuted)))),
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            width: 50,
            height: 60,
            child: OutlinedButton(
              onPressed: onRefresh,
              style: OutlinedButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(50, 60)),
              child: const FaIcon(FontAwesomeIcons.arrowsRotate, size: 16),
            ),
          ),
        ]),
        const SizedBox(height: 10),
        AppTextField(
          controller: controller.answer,
          label: 'Escribe las letras de la imagen',
          icon: FontAwesomeIcons.shieldHalved,
          hint: 'Ej: abc',
          textInputAction: TextInputAction.done,
          validator: (v) => (v ?? '').trim().isEmpty ? 'Escribe el código de seguridad' : null,
        ),
      ]),
    );
  }
}
