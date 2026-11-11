# Auditoría de requisitos funcionales RF-01 a RF-47

Revisión del código de AcadEMI actualizada el 11 de noviembre de 2026, **según el alcance académico acordado: las compras se registran sin pasarela de cobro**. **Implementado** significa que existe un flujo en el código web y/o API que cubre el requisito en ese alcance; no significa que se haya ejecutado una prueba integral de ese RF con todos sus casos. **Parcial** indica una parte funcional con una limitación concreta. **Pendiente** indica que falta el flujo solicitado.

Las pruebas de esta revisión usan una base SQLite aislada y correo en memoria. El usuario confirmó previamente la recepción real de correos mediante Brevo en Render. No se volvió a enviar correo real ni se verificó una respuesta externa de Gemini en esta revisión.

## Módulo 1: usuarios

| RF | Estado | Evidencia y límite |
| --- | --- | --- |
| 01 Registrarse | Implementado | `academi/views/auth.py`: `register_view`; formulario y verificación de correo. |
| 02 Iniciar sesión | Implementado | `academi/views/auth.py`: `login_view`; acceso según rol en dashboard. |
| 03 Cerrar sesión | Implementado | `academi/views/auth.py`: `logout_view`; API `/api/v1/auth/logout/`. |
| 04 Perfil | Implementado | `profile_view` y `UserProfileForm`; API `/me/`. |
| 05 Cursos adquiridos | Implementado | `my_courses_view`; API `/my-courses/`. |
| 06 Progreso e historial | Implementado | `my_progress_view`, `LessonProgress`, API `/progress/`. |
| 07 Recuperar contraseña | Implementado | Enlace y correo en `password_reset_request_view`; transporte HTTPS de Brevo y manejo de fallos. Los enlaces se verifican con correo en memoria; esta revisión no solicitó restablecimientos reales. |
| 08 Cambiar contraseña | Implementado | `change_password_view`; API `/auth/change-password/`. |
| 09 Calificaciones | Implementado | `my_grades_view`; API `/grades/`. |
| 10 Notificaciones | Implementado | `notifications_view`, marcado de lectura y API `/notifications/`. |
| 11 Favoritos | Implementado | `favorite_toggle_view`, `my_favorites_view`; API de favoritos. |

## Módulo 2: cursos

| RF | Estado | Evidencia y límite |
| --- | --- | --- |
| 12 Gestionar cursos | Implementado | `create_course_view`, `edit_course_view`, gestión docente y API `/manage/courses/`. |
| 13 Módulos, lecciones y videos | Implementado | Altas, ediciones, borrado y orden en `academi/views/courses.py` y `academi/views/lessons.py`. |
| 14 Catálogo | Implementado | `catalog_view`; API `/courses/`. |
| 15 Búsqueda y filtros | Implementado | `search_courses_view`, `catalog_view` y API de catálogo. |
| 16 Detalle del curso | Implementado | `course_detail_view`, modelo `Course` y API `/courses/<id>/`. |
| 17 Estudiantes inscritos | Implementado | `course_students_view`; API docente por curso. |
| 18 Estadísticas | Implementado | `compute_course_stats`: progreso, resultados, incidencias, reseñas y ventas visibles. |
| 19 Reseñas visibles para estudiante | Implementado | Detalle del curso y modelo `Review`. |
| 20 Reseñas para docente | Implementado | `mis_resenas_view`; API `/teacher/reviews/`. |

## Módulo 3: aprendizaje y evaluación

| RF | Estado | Evidencia y límite |
| --- | --- | --- |
| 21 Videos y documentos | Implementado | `lesson_view`, recursos y API `/lessons/<id>/`. |
| 22 Progreso por curso | Implementado | `LessonProgress`, `mark_lesson_complete`, API `/learn/<id>/`. |
| 23 Preguntas y respuestas | Implementado | `add_question_view`, `answer_question_view`, panel docente. |
| 24 Gestionar evaluaciones | Implementado | Crear, editar, eliminar y configurar están disponibles antes de registrar intentos. Web y API impiden reemplazar una evaluación con intentos registrados; se debe crear otra evaluación para conservar las respuestas y calificaciones históricas. La edición conserva las opciones escritas por el docente. No se implementó versionado de preguntas dentro de una misma evaluación. |
| 25 Realizar evaluaciones | Implementado | `quiz_view`, API `/quizzes/<id>/start/` y `/submit/`, límites de tiempo e intentos. La calificación compartida guarda la opción elegida, corrección y puntos de cada pregunta en `UserAnswer`. |
| 26 Historial y resultados | Implementado | `my_grades_view`, `quiz_result_view`, API `/grades/`; conservan puntajes e intentos. |
| 27 Comentarios en lecciones | Implementado | Altas, edición y borrado en `academi/views/engagement.py`. |
| 28 Reportar contenido | Implementado | `report_content_view`, API `/reports/`; comentarios, preguntas, reseñas y cursos. |
| 29 Tiempo restante | Implementado | Temporizador en `static/js/quiz.js` y límite en servidor. |
| 30 Resultados e incidencias para docente | Implementado | `course_students_view`, `compute_course_stats`; API `/manage/courses/<id>/results/`. |

**Corrección aplicada en esta auditoría:** las rutas de completar lección web y API ahora exigen una evaluación aprobada para cuestionarios/exámenes y una entrega registrada para tareas. La interfaz deja de ofrecer el botón de completar examen directamente. Esto protege la emisión de certificados a través de esos flujos. No se hizo una revisión retroactiva de certificados anteriores.

## Módulo 4: compras y certificados

| RF | Estado | Evidencia y límite |
| --- | --- | --- |
| 31 Carrito | Implementado | Añadir, consultar y quitar en `academi/views/cart.py` y API `/cart/`. |
| 32 Seleccionar método de pago | Pendiente | El modelo enumera métodos, pero el checkout web y móvil actuales no presentan opciones; ambos envían `demo`/`free` y el servidor asigna esos valores sin usar la elección del cliente. La versión anterior del carrito en Git sí mostraba QR y tarjeta, pero esos botones se retiraron junto con un QR no bancario y una tarjeta sin cobro verificable. |
| 33 Generar certificado | Implementado | `issue_certificate` crea PDF al completar curso; se corrigió el salto directo de evaluación/tarea. |
| 34 Consultar y descargar certificados | Implementado | `my_certificates_view`, `certificate_detail_view`, archivo PDF. |
| 35 Cupones | Implementado | Validación y cálculo en `academi/api/views_commerce.py`, uso en checkout. |
| 36 Estado e historial de compras | Implementado | Pedidos, estados e historial funcionan en el alcance académico. El pedido no representa un cobro bancario. |
| 37 Descargar comprobantes | Implementado | La compra académica genera un PDF descargable; es constancia del pedido y no acredita un abono bancario. |
| 38 Verificar certificados | Implementado | URL pública `/verify-certificate/<code>/`; estado de revocación. |

## Módulo 5: administración

| RF | Estado | Evidencia y límite |
| --- | --- | --- |
| 39 Usuarios | Implementado | CRUD, activar/desactivar y roles en `academi/views/admin_panel.py`; eliminación restringida si existen datos vinculados. |
| 40 Cursos y categorías | Implementado | Aprobar, rechazar, retirar y gestionar categorías; el panel incluye accesos a editar el curso y gestionar su contenido. |
| 41 Compras e ingresos | Implementado | Panel y API muestran pedidos e importes académicos; no representan dinero cobrado. |
| 42 Contenido reportado | Implementado | Panel web permite resolver/descartar y API permite también retirar comentarios, preguntas o reseñas. |
| 43 Certificados emitidos | Implementado | Panel y API listan certificados y permiten revocarlos/reactivarlos. |
| 44 Reportes | Implementado | Web y app móvil generan y muestran reportes por fecha; la API incluye métricas académicas. No se guardan reportes históricos y la vista web de rendimiento muestra menos detalle. |
| 45 Cupones y promociones | Implementado | CRUD y activación de cupones globales/por curso; descuento automático para correo de estudiante EMI. |

## Módulo 6: asistente virtual

| RF | Estado | Evidencia y límite |
| --- | --- | --- |
| 46 Acceder al chatbot | Implementado | `/chatbot/`, widget y API `/chatbot/send/`. |
| 47 Información mediante chatbot | Implementado | Usa catálogo/precios actuales y consulta progreso, compras recientes y resultados de evaluaciones del usuario autenticado. Las pruebas comprueban aislamiento entre usuarios; las respuestas personales se resuelven localmente. La respuesta externa de Gemini no se probó en vivo. |

## Resultado y prioridades

**46 implementados en código para el alcance académico y 1 pendiente (RF-32).** Esto no equivale a 46 RF aprobados mediante pruebas integrales: la suite actual contiene 66 pruebas centradas en flujos específicos, además de los recorridos de usuario documentados. La disponibilidad de servicios externos y dispositivos físicos requiere verificación adicional.

1. Para cumplir RF-32 falta ofrecer una elección de método en la compra académica y conservar esa elección en el pedido. Para cobrar dinero real en el futuro hará falta integrar y verificar un proveedor de cobro.
2. Configurar y comprobar almacenamiento persistente para nuevos archivos subidos si el servicio sigue alojado en Render Free. El soporte S3 está preparado; las credenciales de un bucket externo no se comprobaron en esta revisión.
3. Probar el recorrido completo en el teléfono físico que se utilizará para la presentación, incluida reproducción de YouTube y descarga de archivos.
4. Probar el proveedor externo de IA si se desean demostrar respuestas generadas por Gemini; catálogo, progreso, compras y calificaciones tienen respuestas locales.

Comprobaciones actualizadas: `python manage.py check`, 66 pruebas de `academi.tests`, recopilación de archivos estáticos, análisis de Flutter y 5 pruebas básicas de la app. Se revisaron 740 combinaciones de ruta/rol/ancho/tema en Chromium, 30 casos adicionales del perfil actualizado y 57 recursos públicos del despliegue. Los [recorridos completos de usuario](PRUEBAS_DE_USUARIO_2026_11_11.md) suman 70 pasos de navegador y API móvil. En la auditoría inicial, enviar `payment_method=card` terminó guardando `demo`, confirmando que RF-32 no usa la elección del cliente; ese comportamiento continúa. Las pruebas de escritura usan SQLite y no modifican PostgreSQL de producción. Véase [revisión de coherencia del 11 de noviembre](REVISION_COHERENCIA_2026_11_11.md).
