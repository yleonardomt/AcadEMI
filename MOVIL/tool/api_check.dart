// Verifica contra un servidor real que los servicios y modelos de la app
// interpretan cada respuesta de la API. Uso: dart run tool/api_check.dart [url]
import 'package:academi_movil/core/network/api_client.dart';
import 'package:academi_movil/services/services.dart';

Future<void> main(List<String> args) async {
  final base = args.isNotEmpty ? args.first : 'http://localhost';
  var failures = 0;
  Future<void> check(String name, Future<Object?> Function() f) async {
    try {
      final r = await f();
      print('OK   $name ${r ?? ''}');
    } catch (e, st) {
      failures++;
      print('FAIL $name -> $e\n${st.toString().split('\n').take(3).join('\n')}');
    }
  }

  Future<AppServices> session(String user, String pass) async {
    final api = AppServices(ApiClient(baseUrl: base));
    final (token, _) = await api.login(user, pass);
    api.client.token = token;
    return api;
  }

  final s = await session('estudiante', 'estudiante');
  await check('me', () async => (await s.me()).$1.role);
  await check('home', () async {
    final h = await s.home();
    return '${h.featured.length} destacados, ${h.categories.length} cats, ${h.continueLearning.length} continuar';
  });
  await check('categories', () async => (await s.categories()).length);
  final page = await s.courses(sort: 'popular');
  await check('courses', () async => '${page.courses.length}/${page.total}');
  await check('courses filtros', () async => (await s.courses(q: 'a', level: 'beginner', price: 'paid', sort: 'price_asc')).total);
  await check('courseDetail', () async {
    final c = await s.courseDetail(page.courses.first.id);
    return '${c.modules.length} módulos, docente ${c.teacherInfo?.name}';
  });
  await check('favorites', () async => (await s.favorites()).length);
  await check('cart', () async => (await s.cart()).items.length);
  await check('purchases', () async => (await s.purchases()).$1.length);
  final payments = (await s.purchases()).$1;
  if (payments.isNotEmpty) await check('invoice', () async => (await s.purchaseDetail(payments.first.id)).items.length);
  await check('notifications', () async => (await s.notifications()).$1.length);
  await check('certificates', () async => (await s.certificates()).length);
  await check('grades', () async => (await s.grades()).length);
  await check('chatHistory', () async => (await s.chatHistory()).length);
  final raw = await s.myCoursesRaw();
  final enrollments = (raw['enrollments'] as List);
  await check('myCourses', () async => enrollments.length);
  final cid = (enrollments.first as Map)['course_id'] as int;
  await check('learn', () async => (await s.learn(cid)).modules.length);
  final learn = await s.learn(cid);
  final anyLesson = learn.modules.expand((m) => m.lessons).toList();
  for (final t in ['video', 'text', 'document', 'quiz', 'assignment']) {
    final l = anyLesson.where((l) => l.type == t).firstOrNull;
    if (l != null) {
      await check('lesson[$t]', () async {
        final d = await s.lesson(l.id);
        return '${d.title} quiz=${d.quiz?.questionsCount} yt=${d.youtubeId}';
      });
    }
  }
  await check('chatbot', () async => (await s.chatSend('¿Cómo obtengo un certificado?')).message.substring(0, 40));
  await check('verifyCertificate', () async => await s.verifyCertificate('NOEXISTE'));

  final t = await session('teacher1', 'teacher123');
  await check('teacher dashboard', () async => (await t.teacherDashboard()).keys.length);
  await check('teacher students', () async => (await t.teacherStudents()).length);
  await check('teacher questions', () async => (await t.teacherQuestions()).length);
  await check('teacher reviews', () async => (await t.teacherReviews()).length);
  await check('teacher courses', () async => ((await t.myCoursesRaw())['courses'] as List).length);
  final a = await session('admin', 'admin');
  await check('admin dashboard', () async => (await a.teacherDashboard())['admin'] != null);

  print(failures == 0 ? '\nTODO OK' : '\n$failures FALLOS');
}
