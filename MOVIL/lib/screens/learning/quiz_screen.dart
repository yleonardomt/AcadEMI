import 'dart:async';

import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../models/learning.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';

/// Cuestionario cronometrado: una pregunta por pantalla, con cuenta regresiva.
/// Registra cuántas veces la app pasó a segundo plano (control antitrampas).
class QuizScreen extends StatefulWidget {
  const QuizScreen({super.key, required this.lessonId, required this.title});

  final int lessonId;
  final String title;

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> with WidgetsBindingObserver {
  QuizSession? _session;
  String? _error;
  bool _loading = true;
  bool _submitting = false;
  QuizResult? _result;

  final Map<int, int> _answers = {};
  int _index = 0;
  int _tabSwitches = 0;
  late DateTime _deadline;
  Timer? _timer;
  Duration _left = Duration.zero;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _start();
  }

  @override
  void dispose() {
    _timer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused && _session != null && _result == null) _tabSwitches++;
  }

  Future<void> _start() async {
    try {
      final s = await context.read<AuthProvider>().api.quizStart(widget.lessonId);
      if (!mounted) return;
      _deadline = DateTime.now().add(Duration(minutes: s.timeLimitMinutes));
      _left = Duration(minutes: s.timeLimitMinutes);
      _timer = Timer.periodic(const Duration(seconds: 1), (_) {
        final left = _deadline.difference(DateTime.now());
        if (left <= Duration.zero) {
          _timer?.cancel();
          if (mounted && _result == null && !_submitting) {
            showToast(context, 'Se agotó el tiempo. Enviando tus respuestas…', error: true);
            _submit(force: true);
          }
        }
        if (mounted) setState(() => _left = left < Duration.zero ? Duration.zero : left);
      });
      setState(() {
        _session = s;
        _loading = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = errorText(e);
          _loading = false;
        });
      }
    }
  }

  Future<void> _submit({bool force = false}) async {
    final s = _session!;
    if (!force) {
      final unanswered = s.questions.length - _answers.length;
      final ok = await confirmDialog(
        context,
        title: 'Enviar respuestas',
        message: unanswered > 0
            ? 'Tienes $unanswered pregunta(s) sin responder. ¿Enviar de todas formas?'
            : '¿Confirmas que quieres enviar tus respuestas?',
        confirmLabel: 'Enviar',
      );
      if (!ok || !mounted) return;
    }
    _timer?.cancel();
    setState(() => _submitting = true);
    try {
      final r = await context.read<AuthProvider>().api.quizSubmit(
            widget.lessonId,
            s.token,
            _answers.map((k, v) => MapEntry('$k', v)),
            _tabSwitches,
          );
      if (mounted) setState(() => _result = r);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _submitting = false);
  }

  Future<bool> _confirmExit() async {
    if (_result != null || _session == null) return true;
    return confirmDialog(
      context,
      title: '¿Salir del cuestionario?',
      message: 'Perderás tus respuestas y el intento podría contarse como usado.',
      confirmLabel: 'Salir',
      danger: true,
    );
  }

  String _clock(Duration d) {
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return d.inHours > 0 ? '${d.inHours}:$m:$s' : '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    if (_result != null) return _ResultView(result: _result!, onClose: () => Navigator.pop(context, _result));
    if (_loading) return Scaffold(appBar: AppBar(title: Text(widget.title)), body: const Center(child: CircularProgressIndicator()));
    if (_session == null) {
      return Scaffold(appBar: AppBar(title: Text(widget.title)), body: ErrorState(message: _error ?? '', onRetry: () {
        setState(() => _loading = true);
        _start();
      }));
    }

    final s = _session!;
    final q = s.questions[_index];
    final p = context.palette;
    final low = _left.inSeconds <= 60;
    final last = _index == s.questions.length - 1;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        if (await _confirmExit() && context.mounted) Navigator.pop(context);
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text(s.title.isEmpty ? widget.title : s.title, maxLines: 1, overflow: TextOverflow.ellipsis),
          actions: [
            Container(
              margin: const EdgeInsets.only(right: 16),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: (low ? AppColors.danger : AppColors.primaryLight).withValues(alpha: 0.14),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                FaIcon(FontAwesomeIcons.stopwatch, size: 14, color: low ? AppColors.danger : p.primaryText),
                const SizedBox(width: 6),
                Text(_clock(_left), style: TextStyle(fontWeight: FontWeight.w800, color: low ? AppColors.danger : p.primaryText, fontFeatures: const [FontFeature.tabularFigures()])),
              ]),
            ),
          ],
        ),
        body: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 4),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Text('Pregunta ${_index + 1} de ${s.questions.length}', style: const TextStyle(fontWeight: FontWeight.w800)),
                const Spacer(),
                Text('${q.points} ${q.points == 1 ? 'punto' : 'puntos'}', style: TextStyle(color: p.inkMuted, fontSize: 13)),
              ]),
              const SizedBox(height: 10),
              ProgressBar(value: ((_index + 1) / s.questions.length * 100).round()),
            ]),
          ),
          Expanded(
            child: ListView(padding: const EdgeInsets.fromLTRB(20, 18, 20, 20), children: [
              Text(q.text, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800, height: 1.35)),
              const SizedBox(height: 20),
              if (q.options.isEmpty)
                Text('Esta pregunta no tiene opciones disponibles en la app.', style: TextStyle(color: p.inkMuted)),
              for (var i = 0; i < q.options.length; i++) _optionTile(q, q.options[i], i),
            ]),
          ),
          Container(
            padding: EdgeInsets.fromLTRB(20, 12, 20, MediaQuery.of(context).padding.bottom + 12),
            decoration: BoxDecoration(color: p.surface, border: Border(top: BorderSide(color: p.border))),
            child: Row(children: [
              if (_index > 0)
                SizedBox(
                  width: 54,
                  child: OutlinedButton(
                    onPressed: () => setState(() => _index--),
                    style: OutlinedButton.styleFrom(padding: EdgeInsets.zero),
                    child: const FaIcon(FontAwesomeIcons.arrowLeft, size: 16),
                  ),
                ),
              if (_index > 0) const SizedBox(width: 10),
              Expanded(
                child: last
                    ? LoadingButton(label: 'Enviar respuestas', icon: FontAwesomeIcons.paperPlane, accent: true, loading: _submitting, onPressed: _submit)
                    : LoadingButton(label: 'Siguiente', icon: FontAwesomeIcons.arrowRight, onPressed: () => setState(() => _index++)),
              ),
            ]),
          ),
        ]),
      ),
    );
  }

  Widget _optionTile(QuizQuestion q, QuizOption o, int i) {
    final p = context.palette;
    final selected = _answers[q.id] == o.id;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () => setState(() => _answers[q.id] = o.id),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: selected ? AppColors.primaryLight.withValues(alpha: p.isDark ? 0.28 : 0.10) : p.surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: selected ? p.primaryText : p.border, width: selected ? 2 : 1),
          ),
          child: Row(children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: selected ? AppColors.primary : Colors.transparent,
                border: Border.all(color: selected ? AppColors.primary : p.border, width: 1.6),
              ),
              child: Center(
                child: selected
                    ? const FaIcon(FontAwesomeIcons.check, size: 12, color: Colors.white)
                    : Text(String.fromCharCode(65 + i), style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: p.inkMuted)),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(child: Text(o.text, style: const TextStyle(fontSize: 15.5, height: 1.35, fontWeight: FontWeight.w600))),
          ]),
        ),
      ),
    );
  }
}

class _ResultView extends StatelessWidget {
  const _ResultView({required this.result, required this.onClose});

  final QuizResult result;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final ok = result.passed;
    final color = ok ? AppColors.success : AppColors.danger;
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) onClose();
      },
      child: Scaffold(
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
              Container(
                width: 116,
                height: 116,
                decoration: BoxDecoration(color: color.withValues(alpha: 0.14), shape: BoxShape.circle),
                child: Center(child: FaIcon(ok ? FontAwesomeIcons.trophy : FontAwesomeIcons.faceFrown, size: 48, color: color)),
              ),
              const SizedBox(height: 22),
              Text(ok ? '¡Aprobaste!' : 'No alcanzaste el puntaje', style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
              const SizedBox(height: 6),
              Text('${result.percentage}%', style: TextStyle(fontSize: 56, fontWeight: FontWeight.w800, color: color, height: 1.1)),
              const SizedBox(height: 4),
              Text('${result.score} de ${result.totalPoints} puntos · mínimo ${result.passingScore}%', style: TextStyle(color: p.inkMuted)),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(16), border: Border.all(color: p.border), boxShadow: p.shadow),
                child: Column(children: [
                  _line(FontAwesomeIcons.stopwatch, 'Tiempo', '${result.timeSpent ~/ 60} min ${result.timeSpent % 60} s'),
                  const SizedBox(height: 10),
                  _line(FontAwesomeIcons.repeat, 'Intento', '${result.attemptNumber}'),
                  const SizedBox(height: 10),
                  _line(FontAwesomeIcons.hourglassHalf, 'Intentos restantes', '${result.attemptsLeft}'),
                ]),
              ),
              if (result.courseCompleted) ...[
                const SizedBox(height: 16),
                const SoftTag(label: '¡Curso completado! Certificado emitido', color: AppColors.secondaryDark, icon: FontAwesomeIcons.award),
              ],
              const Spacer(),
              LoadingButton(label: ok ? 'Continuar' : 'Volver a la lección', icon: FontAwesomeIcons.arrowRight, onPressed: onClose),
            ]),
          ),
        ),
      ),
    );
  }

  Widget _line(FaIconData icon, String label, String value) => Row(children: [
        FaIcon(icon, size: 15),
        const SizedBox(width: 12),
        Expanded(child: Text(label)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.w800)),
      ]);
}
