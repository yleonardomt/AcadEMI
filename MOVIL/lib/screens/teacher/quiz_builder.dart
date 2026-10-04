import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/json_utils.dart';

class _Option {
  _Option({String text = '', this.correct = false}) : text = TextEditingController(text: text);

  final TextEditingController text;
  bool correct;
}

class _Question {
  _Question({String text = '', int points = 1, List<_Option>? options})
      : text = TextEditingController(text: text),
        points = TextEditingController(text: '$points'),
        options = options ?? [_Option(correct: true), _Option()];

  final TextEditingController text, points;
  final List<_Option> options;
}

/// Controlador del constructor de preguntas (RF-28): carga las preguntas existentes
/// y las devuelve en el formato que espera la API.
class QuizBuilderController {
  final List<_Question> _questions = [];

  void load(List<Map<String, dynamic>> questions) {
    _questions.clear();
    for (final q in questions) {
      _questions.add(_Question(
        text: asString(q['text']),
        points: asInt(q['points'], 1),
        options: [for (final o in asList(q['options'])) _Option(text: asString(o['text']), correct: asBool(o['is_correct']))],
      ));
    }
  }

  List<Map<String, dynamic>> toJson() => [
        for (final q in _questions)
          {
            'text': q.text.text.trim(),
            'points': int.tryParse(q.points.text) ?? 1,
            'options': [for (final o in q.options) {'text': o.text.text.trim(), 'is_correct': o.correct}],
          }
      ];

  /// Devuelve un mensaje si algo está incompleto.
  String? validate() {
    if (_questions.isEmpty) return 'Agrega al menos una pregunta.';
    for (var i = 0; i < _questions.length; i++) {
      final q = _questions[i];
      if (q.text.text.trim().isEmpty) return 'La pregunta ${i + 1} no tiene enunciado.';
      final filled = q.options.where((o) => o.text.text.trim().isNotEmpty).toList();
      if (filled.length < 2) return 'La pregunta ${i + 1} necesita al menos 2 opciones.';
      if (!filled.any((o) => o.correct)) return 'Marca la respuesta correcta de la pregunta ${i + 1}.';
    }
    return null;
  }

  void dispose() {
    for (final q in _questions) {
      q.text.dispose();
      q.points.dispose();
      for (final o in q.options) {
        o.text.dispose();
      }
    }
  }
}

class QuizBuilder extends StatefulWidget {
  const QuizBuilder({super.key, required this.controller});

  final QuizBuilderController controller;

  @override
  State<QuizBuilder> createState() => _QuizBuilderState();
}

class _QuizBuilderState extends State<QuizBuilder> {
  List<_Question> get _qs => widget.controller._questions;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      for (var i = 0; i < _qs.length; i++)
        Container(
          margin: const EdgeInsets.only(bottom: 14),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: p.surfaceSoft, borderRadius: BorderRadius.circular(16), border: Border.all(color: p.border)),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(children: [
              Container(
                width: 28,
                height: 28,
                decoration: const BoxDecoration(color: AppColors.primary, shape: BoxShape.circle),
                child: Center(child: Text('${i + 1}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13))),
              ),
              const SizedBox(width: 10),
              const Expanded(child: Text('Pregunta', style: TextStyle(fontWeight: FontWeight.w800))),
              SizedBox(
                width: 64,
                child: TextField(
                  controller: _qs[i].points,
                  keyboardType: TextInputType.number,
                  textAlign: TextAlign.center,
                  decoration: const InputDecoration(labelText: 'Pts', isDense: true, contentPadding: EdgeInsets.symmetric(vertical: 8, horizontal: 6)),
                ),
              ),
              IconButton(
                tooltip: 'Eliminar pregunta',
                onPressed: () => setState(() => _qs.removeAt(i)),
                icon: const FaIcon(FontAwesomeIcons.trashCan, size: 16, color: AppColors.danger),
              ),
            ]),
            const SizedBox(height: 10),
            TextField(controller: _qs[i].text, maxLines: 2, decoration: const InputDecoration(hintText: 'Escribe el enunciado…')),
            const SizedBox(height: 10),
            for (var j = 0; j < _qs[i].options.length; j++)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(children: [
                  InkWell(
                    onTap: () => setState(() {
                      // Una sola respuesta correcta a la vez (como el cuestionario web).
                      for (final o in _qs[i].options) {
                        o.correct = false;
                      }
                      _qs[i].options[j].correct = true;
                    }),
                    child: Padding(
                      padding: const EdgeInsets.all(6),
                      child: FaIcon(_qs[i].options[j].correct ? FontAwesomeIcons.solidCircleCheck : FontAwesomeIcons.circle, size: 22,
                          color: _qs[i].options[j].correct ? AppColors.success : p.inkMuted),
                    ),
                  ),
                  Expanded(child: TextField(controller: _qs[i].options[j].text, decoration: InputDecoration(hintText: 'Opción ${String.fromCharCode(65 + j)}', isDense: true))),
                  if (_qs[i].options.length > 2)
                    IconButton(
                      onPressed: () => setState(() => _qs[i].options.removeAt(j)),
                      icon: FaIcon(FontAwesomeIcons.xmark, size: 14, color: p.inkMuted),
                    ),
                ]),
              ),
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: _qs[i].options.length >= 6 ? null : () => setState(() => _qs[i].options.add(_Option())),
                icon: const FaIcon(FontAwesomeIcons.plus, size: 12),
                label: const Text('Agregar opción'),
              ),
            ),
          ]),
        ),
      OutlinedButton.icon(
        onPressed: () => setState(() => _qs.add(_Question())),
        icon: const FaIcon(FontAwesomeIcons.circlePlus, size: 16),
        label: const Text('Agregar pregunta'),
      ),
    ]);
  }
}
