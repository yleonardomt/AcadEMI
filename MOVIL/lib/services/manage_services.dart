import 'dart:convert';

import '../core/utils/json_utils.dart';
import '../models/learning.dart';
import 'services.dart';

/// Endpoints de gestión: progreso del estudiante, docente (cursos, módulos,
/// lecciones, evaluaciones, cupones) y administrador. Devuelven el JSON tal
/// cual: estas pantallas de gestión trabajan directamente con los mapas.
extension ManageApi on AppServices {
  // ---------- Estudiante ----------
  Future<Map<String, dynamic>> progress() => client.get('progress/');

  Future<DiscussionItem> editComment(int id, String content) async => DiscussionItem.fromJson(
      (await client.post('comments/$id/edit/', body: {'content': content}))['comment']);

  Future<String> emailCertificate(int id) async => asString((await client.post('certificates/$id/email/'))['message']);

  // ---------- Docente: cursos ----------
  Future<Map<String, dynamic>> manageCourse(int id) async =>
      (await client.get('manage/courses/$id/'))['course'] as Map<String, dynamic>;

  Future<Map<String, dynamic>> _save(String path, Map<String, dynamic> body, {String? fileField, String? filePath}) {
    if (filePath != null && fileField != null) {
      return client.upload(path,
          fields: body.map((k, v) => MapEntry(k, v is String ? v : (v is List || v is Map ? jsonEncode(v) : '$v'))),
          fileField: fileField,
          filePath: filePath);
    }
    return client.post(path, body: body);
  }

  Future<Map<String, dynamic>> saveCourse(Map<String, dynamic> body, {int? id, String? imagePath}) =>
      _save(id == null ? 'manage/courses/create/' : 'manage/courses/$id/update/', body,
          fileField: 'image', filePath: imagePath);

  Future<String> deleteCourse(int id) async => asString((await client.post('manage/courses/$id/delete/'))['message']);

  Future<String> publishCourse(int id) async => asString((await client.post('manage/courses/$id/publish/'))['message']);

  Future<Map<String, dynamic>> courseStats(int id) => client.get('manage/courses/$id/stats/');

  Future<Map<String, dynamic>> courseResults(int id) => client.get('manage/courses/$id/results/');

  // ---------- Docente: módulos y lecciones ----------
  Future<void> saveModule({int? courseId, int? moduleId, required String title, String description = ''}) =>
      client.post(moduleId == null ? 'manage/courses/$courseId/modules/' : 'manage/modules/$moduleId/update/',
          body: {'title': title, 'description': description});

  Future<void> deleteModule(int id) => client.post('manage/modules/$id/delete/');

  Future<void> moveModule(int id, String direction) => client.post('manage/modules/$id/move/$direction/');

  Future<Map<String, dynamic>> lessonAdmin(int id) async =>
      (await client.get('manage/lessons/$id/'))['lesson'] as Map<String, dynamic>;

  Future<Map<String, dynamic>> saveLesson(Map<String, dynamic> body,
          {int? moduleId, int? lessonId, String? fileField, String? filePath}) =>
      _save(lessonId == null ? 'manage/modules/$moduleId/lessons/' : 'manage/lessons/$lessonId/update/', body,
          fileField: fileField, filePath: filePath);

  Future<void> deleteLesson(int id) => client.post('manage/lessons/$id/delete/');

  Future<void> moveLesson(int id, String direction) => client.post('manage/lessons/$id/move/$direction/');

  Future<Map<String, dynamic>> submissions(int lessonId) => client.get('manage/lessons/$lessonId/submissions/');

  Future<void> gradeSubmission(int id, int grade, String feedback) =>
      client.post('manage/submissions/$id/grade/', body: {'grade': grade, 'feedback': feedback});

  // ---------- Docente: cupones ----------
  Future<Map<String, dynamic>> teacherCoupons() => client.get('manage/coupons/');

  Future<void> saveTeacherCoupon(Map<String, dynamic> body, {int? id}) =>
      client.post(id == null ? 'manage/coupons/save/' : 'manage/coupons/$id/save/', body: body);

  Future<void> toggleTeacherCoupon(int id) => client.post('manage/coupons/$id/toggle/');

  Future<void> deleteTeacherCoupon(int id) => client.post('manage/coupons/$id/delete/');

  // ---------- Administrador ----------
  Future<Map<String, dynamic>> adminUsers({String? q, String? role}) =>
      client.get('admin/users/', query: {'q': q, 'role': role});

  Future<void> adminCreateUser(Map<String, dynamic> body) => client.post('admin/users/create/', body: body);

  Future<void> adminUpdateUser(int id, Map<String, dynamic> body) => client.post('admin/users/$id/update/', body: body);

  Future<void> adminToggleUser(int id) => client.post('admin/users/$id/toggle/');

  Future<void> adminDeleteUser(int id) => client.post('admin/users/$id/delete/');

  Future<void> adminResetPassword(int id, String password) =>
      client.post('admin/users/$id/reset-password/', body: {'new_password': password});

  Future<Map<String, dynamic>> adminCourses({String? status}) => client.get('admin/courses/', query: {'status': status});

  Future<void> adminModerateCourse(int id, String action, {String reason = ''}) =>
      client.post('admin/courses/$id/$action/', body: {'reason': reason});

  Future<Map<String, dynamic>> adminCategories() => client.get('admin/categories/');

  Future<void> adminSaveCategory(Map<String, dynamic> body, {int? id}) =>
      client.post(id == null ? 'admin/categories/save/' : 'admin/categories/$id/save/', body: body);

  Future<void> adminDeleteCategory(int id) => client.post('admin/categories/$id/delete/');

  Future<Map<String, dynamic>> adminReports({String? status}) => client.get('admin/reports/', query: {'status': status});

  Future<void> adminResolveReport(int id, String action) => client.post('admin/reports/$id/$action/');

  Future<Map<String, dynamic>> adminCoupons() => client.get('admin/coupons/');

  Future<void> adminSaveCoupon(Map<String, dynamic> body, {int? id}) =>
      client.post(id == null ? 'admin/coupons/save/' : 'admin/coupons/$id/save/', body: body);

  Future<void> adminToggleCoupon(int id) => client.post('admin/coupons/$id/toggle/');

  Future<Map<String, dynamic>> adminPayments({String? status}) => client.get('admin/payments/', query: {'status': status});

  Future<Map<String, dynamic>> adminCertificates() => client.get('admin/certificates/');

  Future<void> adminToggleCertificate(int id) => client.post('admin/certificates/$id/toggle/');

  Future<Map<String, dynamic>> adminGenerateReport(String? from, String? to) =>
      client.post('admin/generate-report/', body: {'date_from': from, 'date_to': to});
}
