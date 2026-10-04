import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// Error de la API con un mensaje ya listo para mostrarle al usuario.
class ApiException implements Exception {
  ApiException(this.message, {this.status, this.code, this.errors, this.data});

  final String message;
  final int? status;
  final String? code;
  final Map<String, dynamic>? errors;

  /// Respuesta completa del servidor (p. ej. trae un `captcha` nuevo).
  final Map<String, dynamic>? data;

  bool get isUnauthenticated => status == 401;
  bool get emailNotVerified => code == 'EMAIL_NOT_VERIFIED';

  @override
  String toString() => message;
}

/// Cliente HTTP de la API JSON de AcadEMI (`/api/v1/`). Agrega el token
/// Bearer, convierte las respuestas `success:false` y los fallos de red en
/// [ApiException] y avisa cuando la sesión expira.
class ApiClient {
  ApiClient({required this.baseUrl, this.token, this.onUnauthenticated});

  String baseUrl;
  String? token;
  void Function()? onUnauthenticated;

  Uri _uri(String path, [Map<String, dynamic>? query]) {
    final clean = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    final q = <String, String>{};
    query?.forEach((k, v) {
      if (v != null && '$v'.isNotEmpty) q[k] = '$v';
    });
    return Uri.parse('$clean/api/v1/$path').replace(queryParameters: q.isEmpty ? null : q);
  }

  Map<String, String> get _headers => {
        'Accept': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  Future<Map<String, dynamic>> get(String path, {Map<String, dynamic>? query}) =>
      _send(() => http.get(_uri(path, query), headers: _headers));

  Future<Map<String, dynamic>> post(String path, {Map<String, dynamic>? body}) => _send(() => http.post(
        _uri(path),
        headers: {..._headers, 'Content-Type': 'application/json'},
        body: jsonEncode(body ?? {}),
      ));

  /// POST multipart para subir archivos (foto de perfil, entrega de tarea).
  Future<Map<String, dynamic>> upload(
    String path, {
    Map<String, String> fields = const {},
    required String fileField,
    required String filePath,
  }) =>
      _send(() async {
        final request = http.MultipartRequest('POST', _uri(path))
          ..headers.addAll(_headers)
          ..fields.addAll(fields)
          ..files.add(await http.MultipartFile.fromPath(fileField, filePath));
        return http.Response.fromStream(await request.send());
      });

  Future<Map<String, dynamic>> _send(Future<http.Response> Function() request) async {
    http.Response response;
    try {
      response = await request().timeout(const Duration(seconds: 60));
    } on TimeoutException {
      throw ApiException('El servidor tardó demasiado en responder. Intenta nuevamente.');
    } on SocketException {
      throw ApiException('No se pudo conectar con el servidor. Revisa tu conexión o la dirección del servidor.');
    } on http.ClientException {
      throw ApiException('No se pudo conectar con el servidor. Revisa tu conexión o la dirección del servidor.');
    } on HandshakeException {
      throw ApiException('No se pudo establecer una conexión segura con el servidor.');
    }

    Map<String, dynamic> data;
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      data = decoded is Map<String, dynamic> ? decoded : {'success': false};
    } catch (_) {
      throw ApiException(
        response.statusCode == 404
            ? 'No se encontró lo que buscabas.'
            : 'El servidor respondió con un error inesperado (${response.statusCode}).',
        status: response.statusCode,
      );
    }

    if (response.statusCode == 401) onUnauthenticated?.call();
    if (response.statusCode >= 400 || data['success'] == false) {
      throw ApiException(
        (data['message'] as String?) ?? 'Ocurrió un error. Intenta nuevamente.',
        status: response.statusCode,
        code: data['code'] as String?,
        errors: data['errors'] as Map<String, dynamic>?,
        data: data,
      );
    }
    return data;
  }
}
