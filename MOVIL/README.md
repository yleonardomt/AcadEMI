# AcadEMI móvil

App Flutter (Android e iOS) de la plataforma educativa AcadEMI. Usa los mismos colores
(`#02167f` azul y `#ffd014` amarillo), tipografía Inter, íconos Font Awesome y modo claro/oscuro
que el sitio web.

## Qué incluye

**Estudiante:** registro/login, verificación de correo, recuperar contraseña, portada con progreso,
catálogo con búsqueda/filtros/categorías, detalle del curso (contenido, docente, reseñas),
favoritos, carrito, cupones, descuento EMI, pago (QR o tarjeta), historial y factura,
mis cursos, lecciones (video YouTube/archivo, lectura, documento, tareas, cuestionarios con
cronómetro), comentarios y preguntas, progreso, certificados (PDF y verificación por código),
calificaciones, notificaciones, asistente virtual (chatbot) y perfil.

**Docente:** panel con métricas, crear/editar cursos, módulos y lecciones (texto, video, documento, tarea, cuestionario y examen con constructor de preguntas), estadísticas, estudiantes, resultados e incidencias de evaluaciones, calificar tareas, cupones, preguntas de estudiantes y reseñas.

**Administrador:** panel de resumen y módulo de gestión: usuarios y roles, aprobación/rechazo de cursos, categorías, contenido reportado, cupones, compras e ingresos, certificados y generador de reportes.

El cumplimiento requisito por requisito (RF-01 a RF-51 y RNF-01 a RNF-20, web y app) está en [`REQUISITOS.md`](REQUISITOS.md).

## Requisitos

- Flutter estable (probado con 3.47), JDK 17 y Android SDK (`flutter doctor`).
- El backend Django de AcadEMI corriendo con la API `/api/v1/` (carpeta `academi/api/`).

## Cómo ejecutarla

1. Levanta el backend permitiendo conexiones de la red:

   ```bash
   # en ~/Academi/.env:  ALLOWED_HOSTS=*   (solo desarrollo)
   source venv/bin/activate
   python manage.py runserver 0.0.0.0:8001
   ```

2. Ejecuta la app:

   ```bash
   cd MOVIL
   flutter pub get
   flutter run
   ```

3. Dirección del servidor (ícono de engranaje en el login, o Perfil → Servidor):
   - Emulador Android: `http://10.0.2.2:8001` (por defecto).
   - Celular real: `http://IP-DE-TU-PC:8001` (misma red Wi-Fi). En WSL2 necesitas reenviar el
     puerto o usar el modo de red *mirrored*.

## Estructura (`lib/`)

| Carpeta | Contenido |
|---|---|
| `core/` | tema (colores/tipografía), cliente HTTP, utilidades |
| `models/` | modelos por dominio (usuario, curso, aprendizaje, comercio, social) |
| `services/` | un método por endpoint de la API |
| `providers/` | estado: sesión, carrito, ajustes, navegación |
| `widgets/` | componentes reutilizables (tarjetas, botones, campos) |
| `screens/` | pantallas por sección (auth, home, catalog, learning, commerce, profile, teacher, chatbot) |

## Generar el APK

```bash
flutter build apk --release
```

## Pruebas y capturas

```bash
flutter test                                              # pruebas rápidas
dart run tool/api_check.dart http://localhost:8001        # contrato app <-> API real
flutter test --run-skipped --tags golden --update-goldens # capturas en test/screenshots/
```
