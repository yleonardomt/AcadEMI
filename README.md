# AcadEMI

Plataforma educativa online (estilo Udemy) construida con Django. Permite a
estudiantes comprar e inscribirse en cursos, a docentes crear y gestionar
contenido, y a administradores moderar la plataforma — con carrito de
compras, cupones, certificados automáticos, cuestionarios con medidas
anti-copia, y un asistente virtual con IA.

## Índice

- [Requisitos](#requisitos)
- [Instalación manual completa (Ubuntu/Debian)](#instalación-manual-completa-ubuntudebian)
- [Instalación en macOS o Windows](#instalación-en-macos-o-windows)
- [Variables de entorno](#variables-de-entorno)
- [Credenciales de prueba](#credenciales-de-prueba)
- [Datos de ejemplo (seed)](#datos-de-ejemplo-seed)
- [Asistente virtual con IA (opcional)](#asistente-virtual-con-ia-opcional)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Funcionalidades principales](#funcionalidades-principales)

## Requisitos

- Python 3.12 o superior
- PostgreSQL 14 o superior (el proyecto **no** usa SQLite)
- pip y `venv` (vienen con Python)
- Una cuenta de Gmail (opcional, solo si querés que la plataforma envíe
  correos reales de verificación, recuperación de contraseña, certificados
  y comprobantes de compra)

## Instalación manual completa (Ubuntu/Debian)

Todo el bloque de abajo se puede copiar y pegar tal cual en una terminal
limpia (WSL2, Ubuntu, Debian) y deja la plataforma corriendo en
`http://127.0.0.1:8001`. Cambiá `TU_PASSWORD_DB` por una contraseña propia
antes de pegarlo — se usa dos veces (al crear el usuario de PostgreSQL y en
el `.env`), así que tiene que ser la misma en ambos lugares.

```bash
# ============================================
# 1. Instalar PostgreSQL
# ============================================
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql

# ============================================
# 2. Crear la base de datos y el usuario de la app
# ============================================
sudo -u postgres psql -c "CREATE USER academi_user WITH PASSWORD 'TU_PASSWORD_DB';"
sudo -u postgres psql -c "CREATE DATABASE academi_db OWNER academi_user;"

# ============================================
# 3. Clonar el repositorio
# ============================================
git clone git@github.com:yleonardomt/AcadEMI.git
cd AcadEMI

# ============================================
# 4. Instalar Python, crear y activar el entorno virtual
# ============================================
sudo apt install -y python3 python3-venv python3-pip
python3 -m venv venv
source venv/bin/activate

# ============================================
# 5. Instalar las dependencias del proyecto
# ============================================
pip install --upgrade pip
pip install -r requirements.txt

# ============================================
# 6. Configurar variables de entorno
# ============================================
cp .env.example .env
sed -i "s/DB_PASSWORD=change-me/DB_PASSWORD=TU_PASSWORD_DB/" .env
sed -i "s/SECRET_KEY=change-me-to-a-random-secret-key/SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')/" .env
# (Opcional) Editá .env para agregar tu cuenta de Gmail y/o tu clave de
# Groq — ver la sección "Variables de entorno" más abajo.

# ============================================
# 7. Aplicar migraciones (crea todas las tablas en PostgreSQL)
# ============================================
python manage.py migrate

# ============================================
# 8. Cargar datos de ejemplo: usuarios, cursos, exámenes, cupones, etc.
#    (usuario/contraseña de prueba: ver sección "Credenciales de prueba")
# ============================================
python manage.py shell < seed.py

# ============================================
# 9. Levantar el servidor de desarrollo
# ============================================
python manage.py runserver 8001
```

La plataforma queda disponible en `http://127.0.0.1:8001`.

### Reiniciar la base de datos desde cero

Si en algún momento querés borrar todo lo que hay en la base de datos y
volver a sembrarla (por ejemplo, para probar la plataforma desde un estado
limpio), con PostgreSQL ya instalado alcanza con:

```bash
source venv/bin/activate
set -a; source .env; set +a
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public AUTHORIZATION $DB_USER;"
python manage.py migrate
python manage.py shell < seed.py
```

## Instalación en macOS o Windows

<details>
<summary>macOS (Homebrew)</summary>

```bash
brew install postgresql@16 python@3.12
brew services start postgresql@16
psql postgres -c "CREATE USER academi_user WITH PASSWORD 'TU_PASSWORD_DB';"
psql postgres -c "CREATE DATABASE academi_db OWNER academi_user;"

git clone git@github.com:yleonardomt/AcadEMI.git
cd AcadEMI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Editá .env: poné DB_PASSWORD=TU_PASSWORD_DB y un SECRET_KEY propio

python manage.py migrate
python manage.py shell < seed.py
python manage.py runserver 8001
```
</details>

<details>
<summary>Windows (PowerShell)</summary>

1. Instalá PostgreSQL con el instalador oficial:
   https://www.postgresql.org/download/windows/ (durante la instalación te
   pide una contraseña para el usuario `postgres` — anotala).
2. Instalá Python 3.12+ desde https://www.python.org/downloads/ (marcá
   "Add python.exe to PATH").
3. Abrí "SQL Shell (psql)" desde el menú inicio y ejecutá:
   ```sql
   CREATE USER academi_user WITH PASSWORD 'TU_PASSWORD_DB';
   CREATE DATABASE academi_db OWNER academi_user;
   ```
4. En PowerShell:
   ```powershell
   git clone git@github.com:yleonardomt/AcadEMI.git
   cd AcadEMI
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt

   copy .env.example .env
   # Editá .env: poné DB_PASSWORD=TU_PASSWORD_DB y un SECRET_KEY propio

   python manage.py migrate
   python manage.py shell < seed.py
   python manage.py runserver 8001
   ```
</details>

## Variables de entorno

Copiá `.env.example` a `.env` y completá:

| Variable | Descripción | Obligatoria |
|---|---|---|
| `SECRET_KEY` | Clave secreta de Django. Generá una propia para producción. | Sí |
| `DEBUG` | `True` en desarrollo, `False` en producción. | Sí |
| `ALLOWED_HOSTS` | Dominios permitidos, separados por coma (vacío está bien en desarrollo). | No |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | Conexión a PostgreSQL. Deben coincidir con el usuario y la base que creaste en el paso 2 de la instalación. | Sí |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | Cuenta de Gmail y [contraseña de aplicación](https://myaccount.google.com/apppasswords) para enviar correos reales (verificación, recuperación de contraseña, certificados, comprobantes de compra). Si se dejan vacías, Django lanzará un error al intentar enviar un correo — para desarrollo sin correos reales, descomentá la línea de `EMAIL_BACKEND` de consola en `core/settings.py`. | No |
| `SITE_URL` | URL base usada en los enlaces de los correos. | No |
| `GROQ_API_KEY` | Clave gratuita de [Groq](https://console.groq.com/keys) para que el chatbot responda con IA real. Ver sección de abajo. | No |
| `GROQ_MODEL` | Modelo de Groq a usar (por defecto `llama-3.1-8b-instant`). | No |

## Credenciales de prueba

Después de correr `python manage.py shell < seed.py` (paso 8 de la
instalación), estas cuentas ya existen y están listas para entrar por
`/login/`:

| Rol | Usuario | Contraseña | Qué tiene cargado |
|---|---|---|---|
| **Administrador** | `admin` | `admin` | Acceso completo al panel (`/panel/...`): usuarios, cursos, categorías, cupones, pagos, certificados, reportes. |
| **Docente** | `docente` | `docente` | Dos cursos propios publicados y destacados (uno pago, uno gratis), con módulos, lecciones y exámenes; una pregunta de un estudiante ya respondida; un cupón activo (`BIENVENIDA10`, 20%, primeros 10 usos) y uno vencido (`PROMOVENCIDA`), ambos gestionables desde "Mis cupones". |
| **Estudiante** | `estudiante` | `estudiante` | Un curso completado con certificado descargable y una evaluación ya rendida (visible en "Mis calificaciones"), un curso en progreso, un favorito y un curso en el carrito. |

También se crean más usuarios de ejemplo para tener volumen de datos (otros
docentes con sus propios cursos, ~20 estudiantes con inscripciones,
certificados, reseñas y favoritos aleatorios):

| Grupo | Usuarios | Contraseña |
|---|---|---|
| Administradores extra | `admin2` | `admin123` |
| Docentes extra | `teacher1` … `teacher5` | `teacher123` |
| Estudiantes extra | `estudiante01` … `estudiante20` | `student123` |

Cambiá estas contraseñas antes de exponer la plataforma fuera de tu
máquina (Perfil → Cambiar contraseña), o creá un administrador propio:

```bash
python manage.py shell -c "
from academi.models import User
User.objects.create_user(
    username='tu_usuario', email='tu@correo.com', password='tu_contraseña',
    role='admin', is_staff=True, is_superuser=True, is_active=True, email_verified=True,
)
"
```

## Datos de ejemplo (seed)

`seed.py` crea usuarios (estudiantes, docentes, administradores —
incluyendo las tres cuentas de prueba de arriba), categorías, ~30 cursos
con módulos, lecciones y exámenes con preguntas reales, inscripciones,
certificados, cupones, una pregunta al docente ya respondida, reseñas,
favoritos y notificaciones, para que la plataforma no se vea vacía.
Ejecutalo con:

```bash
python manage.py shell < seed.py
```

Es seguro volver a ejecutarlo: usa `get_or_create` para no duplicar datos
existentes. Si querés partir de una base de datos completamente vacía
antes de sembrar de nuevo, mirá "Reiniciar la base de datos desde cero" en
la sección de instalación.

## Asistente virtual con IA (opcional)

El chatbot (esquina inferior derecha del sitio, y en `/chatbot/`) funciona
de dos formas:

1. **Sin configurar nada:** responde usando su propia base de conocimiento
   (`ChatKnowledgeBase` / `ChatIntent` en la base de datos), con respuestas
   ya cargadas sobre cursos, compras, progreso, certificados y ayuda.
2. **Con `GROQ_API_KEY` configurada:** además de esa base de conocimiento,
   genera respuestas con un modelo de lenguaje real (vía la API gratuita de
   [Groq](https://console.groq.com/keys)), usando datos reales de la
   plataforma como contexto (cantidad de cursos, categorías, y — si el
   usuario tiene sesión iniciada — sus propios cursos y progreso). Si la
   llamada a la IA falla o no hay clave configurada, el chatbot vuelve a su
   base de conocimiento automáticamente, sin que el usuario note nada.

Para activarlo: creá una cuenta gratuita en Groq, generá una clave en
[console.groq.com/keys](https://console.groq.com/keys), y ponela en
`GROQ_API_KEY` dentro de tu `.env`.

## Estructura del proyecto

El código está organizado por dominio (no en archivos gigantes), tanto en
el backend como en los estáticos:

```
academi/
  models/        Un archivo por dominio (users, courses, learning,
                 evaluations, commerce, chatbot, system) reexportados
                 desde models/__init__.py
  views/         Igual que models/, un archivo por dominio (auth,
                 dashboard, courses, lessons, quizzes, cart, payments,
                 admin_panel, chatbot)
  admin/         Configuración del admin de Django, por dominio
  utils/         email.py, ai_chatbot.py, security.py, http.py
  decorators/    Decoradores reutilizables (quiz_decorators.py)
  templatetags/  Tags/filtros propios (course_tags.py, static_extras.py)
  migrations/

templates/
  partials/      base.html, header.html, footer.html, chatbot_widget.html
  academi/       Un directorio por sección (auth, courses, dashboard,
                 payments, admin, users, emails, pages, chatbot)

static/
  css/
    base.css           Variables y reset — única fuente de verdad de colores
    layout.css         Navbar, sidebar, footer, contenido principal
    components/        Un archivo por componente reutilizable (botones,
                        tarjetas, formularios, tablas, modales, alertas,
                        notificaciones, widget del chatbot, fondo de
                        partículas, etc.)
    pages/              Estilos específicos de una sola página
  js/
    csrf.js, notifications.js, modals.js, tooltips.js   Utilidades globales
    chatbot.js / chatbot-widget.js                       Asistente virtual
    particles-bg.js                                      Fondo 3D (Three.js)
    forms-validation.js, landing.js                      Por página
```

## Funcionalidades principales

- **Autenticación:** registro (con selector visual de rol), inicio de
  sesión con CAPTCHA, recuperación y cambio de contraseña, verificación de
  correo.
- **Catálogo:** navegación por categorías, cursos destacados y más
  comprados, búsqueda, favoritos.
- **Cursos:** creación y gestión por el docente (módulos, lecciones de
  video/documento/texto/cuestionario/tarea), publicación, aprobación por
  un administrador.
- **Aprendizaje:** reproductor de lecciones, seguimiento de progreso,
  cuestionarios cronometrados con medidas anti-copia (bloqueo de
  copiar/pegar, detección de cambio de pestaña con bloqueo tras 3
  intentos, registro de incidentes de seguridad para el docente).
- **Certificados:** se generan automáticamente al completar un curso, se
  envían por correo, y se pueden verificar públicamente por código.
- **Carrito y pagos:** cupones de descuento, múltiples métodos de pago,
  historial de compras, comprobante descargable/imprimible, correo de
  confirmación de compra.
- **Panel de administración** (`/panel/...`): usuarios, cursos (aprobar/
  rechazar/retirar), categorías, cupones, pagos, certificados emitidos,
  contenido reportado, generación de reportes.
- **Asistente virtual:** widget flotante en todo el sitio + página
  completa, con IA opcional (ver arriba).
