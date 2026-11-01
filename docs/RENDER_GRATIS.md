# AcadEMI en Render sin pagar

Esta guía usa Render Free para Django y Neon Free para PostgreSQL. El código ya
incluye `build.sh`, `start.sh` y Python 3.12. No ejecutes `seed.py` en el
servidor: crea usuarios de prueba con contraseñas conocidas.

## 1. Base de datos

1. Crea un proyecto en [Neon](https://console.neon.tech/) con el plan Free.
2. Copia la URL PostgreSQL **directa** (incluye `sslmode=require`). Guárdala
   como `DATABASE_URL` en Render. No la publiques en Git ni en capturas.
3. Para conservar imágenes, entregas y certificados tras los reinicios, crea
   un bucket **privado** en Neon Object Storage. Copia sus datos S3 a las
   variables `AWS_*` de abajo. Puedes añadirlo después, pero los archivos
   subidos antes de configurarlo no se trasladan automáticamente.

## 2. Correo para registro y recuperación

Render Free bloquea SMTP en los puertos 25, 465 y 587. Una opción gratuita es
[Brevo](https://www.brevo.com/), con su servidor SMTP en el puerto 2525.
Crea una cuenta Free, verifica un remitente y genera una clave SMTP. Sin un
servicio de correo configurado, el registro y la recuperación de contraseña
no podrán enviar mensajes.

## 3. Formulario de Render

En **New Web Service**, usa estos valores:

| Campo | Valor |
| --- | --- |
| Repository | `yleonardomt/AcadEMI` |
| Branch | `main` |
| Language | `Python 3` |
| Root Directory | Vacío |
| Build Command | `./build.sh` |
| Start Command | `./start.sh` |
| Instance Type | `Free ($0/mes)` |

Variables de entorno **obligatorias**:

| Clave | Valor |
| --- | --- |
| `DEBUG` | `False` |
| `SECRET_KEY` | Pulsa **Generate** en Render; conserva el mismo valor en futuros despliegues |
| `DATABASE_URL` | URL directa de PostgreSQL de Neon |
| `DEMO_CHECKOUT` | `True` para el flujo académico sin cobros reales |
| `ADMIN_USERNAME` | Nombre de usuario del administrador inicial |
| `ADMIN_EMAIL` | Correo del administrador inicial |
| `ADMIN_PASSWORD` | Contraseña fuerte y distinta de la contraseña de Ubuntu |

No necesitas escribir `ALLOWED_HOSTS`, `SITE_URL`, `FORCE_HTTPS`,
`BEHIND_PROXY` ni `PORT`: el proyecto usa las variables que Render proporciona
automáticamente. Si luego añades un dominio propio, sí tendrás que ajustar
`ALLOWED_HOSTS` y `SITE_URL`.

Para correo, añade además:

| Clave | Valor |
| --- | --- |
| `EMAIL_HOST` | `smtp-relay.brevo.com` |
| `EMAIL_PORT` | `2525` |
| `EMAIL_USE_TLS` | `True` |
| `EMAIL_HOST_USER` | Usuario SMTP mostrado por Brevo |
| `EMAIL_HOST_PASSWORD` | Clave SMTP de Brevo |
| `DEFAULT_FROM_EMAIL` | Remitente verificado en Brevo, por ejemplo `AcadEMI <correo-verificado@ejemplo.com>` |

Para Neon Object Storage, añade las cinco variables que muestra Neon:

| Clave | Valor |
| --- | --- |
| `AWS_ENDPOINT_URL_S3` | URL HTTPS del endpoint S3 de la rama |
| `AWS_STORAGE_BUCKET_NAME` | Nombre del bucket privado |
| `AWS_ACCESS_KEY_ID` | ID de acceso S3 |
| `AWS_SECRET_ACCESS_KEY` | Clave secreta S3 |
| `AWS_REGION` | Región S3 indicada por Neon |

Si usas el asistente con Gemini, añade `GEMINI_API_KEY` de Google AI Studio.
Sin ella responde con la base de conocimiento interna.

## 4. Publicar y comprobar

Pulsa **Deploy web service** cuando el código actualizado esté en `main`.
El build aplica migraciones, crea el administrador si aún no existe y carga
el catálogo de ingeniería únicamente si la base está vacía. Si falla,
consulta los logs de **Build** y **Events** en Render.

Cuando Render muestre **Live**, abre la URL `https://...onrender.com` y prueba:

1. Portada, catálogo e imágenes de cursos.
2. Inicio de sesión del administrador, `/dashboard/` y `/panel/usuarios/`.
3. Registro con una dirección propia y recepción del correo de verificación.
4. Una ruta inexistente para comprobar la página 404.
5. Una subida y descarga de archivo si conectaste Object Storage.

Render gestiona gratuitamente HTTPS y redirige HTTP a HTTPS. No hay que
exponer el proceso Python en el puerto 80: `start.sh` escucha el puerto
interno `PORT` que Render le indica.

## Límites del plan gratuito

Render Free puede dormirse tras 15 minutos sin visitas y tardar cerca de un
minuto en despertar. Su disco local no conserva archivos tras un reinicio.
Neon Free y Brevo Free también tienen cuotas. Comprueba el consumo en sus
paneles antes de una revisión con varios usuarios. El flujo académico de
compra no realiza cargos: para ventas reales habrá que integrar y verificar
una pasarela de pago.
