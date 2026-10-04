# Cumplimiento de requisitos de AcadEMI (web + app móvil)

Leyenda: **Web** = sitio Django · **App** = app Flutter (`MOVIL/`) · **Sí** = cumple · **Parcial** = falta algo · **Infra** = depende de infraestructura, no del código.

## Requisitos funcionales

| N.º | Requisito | Web | App | Dónde / notas |
|---|---|---|---|---|
| RF-01 | Registrarse | Sí | Sí | Estudiante y docente. La app pide CAPTCHA. |
| RF-02 | Iniciar sesión | Sí | Sí | Los tres roles. La app pide CAPTCHA tras 3 intentos fallidos. |
| RF-03 | Recuperar contraseña | Sí | Sí | Enlace por correo (con CAPTCHA). |
| RF-04 | Cerrar sesión | Sí | Sí | Perfil → Cerrar sesión. |
| RF-05 | Cambiar contraseña | Sí | Sí | Perfil → Cambiar contraseña. |
| RF-06 | Validar CAPTCHA | Sí | Sí | Web: login, registro, recuperación. App: registro, recuperación y login (tras fallos). |
| RF-07 | Gestionar perfil | Sí | Sí | Los tres roles, con foto. |
| RF-08 | Cursos adquiridos | Sí | Sí | "Mis cursos". |
| RF-09 | Progreso e historial | Sí | Sí | App: Perfil → Mi progreso (lecciones + actividad). |
| RF-10 | Calificaciones | Sí | Sí | Perfil → Calificaciones. |
| RF-11 | Cursos favoritos | Sí | Sí | Corazón en tarjetas y detalle. |
| RF-12 | Notificaciones | Sí | Sí | Estudiante, docente y administrador. |
| RF-13 | Gestionar cursos (docente) | Sí | Sí | App: Mis cursos → Nuevo curso / Editar (imagen, precio, categoría). |
| RF-14 | Módulos y lecciones | Sí | Sí | App: crear, editar, ordenar y eliminar; texto, video, documento, tarea, cuestionario, examen. |
| RF-15 | Estudiantes inscritos | Sí | Sí | |
| RF-16 | Estadísticas del curso | Sí | Sí | Estudiantes, progreso, evaluaciones, valoraciones y ventas. **La página del web era un borrador con ceros fijos; se reescribió.** |
| RF-17 | Valoraciones (docente) | Sí | Sí | |
| RF-18 | Catálogo | Sí | Sí | |
| RF-19 | Buscar y filtrar | Sí | Sí | Texto, categoría, nivel, precio y orden. |
| RF-20 | Información del curso | Sí | Sí | |
| RF-21 | Valoraciones y reseñas | Sí | Sí | |
| RF-22 | Contenido de muestra | Sí | Sí | Lecciones con "vista previa gratuita". |
| RF-23 | Videos y documentos | Sí | Sí | YouTube, archivo de video y documentos. |
| RF-24 | Registrar progreso | Sí | Sí | |
| RF-25 | Comentarios en lecciones | Sí | Sí | Publicar, **editar** y eliminar (la app no permitía editar; se agregó). |
| RF-26 | Preguntas y respuestas | Sí | Sí | El docente responde desde "Preguntas". |
| RF-27 | Reportar contenido | Sí | Sí | Comentarios, preguntas, reseñas y cursos. |
| RF-28 | Gestionar evaluaciones | Sí | Sí | App: constructor de preguntas, tiempo, intentos y puntaje. |
| RF-29 | Realizar evaluaciones | Sí | Sí | |
| RF-30 | Tiempo restante | Sí | Sí | Cuenta regresiva. |
| RF-31 | Resultados e historial | Sí | Sí | |
| RF-32 | Resultados e incidencias (docente) | Sí | Sí | **El web registraba las incidencias pero el docente no podía verlas; se agregó.** App: Resultados e incidencias. |
| RF-33 | Carrito | Sí | Sí | |
| RF-34 | Método de pago | Sí | Sí | QR o tarjeta. |
| RF-35 | Aplicar cupones | Sí | Sí | Más descuento EMI automático. |
| RF-36 | Cupones del docente | Sí | Sí | App: Perfil → Mis cupones. |
| RF-37 | Estado e historial de compras | Sí | Sí | |
| RF-38 | Descargar comprobantes | Sí | Sí | **PDF real** en web y app (antes solo se imprimía). |
| RF-39 | Generar certificado | Sí | Sí | Automático al completar el curso. |
| RF-40 | Consultar y descargar certificados | Sí | Sí | PDF. |
| RF-41 | Certificado por correo | Sí | Sí | **A solicitud** del estudiante (antes solo automático). |
| RF-42 | Verificar certificados | Sí | Sí | Por código; pública. |
| RF-43 | Gestionar usuarios | Sí | Sí | App: Gestión → Usuarios (crear, editar, roles, activar, eliminar, restablecer contraseña). |
| RF-44 | Cursos y categorías | Sí | Sí | Aprobar, rechazar, retirar; categorías. |
| RF-45 | Contenido reportado | Sí | Sí | Resolver, descartar o eliminar el contenido. |
| RF-46 | Cupones y promociones | Sí | Sí | |
| RF-47 | Compras e ingresos | Sí | Sí | |
| RF-48 | Certificados emitidos | Sí | Sí | Con revocar/reactivar. |
| RF-49 | Generar reportes | Sí | Sí | Por rango de fechas: usuarios, cursos, ventas y rendimiento. |
| RF-50 | Asistente virtual | Sí | Sí | |
| RF-51 | Consultas por chatbot | Sí | Sí | Los tres roles. |

## Requisitos no funcionales

| N.º | Estado | Cómo se cumple / qué falta |
|---|---|---|
| RNF-01 Rendimiento | Infra | La API pagina y usa consultas acotadas; **no se midió** el tiempo de carga (< 3 s) bajo carga real. |
| RNF-02 Disponibilidad 99 % | Infra | Depende del hosting y monitoreo; no es algo del código. |
| RNF-03 Escalabilidad | Parcial | Código modular (paquetes por dominio) y API sin estado (token firmado), lista para varias instancias. |
| RNF-04 Hash de contraseñas | Sí | Hasher de Django (nunca texto plano). |
| RNF-05 HTTPS/TLS | Parcial | Se activa solo con `DEBUG=False` (redirección, HSTS, cookies seguras). Falta el certificado y el proxy del servidor; con proxy usar `BEHIND_PROXY=True`. |
| RNF-06 Control por roles | Sí | Web y API validan rol y propiedad (probado: estudiante/docente no acceden a funciones ajenas). |
| RNF-07 Sesiones | Sí | Web: sesión de 24 h con cookie protegida. App: token firmado que caduca a los 7 días y se invalida al cambiar la contraseña. |
| RNF-08 Privacidad | Sí | Acceso solo a datos propios (por rol); la API no expone datos de otros usuarios. |
| RNF-09 Validación de entradas | Sí | Validación en formularios y en cada endpoint de la API. |
| RNF-10 Copias de seguridad | Parcial | `scripts/backup_db.sh` (base de datos + media, con retención). **Falta programarlo** con cron. |
| RNF-11 Recuperación | Parcial | `scripts/restore_db.sh` restaura la base y los archivos. Probado el respaldo; el restore no se ejecutó para no pisar tus datos. |
| RNF-12 Usabilidad | Sí | Mismo estilo y flujos en web y app. |
| RNF-13 Accesibilidad | Parcial | Contraste, tamaños táctiles, etiquetas y modo oscuro; **no se hizo una auditoría formal** (lector de pantalla). |
| RNF-14 Responsive | Sí | Web responsive + app móvil. |
| RNF-15 Compatibilidad | Infra | No se probó en todos los navegadores. |
| RNF-16 Mantenibilidad | Sí | Código modular y documentado (`README`, `app.txt`, este archivo). |
| RNF-17 Registro de eventos | Sí | `ActivityLog`: inicios/cierres de sesión y fallos, registro, cambios de contraseña, pagos, acciones de administrador y de cursos (web y app). |
| RNF-18 Integridad | Sí | Compras dentro de transacciones atómicas; el progreso y las notas se calculan en el servidor. |
| RNF-19 Carga de contenido | Sí | Formatos y tamaños limitados (imagen 5 MB, documento 50 MB, entrega 25 MB, video 500 MB) en web (middleware) y API. |
| RNF-20 Seguridad de pagos | Sí | Ni el web ni la app envían el número completo, el vencimiento ni el CVC: solo los últimos 4 dígitos. **El web enviaba la tarjeta completa; se corrigió.** El pago sigue siendo simulado (sin pasarela real). |
