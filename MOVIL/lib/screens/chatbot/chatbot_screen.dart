import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../models/social.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';

/// Asistente virtual de AcadEMI (RF-77 a RF-82): responde dudas y recomienda cursos.
class ChatbotScreen extends StatefulWidget {
  const ChatbotScreen({super.key});

  @override
  State<ChatbotScreen> createState() => _ChatbotScreenState();
}

class _ChatbotScreenState extends State<ChatbotScreen> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _loading = true;
  bool _typing = false;

  static const _suggestions = [
    '¿Qué cursos me recomiendas?',
    '¿Cómo obtengo un certificado?',
    '¿Cómo funciona el descuento EMI?',
    '¿Cómo pago un curso?',
  ];

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    try {
      final history = await context.read<AuthProvider>().api.chatHistory();
      if (mounted) setState(() => _messages.addAll(history));
    } catch (_) {}
    if (mounted) {
      setState(() => _loading = false);
      _toBottom();
    }
  }

  void _toBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scroll.hasClients) {
          _scroll.animateTo(_scroll.position.maxScrollExtent + 200, duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
        }
      });

  Future<void> _send([String? preset]) async {
    final text = (preset ?? _input.text).trim();
    if (text.isEmpty || _typing) return;
    _input.clear();
    setState(() {
      _messages.add(ChatMessage(id: -DateTime.now().millisecondsSinceEpoch, sender: 'user', message: text, createdAt: DateTime.now()));
      _typing = true;
    });
    _toBottom();
    try {
      final reply = await context.read<AuthProvider>().api.chatSend(text);
      if (mounted) setState(() => _messages.add(reply));
    } catch (e) {
      if (mounted) {
        setState(() => _messages.add(ChatMessage(id: -1, sender: 'bot', message: 'Lo siento, no pude responder ahora. ${errorText(e)}')));
      }
    }
    if (mounted) setState(() => _typing = false);
    _toBottom();
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(children: [
          Container(
            width: 38,
            height: 38,
            decoration: const BoxDecoration(gradient: AppColors.primaryGradient, shape: BoxShape.circle),
            child: const Center(child: FaIcon(FontAwesomeIcons.robot, size: 17, color: AppColors.secondary)),
          ),
          const SizedBox(width: 12),
          const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Asistente AcadEMI', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
            Text('En línea', style: TextStyle(fontSize: 12, color: AppColors.success, fontWeight: FontWeight.w600)),
          ]),
        ]),
      ),
      body: Column(children: [
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : ListView(controller: _scroll, padding: const EdgeInsets.fromLTRB(16, 16, 16, 8), children: [
                  if (_messages.isEmpty)
                    Column(children: [
                      const SizedBox(height: 30),
                      Container(
                        width: 84,
                        height: 84,
                        decoration: const BoxDecoration(gradient: AppColors.primaryGradient, shape: BoxShape.circle),
                        child: const Center(child: FaIcon(FontAwesomeIcons.robot, size: 36, color: AppColors.secondary)),
                      ),
                      const SizedBox(height: 16),
                      const Text('¡Hola! Soy tu asistente', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                      const SizedBox(height: 6),
                      Text('Pregúntame sobre cursos, pagos, certificados o cómo usar la plataforma.', textAlign: TextAlign.center, style: TextStyle(color: p.inkMuted, height: 1.45)),
                      const SizedBox(height: 22),
                      Wrap(spacing: 8, runSpacing: 8, alignment: WrapAlignment.center, children: [
                        for (final s in _suggestions) ActionChip(label: Text(s), onPressed: () => _send(s)),
                      ]),
                    ]),
                  for (final m in _messages) _Bubble(message: m),
                  if (_typing) const _TypingBubble(),
                ]),
        ),
        Container(
          padding: EdgeInsets.fromLTRB(12, 10, 12, MediaQuery.of(context).padding.bottom + 10),
          decoration: BoxDecoration(color: p.surface, border: Border(top: BorderSide(color: p.border))),
          child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
            Expanded(
              child: TextField(
                controller: _input,
                minLines: 1,
                maxLines: 4,
                textCapitalization: TextCapitalization.sentences,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _send(),
                decoration: const InputDecoration(hintText: 'Escribe tu pregunta…'),
              ),
            ),
            const SizedBox(width: 10),
            SizedBox(
              width: 50,
              height: 50,
              child: FilledButton(
                onPressed: _typing ? null : () => _send(),
                style: FilledButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(50, 50), backgroundColor: AppColors.secondary, foregroundColor: AppColors.primaryDark),
                child: const FaIcon(FontAwesomeIcons.paperPlane, size: 17),
              ),
            ),
          ]),
        ),
      ]),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.message});

  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final bot = message.isBot;
    return Align(
      alignment: bot ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
        decoration: BoxDecoration(
          gradient: bot ? null : AppColors.primaryGradient,
          color: bot ? p.surface : null,
          border: bot ? Border.all(color: p.border) : null,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(bot ? 4 : 18),
            bottomRight: Radius.circular(bot ? 18 : 4),
          ),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SelectableText(message.message, style: TextStyle(color: bot ? p.ink : Colors.white, height: 1.45, fontSize: 14.5)),
          if (message.createdAt != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(Fmt.ago(message.createdAt), style: TextStyle(fontSize: 10.5, color: bot ? p.inkMuted : Colors.white70)),
            ),
        ]),
      ),
    );
  }
}

class _TypingBubble extends StatelessWidget {
  const _TypingBubble();

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        decoration: BoxDecoration(color: p.surface, border: Border.all(color: p.border), borderRadius: BorderRadius.circular(18)),
        child: SizedBox(
          width: 34,
          child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: List.generate(3, (_) => Container(width: 7, height: 7, decoration: BoxDecoration(color: p.inkMuted, shape: BoxShape.circle)))),
        ),
      ),
    );
  }
}
