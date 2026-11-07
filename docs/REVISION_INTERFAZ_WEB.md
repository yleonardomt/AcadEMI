# Revisión de interfaz web — 6 de noviembre de 2026

Se conserva el azul de marca `#02167f` y el amarillo `#ffd014`. Los componentes compartidos definen colores legibles para botones normales, hover, foco, pulsación y estados deshabilitados. Se ajustaron formularios, selectores, tablas, etiquetas, avisos, navegación, tarjetas y ventanas emergentes para ambos temas.

Se corrigieron los desbordamientos de métricas en los dashboards y de nombres de categorías en teléfonos pequeños. Los títulos, áreas de texto, separación de iconos y controles se adaptan al ancho disponible. Las tarjetas de formulario permanecen estables al pasar el cursor. La impresión del certificado mantiene papel blanco y texto oscuro aun cuando se esté usando el modo noche.

## Comprobación

- Chromium: 74 combinaciones de página y rol, en 320, 390, 768, 1024 y 1440 px, con temas claro y oscuro: 740 cargas.
- Incluye páginas públicas, registro/verificación, estudiante, docente y administrador; certificados, comprobantes, evaluaciones y formularios de lecciones.
- Tras las correcciones y la repetición de los casos afectados: sin errores HTTP, desbordamiento horizontal del documento ni fallos de contraste detectados por el análisis de los controles y textos seleccionados.
- 522 comprobaciones de estados de botones; revisión adicional del buscador tras corregir el destello del degradado durante hover.
- Ventana de cupones revisada en móvil con ambos temas. Certificado revisado con medios de impresión y preferencia oscura.
- 41 pruebas Django, incluida la conservación de importes históricos y progreso al actualizar el catálogo.

La comprobación automática usa colores calculados del navegador. Los textos con degradado recortado y fondos audiovisuales requieren inspección visual; no constituye una certificación formal de accesibilidad ni una prueba en todos los navegadores o dispositivos físicos.

## Precios

Los 33 cursos del catálogo tienen precios base entre Bs 100 y Bs 150, antes de aplicar descuentos. MySQL cuesta Bs 150. La migración `0013_catalog_prices_range` actualiza los cursos existentes una sola vez; los pedidos, comprobantes, inscripciones y progresos anteriores conservan sus datos. El cargador utiliza los mismos importes para cursos nuevos.
