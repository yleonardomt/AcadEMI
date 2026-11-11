# Pruebas de usuario — 11 de noviembre de 2026

Se ejecutaron recorridos completos con Chromium y Playwright, usando formularios, CAPTCHA, clics, subida de archivos y peticiones de la API móvil. La aplicación utiliza su código normal y una copia SQLite aislada, cuentas específicas y almacenamiento local de pruebas. Las compras, cursos, preguntas y resultados creados no se insertaron en producción.

Los correos de esta prueba se escribieron en archivos locales: se extrajo el enlace del mensaje generado por la aplicación y se abrió desde el navegador. Esto comprueba la composición y el recorrido del enlace, sin enviar correos a personas ni comprobar nuevamente la entrega de Brevo.

## Recorridos terminados

| Recorrido | Pasos aprobados | Acciones y resultado |
| --- | ---: | --- |
| Estudiante, docente y administrador en navegador | 33 | Ingresar con CAPTCHA; bloquear una lección antes de comprar; agregar al carrito; rechazar cupón inválido; aplicar 25%; comprar; abrir historial; descargar comprobante PDF; abrir y completar texto, video y documento; comentar; preguntar; subir práctica PDF; reprobar y reintentar cuestionario; aprobar examen; llegar a 100%; consultar notas; descargar y verificar certificado; respuesta y calificación del docente; consultar estudiante/resultados/venta; publicar reseña y ver retroalimentación. |
| Creación y aprobación de curso en navegador | 9 | Crear curso pago con imagen, módulo, texto, video y cuestionario de cuatro opciones; editarlo conservando opciones y respuesta correcta; enviar a revisión; aprobar como administrador; comprobar detalle público e imagen. |
| Cuenta desde navegador con ancho de teléfono | 13 | Registrarse; generar correo de verificación; bloquear dashboard mientras está pendiente; activar mediante el enlace del correo; actualizar nombre, apellidos, teléfono y biografía; comprobar nombre en API; cambiar contraseña; salir; ingresar; solicitar recuperación; abrir enlace y restablecer; ingresar de nuevo; rechazar reutilización del enlace. |
| API utilizada por la app móvil | 15 | Ingresar; bloquear contenido antes de comprar; impedir consultar compras/certificados de otra cuenta y el panel admin; favoritos; carrito/cupón; compra e historial; PDF; lecciones; entrega obligatoria de tarea; reprobar, reintentar y aprobar; límite de intentos; progreso 100% y certificado; asistente con compras propias. |
| **Total** | **70** | **55 pasos en navegador y 15 pasos de API.** |

## Coherencia de los datos

Cada uno de los dos estudiantes compró el curso de prueba de **Bs 120**, con cupón de **25%**, descuento de **Bs 30** y pedido por **Bs 90**. El historial y los comprobantes PDF reflejan ese importe. El curso registra dos estudiantes completados, dos pedidos por un total de **Bs 180** dentro del alcance académico, seis intentos de evaluación, dieciocho respuestas guardadas y dos certificados.

Cada estudiante realizó tres intentos: cuestionario reprobado con 0/15, reintento aprobado con 15/15 y examen aprobado con 15/15. El primer fallo no completó la evaluación; la aprobación sí actualizó el progreso. Se verificó que otra cuenta no pueda consultar los comprobantes y certificados privados del propietario. La verificación pública de un certificado por su código sí está disponible.

La tarea del primer estudiante recibió **95/100** y retroalimentación del docente, visibles después para el estudiante. También se comprobó el intercambio de pregunta y respuesta y la publicación de una reseña.

## Fallos encontrados y corregidos

1. **Respuestas de evaluaciones sin persistencia.** Web y API calculaban la nota, pero no creaban los registros de `UserAnswer`. Ahora comparten una función que califica y guarda cada respuesta, incluida una pregunta omitida, con sus puntos y la opción elegida. La operación es transaccional y comprueba el límite de intentos con bloqueo de la inscripción.
2. **Opciones reemplazadas al editar.** El editor web interpretaba incorrectamente los nombres de campos y sustituía las opciones por textos genéricos. Ahora reconoce los índices enviados por el formulario y conserva los textos y la respuesta correcta. La prueba comprueba sus valores, además de contar las opciones.
3. **Nombre de perfil incoherente.** El formulario no mostraba nombre/apellidos, aunque esos campos estaban incluidos en el modelo de formulario. Ahora se pueden editar, se conservan al modificar otros datos y se sincronizan con el nombre que presenta la API. Actualizar el nombre completo desde móvil tampoco duplica el apellido anterior en web.

Se añadieron diez regresiones a Django: **66 pruebas correctas** en total. El perfil actualizado pasó **30 comprobaciones** de rol/ancho/tema, sin errores HTTP, desbordamiento horizontal ni fallos de contraste detectados en los elementos analizados.

## Alcance y límites

- Las descargas se comprobaron por respuesta HTTP y cabecera binaria `%PDF`; no solo por la existencia de un botón.
- Las pruebas de cuenta usan un ancho de 390 px. Eso no sustituye probar la app instalada en el teléfono físico de la presentación.
- Se abrió el reproductor MySQL con el título correcto y se reprodujo un fragmento real del primer video: el tiempo avanzó más de cinco segundos. No se da por aprobada la reproducción completa de todo el catálogo ni de todos los videos en redes/dispositivos diferentes.
- Los recorridos de escritura se hicieron en el entorno aislado. Los chequeos públicos del despliegue son de lectura.
- Para subir nuevos archivos a Render deben resolverse las URL y persistencia mediante almacenamiento externo. El entorno local de estas pruebas sirve archivos de desarrollo y no verifica un bucket de producción.
- RF-32, selección de distintos métodos de pago, sigue pendiente. Estos recorridos verifican las compras académicas acordadas, sin confirmar cobros bancarios.

La revisión general está en [REVISION_COHERENCIA_2026_11_11.md](REVISION_COHERENCIA_2026_11_11.md).
