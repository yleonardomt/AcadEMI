import 'package:flutter/foundation.dart';

/// Controla la pestaña activa del menú inferior y permite que otras
/// pantallas abran el catálogo con una búsqueda o categoría ya aplicada.
class ShellNav extends ChangeNotifier {
  int tab = 0;
  String catalogQuery = '';
  int? catalogCategory;
  int _catalogRequest = 0;

  /// Contador que cambia con cada petición, para que el catálogo detecte
  /// que debe volver a aplicar filtros aunque sean los mismos.
  int get catalogRequest => _catalogRequest;

  void setTab(int index) {
    tab = index;
    notifyListeners();
  }

  void openCatalog(int catalogTabIndex, {String query = '', int? category}) {
    catalogQuery = query;
    catalogCategory = category;
    _catalogRequest++;
    tab = catalogTabIndex;
    notifyListeners();
  }
}
