import base64
import hashlib
import re
import secrets
import time
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST
from django_ratelimit.decorators import ratelimit

from ..forms_google import GoogleSignupForm
from ..models import GoogleIdentity, User, Notification, is_emi_student_email, EMI_STUDENT_DISCOUNT_PERCENT
from ..utils.email import send_verification_email
from ..utils.google_oauth import AUTHORIZATION_URL, FLOW_TTL, GoogleLoginError, available, callback_uri, exchange_code

BACKEND = 'academi.auth_backends.UsernameOrEmailBackend'
FLOW_KEY = 'google_oauth_flow'
SIGNUP_KEY = 'google_oauth_signup'


def _recent(data):
    return isinstance(data, dict) and 0 <= time.time() - data.get('issued', 0) < FLOW_TTL


def _finish(request, user, next_url=''):
    login(request, user, backend=BACKEND)
    return redirect(next_url or 'dashboard')


def _failure(request, text, destination='login'):
    messages.error(request, text)
    return redirect(destination)


@never_cache
@require_POST
@ratelimit(key='ip', rate='20/m', method='POST', block=False)
def google_start(request):
    intent = request.POST.get('intent', 'login')
    if intent not in ('login', 'register', 'link'):
        return _failure(request, 'La solicitud de acceso no es válida.')
    if getattr(request, 'limited', False):
        return _failure(request, 'Has realizado muchos intentos. Espera un minuto y vuelve a intentarlo.')
    if not available():
        return _failure(request, 'El acceso con Google todavía no está disponible. Puedes usar tu correo y contraseña.')
    if intent == 'link':
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.email_verified:
            return _failure(request, 'Confirma tu correo antes de vincular Google.', 'verify_pending')
        if not request.user.check_password(request.POST.get('password') or ''):
            return _failure(request, 'Confirma tu contraseña actual para vincular Google.', 'profile')
    elif request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = ''
    verifier = secrets.token_urlsafe(64)
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    flow = {'state': state, 'nonce': nonce, 'verifier': verifier, 'issued': time.time(),
            'intent': intent, 'next': next_url, 'role': 'teacher' if request.POST.get('role') == 'teacher' else 'student',
            'user_id': request.user.pk if intent == 'link' else None, 'redirect_uri': callback_uri(request)}
    request.session[FLOW_KEY] = flow
    request.session.pop(SIGNUP_KEY, None)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('ascii')).digest()).decode('ascii').rstrip('=')
    params = {'client_id': settings.GOOGLE_OAUTH_CLIENT_ID, 'redirect_uri': flow['redirect_uri'],
              'response_type': 'code', 'scope': 'openid email profile', 'state': state, 'nonce': nonce,
              'code_challenge': challenge, 'code_challenge_method': 'S256', 'prompt': 'select_account'}
    return redirect(AUTHORIZATION_URL + '?' + urlencode(params))


def _identity_user(identity):
    linked = GoogleIdentity.objects.select_related('user').filter(subject=identity['subject']).first()
    if linked:
        return linked.user
    matches = list(User.objects.filter(email__iexact=identity['email'])[:2])
    if not matches:
        return None
    if len(matches) != 1:
        raise GoogleLoginError('Hay más de una cuenta con ese correo. Ingresa con tu usuario y vincula Google desde Mi perfil.')
    user = matches[0]
    if not user.is_active:
        raise GoogleLoginError('Esta cuenta está desactivada. Contacta al administrador.')
    if (not user.email_verified or not identity['authoritative'] or user.is_staff or user.is_superuser or user.role == 'admin'):
        raise GoogleLoginError('Ya tienes una cuenta con ese correo. Ingresa con tu contraseña, verifica tu correo y vincula Google desde Mi perfil.')
    if GoogleIdentity.objects.filter(user=user).exists():
        raise GoogleLoginError('Tu cuenta ya está vinculada a otra cuenta de Google. Ingresa con tu contraseña.')
    GoogleIdentity.objects.create(user=user, subject=identity['subject'], google_email=identity['email'])
    return user


@never_cache
@require_http_methods(['GET'])
def google_callback(request):
    flow = request.session.get(FLOW_KEY)
    if not _recent(flow) or not secrets.compare_digest(str(request.GET.get('state', '')), str(flow.get('state', ''))):
        return _failure(request, 'El enlace de acceso venció o no corresponde a esta sesión. Vuelve a pulsar Continuar con Google.')
    request.session.pop(FLOW_KEY, None)
    destination = 'profile' if flow['intent'] == 'link' else ('register' if flow['intent'] == 'register' else 'login')
    if request.GET.get('error') or not request.GET.get('code'):
        return _failure(request, 'No se completó el acceso con Google. Puedes volver a intentarlo.', destination)
    if not available():
        return _failure(request, 'El acceso con Google no está disponible en este momento.', destination)
    try:
        identity = exchange_code(request.GET['code'], flow['nonce'], flow['verifier'], flow['redirect_uri'])
        with transaction.atomic():
            if flow['intent'] == 'link':
                if not request.user.is_authenticated or request.user.pk != flow['user_id']:
                    raise GoogleLoginError('Tu sesión cambió. Ingresa de nuevo antes de vincular Google.')
                if not request.user.is_active:
                    raise GoogleLoginError('Esta cuenta está desactivada.')
                if GoogleIdentity.objects.filter(subject=identity['subject']).exclude(user=request.user).exists():
                    raise GoogleLoginError('Esa cuenta de Google ya está vinculada a otro usuario de AcadEMI.')
                linked, _ = GoogleIdentity.objects.get_or_create(user=request.user,
                    defaults={'subject': identity['subject'], 'google_email': identity['email']})
                if linked.subject != identity['subject']:
                    raise GoogleLoginError('Tu cuenta ya tiene otra cuenta de Google vinculada.')
                messages.success(request, 'Cuenta de Google vinculada. Ya puedes usarla para iniciar sesión.')
                return redirect('profile')
            if request.user.is_authenticated:
                raise GoogleLoginError('Tu sesión cambió. Cierra sesión antes de acceder con otra cuenta.')
            user = _identity_user(identity)
            if user:
                if not user.is_active:
                    raise GoogleLoginError('Esta cuenta está desactivada. Contacta al administrador.')
                return _finish(request, user, flow['next'])
        request.session[SIGNUP_KEY] = {**identity, 'issued': time.time(), 'role': flow['role'], 'next': flow['next']}
        return redirect('google_complete')
    except GoogleLoginError as exc:
        return _failure(request, str(exc), destination)
    except IntegrityError:
        return _failure(request, 'Esta cuenta ya fue vinculada o registrada. Vuelve a iniciar sesión con Google.', destination)


@never_cache
@require_http_methods(['GET', 'POST'])
def google_complete(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    identity = request.session.get(SIGNUP_KEY)
    if not _recent(identity):
        request.session.pop(SIGNUP_KEY, None)
        return _failure(request, 'El registro con Google venció. Vuelve a iniciarlo.', 'register')
    initial = {'role': identity['role'], 'full_name': identity['name'], 'teacher_full_name': identity['name']}
    form = GoogleSignupForm(request.POST if request.method == 'POST' else None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                if User.objects.filter(email__iexact=identity['email']).exists():
                    raise GoogleLoginError('Ya existe una cuenta con ese correo.')
                role = form.cleaned_data['role']
                name = form.cleaned_data['teacher_full_name' if role == 'teacher' else 'full_name']
                base = re.sub(r'[^a-zA-Z0-9_]', '', identity['email'].split('@')[0])[:25] or 'usuario'
                username = base
                while User.objects.filter(username=username).exists():
                    username = f'{base}_{secrets.token_hex(4)}'
                user = User.objects.create_user(username=username, email=identity['email'], password=None,
                    role=role, first_name=name, email_verified=identity['authoritative'],
                    full_name=name if role == 'student' else '', teacher_full_name=name if role == 'teacher' else '',
                    specialty=form.cleaned_data.get('specialty', '') if role == 'teacher' else '')
                GoogleIdentity.objects.create(user=user, subject=identity['subject'], google_email=identity['email'],
                                              terms_accepted_at=timezone.now())
                if role == 'student' and is_emi_student_email(user.email):
                    Notification.objects.create(user=user, type='system', title='Descuento estudiante EMI',
                        message=f'Tienes {EMI_STUDENT_DISCOUNT_PERCENT:g}% de descuento en tu primera compra paga.', link='/catalog/')
            request.session.pop(SIGNUP_KEY, None)
            login(request, user, backend=BACKEND)
            if not user.email_verified:
                try:
                    send_verification_email(user, request)
                    request.session['verification_email_sent'] = True
                except Exception:
                    request.session['verification_email_sent'] = False
                    messages.warning(request, 'Cuenta creada. Reenvía el correo de verificación desde esta página.')
                return redirect('verify_pending')
            messages.success(request, 'Tu cuenta está lista. Bienvenido a AcadEMI.')
            return redirect(identity['next'] or 'dashboard')
        except (GoogleLoginError, IntegrityError):
            request.session.pop(SIGNUP_KEY, None)
            return _failure(request, 'Esta cuenta ya fue registrada. Inicia sesión para continuar.')
    return render(request, 'academi/auth/google_complete.html', {'form': form, 'google_email': identity['email']})
