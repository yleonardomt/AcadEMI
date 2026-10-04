import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../core/network/api_client.dart';
import '../models/user.dart';
import '../services/services.dart';
import 'settings_provider.dart';

enum AuthStatus { loading, unauthenticated, authenticated }

/// Sesión del usuario: guarda el token de forma segura, expone el cliente de
/// la API ya autenticado y cierra sesión sola si el servidor la invalida.
class AuthProvider extends ChangeNotifier {
  /// [testClient] permite inyectar un cliente falso en las pruebas.
  AuthProvider(this._settings, {ApiClient? testClient}) {
    client = testClient ?? ApiClient(baseUrl: _settings.serverUrl, onUnauthenticated: _onExpired);
    api = AppServices(client);
    _settings.addListener(_syncServer);
  }

  static const _kToken = 'auth_token';
  static const _storage = FlutterSecureStorage();

  final SettingsProvider _settings;
  late final ApiClient client;
  late final AppServices api;

  AuthStatus status = AuthStatus.loading;
  AppUser? user;
  int unreadNotifications = 0;

  bool get isAuthenticated => status == AuthStatus.authenticated;

  void _syncServer() => client.baseUrl = _settings.serverUrl;

  void _onExpired() {
    if (status == AuthStatus.authenticated) {
      _clear();
    }
  }

  /// Restaura la sesión guardada (si el token sigue siendo válido).
  Future<void> restore() async {
    try {
      final token = await _storage.read(key: _kToken);
      if (token == null) {
        status = AuthStatus.unauthenticated;
      } else {
        client.token = token;
        await refresh();
      }
    } on ApiException catch (e) {
      // Sin conexión al abrir: conservamos el token y mostramos la app igual
      // solo si no fue un rechazo de sesión.
      if (e.isUnauthenticated) {
        await _clear();
      } else {
        status = AuthStatus.unauthenticated;
        client.token = null;
      }
    } catch (_) {
      status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<void> refresh() async {
    final (u, unread) = await api.me();
    user = u;
    unreadNotifications = unread;
    status = AuthStatus.authenticated;
    notifyListeners();
  }

  Future<void> _startSession(String token, AppUser u) async {
    client.token = token;
    await _storage.write(key: _kToken, value: token);
    user = u;
    status = AuthStatus.authenticated;
    notifyListeners();
  }

  Future<void> login(String identifier, String password, {Map<String, dynamic>? captcha}) async {
    final (token, u) = await api.login(identifier, password, captcha: captcha);
    await _startSession(token, u);
    await _refreshUnread();
  }

  /// Devuelve `true` si se pudo enviar el correo de verificación.
  Future<bool> register(Map<String, dynamic> body) async {
    final (token, u, emailSent) = await api.register(body);
    await _startSession(token, u);
    return emailSent;
  }

  Future<void> _refreshUnread() async {
    try {
      final (_, unread) = await api.me();
      unreadNotifications = unread;
      notifyListeners();
    } catch (_) {}
  }

  void setUnread(int n) {
    unreadNotifications = n;
    notifyListeners();
  }

  void updateUser(AppUser u) {
    user = u;
    notifyListeners();
  }

  /// Cambiar la contraseña invalida el token anterior: guardamos el nuevo.
  Future<void> replaceToken(String token) async {
    client.token = token;
    await _storage.write(key: _kToken, value: token);
  }

  Future<void> logout() async {
    try {
      await api.client.post('auth/logout/');
    } catch (_) {}
    await _clear();
  }

  Future<void> _clear() async {
    client.token = null;
    user = null;
    unreadNotifications = 0;
    status = AuthStatus.unauthenticated;
    await _storage.delete(key: _kToken);
    notifyListeners();
  }

  @override
  void dispose() {
    _settings.removeListener(_syncServer);
    super.dispose();
  }
}
