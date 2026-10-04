import 'dart:io';

import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/json_utils.dart';
import '../../models/course.dart';
import '../../providers/auth_provider.dart';
import '../../services/manage_services.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';

/// RF-13: crear o editar un curso (título, descripción, categoría, nivel, precio e imagen).
class CourseFormScreen extends StatefulWidget {
  const CourseFormScreen({super.key, this.courseId});

  final int? courseId;

  @override
  State<CourseFormScreen> createState() => _CourseFormScreenState();
}

class _CourseFormScreenState extends State<CourseFormScreen> {
  final _form = GlobalKey<FormState>();
  final _title = TextEditingController();
  final _description = TextEditingController();
  final _price = TextEditingController(text: '0');

  List<CategoryItem> _categories = [];
  int? _category;
  String _level = 'beginner';
  bool _free = false;
  bool _featured = false;
  String? _imageUrl;
  String? _imagePath;
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _title.dispose();
    _description.dispose();
    _price.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final api = context.read<AuthProvider>().api;
    try {
      _categories = await api.categories();
      if (widget.courseId != null) {
        final c = await api.manageCourse(widget.courseId!);
        _title.text = asString(c['title']);
        _description.text = asString(c['description']);
        _price.text = '${asDouble(c['price'])}';
        _category = c['category_id'] == null ? null : asInt(c['category_id']);
        _level = asString(c['level'], 'beginner');
        _free = asBool(c['is_free']);
        _featured = asBool(c['is_featured']);
        _imageUrl = asStringOrNull(c['image']);
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _pickImage() async {
    final f = await ImagePicker().pickImage(source: ImageSource.gallery, maxWidth: 1600, imageQuality: 85);
    if (f != null && mounted) setState(() => _imagePath = f.path);
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      final r = await context.read<AuthProvider>().api.saveCourse({
        'title': _title.text.trim(),
        'description': _description.text.trim(),
        'level': _level,
        'is_free': _free,
        'is_featured': _featured,
        'price': _free ? '0' : _price.text.trim(),
        if (_category != null) 'category': _category,
      }, id: widget.courseId, imagePath: _imagePath);
      if (mounted) {
        showToast(context, asString(r['message']), success: true);
        Navigator.pop(context, asInt((r['course'] as Map)['id']));
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: Text(widget.courseId == null ? 'Nuevo curso' : 'Editar curso')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : GestureDetector(
              onTap: () => FocusScope.of(context).unfocus(),
              child: Form(
                key: _form,
                child: ListView(padding: const EdgeInsets.all(16), children: [
                  InkWell(
                    onTap: _pickImage,
                    borderRadius: BorderRadius.circular(18),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(18),
                      child: SizedBox(
                        height: 170,
                        child: Stack(fit: StackFit.expand, children: [
                          _imagePath != null
                              ? Image.file(File(_imagePath!), fit: BoxFit.cover)
                              : CourseImage(url: _imageUrl, category: _title.text),
                          Container(color: Colors.black26),
                          const Center(
                            child: Column(mainAxisSize: MainAxisSize.min, children: [
                              FaIcon(FontAwesomeIcons.camera, color: Colors.white, size: 26),
                              SizedBox(height: 8),
                              Text('Cambiar imagen del curso', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                            ]),
                          ),
                        ]),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  FormCard(
                    title: 'Información',
                    icon: FontAwesomeIcons.circleInfo,
                    child: Column(children: [
                      AppTextField(controller: _title, label: 'Título', icon: FontAwesomeIcons.heading, validator: (v) => (v ?? '').trim().length < 3 ? 'Mínimo 3 caracteres' : null),
                      const SizedBox(height: 14),
                      AppTextField(controller: _description, label: 'Descripción', icon: FontAwesomeIcons.alignLeft, maxLines: 5, validator: (v) => (v ?? '').trim().isEmpty ? 'La descripción es obligatoria' : null),
                      const SizedBox(height: 14),
                      AppDropdown<int>(
                        label: 'Categoría',
                        icon: FontAwesomeIcons.layerGroup,
                        value: _category,
                        items: {for (final c in _categories) c.id: c.name},
                        onChanged: (v) => setState(() => _category = v),
                      ),
                      const SizedBox(height: 14),
                      AppDropdown<String>(
                        label: 'Nivel',
                        icon: FontAwesomeIcons.stairs,
                        value: _level,
                        items: const {'beginner': 'Principiante', 'intermediate': 'Intermedio', 'advanced': 'Avanzado', 'expert': 'Experto'},
                        onChanged: (v) => setState(() => _level = v ?? 'beginner'),
                      ),
                    ]),
                  ),
                  const SizedBox(height: 14),
                  FormCard(
                    title: 'Precio',
                    icon: FontAwesomeIcons.coins,
                    child: Column(children: [
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Curso gratuito', style: TextStyle(fontWeight: FontWeight.w700)),
                        activeThumbColor: AppColors.primary,
                        value: _free,
                        onChanged: (v) => setState(() => _free = v),
                      ),
                      if (!_free)
                        AppTextField(
                          controller: _price,
                          label: 'Precio (Bs.)',
                          icon: FontAwesomeIcons.moneyBill,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          validator: (v) => (double.tryParse((v ?? '').replaceAll(',', '.')) ?? -1) < 0 ? 'Precio inválido' : null,
                        ),
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Destacar en el catálogo', style: TextStyle(fontWeight: FontWeight.w700)),
                        subtitle: Text('Aparece primero en la portada', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                        activeThumbColor: AppColors.primary,
                        value: _featured,
                        onChanged: (v) => setState(() => _featured = v),
                      ),
                    ]),
                  ),
                  const SizedBox(height: 22),
                  LoadingButton(label: widget.courseId == null ? 'Crear curso' : 'Guardar cambios', icon: FontAwesomeIcons.floppyDisk, loading: _saving, onPressed: _save),
                  const SizedBox(height: 24),
                ]),
              ),
            ),
    );
  }
}
