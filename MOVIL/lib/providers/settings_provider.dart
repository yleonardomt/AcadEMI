import 'dart:io';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Preferencias locales: dirección del servidor y tema (claro/oscuro/sistema).
class SettingsProvider extends ChangeNotifier {
  static const _kServer = 'server_url';
  static const _kTheme = 'theme_mode';

  /// 10.0.2.2 es cómo el emulador de Android ve el localhost de la PC.
  static String get defaultServer => Platform.isAndroid ? 'http://10.0.2.2:8001' : 'http://127.0.0.1:8001';

  String _serverUrl = defaultServer;
  ThemeMode _themeMode = ThemeMode.system;

  String get serverUrl => _serverUrl;
  ThemeMode get themeMode => _themeMode;

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _serverUrl = prefs.getString(_kServer) ?? defaultServer;
    _themeMode = switch (prefs.getString(_kTheme)) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
    notifyListeners();
  }

  Future<void> setServerUrl(String url) async {
    var clean = url.trim();
    if (clean.isEmpty) clean = defaultServer;
    if (!clean.startsWith('http://') && !clean.startsWith('https://')) clean = 'http://$clean';
    while (clean.endsWith('/')) {
      clean = clean.substring(0, clean.length - 1);
    }
    _serverUrl = clean;
    (await SharedPreferences.getInstance()).setString(_kServer, clean);
    notifyListeners();
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    (await SharedPreferences.getInstance()).setString(_kTheme, mode.name);
    notifyListeners();
  }
}
