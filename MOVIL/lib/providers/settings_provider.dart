import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// La app usa AcadEMI publicado. Solo el equipo puede cambiar la API al
/// compilar con --dart-define=ACADEMI_API_BASE_URL=... para desarrollo local.
class SettingsProvider extends ChangeNotifier {
  static const _kTheme = 'theme_mode';
  static const defaultServer = String.fromEnvironment(
    'ACADEMI_API_BASE_URL',
    defaultValue: 'https://academi-efte.onrender.com',
  );
  ThemeMode _themeMode = ThemeMode.system;

  String get serverUrl => defaultServer;
  ThemeMode get themeMode => _themeMode;

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _themeMode = switch (prefs.getString(_kTheme)) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
    notifyListeners();
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    (await SharedPreferences.getInstance()).setString(_kTheme, mode.name);
    notifyListeners();
  }
}
