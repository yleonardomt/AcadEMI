/// Lectores tolerantes de JSON: la API a veces devuelve null o números como
/// int/double indistintamente.
int asInt(dynamic v, [int fallback = 0]) {
  if (v is int) return v;
  if (v is num) return v.toInt();
  if (v is String) return int.tryParse(v) ?? fallback;
  return fallback;
}

double asDouble(dynamic v, [double fallback = 0]) {
  if (v is num) return v.toDouble();
  if (v is String) return double.tryParse(v) ?? fallback;
  return fallback;
}

String asString(dynamic v, [String fallback = '']) => v == null ? fallback : '$v';

String? asStringOrNull(dynamic v) {
  if (v == null) return null;
  final s = '$v';
  return s.isEmpty ? null : s;
}

bool asBool(dynamic v) => v == true || v == 1 || v == 'true';

DateTime? asDate(dynamic v) => v is String ? DateTime.tryParse(v)?.toLocal() : null;

List<Map<String, dynamic>> asList(dynamic v) =>
    v is List ? v.whereType<Map<String, dynamic>>().toList() : <Map<String, dynamic>>[];
