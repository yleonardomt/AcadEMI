# Acceso web con Google

La web ofrece **Continuar con Google** en `/login/` y `/register/`. Utiliza OAuth/OpenID Connect con Google y la base de datos existente. No requiere contratar otro proveedor de autenticación. La creación del proyecto y del cliente se describe en el [codelab gratuito de Google](https://codelabs.developers.google.com/codelabs/sign-in-with-google-button).

## Render

Configurar y guardar las dos variables en **Environment → Save, rebuild, and deploy**:

| Variable | Valor |
| --- | --- |
| `GOOGLE_OAUTH_CLIENT_ID` | ID del cliente OAuth de tipo Aplicación web |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Secreto del mismo cliente, únicamente en las variables del servicio |

En Google Auth Platform, el cliente debe tener:

- Origen autorizado: `https://academi-efte.onrender.com`
- URI de redirección autorizada: `https://academi-efte.onrender.com/auth/google/callback/`

La aplicación obtiene el origen del callback desde `SITE_URL` o la URL externa de Render. La URI registrada en Google debe coincidir exactamente, incluida la barra final. Si se usa un dominio propio, actualizar `SITE_URL`, el origen y la URI en Google. No subir el archivo JSON de credenciales al repositorio.

El botón aparece al configurar ambas variables. Sin ellas, continúa funcionando el ingreso tradicional. La migración `0014_google_identity` añade una tabla de vínculos; no modifica compras, cursos o perfiles existentes.

## Comportamiento

- Cuenta nueva: después de elegir Google, se confirma el nombre, el rol Estudiante/Docente y los términos. Un docente indica su especialidad. Google no permite crear administradores desde el registro.
- Gmail o Google Workspace con correo verificado: acceso directo después de completar el registro, sin otro correo de activación. Si Google no es autoridad del correo externo, se conserva la verificación por email de AcadEMI.
- Cuenta local existente con el mismo correo verificado de Gmail/Workspace: se conserva la cuenta, sus cursos, su contraseña y su rol. No se modifica el rol por elegir otro perfil en el registro.
- Administrador, cuenta con correo local pendiente, correo externo o coincidencia ambigua: ingresar primero con usuario/contraseña. Después de verificar el correo, usar **Mi perfil → Vincular Google**, confirmando la contraseña actual. Para correos duplicados, cada titular debe identificar su cuenta por usuario.
- Una identidad de Google corresponde a una sola cuenta de AcadEMI. No se permite moverla a otro usuario desde un inicio de sesión diferente.
- Las cuentas nuevas de Google pueden crear una contraseña desde **Mi perfil → Crear contraseña**. Luego también pueden ingresar con correo y contraseña, incluida la app móvil actual. Esta implementación añade Google a la web; no incluye el selector nativo de Google de Android/iOS.
- Cancelar la selección de Google, un enlace vencido o una interrupción del proveedor devuelve al formulario con un mensaje y permite reintentar.

## Verificación

Revisión del 18 de noviembre de 2026:

- **85 pruebas Django correctas**, incluidas **19 pruebas nuevas** para esta integración.
- Tokens JWT firmados con claves RSA de prueba, verificados por la biblioteca oficial: se rechazan firma incorrecta, audiencia/issuer incorrectos, token vencido, nonce incorrecto y correo sin verificar. Las peticiones de red se sustituyen por respuestas de prueba.
- Pruebas de CSRF, método HTTP, estado vencido/reutilizado, PKCE, roles, términos, vínculo de cuentas, cuentas desactivadas, errores del proveedor, conservación de inscripciones y creación opcional de contraseña.
- **9 pasos de navegador** en una base aislada, con un proveedor OAuth local de prueba: registro de estudiante y docente, acceso repetido a la misma cuenta, perfil vinculado y creación de contraseña. El doble del proveedor existe solo en el directorio local de revisión; no forma parte del código desplegado.
- **30 combinaciones** de página/ancho/tema para login, registro y completar cuenta, en 320/390/768/1024/1440 px y temas claro/oscuro: sin desbordamiento horizontal ni fallos de contraste detectados en los controles analizados.
- `manage.py check`, migración sobre SQLite aislado y recopilación de estáticos correctos.

El acceso con una cuenta personal real de Google requiere que su titular complete el selector/consentimiento de Google. Las pruebas locales no sustituyen ese último recorrido en Render ni verifican las restricciones de audiencia del proyecto en Google.

## Desarrollo local

Si se quiere utilizar el mismo cliente en desarrollo, registrar también el origen local y el callback exacto del puerto usado, por ejemplo `http://localhost:8000` y `http://localhost:8000/auth/google/callback/`. Configurar en un `.env` ignorado las dos variables y `SITE_URL=http://localhost:8000`. Mantener en producción el callback HTTPS de Render.

## Referencias

- [OpenID Connect de Google](https://developers.google.com/identity/openid-connect/openid-connect)
- [Verificación del ID token y autoridad del correo](https://developers.google.com/identity/sign-in/web/backend-auth)
- [Biblioteca oficial google-auth para ID tokens](https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.id_token.html)
- [Identidad visual del botón de Google](https://developers.google.com/identity/branding-guidelines)

Solo se solicitan `openid email profile`. La identidad se asocia por `sub`, se verifican firma, audiencia, issuer, caducidad y nonce, y el intercambio de código utiliza PKCE y estado de sesión. No se guardan tokens de acceso/refresh ni secretos de Google en perfiles o plantillas.
