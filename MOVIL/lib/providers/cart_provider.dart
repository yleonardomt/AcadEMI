import 'package:flutter/foundation.dart';

import '../models/commerce.dart';
import 'auth_provider.dart';

/// Estado del carrito (cursos, totales y contador para la insignia).
class CartProvider extends ChangeNotifier {
  CartProvider(this._auth);

  final AuthProvider _auth;

  CartData data = CartData.empty();
  bool loading = false;
  String? error;

  int get count => data.items.length;

  bool contains(int courseId) => data.items.any((i) => i.courseId == courseId);

  Future<void> load() async {
    if (!_auth.isAuthenticated || !(_auth.user?.isStudent ?? false)) return;
    loading = true;
    error = null;
    notifyListeners();
    try {
      data = await _auth.api.cart();
    } catch (e) {
      error = '$e';
    }
    loading = false;
    notifyListeners();
  }

  Future<void> add(int courseId) async {
    await _auth.api.cartAdd(courseId);
    data = await _auth.api.cart();
    notifyListeners();
  }

  Future<void> remove(int courseId) async {
    await _auth.api.cartRemove(courseId);
    data = await _auth.api.cart();
    notifyListeners();
  }

  /// Devuelve (mensaje, aplicado).
  Future<(String, bool)> applyCoupon(String code) async {
    final (cart, message, applied) = await _auth.api.applyCoupon(code);
    data = cart;
    notifyListeners();
    return (message, applied);
  }

  void clear() {
    data = CartData.empty();
    notifyListeners();
  }
}
