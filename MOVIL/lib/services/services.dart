import '../core/network/api_client.dart';
import '../core/utils/json_utils.dart';
import '../models/commerce.dart';
import '../models/course.dart';
import '../models/learning.dart';
import '../models/social.dart';
import '../models/user.dart';

/// Resultado de la portada.
class HomeData {
  HomeData({
    required this.featured,
    required this.bestsellers,
    required this.newest,
    required this.categories,
    required this.continueLearning,
    this.stats,
    this.emiDiscount,
    this.totalCourses = 0,
  });

  final List<Course> featured, bestsellers, newest;
  final List<CategoryItem> categories;
  final List<EnrollmentItem> continueLearning;
  final Map<String, dynamic>? stats;
  final double? emiDiscount;
  final int totalCourses;
}

class CoursePage {
  CoursePage({required this.courses, required this.page, required this.total, required this.hasMore});

  final List<Course> courses;
  final int page, total;
  final bool hasMore;
}

/// Fachada de la API: un método por endpoint, agrupados por dominio.
class AppServices {
  AppServices(this.client);

  final ApiClient client;

  // ---------- Cuenta ----------
  /// RF-06: el servidor pide CAPTCHA tras varios intentos fallidos.
  Future<Map<String, dynamic>> captcha() async =>
      (await client.get('auth/captcha/'))['captcha'] as Map<String, dynamic>;

  Future<(String, AppUser)> login(String identifier, String password, {Map<String, dynamic>? captcha}) async {
    final r = await client.post('auth/login/', body: {
      'identifier': identifier,
      'password': password,
      if (captcha != null) ...captcha,
    });
    return (asString(r['token']), AppUser.fromJson(r['user']));
  }

  Future<(String, AppUser, bool)> register(Map<String, dynamic> body) async {
    final r = await client.post('auth/register/', body: body);
    return (asString(r['token']), AppUser.fromJson(r['user']), r['email_sent'] != false);
  }

  Future<String> requestPasswordReset(String email, Map<String, dynamic> captcha) async {
    final r = await client.post('auth/password-reset/', body: {'email': email, ...captcha});
    return asString(r['message']);
  }

  Future<(AppUser, int)> me() async {
    final r = await client.get('me/');
    return (AppUser.fromJson(r['user']), asInt(r['unread_notifications']));
  }

  Future<AppUser> updateProfile(Map<String, dynamic> body, {String? picturePath}) async {
    final Map<String, dynamic> r;
    if (picturePath != null) {
      r = await client.upload(
        'me/',
        fields: body.map((k, v) => MapEntry(k, '$v')),
        fileField: 'profile_picture',
        filePath: picturePath,
      );
    } else {
      r = await client.post('me/', body: body);
    }
    return AppUser.fromJson(r['user']);
  }

  Future<String> changePassword(String oldPw, String newPw, String confirm) async {
    final r = await client.post('auth/change-password/',
        body: {'old_password': oldPw, 'new_password': newPw, 'confirm_password': confirm});
    return asString(r['token']);
  }

  Future<String> resendVerification() async =>
      asString((await client.post('auth/resend-verification/'))['message']);

  Future<bool> isEmailVerified() async =>
      asBool((await client.get('auth/verification-status/'))['email_verified']);

  // ---------- Catálogo ----------
  Future<HomeData> home() async {
    final r = await client.get('home/');
    List<Course> courses(String k) => asList(r[k]).map(Course.fromJson).toList();
    return HomeData(
      featured: courses('featured'),
      bestsellers: courses('bestsellers'),
      newest: courses('newest'),
      categories: asList(r['categories']).map(CategoryItem.fromJson).toList(),
      continueLearning: asList(r['continue_learning']).map(EnrollmentItem.fromJson).toList(),
      stats: r['stats'] as Map<String, dynamic>?,
      emiDiscount: r['emi_discount'] == null ? null : asDouble(r['emi_discount']),
      totalCourses: asInt(r['total_courses']),
    );
  }

  Future<List<CategoryItem>> categories() async =>
      asList((await client.get('categories/'))['categories']).map(CategoryItem.fromJson).toList();

  Future<CoursePage> courses({
    String? q,
    int? category,
    String? level,
    String? price,
    String sort = 'featured',
    int page = 1,
  }) async {
    final r = await client.get('courses/', query: {
      'q': q,
      'category': category,
      'level': level,
      'price': price,
      'sort': sort,
      'page': page,
    });
    return CoursePage(
      courses: asList(r['courses']).map(Course.fromJson).toList(),
      page: asInt(r['page'], 1),
      total: asInt(r['total']),
      hasMore: asBool(r['has_more']),
    );
  }

  Future<Course> courseDetail(int id) async => Course.fromJson((await client.get('courses/$id/'))['course']);

  Future<bool> toggleFavorite(int courseId) async =>
      asBool((await client.post('courses/$courseId/favorite/'))['is_favorite']);

  Future<List<Course>> favorites() async =>
      asList((await client.get('favorites/'))['courses']).map(Course.fromJson).toList();

  Future<String> saveReview(int courseId, int rating, String comment) async => asString(
      (await client.post('courses/$courseId/review/', body: {'rating': rating, 'comment': comment}))['message']);

  Future<void> deleteReview(int reviewId) => client.post('reviews/$reviewId/delete/');

  Future<String> report(String type, int contentId, String reason) async => asString((await client.post(
          'reports/', body: {'report_type': type, 'content_id': contentId, 'reason': reason}))['message']);

  // ---------- Carrito y compras ----------
  Future<CartData> cart() async => CartData.fromResponse(await client.get('cart/'));

  Future<int> cartAdd(int courseId) async => asInt((await client.post('cart/add/$courseId/'))['items_count']);

  Future<int> cartRemove(int courseId) async =>
      asInt((await client.post('cart/remove/$courseId/'))['items_count']);

  Future<(CartData, String, bool)> applyCoupon(String code) async {
    final r = await client.post('cart/coupon/', body: {'code': code});
    return (CartData.fromResponse(r), asString(r['message']), asBool(r['applied']));
  }

  Future<Map<String, dynamic>> checkout(Map<String, dynamic> body) => client.post('checkout/', body: body);

  Future<(List<PaymentSummary>, double)> purchases() async {
    final r = await client.get('purchases/');
    return (asList(r['payments']).map(PaymentSummary.fromJson).toList(), asDouble(r['total_spent']));
  }

  Future<PaymentSummary> purchaseDetail(int id) async =>
      PaymentSummary.fromJson((await client.get('purchases/$id/'))['payment']);

  // ---------- Aprendizaje ----------
  /// Para un estudiante: sus inscripciones. Para un docente: sus cursos.
  Future<Map<String, dynamic>> myCoursesRaw() => client.get('my-courses/');

  Future<LearnData> learn(int courseId) async => LearnData.fromJson(await client.get('learn/$courseId/'));

  Future<LessonDetail> lesson(int id) async => LessonDetail.fromJson((await client.get('lessons/$id/'))['lesson']);

  Future<Map<String, dynamic>> completeLesson(int id) => client.post('lessons/$id/complete/');

  Future<QuizSession> quizStart(int lessonId) async =>
      QuizSession.fromJson(await client.post('quizzes/$lessonId/start/'));

  Future<QuizResult> quizSubmit(int lessonId, String token, Map<String, int> answers, int tabSwitches) async =>
      QuizResult.fromJson(await client.post('quizzes/$lessonId/submit/', body: {
        'token': token,
        'answers': answers.map((k, v) => MapEntry(k, v)),
        'tab_switches': tabSwitches,
      }));

  Future<String> submitAssignment(int lessonId, String filePath, String comment) async => asString((await client
          .upload('lessons/$lessonId/assignment/', fields: {'comment': comment}, fileField: 'file', filePath: filePath))[
      'message']);

  Future<DiscussionItem> addComment(int lessonId, String content) async => DiscussionItem.fromJson(
      (await client.post('lessons/$lessonId/comments/', body: {'content': content}))['comment']);

  Future<void> deleteComment(int id) => client.post('comments/$id/delete/');

  Future<DiscussionItem> addQuestion(int lessonId, String content) async => DiscussionItem.fromJson(
      (await client.post('lessons/$lessonId/questions/', body: {'content': content}))['question']);

  // ---------- Social ----------
  Future<(List<AppNotification>, int)> notifications() async {
    final r = await client.get('notifications/');
    return (asList(r['notifications']).map(AppNotification.fromJson).toList(), asInt(r['unread']));
  }

  Future<void> markAllNotificationsRead() => client.post('notifications/read-all/');

  Future<void> markNotificationRead(int id) => client.post('notifications/$id/read/');

  Future<List<CertificateItem>> certificates() async =>
      asList((await client.get('certificates/'))['certificates']).map(CertificateItem.fromJson).toList();

  Future<CertificateItem?> verifyCertificate(String code) async {
    final r = await client.get('certificates/verify/${Uri.encodeComponent(code.trim())}/');
    return r['certificate'] is Map<String, dynamic> && asBool(r['valid'])
        ? CertificateItem.fromJson(r['certificate'])
        : null;
  }

  Future<List<GradeResult>> grades() async =>
      asList((await client.get('grades/'))['results']).map(GradeResult.fromJson).toList();

  Future<List<ChatMessage>> chatHistory() async =>
      asList((await client.get('chatbot/history/'))['messages']).map(ChatMessage.fromJson).toList();

  Future<ChatMessage> chatSend(String message) async =>
      ChatMessage.fromJson((await client.post('chatbot/send/', body: {'message': message}))['reply']);

  // ---------- Docente / administrador ----------
  Future<Map<String, dynamic>> teacherDashboard() => client.get('teacher/dashboard/');

  Future<List<TeacherStudent>> teacherStudents() async =>
      asList((await client.get('teacher/students/'))['students']).map(TeacherStudent.fromJson).toList();

  Future<(String, List<TeacherStudent>)> courseStudents(int courseId) async {
    final r = await client.get('teacher/courses/$courseId/students/');
    return (
      asString((r['course'] as Map<String, dynamic>)['title']),
      asList(r['students']).map(TeacherStudent.fromJson).toList()
    );
  }

  Future<List<DiscussionItem>> teacherQuestions() async =>
      asList((await client.get('teacher/questions/'))['questions']).map(DiscussionItem.fromJson).toList();

  Future<void> answerQuestion(int id, String content) =>
      client.post('teacher/questions/$id/answer/', body: {'content': content});

  Future<List<Review>> teacherReviews() async =>
      asList((await client.get('teacher/reviews/'))['reviews']).map(Review.fromJson).toList();
}
