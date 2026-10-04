import logging
import re

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django_ratelimit.decorators import ratelimit

from ..models import User, Notification, EMI_STUDENT_DISCOUNT_PERCENT, is_emi_student_email
from ..utils import (
    send_verification_email, send_password_reset_email, generate_reset_link,
)
from .auth import api_view, error, ok, make_token, parse_body
from .serializers import user_json
from .support import (
    new_captcha, check_captcha, login_needs_captcha, register_login_failure,
    clear_login_failures, log_action, validate_upload,
)

logger = logging.getLogger(__name__)

PASSWORD_RULES = [
    (r'.{8,}', 'La contraseña debe tener al menos 8 caracteres'),
    (r'[A-Z]', 'Debe tener al menos una mayúscula'),
    (r'[a-z]', 'Debe tener al menos una minúscula'),
    (r'[0-9]', 'Debe tener al menos un número'),
    (r'[!@#$%^&*(),.?":{}|<>]', 'Debe tener al menos un carácter especial (!@#$%^&*)'),
]


def check_password_rules(password):
    for pattern, message in PASSWORD_RULES:
        if not re.search(pattern, password or ''):
            return message
    return None


def _username_from_email(email):
    base = re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0])[:25] or 'usuario'
    candidate, n = base, 1
    while User.objects.filter(username=candidate).exists():
        n += 1
        candidate = f'{base}{n}'
    return candidate


@ratelimit(key='ip', rate='20/m', method='POST', block=False)
@api_view(('POST',), auth='none')
def login(request):
    if getattr(request, 'limited', False):
        return error('Demasiados intentos. Espera un minuto.', 429)
    data = parse_body(request)
    identifier = (data.get('identifier') or '').strip()
    password = data.get('password') or ''
    if not identifier or not password:
        return error('Ingresa tu usuario o correo y tu contraseña.')

    # RF-06: tras varios intentos fallidos se exige CAPTCHA.
    if login_needs_captcha(identifier) and not check_captcha(data.get('captcha_key'), data.get('captcha_answer')):
        return error('Escribe el código de seguridad para continuar.', 400,
                     code='CAPTCHA_REQUIRED', captcha=new_captcha(request))

    user = authenticate(request, username=identifier, password=password)
    if user is None or not user.is_active:
        register_login_failure(identifier)
        extra = {'captcha': new_captcha(request), 'code': 'CAPTCHA_REQUIRED'} if login_needs_captcha(identifier) else {}
        return error('Usuario o contraseña incorrectos.', 401, **extra)
    clear_login_failures(identifier)
    log_action(request, user, 'login', f'Inicio de sesión de {user.username}')
    return ok(token=make_token(user), user=user_json(request, user))


@ratelimit(key='ip', rate='10/m', method='POST', block=False)
@api_view(('POST',), auth='none')
def register(request):
    if getattr(request, 'limited', False):
        return error('Demasiados intentos. Espera un minuto.', 429)
    data = parse_body(request)
    if not check_captcha(data.get('captcha_key'), data.get('captcha_answer')):
        return error('Código de seguridad incorrecto.', 422, code='CAPTCHA_REQUIRED',
                     captcha=new_captcha(request), errors={'captcha': 'Código de seguridad incorrecto.'})
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = data.get('role') or 'student'
    errors = {}

    try:
        validate_email(email)
        if User.objects.filter(email__iexact=email).exists():
            errors['email'] = 'Este email ya está registrado'
    except ValidationError:
        errors['email'] = 'Ingresa un correo válido'

    pw_error = check_password_rules(password)
    if pw_error:
        errors['password'] = pw_error
    if role not in ('student', 'teacher'):
        errors['role'] = 'Rol inválido'
    if str(data.get('accept_terms')).lower() not in ('true', '1', 'on'):
        errors['accept_terms'] = 'Debes aceptar los términos y condiciones para registrarte.'

    if role == 'teacher':
        full_name = (data.get('full_name') or '').strip()
        if not full_name:
            errors['full_name'] = 'El nombre completo es requerido para docentes'
        if not (data.get('specialty') or '').strip():
            errors['specialty'] = 'La especialidad es requerida'
        if not (data.get('experience_years') or '').strip():
            errors['experience_years'] = 'Los años de experiencia son requeridos'
    else:
        full_name = (data.get('full_name') or '').strip()
        if not full_name:
            errors['full_name'] = 'El nombre completo es requerido para estudiantes'
        if not (data.get('university') or '').strip():
            errors['university'] = 'La universidad/institución es requerida'
        if not (data.get('career') or '').strip():
            errors['career'] = 'La carrera es requerida'

    if errors:
        return error(next(iter(errors.values())), 422, errors=errors, captcha=new_captcha(request))

    user = User(username=_username_from_email(email), email=email, role=role, first_name=full_name)
    user.set_password(password)
    phone = (data.get('phone') or '').strip()
    user.phone = phone or None
    if role == 'teacher':
        user.teacher_full_name = full_name
        user.teacher_phone = phone or None
        user.teacher_email = email
        user.specialty = data.get('specialty', '').strip()
        user.experience_years = data.get('experience_years', '').strip()
        user.institution = (data.get('institution') or '').strip() or None
    else:
        user.full_name = full_name
        user.university = data.get('university', '').strip()
        user.career = data.get('career', '').strip()
        user.city = (data.get('city') or '').strip() or None
        user.semester = (data.get('semester') or '').strip() or None
        user.education_level = (data.get('education_level') or '').strip() or None
    user.save()
    log_action(request, user, 'register', f'Registro de {user.username} ({user.role})')

    if is_emi_student_email(user.email):
        Notification.objects.create(
            user=user, type='system', title='Descuento estudiante EMI',
            message=f'¡Bienvenido! Por ser estudiante de la EMI tienes {EMI_STUDENT_DISCOUNT_PERCENT:g}% '
                    'de descuento en tu primer curso. Se aplica automáticamente al pagar.',
        )

    email_sent = True
    try:
        send_verification_email(user, request)
    except Exception:
        logger.exception('Fallo el envío del correo de verificación para %s', user.email)
        email_sent = False

    return ok(token=make_token(user), user=user_json(request, user), email_sent=email_sent)


@api_view(('POST',), auth='none')
def password_reset(request):
    data = parse_body(request)
    if not check_captcha(data.get('captcha_key'), data.get('captcha_answer')):
        return error('Código de seguridad incorrecto.', 422, code='CAPTCHA_REQUIRED', captcha=new_captcha(request))
    email = (data.get('email') or '').strip()
    if not email:
        return error('Ingresa tu correo.', captcha=new_captcha(request))
    user = User.objects.filter(email__iexact=email).first()
    # Misma respuesta exista o no la cuenta, para no revelar qué correos están registrados.
    if user:
        try:
            send_password_reset_email(user, request, generate_reset_link(user, request))
        except Exception:
            logger.exception('Fallo el envío del correo de recuperación')
            return error('No pudimos enviar el correo. Intenta nuevamente.', 500)
    return ok(message='Si el correo existe, te enviamos un enlace de recuperación.')


@api_view(('GET', 'POST', 'PATCH'), name='me')
def me(request):
    user = request.user
    if request.method in ('POST', 'PATCH'):
        data = parse_body(request)
        text_fields = [
            'first_name', 'last_name', 'phone', 'bio', 'city', 'university', 'career',
            'semester', 'education_level', 'interests', 'specialty', 'institution',
            'experience_years', 'teacher_bio', 'linkedin', 'website',
        ]
        for field in text_fields:
            if field in data:
                setattr(user, field, (data.get(field) or '').strip() or None)
        if 'name' in data and data['name'].strip():
            name = data['name'].strip()
            if user.role == 'teacher':
                user.teacher_full_name = name
            else:
                user.full_name = name
            user.first_name = name
        if 'email' in data and data['email'].strip().lower() != user.email:
            new_email = data['email'].strip().lower()
            try:
                validate_email(new_email)
            except ValidationError:
                return error('Correo inválido')
            if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
                return error('Este email ya está registrado')
            user.email = new_email
        if request.FILES.get('profile_picture'):
            problem = validate_upload(request.FILES['profile_picture'], 'image')
            if problem:
                return error(problem)
            user.profile_picture = request.FILES['profile_picture']
        user.save()
    unread = Notification.objects.filter(user=user, is_read=False).count()
    return ok(user=user_json(request, user), unread_notifications=unread)


@api_view(('POST',))
def change_password(request):
    data = parse_body(request)
    user = request.user
    if not user.check_password(data.get('old_password') or ''):
        return error('La contraseña actual es incorrecta.')
    new_password = data.get('new_password') or ''
    if new_password != data.get('confirm_password', new_password):
        return error('Las contraseñas no coinciden.')
    pw_error = check_password_rules(new_password)
    if pw_error:
        return error(pw_error)
    user.set_password(new_password)
    user.save()
    log_action(request, user, 'password_change', 'Cambio de contraseña')
    # Cambiar la contraseña invalida el token anterior; devolvemos uno nuevo.
    return ok(token=make_token(user), message='Contraseña cambiada correctamente.')


@api_view(('POST',), name='resend_verification')
def resend_verification(request):
    if request.user.email_verified:
        return ok(message='Tu correo ya estaba verificado.')
    try:
        send_verification_email(request.user, request)
    except Exception:
        return error('No pudimos enviar el correo. Intenta nuevamente.', 500)
    return ok(message='Te enviamos un nuevo correo de verificación.')


@api_view(('POST',), name='logout')
def logout(request):
    log_action(request, request.user, 'logout', f'Cierre de sesión de {request.user.username}')
    return ok()


@api_view(('GET',), auth='none')
def captcha(request):
    """RF-06: entrega un CAPTCHA (imagen + clave) para registro, recuperación y login."""
    return ok(captcha=new_captcha(request))


@api_view(('GET',), name='me')
def verification_status(request):
    """La app consulta esto mientras espera que el usuario confirme su correo."""
    return ok(email_verified=request.user.email_verified)
