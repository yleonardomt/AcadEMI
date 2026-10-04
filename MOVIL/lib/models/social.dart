import '../core/utils/json_utils.dart';

class AppNotification {
  AppNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.message,
    required this.isRead,
    this.createdAt,
  });

  final int id;
  final String type, title, message;
  final bool isRead;
  final DateTime? createdAt;

  AppNotification asRead() =>
      AppNotification(id: id, type: type, title: title, message: message, isRead: true, createdAt: createdAt);

  factory AppNotification.fromJson(Map<String, dynamic> j) => AppNotification(
        id: asInt(j['id']),
        type: asString(j['type']),
        title: asString(j['title']),
        message: asString(j['message']),
        isRead: asBool(j['is_read']),
        createdAt: asDate(j['created_at']),
      );
}

class ChatMessage {
  ChatMessage({required this.id, required this.sender, required this.message, this.createdAt});

  final int id;
  final String sender, message;
  final DateTime? createdAt;

  bool get isBot => sender == 'bot';

  factory ChatMessage.fromJson(Map<String, dynamic> j) => ChatMessage(
        id: asInt(j['id']),
        sender: asString(j['sender']),
        message: asString(j['message']),
        createdAt: asDate(j['created_at']),
      );
}

class TeacherStudent {
  TeacherStudent({
    required this.id,
    required this.student,
    required this.email,
    this.picture,
    this.course = '',
    this.courseId,
    required this.progress,
    required this.statusLabel,
    this.evaluations = 0,
    this.averageScore,
  });

  final int id, progress, evaluations;
  final String student, email, course, statusLabel;
  final String? picture;
  final int? courseId, averageScore;

  factory TeacherStudent.fromJson(Map<String, dynamic> j) => TeacherStudent(
        id: asInt(j['id']),
        student: asString(j['student']),
        email: asString(j['email']),
        picture: asStringOrNull(j['picture']),
        course: asString(j['course']),
        courseId: j['course_id'] == null ? null : asInt(j['course_id']),
        progress: asInt(j['progress']),
        statusLabel: asString(j['status_label']),
        evaluations: asInt(j['evaluations']),
        averageScore: j['average_score'] == null ? null : asInt(j['average_score']),
      );
}
