@Tags(['golden'])
library;

import 'package:flutter_test/flutter_test.dart' show Tags;
// Genera capturas (test/screenshots/*.png) de las pantallas principales usando
// respuestas reales del backend guardadas en test/fixtures. Uso:
//   flutter test test/screenshots_test.dart --update-goldens
import 'dart:convert';
import 'dart:io';

import 'package:academi_movil/core/network/api_client.dart';
import 'package:academi_movil/core/theme/app_theme.dart';
import 'package:academi_movil/models/learning.dart';
import 'package:academi_movil/providers/auth_provider.dart';
import 'package:academi_movil/providers/cart_provider.dart';
import 'package:academi_movil/providers/settings_provider.dart';
import 'package:academi_movil/providers/shell_nav.dart';
import 'package:academi_movil/screens/auth/login_screen.dart';
import 'package:academi_movil/screens/catalog/course_detail_screen.dart';
import 'package:academi_movil/screens/chatbot/chatbot_screen.dart';
import 'package:academi_movil/screens/commerce/cart_screen.dart';
import 'package:academi_movil/screens/commerce/purchases_screen.dart';
import 'package:academi_movil/screens/home/main_shell.dart';
import 'package:academi_movil/screens/learning/learn_screen.dart';
import 'package:academi_movil/screens/learning/lesson_screen.dart';
import 'package:academi_movil/screens/profile/certificate_detail_screen.dart';
import 'package:academi_movil/screens/profile/certificates_screen.dart';
import 'package:academi_movil/screens/profile/grades_screen.dart';
import 'package:academi_movil/screens/profile/notifications_screen.dart';
import 'package:academi_movil/screens/auth/register_screen.dart';
import 'package:academi_movil/screens/learning/quiz_screen.dart';
import 'package:academi_movil/screens/admin/admin_categories_screen.dart';
import 'package:academi_movil/screens/admin/admin_certificates_screen.dart';
import 'package:academi_movil/screens/admin/admin_coupons_screen.dart';
import 'package:academi_movil/screens/admin/admin_courses_screen.dart';
import 'package:academi_movil/screens/admin/admin_hub_screen.dart';
import 'package:academi_movil/screens/admin/admin_payments_screen.dart';
import 'package:academi_movil/screens/admin/admin_report_generator_screen.dart';
import 'package:academi_movil/screens/admin/admin_reports_screen.dart';
import 'package:academi_movil/screens/admin/admin_users_screen.dart';
import 'package:academi_movil/screens/profile/progress_screen.dart';
import 'package:academi_movil/screens/teacher/course_form_screen.dart';
import 'package:academi_movil/screens/teacher/course_stats_screen.dart';
import 'package:academi_movil/screens/teacher/lesson_form_screen.dart';
import 'package:academi_movil/screens/teacher/manage_course_screen.dart';
import 'package:academi_movil/screens/teacher/teacher_coupons_screen.dart';
import 'package:flutter/material.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:flutter/rendering.dart' show debugDisableShadows;
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

Map<String, dynamic> fx(String name) =>
    jsonDecode(File('test/fixtures/$name.json').readAsStringSync()) as Map<String, dynamic>;

/// Cliente que responde con los fixtures en vez de usar la red.
class FakeClient extends ApiClient {
  FakeClient(this.role) : super(baseUrl: 'http://fake');
  final String role;

  Map<String, dynamic> _route(String path) {
    if (path.startsWith('me')) return {'success': true, 'user': fx('login_$role')['user'], 'unread_notifications': 3};
    if (path.startsWith('home')) return fx('home');
    if (path.startsWith('categories')) return fx('categories');
    if (path.startsWith('courses/?') || path == 'courses/') return fx('courses');
    if (path.startsWith('courses/')) return fx('course_detail');
    if (path.startsWith('favorites')) return fx('favorites');
    if (path.startsWith('cart')) return fx('cart');
    if (path.startsWith('my-courses')) return role == 'teacher' ? fx('t_courses') : fx('my_courses');
    if (path.startsWith('learn/')) return fx('learn');
    if (path.startsWith('lessons/')) return fx('lesson_${_lessonType ?? 'video'}');
    if (path.startsWith('purchases/')) return fx('invoice');
    if (path.startsWith('purchases')) return fx('purchases');
    if (path.startsWith('notifications')) return fx('notifications');
    if (path.startsWith('certificates')) return fx('certificates');
    if (path.startsWith('grades')) return fx('grades');
    if (path.startsWith('chatbot/history')) return fx('chat_history');
    if (path.startsWith('teacher/dashboard')) return fx(role == 'admin' ? 'a_dashboard' : 't_dashboard');
    if (path.startsWith('teacher/questions')) return fx('t_questions');
    if (path.startsWith('teacher/students')) return fx('t_students');
    if (path.startsWith('teacher/reviews')) return fx('t_reviews');
    if (path.startsWith('progress')) return fx('progress');
    if (path.startsWith('admin/users')) return fx('admin_users');
    if (path.startsWith('admin/courses')) return fx('admin_courses');
    if (path.startsWith('admin/categories')) return fx('admin_categories');
    if (path.startsWith('admin/reports')) return fx('admin_reports');
    if (path.startsWith('admin/coupons')) return fx('admin_coupons');
    if (path.startsWith('admin/payments')) return fx('admin_payments');
    if (path.startsWith('admin/certificates')) return fx('admin_certificates');
    if (path.startsWith('admin/generate-report')) return fx('admin_report_gen');
    if (path.startsWith('manage/courses') && path.endsWith('/stats/')) return fx('course_stats');
    if (path.startsWith('manage/courses') && path.endsWith('/results/')) return fx('course_results');
    if (path.startsWith('manage/courses')) return fx('manage_course');
    if (path.startsWith('manage/coupons')) return fx('manage_coupons');
    if (path.startsWith('manage/lessons')) return fx('lesson_admin_quiz');
    if (path.startsWith('auth/captcha')) return fx('captcha');
    if (path.startsWith('quizzes/')) {
      return {
        'success': true, 'token': 't', 'title': 'Cuestionario del módulo', 'time_limit_minutes': 30, 'passing_score': 70,
        'questions': [
          {'id': 1, 'text': '¿Cuál de las siguientes opciones describe mejor el concepto principal visto en la lección?', 'type': 'single', 'points': 2,
           'options': [{'id': 1, 'text': 'Una respuesta larga que debe ajustarse correctamente al ancho de la pantalla del móvil'}, {'id': 2, 'text': 'Opción B'}, {'id': 3, 'text': 'Opción C'}]},
        ],
      };
    }
    return {'success': true};
  }

  String? _lessonType;
  void lessonType(String t) => _lessonType = t;

  @override
  Future<Map<String, dynamic>> get(String path, {Map<String, dynamic>? query}) async => _route(path);
  @override
  Future<Map<String, dynamic>> post(String path, {Map<String, dynamic>? body}) async {
    if (path.startsWith('auth/login')) return fx('login_$role');
    return _route(path);
  }
}

Future<void> loadFonts() async {
  Future<void> load(String family, String path) async {
    final bytes = await File(path).readAsBytes();
    final loader = FontLoader(family)..addFont(Future.value(ByteData.view(Uint8List.fromList(bytes).buffer)));
    await loader.load();
  }

  await load('Inter', 'assets/fonts/Inter.ttf');
  const fa = '${'/home/yhonatan/.pub-cache/hosted/pub.dev/font_awesome_flutter-11.0.0/lib/fonts'}';
  await load('FontAwesomeSolid', '$fa/Font-Awesome-7-Free-Solid-900.otf');
  await load('packages/font_awesome_flutter/FontAwesomeSolid', '$fa/Font-Awesome-7-Free-Solid-900.otf');
  await load('FontAwesomeRegular', '$fa/Font-Awesome-7-Free-Regular-400.otf');
  await load('packages/font_awesome_flutter/FontAwesomeRegular', '$fa/Font-Awesome-7-Free-Regular-400.otf');
  await load('FontAwesomeBrands', '$fa/Font-Awesome-7-Brands-Regular-400.otf');
  await load('packages/font_awesome_flutter/FontAwesomeBrands', '$fa/Font-Awesome-7-Brands-Regular-400.otf');
}

Future<void> shot(WidgetTester tester, String name, Widget screen,
    {String role = 'student', bool dark = false, String? lesson, int tab = 0}) async {
  debugDisableShadows = false; // sombras difuminadas reales
  tester.view.physicalSize = const Size(1170, 2532);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  SharedPreferences.setMockInitialValues({});
  final settings = SettingsProvider();
  final client = FakeClient(role);
  if (lesson != null) client.lessonType(lesson);
  final auth = AuthProvider(settings, testClient: client);
  await auth.login('x', 'y');
  final nav = ShellNav()..tab = tab;
  await tester.pumpWidget(MultiProvider(
    providers: [
      ChangeNotifierProvider<SettingsProvider>.value(value: settings),
      ChangeNotifierProvider<AuthProvider>.value(value: auth),
      ChangeNotifierProvider<CartProvider>(create: (_) => CartProvider(auth)..load()),
      ChangeNotifierProvider<ShellNav>.value(value: nav),
    ],
    child: MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: dark ? ThemeMode.dark : ThemeMode.light,
      home: screen,
    ),
  ));
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
  await expectLater(find.byType(MaterialApp), matchesGoldenFile('screenshots/$name.png'));
  debugDisableShadows = true;
}

void main() {
  setUpAll(() async {
    await loadFonts();
    await initializeDateFormatting('es');
    FlutterSecureStorageMock.install();
  });

  testWidgets('login', (t) async => shot(t, 'login', const LoginScreen()));
  testWidgets('register', (t) async => shot(t, 'register', const RegisterScreen()));
  testWidgets('home', (t) async => shot(t, 'home', const MainShell()));
  testWidgets('home dark', (t) async => shot(t, 'home_dark', const MainShell(), dark: true));
  testWidgets('catalog', (t) async => shot(t, 'catalog', const MainShell(), tab: 1));
  testWidgets('my courses', (t) async => shot(t, 'my_courses', const MainShell(), tab: 2));
  testWidgets('profile', (t) async => shot(t, 'profile', const MainShell(), tab: 3));
  testWidgets('detail', (t) async => shot(t, 'course_detail', const CourseDetailScreen(courseId: 1)));
  testWidgets('learn', (t) async => shot(t, 'learn', const LearnScreen(courseId: 1)));
  testWidgets('lesson video', (t) async => shot(t, 'lesson_video', const LessonScreen(lessonId: 1), lesson: 'video'));
  testWidgets('lesson quiz', (t) async => shot(t, 'lesson_quiz', const LessonScreen(lessonId: 1), lesson: 'quiz'));
  testWidgets('quiz', (t) async => shot(t, 'quiz', const QuizScreen(lessonId: 1, title: 'Quiz')));
  testWidgets('cart', (t) async => shot(t, 'cart', const CartScreen()));
  testWidgets('purchases', (t) async => shot(t, 'purchases', const PurchasesScreen()));
  testWidgets('invoice', (t) async => shot(t, 'invoice', const InvoiceScreen(paymentId: 1)));
  testWidgets('certificates', (t) async => shot(t, 'certificates', const CertificatesScreen()));
  testWidgets('certificate', (t) async => shot(t, 'certificate', CertificateDetailScreen(certificate: CertificateItem(id: 1, code: 'AB12CD34EF56', courseId: 1, course: 'Curso de ejemplo', student: 'Estudiante Demo', issuedAt: DateTime(2026, 9, 1)))));
  testWidgets('grades', (t) async => shot(t, 'grades', const GradesScreen()));
  testWidgets('notifications', (t) async => shot(t, 'notifications', const NotificationsScreen()));
  testWidgets('chatbot', (t) async => shot(t, 'chatbot', const ChatbotScreen()));
  testWidgets('teacher', (t) async => shot(t, 'teacher_home', const MainShell(), role: 'teacher'));
  testWidgets('teacher courses', (t) async => shot(t, 'teacher_courses', const MainShell(), role: 'teacher', tab: 1));
  testWidgets('admin', (t) async => shot(t, 'admin_home', const MainShell(), role: 'admin'));
  testWidgets('admin hub', (t) async => shot(t, 'admin_hub', const MainShell(), role: 'admin', tab: 1));
  testWidgets('admin users', (t) async => shot(t, 'admin_users', const AdminUsersScreen(), role: 'admin'));
  testWidgets('admin courses', (t) async => shot(t, 'admin_courses', const AdminCoursesScreen(), role: 'admin'));
  testWidgets('admin categories', (t) async => shot(t, 'admin_categories', const AdminCategoriesScreen(), role: 'admin'));
  testWidgets('admin reports', (t) async => shot(t, 'admin_reports', const AdminReportsScreen(), role: 'admin'));
  testWidgets('admin coupons', (t) async => shot(t, 'admin_coupons', const AdminCouponsScreen(), role: 'admin'));
  testWidgets('admin payments', (t) async => shot(t, 'admin_payments', const AdminPaymentsScreen(), role: 'admin'));
  testWidgets('admin certificates', (t) async => shot(t, 'admin_certificates', const AdminCertificatesScreen(), role: 'admin'));
  testWidgets('admin report gen', (t) async => shot(t, 'admin_report_generator', const AdminReportGeneratorScreen(), role: 'admin'));
  testWidgets('progress', (t) async => shot(t, 'progress', const ProgressScreen()));
  testWidgets('course form', (t) async => shot(t, 'course_form', const CourseFormScreen(courseId: 1), role: 'teacher'));
  testWidgets('manage course', (t) async => shot(t, 'manage_course', const ManageCourseScreen(courseId: 1), role: 'teacher'));
  testWidgets('lesson form quiz', (t) async => shot(t, 'lesson_form_quiz', const LessonFormScreen(lessonId: 1, type: 'quiz'), role: 'teacher'));
  testWidgets('course stats', (t) async => shot(t, 'course_stats', const CourseStatsScreen(courseId: 1), role: 'teacher'));
  testWidgets('course results', (t) async => shot(t, 'course_results', const CourseResultsScreen(courseId: 1), role: 'teacher'));
  testWidgets('teacher coupons', (t) async => shot(t, 'teacher_coupons', const TeacherCouponsScreen(), role: 'teacher'));
}

/// flutter_secure_storage no tiene implementación en las pruebas: se simula.
class FlutterSecureStorageMock {
  static void install() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
      (call) async => null,
    );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('plugins.flutter.io/path_provider'),
      (call) async => Directory.systemTemp.path,
    );
  }
}
