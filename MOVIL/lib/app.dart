import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_colors.dart';
import 'core/theme/app_theme.dart';
import 'providers/auth_provider.dart';
import 'providers/cart_provider.dart';
import 'providers/settings_provider.dart';
import 'providers/shell_nav.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/verify_pending_screen.dart';
import 'screens/home/main_shell.dart';
import 'widgets/common.dart';

class AcademiApp extends StatelessWidget {
  const AcademiApp({super.key, required this.settings});

  final SettingsProvider settings;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<SettingsProvider>.value(value: settings),
        ChangeNotifierProvider<AuthProvider>(create: (c) => AuthProvider(c.read<SettingsProvider>())..restore()),
        ChangeNotifierProxyProvider<AuthProvider, CartProvider>(
          create: (c) => CartProvider(c.read<AuthProvider>()),
          update: (_, auth, cart) => cart ?? CartProvider(auth),
        ),
        ChangeNotifierProvider<ShellNav>(create: (_) => ShellNav()),
      ],
      child: Consumer<SettingsProvider>(
        builder: (context, settings, _) => MaterialApp(
          title: 'AcadEMI',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.light(),
          darkTheme: AppTheme.dark(),
          themeMode: settings.themeMode,
          locale: const Locale('es'),
          supportedLocales: const [Locale('es'), Locale('en')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          builder: (context, child) {
            final dark = Theme.of(context).brightness == Brightness.dark;
            return AnnotatedRegion<SystemUiOverlayStyle>(
              value: dark ? SystemUiOverlayStyle.light : SystemUiOverlayStyle.dark,
              child: child!,
            );
          },
          home: const _AuthGate(),
        ),
      ),
    );
  }
}

/// Decide qué mostrar según la sesión: cargando, login, verificación de correo o la app.
class _AuthGate extends StatelessWidget {
  const _AuthGate();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    final Widget page;
    switch (auth.status) {
      case AuthStatus.loading:
        page = const _Splash();
      case AuthStatus.unauthenticated:
        page = const LoginScreen();
      case AuthStatus.authenticated:
        final user = auth.user!;
        page = (!user.emailVerified && !user.isAdmin) ? const VerifyPendingScreen() : const MainShell();
    }

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 250),
      child: KeyedSubtree(key: ValueKey(page.runtimeType), child: page),
    );
  }
}

class _Splash extends StatelessWidget {
  const _Splash();

  @override
  Widget build(BuildContext context) => const Scaffold(
        body: DecoratedBox(
          decoration: BoxDecoration(gradient: AppColors.heroGradient),
          child: SizedBox.expand(
            child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
              BrandLogo(size: 38, light: true),
              SizedBox(height: 28),
              SizedBox(width: 26, height: 26, child: CircularProgressIndicator(strokeWidth: 2.6, color: AppColors.secondary)),
            ]),
          ),
        ),
      );
}
