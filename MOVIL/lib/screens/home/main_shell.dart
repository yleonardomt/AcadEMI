import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/nav.dart';
import '../../providers/auth_provider.dart';
import '../../providers/cart_provider.dart';
import '../../providers/shell_nav.dart';
import '../admin/admin_hub_screen.dart';
import '../catalog/catalog_tab.dart';
import '../chatbot/chatbot_screen.dart';
import '../learning/my_courses_tab.dart';
import '../profile/profile_tab.dart';
import '../teacher/teacher_dashboard_tab.dart';
import '../teacher/teacher_questions_screen.dart';
import 'home_tab.dart';

class _TabSpec {
  const _TabSpec(this.label, this.icon, this.page);

  final String label;
  final FaIconData icon;
  final Widget page;
}

/// Contenedor principal con el menú inferior; las pestañas dependen del rol.
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  /// Las pestañas se construyen la primera vez que se visitan (evita pedir todo al abrir).
  final Set<int> _visited = {0};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => context.read<CartProvider>().load());
  }

  List<_TabSpec> _tabs(AuthProvider auth) {
    final user = auth.user!;
    if (user.isTeacher) {
      return const [
        _TabSpec('Panel', FontAwesomeIcons.chartPie, TeacherDashboardTab()),
        _TabSpec('Mis cursos', FontAwesomeIcons.chalkboard, MyCoursesTab()),
        _TabSpec('Preguntas', FontAwesomeIcons.comments, TeacherQuestionsScreen(embedded: true)),
        _TabSpec('Perfil', FontAwesomeIcons.user, ProfileTab()),
      ];
    }
    if (user.isAdmin) {
      return const [
        _TabSpec('Panel', FontAwesomeIcons.chartPie, TeacherDashboardTab()),
        _TabSpec('Gestión', FontAwesomeIcons.screwdriverWrench, AdminHubScreen()),
        _TabSpec('Catálogo', FontAwesomeIcons.compass, CatalogTab()),
        _TabSpec('Perfil', FontAwesomeIcons.user, ProfileTab()),
      ];
    }
    return const [
      _TabSpec('Inicio', FontAwesomeIcons.house, HomeTab()),
      _TabSpec('Catálogo', FontAwesomeIcons.compass, CatalogTab()),
      _TabSpec('Mis cursos', FontAwesomeIcons.bookOpenReader, MyCoursesTab()),
      _TabSpec('Perfil', FontAwesomeIcons.user, ProfileTab()),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final nav = context.watch<ShellNav>();
    final tabs = _tabs(auth);
    final index = nav.tab.clamp(0, tabs.length - 1);
    _visited.add(index);
    final showChatFab = index == 0 || tabs[index].label == 'Catálogo';

    return Scaffold(
      body: IndexedStack(index: index, children: [
        for (var i = 0; i < tabs.length; i++) _visited.contains(i) ? tabs[i].page : const SizedBox.shrink(),
      ]),
      floatingActionButton: showChatFab
          ? FloatingActionButton(
              tooltip: 'Asistente virtual',
              backgroundColor: AppColors.secondary,
              foregroundColor: AppColors.primaryDark,
              elevation: 3,
              onPressed: () => push(context, const ChatbotScreen()),
              child: const FaIcon(FontAwesomeIcons.robot, size: 22),
            )
          : null,
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => context.read<ShellNav>().setTab(i),
        destinations: [
          for (final t in tabs)
            NavigationDestination(icon: FaIcon(t.icon), label: t.label),
        ],
      ),
    );
  }
}
