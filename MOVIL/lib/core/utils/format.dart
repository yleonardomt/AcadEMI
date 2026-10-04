import 'package:flutter/widgets.dart' show StringCharacters;
import 'package:intl/intl.dart';

class Fmt {
  Fmt._();

  static String money(num v) => v == 0 ? 'Gratis' : 'Bs. ${v.toStringAsFixed(2)}';

  static String amount(num v) => 'Bs. ${v.toStringAsFixed(2)}';

  static String date(DateTime? d) => d == null ? '' : DateFormat('d MMM yyyy', 'es').format(d);

  static String dateTime(DateTime? d) => d == null ? '' : DateFormat('d MMM yyyy, HH:mm', 'es').format(d);

  static String ago(DateTime? d) {
    if (d == null) return '';
    final diff = DateTime.now().difference(d);
    if (diff.inMinutes < 1) return 'ahora';
    if (diff.inMinutes < 60) return 'hace ${diff.inMinutes} min';
    if (diff.inHours < 24) return 'hace ${diff.inHours} h';
    if (diff.inDays < 7) return 'hace ${diff.inDays} d';
    return date(d);
  }

  static String duration(int minutes) {
    if (minutes <= 0) return '';
    final h = minutes ~/ 60;
    final m = minutes % 60;
    if (h == 0) return '$m min';
    return m == 0 ? '$h h' : '$h h $m min';
  }

  /// Primer nombre real, saltando títulos como Dr., Dra., Lic., Ing., Prof.
  static String firstName(String name) {
    const titles = {'dr', 'dra', 'lic', 'ing', 'prof', 'msc', 'mg', 'sr', 'sra', 'arq', 'tte', 'cnl', 'cap', 'my', 'gral'};
    final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    for (final p in parts) {
      if (!titles.contains(p.replaceAll('.', '').toLowerCase())) return p;
    }
    return parts.isEmpty ? '' : parts.first;
  }

  static String initials(String name) {
    final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first.characters.first.toUpperCase();
    return (parts.first.characters.first + parts.last.characters.first).toUpperCase();
  }
}
