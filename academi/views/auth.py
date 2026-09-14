import logging

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg, Count, Q
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from ..forms import (
    RegisterForm, LoginForm, UserProfileForm,
    PasswordResetRequestForm, PasswordResetConfirmForm,
    CustomPasswordChangeForm,
)
from ..models import (
    Course, Category, Enrollment, Review, Notification,
    is_emi_student_email, EMI_STUDENT_DISCOUNT_PERCENT,
)
from ..utils import send_verification_email, send_password_reset_email, generate_reset_link

User = get_user_model()
logger = logging.getLogger(__name__)

# Las categorías son datos libres (el admin las crea desde el panel),
# así que no tienen un campo de ícono en el modelo. Buscamos por
# coincidencia parcial de palabras clave para la portada y usamos un
# ícono genérico si ninguna palabra clave coincide con el nombre.
CATEGORY_ICONS = (
    ('dato', 'fa-chart-pie'), ('data', 'fa-chart-pie'),
    ('ia', 'fa-robot'), ('inteligencia artificial', 'fa-robot'),
    ('program', 'fa-code'), ('desarroll', 'fa-code'), ('web', 'fa-globe'),
    ('diseñ', 'fa-palette'), ('diseno', 'fa-palette'), ('creativ', 'fa-palette'),
    ('marketing', 'fa-bullhorn'), ('negocio', 'fa-briefcase'), ('finanza', 'fa-chart-line'),
    ('matemátic', 'fa-calculator'), ('matematic', 'fa-calculator'), ('ciencia', 'fa-flask'),
    ('idioma', 'fa-language'), ('música', 'fa-music'), ('musica', 'fa-music'),
    ('foto', 'fa-camera'), ('salud', 'fa-heart-pulse'),
    ('red', 'fa-network-wired'), ('hardware', 'fa-microchip'),
    ('seguridad', 'fa-shield-halved'), ('móvil', 'fa-mobile-screen'), ('movil', 'fa-mobile-screen'),
)


def _category_icon(name):
    lowered = (name or '').strip().lower()
    for keyword, icon in CATEGORY_ICONS:
        if keyword in lowered:
            return icon
    return 'fa-layer-group'


# ============================================
# HOME
# ============================================
def home_view(request):
    published = Course.objects.filter(status='published')

    featured_courses = published.annotate(
        student_count=Count('enrollments', distinct=True)
    ).select_related('category', 'teacher').order_by('-is_featured', '-student_count')[:6]

    avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg']

    # RF-29: testimonios reales (reseñas de estudiantes), no textos
    # inventados. Solo reseñas con comentario y buena calificación.
    testimonials = Review.objects.filter(
        rating__gte=4, comment__isnull=False
    ).exclude(comment='').select_related('student', 'course').order_by('-rating', '-created_at')[:3]

    categories = Category.objects.annotate(
        course_count=Count('courses', filter=Q(courses__status='published'), distinct=True)
    ).filter(course_count__gt=0).order_by('-course_count')[:6]
    for cat in categories:
        cat.icon = _category_icon(cat.name)

    newest_courses = published.select_related('category').order_by('-published_at', '-created_at')[:4]

    context = {
        'featured_courses': featured_courses,
        'categories': categories,
        'newest_courses': newest_courses,
        'total_courses': published.count(),
        'total_students': User.objects.filter(role='student').count(),
        'total_teachers': User.objects.filter(role='teacher').count(),
        'total_enrollments': Enrollment.objects.count(),
        'avg_rating': round(avg_rating, 1) if avg_rating else None,
        'testimonials': testimonials,
    }
    return render(request, 'academi/index.html', context)


# ============================================
# RF-01: REGISTRARSE
# ============================================
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            if is_emi_student_email(user.email):
                Notification.objects.create(
                    user=user,
                    type='system',
                    title='Descuento estudiante EMI',
                    message=f'¡Bienvenido! Por ser estudiante de la EMI tienes {EMI_STUDENT_DISCOUNT_PERCENT:g}% de descuento en tu primer curso. Se aplica automáticamente al pagar.',
                    link=reverse('catalog'),
                )

            try:
                send_verification_email(user, request)
                messages.success(request, 'Registro exitoso. Te hemos enviado un correo de verificación.')
            except Exception:
                logger.exception('Fallo el envío del correo de verificación para %s', user.email)
                messages.warning(request, 'Registro exitoso, pero no pudimos enviar el correo de verificación. Puedes reenviarlo desde esta página.')

            # No lo mandamos al dashboard todavía: el middleware de
            # verificación lo rebotaría igual hasta que confirme el correo.
            return redirect('verify_pending')
    else:
        form = RegisterForm()

    return render(request, 'academi/auth/register.html', {'form': form})


# ============================================
# RF-07: ESPERAR VERIFICACIÓN DE CORREO
# ============================================
@login_required
def verify_pending_view(request):
    if request.user.email_verified:
        return redirect('dashboard')
    return render(request, 'academi/auth/verificacion_pendiente.html')


@login_required
def resend_verification_email_view(request):
    if request.user.email_verified:
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            send_verification_email(request.user, request)
            messages.success(request, 'Te reenviamos el correo de verificación. Revisa tu bandeja de entrada (y spam).')
        except Exception:
            logger.exception('Fallo el reenvío del correo de verificación para %s', request.user.email)
            messages.error(request, 'No pudimos reenviar el correo. Intenta de nuevo en unos minutos.')

    return redirect('verify_pending')


# ============================================
# TÉRMINOS Y CONDICIONES
# ============================================
def terms_view(request):
    return render(request, 'academi/pages/terminos.html')


# ============================================
# RF-02: INICIAR SESIÓN
# ============================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Bienvenido de vuelta, {user.username}.')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
    else:
        form = LoginForm()

    return render(request, 'academi/auth/login.html', {'form': form})


# ============================================
# RF-04: CERRAR SESIÓN
# ============================================
def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


# ============================================
# RF-05: CAMBIAR CONTRASEÑA
# ============================================
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña cambiada correctamente.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Error al cambiar la contraseña. Revisa los campos.')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'academi/auth/cambiar_contraseña.html', {'form': form})


# ============================================
# RF-03: RECUPERAR CONTRASEÑA - SOLICITAR
# ============================================
def password_reset_request_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'No existe un usuario con este email.')
                return render(request, 'academi/auth/password_reset_request.html', {'form': form})

            reset_link = generate_reset_link(user, request)

            try:
                send_password_reset_email(user, request, reset_link)
                messages.success(request, 'Se ha enviado un enlace de recuperación a tu email.')
                return render(request, 'academi/auth/password_reset_done.html')
            except:
                messages.error(request, 'Error al enviar el email. Intenta nuevamente.')

    else:
        form = PasswordResetRequestForm()

    return render(request, 'academi/auth/password_reset_request.html', {'form': form})


# ============================================
# RF-03: RECUPERAR CONTRASEÑA - CONFIRMAR
# ============================================
def password_reset_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                new_password = form.cleaned_data['new_password']
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
                return redirect('login')
        else:
            form = PasswordResetConfirmForm()

        return render(request, 'academi/auth/password_reset_confirm.html', {'form': form, 'valid': True})
    else:
        messages.error(request, 'El enlace de recuperación es inválido o ha expirado.')
        return redirect('password_reset_request')


# ============================================
# RF-07: CONFIRMAR CORREO ELECTRÓNICO
# ============================================
def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if not user.email_verified:
            user.verify_email()
            messages.success(request, 'Tu correo ha sido verificado correctamente.')
        else:
            messages.info(request, 'Tu correo ya estaba verificado.')
        return redirect('dashboard')
    else:
        messages.error(request, 'El enlace de verificación es inválido o ha expirado.')
        return redirect('login')


# ============================================
# RF-08: PERFIL
# ============================================
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('profile')
        else:
            messages.error(request, 'Error al actualizar el perfil. Revisa los campos.')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'academi/users/perfil.html', {'form': form})
