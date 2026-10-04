import 'dart:io';

import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../models/user.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';

class EditProfileScreen extends StatefulWidget {
  const EditProfileScreen({super.key});

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _form = GlobalKey<FormState>();
  late final AppUser _user = context.read<AuthProvider>().user!;
  late final Map<String, TextEditingController> _c = {
    'name': TextEditingController(text: _user.name),
    'email': TextEditingController(text: _user.email),
    'phone': TextEditingController(text: _user.phone),
    'bio': TextEditingController(text: _user.isTeacher ? _user.teacherBio : _user.bio),
    'city': TextEditingController(text: _user.city),
    'university': TextEditingController(text: _user.university),
    'career': TextEditingController(text: _user.career),
    'semester': TextEditingController(text: _user.semester),
    'specialty': TextEditingController(text: _user.specialty),
    'institution': TextEditingController(text: _user.institution),
    'linkedin': TextEditingController(text: _user.linkedin),
    'website': TextEditingController(text: _user.website),
  };

  String? _picturePath;
  bool _saving = false;

  @override
  void dispose() {
    for (final c in _c.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _pickPicture() async {
    final file = await ImagePicker().pickImage(source: ImageSource.gallery, maxWidth: 1024, imageQuality: 85);
    if (file != null && mounted) setState(() => _picturePath = file.path);
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _saving = true);
    final auth = context.read<AuthProvider>();
    final body = <String, dynamic>{
      'name': _c['name']!.text.trim(),
      'email': _c['email']!.text.trim(),
      'phone': _c['phone']!.text.trim(),
      if (_user.isTeacher) ...{
        'teacher_bio': _c['bio']!.text.trim(),
        'specialty': _c['specialty']!.text.trim(),
        'institution': _c['institution']!.text.trim(),
        'linkedin': _c['linkedin']!.text.trim(),
        'website': _c['website']!.text.trim(),
      } else ...{
        'bio': _c['bio']!.text.trim(),
        'city': _c['city']!.text.trim(),
        'university': _c['university']!.text.trim(),
        'career': _c['career']!.text.trim(),
        'semester': _c['semester']!.text.trim(),
      },
    };
    try {
      final updated = await auth.api.updateProfile(body, picturePath: _picturePath);
      auth.updateUser(updated);
      if (mounted) {
        showToast(context, 'Perfil actualizado correctamente.', success: true);
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _saving = false);
  }

  Widget _gap() => const SizedBox(height: 14);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Editar perfil')),
      body: GestureDetector(
        onTap: () => FocusScope.of(context).unfocus(),
        child: Form(
          key: _form,
          child: ListView(padding: const EdgeInsets.all(16), children: [
            Center(
              child: Stack(children: [
                _picturePath != null
                    ? CircleAvatar(radius: 52, backgroundImage: FileImage(File(_picturePath!)))
                    : UserAvatar(name: _user.name, url: _user.picture, radius: 52),
                Positioned(
                  right: 0,
                  bottom: 0,
                  child: InkWell(
                    onTap: _pickPicture,
                    child: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(color: Theme.of(context).colorScheme.primary, shape: BoxShape.circle, border: Border.all(color: context.palette.surface, width: 2)),
                      child: const Center(child: FaIcon(FontAwesomeIcons.camera, size: 14, color: Colors.white)),
                    ),
                  ),
                ),
              ]),
            ),
            const SizedBox(height: 20),
            FormCard(
              title: 'Datos personales',
              icon: FontAwesomeIcons.idCard,
              child: Column(children: [
                AppTextField(controller: _c['name']!, label: 'Nombre completo', icon: FontAwesomeIcons.user, validator: (v) => (v ?? '').trim().isEmpty ? 'Ingresa tu nombre' : null),
                _gap(),
                AppTextField(
                  controller: _c['email']!,
                  label: 'Correo electrónico',
                  icon: FontAwesomeIcons.envelope,
                  keyboardType: TextInputType.emailAddress,
                  validator: (v) => RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch((v ?? '').trim()) ? null : 'Ingresa un correo válido',
                ),
                _gap(),
                AppTextField(controller: _c['phone']!, label: 'Teléfono', icon: FontAwesomeIcons.phone, keyboardType: TextInputType.phone),
                _gap(),
                AppTextField(controller: _c['bio']!, label: _user.isTeacher ? 'Biografía profesional' : 'Sobre mí', icon: FontAwesomeIcons.quoteLeft, maxLines: 4),
              ]),
            ),
            const SizedBox(height: 14),
            if (_user.isStudent)
              FormCard(
                title: 'Estudios',
                icon: FontAwesomeIcons.graduationCap,
                child: Column(children: [
                  AppTextField(controller: _c['university']!, label: 'Universidad o institución', icon: FontAwesomeIcons.buildingColumns),
                  _gap(),
                  AppTextField(controller: _c['career']!, label: 'Carrera', icon: FontAwesomeIcons.book),
                  _gap(),
                  Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Expanded(child: AppTextField(controller: _c['city']!, label: 'Ciudad', icon: FontAwesomeIcons.locationDot)),
                    const SizedBox(width: 12),
                    Expanded(child: AppTextField(controller: _c['semester']!, label: 'Semestre', icon: FontAwesomeIcons.hashtag)),
                  ]),
                ]),
              )
            else if (_user.isTeacher)
              FormCard(
                title: 'Perfil docente',
                icon: FontAwesomeIcons.chalkboardUser,
                child: Column(children: [
                  AppTextField(controller: _c['specialty']!, label: 'Especialidad', icon: FontAwesomeIcons.award),
                  _gap(),
                  AppTextField(controller: _c['institution']!, label: 'Institución', icon: FontAwesomeIcons.buildingColumns),
                  _gap(),
                  AppTextField(controller: _c['linkedin']!, label: 'LinkedIn', icon: FontAwesomeIcons.linkedin, keyboardType: TextInputType.url),
                  _gap(),
                  AppTextField(controller: _c['website']!, label: 'Sitio web', icon: FontAwesomeIcons.globe, keyboardType: TextInputType.url),
                ]),
              ),
            const SizedBox(height: 22),
            LoadingButton(label: 'Guardar cambios', icon: FontAwesomeIcons.floppyDisk, loading: _saving, onPressed: _save),
            const SizedBox(height: 20),
          ]),
        ),
      ),
    );
  }
}
