# Revisión de coherencia — 11 de noviembre de 2026

## Hallazgos corregidos

El catálogo publicado mostraba **47 tarjetas correspondientes a 33 cursos únicos**: los destacados y populares se repetían antes de la lista completa. Ahora el catálogo presenta cada curso una sola vez y mantiene las etiquetas de destacado/popular. El total se consulta desde los cursos publicados, como en inicio, API móvil y chatbot; no se fijó artificialmente en 33 ni se eliminaron cursos.

- Se eliminaron también los identificadores de controles repetidos que afectaban los botones del carrito.
- En teléfonos, las categorías se desplazan horizontalmente para dejar visibles los cursos sin recorrer primero una lista larga de filtros.
- Los filtros de categoría inválidos devuelven 404 en web o 400/404 en API, en lugar de producir un error 500.
- La búsqueda por categoría y nombre del docente funciona tanto en web como en API y recorta espacios sobrantes.
- La paginación móvil tiene un desempate estable para que cursos con igual precio o fecha no aparezcan repetidos entre páginas.
- Las inscripciones pendientes o canceladas no cuentan para destacar un curso como popular. Los botones de compra del catálogo se muestran al estudiante.
- Web y móvil seleccionan la promoción que más descuenta en bolivianos, comparando cupones globales y específicos, porcentuales y de monto fijo.
- El asistente diferencia preguntas sobre el total de consultas por una materia; maneja cursos sin categoría y solo enumera categorías publicadas. Consulta las compras y calificaciones del usuario conectado sin mezclar datos de otras cuentas.
- La ayuda y el asistente siguen accesibles mientras se verifica el correo; los accesos privados continúan bloqueados hasta confirmar la cuenta.
- El panel administrador incluye enlaces a editar cursos y gestionar su contenido.
- Una evaluación con intentos registrados no se puede reemplazar desde web ni API. Para cambiar sus preguntas se crea otra evaluación; así se conservan respuestas y resultados anteriores.
- Los correos de verificación y recuperación usan enlaces públicos de ayuda, términos y privacidad, sin enlaces vacíos, correo de soporte inventado ni año fijo. El texto de caducidad evita prometer un plazo distinto al configurado.

## Comprobaciones

| Comprobación | Resultado |
| --- | --- |
| Django: 66 pruebas | Correctas; incluyen 25 regresiones añadidas desde la revisión anterior de 41 pruebas |
| `manage.py check` | Sin incidencias |
| `collectstatic --noinput` con almacenamiento de producción para estáticos | Correcto |
| Chromium: 74 combinaciones de ruta/rol × 5 anchos × 2 temas | 740 cargas sin errores HTTP ni desbordamientos horizontales detectados |
| Contraste calculado de textos y controles seleccionados | Sin fallos detectados en las 740 cargas |
| Catálogo: favoritos, añadir/quitar del carrito y filtro de categoría en 390/1440 px y ambos temas | Correctos; cada curso y control aparece una sola vez |
| `flutter analyze` | Sin incidencias |
| `flutter test test/smoke_test.dart` | 5 pruebas correctas |
| Recursos públicos de Render: inicio, autenticación, catálogo, categorías, búsqueda, ayuda, términos, salud, 33 detalles de curso e imágenes | 57 comprobaciones HTTP correctas |
| Recorridos de usuario completos | 55 pasos en navegador y 15 por API móvil, con datos aislados |
| Perfil actualizado: tres roles × cinco anchos × dos temas | 30 comprobaciones adicionales sin fallos detectados |

Los anchos revisados son 320, 390, 768, 1024 y 1440 px. Se verifican rutas públicas y de estudiante, docente, administrador y usuario pendiente de verificación. Las acciones GET que redirigen deliberadamente se comprueban en su destino. Los datos de escritura de las pruebas son locales y no alteran compras, usuarios o progreso de producción.

Las mediciones automáticas de contraste cubren elementos seleccionados; no constituyen una certificación de accesibilidad. Las pruebas básicas de Flutter tampoco equivalen a comprobar todos los flujos en un dispositivo físico. Los videos de terceros pueden depender de disponibilidad y restricciones de YouTube.

## Límites concretos para preparar la presentación

1. **RF-32 sigue pendiente:** el checkout registra la compra académica con un método interno; todavía no permite elegir y conservar distintos métodos de pago. Las compras, accesos y comprobantes se prueban dentro del alcance académico acordado, sin cobro bancario.
2. **Nuevos archivos subidos:** el proyecto admite un bucket S3 compatible, pero hay que comprobar su configuración y persistencia en el despliegue. En producción, con el backend local, solo se publican directamente las imágenes incluidas en el repositorio; las URL de nuevos archivos requieren configurar almacenamiento externo. La base PostgreSQL no almacena los archivos multimedia.
3. **Dispositivo de presentación:** queda probar en el teléfono físico el ingreso con cada rol, una lección de video, una evaluación y la descarga de un PDF. En esta revisión se probaron la API y los componentes básicos de Flutter, sin instalar otro APK.
4. **Servicios externos:** no se enviaron correos reales ni consultas a Gemini como parte de estas pruebas. La recepción por Brevo ya había sido confirmada por el usuario; las respuestas locales del asistente se probaron sin depender de Gemini.

El estado de los 47 requisitos está en [AUDITORIA_RF_01_47.md](AUDITORIA_RF_01_47.md). Esta revisión respalda una presentación académica con los recorridos probados y sus límites; no demuestra que todos los posibles flujos estén libres de fallos.

La ampliación solicitada con compras, entregas, exámenes, certificados y gestión docente se detalla en [PRUEBAS_DE_USUARIO_2026_11_11.md](PRUEBAS_DE_USUARIO_2026_11_11.md).
