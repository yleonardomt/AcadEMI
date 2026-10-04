import 'package:academi_movil/core/theme/app_theme.dart';
import 'package:academi_movil/models/course.dart';
import 'package:academi_movil/providers/auth_provider.dart';
import 'package:academi_movil/providers/settings_provider.dart';
import 'package:academi_movil/screens/auth/login_screen.dart';
import 'package:academi_movil/widgets/course_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

Course sample() => Course.fromJson({
      'id': 1, 'title': 'Curso de prueba con un título bastante largo para revisar el recorte',
      'description': 'd', 'level': 'beginner', 'level_label': 'Principiante', 'price': 39.99,
      'is_free': false, 'price_label': 'Bs. 39.99', 'is_featured': true, 'teacher': 'Docente Demo',
      'rating': 4.5, 'reviews_count': 3, 'students_count': 10, 'lessons_count': 12,
      'duration_minutes': 120, 'is_enrolled': false, 'is_favorite': false, 'category': 'Programación',
      'coupon': {'code': 'X', 'type': 'percentage', 'value': 15},
    });

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  for (final theme in [AppTheme.light(), AppTheme.dark()]) {
    testWidgets('login se dibuja (${theme.brightness.name})', (tester) async {
      tester.view.physicalSize = const Size(1080, 2200);
      tester.view.devicePixelRatio = 3;
      addTearDown(tester.view.reset);
      final settings = SettingsProvider();
      await tester.pumpWidget(MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: settings),
          ChangeNotifierProvider(create: (c) => AuthProvider(settings)),
        ],
        child: MaterialApp(theme: theme, home: const LoginScreen()),
      ));
      await tester.pump();
      expect(find.text('Iniciar sesión'), findsWidgets);
      expect(tester.takeException(), isNull);
    });

    testWidgets('tarjetas de curso (${theme.brightness.name})', (tester) async {
      tester.view.physicalSize = const Size(1080, 2200);
      tester.view.devicePixelRatio = 3;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(MaterialApp(
        theme: theme,
        home: Scaffold(
          body: ListView(children: [
            CourseCard(course: sample(), onTap: () {}),
            SizedBox(height: 132, child: CourseListTile(course: sample(), onTap: () {}, onFavorite: () {})),
          ]),
        ),
      ));
      await tester.pump();
      // La fuente de prueba (Ahem) es mucho más ancha que Inter: se ignoran los
      // desbordes de texto y solo se falla ante cualquier otro error de dibujo.
      final e = tester.takeException();
      expect(e == null || e.toString().contains('overflowed'), isTrue, reason: '$e');
    });
  }
}
