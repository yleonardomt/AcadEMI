import '../core/utils/json_utils.dart';
import 'course.dart';

class EnrollmentItem {
  EnrollmentItem({
    required this.id,
    required this.courseId,
    required this.title,
    this.image,
    this.category,
    required this.teacher,
    required this.status,
    required this.progress,
    this.lastAccessed,
    this.certificateId,
  });

  final int id, courseId, progress;
  final String title, teacher, status;
  final String? image, category;
  final DateTime? lastAccessed;
  final int? certificateId;

  bool get isCompleted => status == 'completed';

  factory EnrollmentItem.fromJson(Map<String, dynamic> j) => EnrollmentItem(
        id: asInt(j['id']),
        courseId: asInt(j['course_id']),
        title: asString(j['title']),
        image: asStringOrNull(j['image']),
        category: asStringOrNull(j['category']),
        teacher: asString(j['teacher']),
        status: asString(j['status']),
        progress: asInt(j['progress']),
        lastAccessed: asDate(j['last_accessed']),
        certificateId: j['certificate_id'] == null ? null : asInt(j['certificate_id']),
      );
}

class CertificateItem {
  CertificateItem({
    required this.id,
    required this.code,
    required this.courseId,
    required this.course,
    required this.student,
    this.issuedAt,
    this.isRevoked = false,
    this.pdf,
  });

  final int id, courseId;
  final String code, course, student;
  final DateTime? issuedAt;
  final bool isRevoked;
  final String? pdf;

  factory CertificateItem.fromJson(Map<String, dynamic> j) => CertificateItem(
        id: asInt(j['id']),
        code: asString(j['code']),
        courseId: asInt(j['course_id']),
        course: asString(j['course']),
        student: asString(j['student']),
        issuedAt: asDate(j['issued_at']),
        isRevoked: asBool(j['is_revoked']),
        pdf: asStringOrNull(j['pdf']),
      );
}

class LearnData {
  LearnData({
    required this.courseId,
    required this.title,
    this.image,
    this.teacher = '',
    required this.modules,
    required this.progress,
    required this.completedCount,
    required this.totalLessons,
    this.status = '',
    this.nextLessonId,
    this.certificate,
    this.preview = false,
  });

  final int courseId, progress, completedCount, totalLessons;
  final String title, teacher, status;
  final String? image;
  final List<ModuleOutline> modules;
  final int? nextLessonId;
  final CertificateItem? certificate;
  final bool preview;

  factory LearnData.fromJson(Map<String, dynamic> j) {
    final c = (j['course'] as Map<String, dynamic>?) ?? {};
    return LearnData(
      courseId: asInt(c['id']),
      title: asString(c['title']),
      image: asStringOrNull(c['image']),
      teacher: asString(c['teacher']),
      modules: asList(j['modules']).map(ModuleOutline.fromJson).toList(),
      progress: asInt(j['progress']),
      completedCount: asInt(j['completed_count']),
      totalLessons: asInt(j['total_lessons']),
      status: asString(j['status']),
      nextLessonId: j['next_lesson_id'] == null ? null : asInt(j['next_lesson_id']),
      certificate:
          j['certificate'] is Map<String, dynamic> ? CertificateItem.fromJson(j['certificate']) : null,
      preview: asBool(j['preview']),
    );
  }
}

class LessonResource {
  LessonResource({required this.id, required this.title, required this.type, this.url});

  final int id;
  final String title, type;
  final String? url;

  factory LessonResource.fromJson(Map<String, dynamic> j) => LessonResource(
        id: asInt(j['id']),
        title: asString(j['title']),
        type: asString(j['type']),
        url: asStringOrNull(j['url']),
      );
}

class QuizInfo {
  QuizInfo({
    required this.title,
    this.description = '',
    required this.timeLimitMinutes,
    required this.passingScore,
    required this.maxAttempts,
    required this.attempts,
    this.bestScore,
    required this.questionsCount,
  });

  final String title, description;
  final int timeLimitMinutes, passingScore, maxAttempts, attempts, questionsCount;
  final int? bestScore;

  int get attemptsLeft => (maxAttempts - attempts).clamp(0, maxAttempts);

  factory QuizInfo.fromJson(Map<String, dynamic> j) => QuizInfo(
        title: asString(j['title']),
        description: asString(j['description']),
        timeLimitMinutes: asInt(j['time_limit_minutes']),
        passingScore: asInt(j['passing_score']),
        maxAttempts: asInt(j['max_attempts']),
        attempts: asInt(j['attempts']),
        bestScore: j['best_score'] == null ? null : asInt(j['best_score']),
        questionsCount: asInt(j['questions_count']),
      );
}

class Submission {
  Submission({this.file, this.comment = '', this.submittedAt, this.grade, this.feedback = '', this.gradedAt});

  final String? file;
  final String comment, feedback;
  final DateTime? submittedAt, gradedAt;
  final int? grade;

  factory Submission.fromJson(Map<String, dynamic> j) => Submission(
        file: asStringOrNull(j['file']),
        comment: asString(j['comment']),
        submittedAt: asDate(j['submitted_at']),
        grade: j['grade'] == null ? null : asInt(j['grade']),
        feedback: asString(j['feedback']),
        gradedAt: asDate(j['graded_at']),
      );
}

class AnswerItem {
  AnswerItem({required this.id, required this.content, required this.teacher});

  final int id;
  final String content, teacher;

  factory AnswerItem.fromJson(Map<String, dynamic> j) =>
      AnswerItem(id: asInt(j['id']), content: asString(j['content']), teacher: asString(j['teacher']));
}

/// Comentario o pregunta de una lección.
class DiscussionItem {
  DiscussionItem({
    required this.id,
    required this.content,
    required this.author,
    this.picture,
    this.isMine = false,
    this.isEdited = false,
    this.isAnswered = false,
    this.createdAt,
    this.answers = const [],
    this.lesson,
    this.course,
    this.lessonId,
  });

  final int id;
  final String content, author;
  final String? picture, lesson, course;
  final bool isMine, isEdited, isAnswered;
  final DateTime? createdAt;
  final List<AnswerItem> answers;
  final int? lessonId;

  factory DiscussionItem.fromJson(Map<String, dynamic> j) => DiscussionItem(
        id: asInt(j['id']),
        content: asString(j['content']),
        author: asString(j['author']),
        picture: asStringOrNull(j['picture']),
        isMine: asBool(j['is_mine']),
        isEdited: asBool(j['is_edited']),
        isAnswered: asBool(j['is_answered']),
        createdAt: asDate(j['created_at']),
        answers: asList(j['answers']).map(AnswerItem.fromJson).toList(),
        lesson: asStringOrNull(j['lesson']),
        course: asStringOrNull(j['course']),
        lessonId: j['lesson_id'] == null ? null : asInt(j['lesson_id']),
      );
}

class LessonDetail {
  LessonDetail({
    required this.id,
    required this.title,
    this.description = '',
    this.content = '',
    required this.type,
    this.durationMinutes = 0,
    this.isFree = false,
    this.videoUrl,
    this.youtubeId,
    this.videoFile,
    this.documentFile,
    this.resources = const [],
    this.module = '',
    required this.courseId,
    this.courseTitle = '',
    this.completed = false,
    this.progress = 0,
    this.isEnrolled = false,
    this.isStaff = false,
    this.nextLessonId,
    this.nextLessonTitle,
    this.prevLessonId,
    this.quiz,
    this.submission,
    this.assignmentDeadlineDays,
    this.comments = const [],
    this.questions = const [],
  });

  final int id, courseId, durationMinutes, progress;
  final String title, description, content, type, module, courseTitle;
  final bool isFree, completed, isEnrolled, isStaff;
  final String? videoUrl, youtubeId, videoFile, documentFile, nextLessonTitle;
  final List<LessonResource> resources;
  final int? nextLessonId, prevLessonId, assignmentDeadlineDays;
  final QuizInfo? quiz;
  final Submission? submission;
  final List<DiscussionItem> comments, questions;

  bool get isQuiz => type == 'quiz' || type == 'exam';

  factory LessonDetail.fromJson(Map<String, dynamic> j) => LessonDetail(
        id: asInt(j['id']),
        title: asString(j['title']),
        description: asString(j['description']),
        content: asString(j['content']),
        type: asString(j['type']),
        durationMinutes: asInt(j['duration_minutes']),
        isFree: asBool(j['is_free']),
        videoUrl: asStringOrNull(j['video_url']),
        youtubeId: asStringOrNull(j['youtube_id']),
        videoFile: asStringOrNull(j['video_file']),
        documentFile: asStringOrNull(j['document_file']),
        resources: asList(j['resources']).map(LessonResource.fromJson).toList(),
        module: asString(j['module']),
        courseId: asInt(j['course_id']),
        courseTitle: asString(j['course_title']),
        completed: asBool(j['completed']),
        progress: asInt(j['progress']),
        isEnrolled: asBool(j['is_enrolled']),
        isStaff: asBool(j['is_staff']),
        nextLessonId: j['next_lesson_id'] == null ? null : asInt(j['next_lesson_id']),
        nextLessonTitle: asStringOrNull(j['next_lesson_title']),
        prevLessonId: j['prev_lesson_id'] == null ? null : asInt(j['prev_lesson_id']),
        quiz: j['quiz'] is Map<String, dynamic> ? QuizInfo.fromJson(j['quiz']) : null,
        submission: j['submission'] is Map<String, dynamic> ? Submission.fromJson(j['submission']) : null,
        assignmentDeadlineDays: j['assignment_deadline_days'] == null ? null : asInt(j['assignment_deadline_days']),
        comments: asList(j['comments']).map(DiscussionItem.fromJson).toList(),
        questions: asList(j['questions']).map(DiscussionItem.fromJson).toList(),
      );
}

class QuizOption {
  QuizOption({required this.id, required this.text});

  final int id;
  final String text;

  factory QuizOption.fromJson(Map<String, dynamic> j) => QuizOption(id: asInt(j['id']), text: asString(j['text']));
}

class QuizQuestion {
  QuizQuestion({required this.id, required this.text, required this.type, required this.points, required this.options});

  final int id, points;
  final String text, type;
  final List<QuizOption> options;

  factory QuizQuestion.fromJson(Map<String, dynamic> j) => QuizQuestion(
        id: asInt(j['id']),
        text: asString(j['text']),
        type: asString(j['type']),
        points: asInt(j['points'], 1),
        options: asList(j['options']).map(QuizOption.fromJson).toList(),
      );
}

class QuizSession {
  QuizSession({
    required this.token,
    required this.title,
    required this.timeLimitMinutes,
    required this.passingScore,
    required this.questions,
  });

  final String token, title;
  final int timeLimitMinutes, passingScore;
  final List<QuizQuestion> questions;

  factory QuizSession.fromJson(Map<String, dynamic> j) => QuizSession(
        token: asString(j['token']),
        title: asString(j['title']),
        timeLimitMinutes: asInt(j['time_limit_minutes']),
        passingScore: asInt(j['passing_score']),
        questions: asList(j['questions']).map(QuizQuestion.fromJson).toList(),
      );
}

class QuizResult {
  QuizResult({
    required this.score,
    required this.totalPoints,
    required this.percentage,
    required this.passed,
    required this.passingScore,
    required this.timeSpent,
    required this.attemptNumber,
    required this.attemptsLeft,
    this.courseCompleted = false,
    this.certificateId,
  });

  final int score, totalPoints, percentage, passingScore, timeSpent, attemptNumber, attemptsLeft;
  final bool passed, courseCompleted;
  final int? certificateId;

  factory QuizResult.fromJson(Map<String, dynamic> j) {
    final r = (j['result'] as Map<String, dynamic>?) ?? {};
    final p = j['progress'] as Map<String, dynamic>?;
    return QuizResult(
      score: asInt(r['score']),
      totalPoints: asInt(r['total_points']),
      percentage: asInt(r['percentage']),
      passed: asBool(r['passed']),
      passingScore: asInt(r['passing_score']),
      timeSpent: asInt(r['time_spent']),
      attemptNumber: asInt(r['attempt_number']),
      attemptsLeft: asInt(r['attempts_left']),
      courseCompleted: p != null && asBool(p['course_completed']),
      certificateId: p?['certificate_id'] == null ? null : asInt(p!['certificate_id']),
    );
  }
}

class GradeResult {
  GradeResult({
    required this.id,
    required this.course,
    required this.courseId,
    required this.evaluation,
    required this.score,
    required this.totalPoints,
    required this.percentage,
    required this.passed,
    required this.attempt,
    this.completedAt,
  });

  final int id, courseId, score, totalPoints, percentage, attempt;
  final String course, evaluation;
  final bool passed;
  final DateTime? completedAt;

  factory GradeResult.fromJson(Map<String, dynamic> j) => GradeResult(
        id: asInt(j['id']),
        course: asString(j['course']),
        courseId: asInt(j['course_id']),
        evaluation: asString(j['evaluation']),
        score: asInt(j['score']),
        totalPoints: asInt(j['total_points']),
        percentage: asInt(j['percentage']),
        passed: asBool(j['passed']),
        attempt: asInt(j['attempt']),
        completedAt: asDate(j['completed_at']),
      );
}
