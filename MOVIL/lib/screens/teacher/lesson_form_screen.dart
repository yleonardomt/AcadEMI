import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/json_utils.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';
import 'quiz_builder.dart';

/// RF-14 y RF-28: crear o editar una lección (texto, video, documento, tarea,
/// cuestionario o examen).
class LessonFormScreen extends StatefulWidget {
  const LessonFormScreen({super.key, this.moduleId, this.lessonId, this.type = 'text'});

  final int? moduleId, lessonId;
  final String type;

  @override
  State<LessonFormScreen> createState() => _LessonFormScreenState();
}

class _LessonFormScreenState extends State<LessonFormScreen> {
  final _form = GlobalKey<FormState>();
  final _title = TextEditingController();
  final _description = TextEditingController();
  final _content = TextEditingController();
  final _duration = TextEditingController(text: '0');
  final _videoUrl = TextEditingController();
  final _deadlineDays = TextEditingController(text: '7');
  final _deadlineHours = TextEditingController(text: '0');
  late final _timeLimit = TextEditingController(text: widget.type == 'exam' ? '60' : '30');
  final _passing = TextEditingController(text: '70');
  final _attempts = TextEditingController(text: '1');
  final _quiz = QuizBuilderController();

  late String _type = widget.type;
  bool _free = false;
  bool _loading = false;
  bool _saving = false;
  PlatformFile? _file;
  String? _existingFile;

  bool get _isQuiz => _type == 'quiz' || _type == 'exam';

  @override
  void initState() {
    super.initState();
    if (widget.lessonId != null) _load();
  }

  @override
  void dispose() {
    for (final c in [_title, _description, _content, _duration, _videoUrl, _deadlineDays, _deadlineHours, _timeLimit, _passing, _attempts]) {
      c.dispose();
    }
    _quiz.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final l = await context.read<AuthProvider>().api.lessonAdmin(widget.lessonId!);
      _type = asString(l['type'], 'text');
      _title.text = asString(l['title']);
      _description.text = asString(l['description']);
      _content.text = asString(l['content']);
      _duration.text = '${asInt(l['duration_minutes'])}';
      _videoUrl.text = asString(l['video_url']);
      _free = asBool(l['is_free']);
      _existingFile = asStringOrNull(l['video_file']) ?? asStringOrNull(l['document_file']);
      if (l['deadline_days'] != null) _deadlineDays.text = '${asInt(l['deadline_days'])}';
      if (l['deadline_hours'] != null) _deadlineHours.text = '${asInt(l['deadline_hours'])}';
      final quiz = l['quiz'] as Map<String, dynamic>?;
      if (quiz != null) {
        _timeLimit.text = '${asInt(quiz['time_limit_minutes'])}';
        _passing.text = '${asInt(quiz['passing_score'])}';
        _attempts.text = '${asInt(quiz['max_attempts'])}';
        _quiz.load(asList(quiz['questions']));
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _pickFile() async {
    final f = await FilePicker.pickFile(type: _type == 'video' ? FileType.video : FileType.any);
    if (f != null && mounted) setState(() => _file = f);
  }

  /// Si el docente escribe texto plano, lo convertimos en párrafos HTML (la app y el
  /// sitio web muestran el contenido como HTML).
  String _html(String text) {
    final t = text.trim();
    if (t.contains('<')) return t;
    return t.split(RegExp(r'\n\s*\n')).map((p) => '<p>${p.replaceAll('\n', '<br>')}</p>').join();
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    if (_isQuiz) {
      final problem = _quiz.validate();
      if (problem != null) {
        showToast(context, problem, error: true);
        return;
      }
    }
    setState(() => _saving = true);
    final body = <String, dynamic>{
      'type': _type,
      'title': _title.text.trim(),
      'description': _description.text.trim(),
      'content': _html(_content.text),
      'duration_minutes': _duration.text.trim(),
      'is_free': _free,
      if (_type == 'video') 'video_url': _videoUrl.text.trim(),
      if (_type == 'assignment') ...{'deadline_days': _deadlineDays.text.trim(), 'deadline_hours': _deadlineHours.text.trim()},
      if (_isQuiz) ...{
        'time_limit_minutes': _timeLimit.text.trim(),
        'passing_score': _passing.text.trim(),
        'max_attempts': _attempts.text.trim(),
        'questions': _quiz.toJson(),
      },
    };
    try {
      final r = await context.read<AuthProvider>().api.saveLesson(
            body,
            moduleId: widget.moduleId,
            lessonId: widget.lessonId,
            fileField: _file == null ? null : (_type == 'video' ? 'video_file' : 'document_file'),
            filePath: _file?.path,
          );
      if (mounted) {
        showToast(context, asString(r['message']), success: true);
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _saving = false);
  }

  static const _labels = {
    'text': 'lección de lectura',
    'video': 'lección de video',
    'document': 'lección de documento',
    'assignment': 'tarea',
    'quiz': 'cuestionario',
    'exam': 'examen',
  };

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: Text('${widget.lessonId == null ? 'Nueva' : 'Editar'} ${_labels[_type] ?? 'lección'}')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : GestureDetector(
              onTap: () => FocusScope.of(context).unfocus(),
              child: Form(
                key: _form,
                child: ListView(padding: const EdgeInsets.all(16), children: [
                  FormCard(
                    title: 'General',
                    icon: FontAwesomeIcons.circleInfo,
                    child: Column(children: [
                      AppTextField(controller: _title, label: 'Título', icon: FontAwesomeIcons.heading, validator: (v) => (v ?? '').trim().length < 3 ? 'Mínimo 3 caracteres' : null),
                      const SizedBox(height: 14),
                      AppTextField(controller: _description, label: 'Descripción breve (opcional)', icon: FontAwesomeIcons.alignLeft, maxLines: 2),
                      const SizedBox(height: 14),
                      AppTextField(controller: _duration, label: 'Duración (minutos)', icon: FontAwesomeIcons.clock, keyboardType: TextInputType.number),
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Vista previa gratuita', style: TextStyle(fontWeight: FontWeight.w700)),
                        subtitle: Text('Cualquiera puede verla sin comprar el curso', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                        value: _free,
                        onChanged: (v) => setState(() => _free = v),
                      ),
                    ]),
                  ),
                  const SizedBox(height: 14),
                  if (_type == 'video')
                    FormCard(
                      title: 'Video',
                      icon: FontAwesomeIcons.circlePlay,
                      child: Column(children: [
                        AppTextField(controller: _videoUrl, label: 'Enlace de YouTube u otro sitio', icon: FontAwesomeIcons.link, keyboardType: TextInputType.url),
                        const SizedBox(height: 12),
                        Text('o sube un archivo', style: TextStyle(color: p.inkMuted)),
                        const SizedBox(height: 10),
                        _filePicker(p),
                      ]),
                    ),
                  if (_type == 'document')
                    FormCard(title: 'Documento', icon: FontAwesomeIcons.fileLines, child: _filePicker(p)),
                  if (_type == 'assignment')
                    FormCard(
                      title: 'Plazo de entrega',
                      icon: FontAwesomeIcons.calendarDay,
                      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Expanded(child: AppTextField(controller: _deadlineDays, label: 'Días', keyboardType: TextInputType.number)),
                        const SizedBox(width: 12),
                        Expanded(child: AppTextField(controller: _deadlineHours, label: 'Horas', keyboardType: TextInputType.number)),
                      ]),
                    ),
                  if (_isQuiz)
                    FormCard(
                      title: 'Configuración',
                      icon: FontAwesomeIcons.gear,
                      child: Column(children: [
                        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Expanded(child: AppTextField(controller: _timeLimit, label: 'Tiempo (min)', keyboardType: TextInputType.number)),
                          const SizedBox(width: 12),
                          Expanded(child: AppTextField(controller: _passing, label: 'Aprobar (%)', keyboardType: TextInputType.number)),
                          const SizedBox(width: 12),
                          Expanded(child: AppTextField(controller: _attempts, label: 'Intentos', keyboardType: TextInputType.number)),
                        ]),
                      ]),
                    ),
                  if (_isQuiz) const SizedBox(height: 14),
                  FormCard(
                    title: _isQuiz ? 'Instrucciones' : (_type == 'assignment' ? 'Consigna' : 'Contenido'),
                    icon: FontAwesomeIcons.penToSquare,
                    child: AppTextField(
                      controller: _content,
                      label: _isQuiz ? 'Instrucciones para el estudiante' : 'Texto (puedes usar HTML)',
                      maxLines: 8,
                      validator: (v) => (_type == 'text' || _isQuiz) && (v ?? '').trim().isEmpty ? 'Este campo es obligatorio' : null,
                    ),
                  ),
                  if (_isQuiz) ...[
                    const SectionHeader(title: 'Preguntas', subtitle: 'Toca el círculo para marcar la respuesta correcta', padding: EdgeInsets.fromLTRB(4, 22, 4, 10)),
                    QuizBuilder(controller: _quiz),
                  ],
                  const SizedBox(height: 22),
                  LoadingButton(label: 'Guardar', icon: FontAwesomeIcons.floppyDisk, loading: _saving, onPressed: _save),
                  const SizedBox(height: 24),
                ]),
              ),
            ),
    );
  }

  Widget _filePicker(Palette p) => InkWell(
        onTap: _pickFile,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(color: p.surfaceSoft, borderRadius: BorderRadius.circular(14), border: Border.all(color: p.border)),
          child: Row(children: [
            FaIcon(_file != null ? FontAwesomeIcons.fileCircleCheck : FontAwesomeIcons.cloudArrowUp, color: p.primaryText),
            const SizedBox(width: 14),
            Expanded(
              child: Text(_file?.name ?? (_existingFile != null ? 'Ya hay un archivo subido. Toca para reemplazarlo.' : 'Toca para elegir un archivo'),
                  style: const TextStyle(fontWeight: FontWeight.w600)),
            ),
          ]),
        ),
      );
}
