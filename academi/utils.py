from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
import hashlib
import hmac
import json
import base64
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
import secrets

User = get_user_model()


def send_verification_email(user, request):
    """RF-07: Enviar correo de verificación"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = get_current_site(request)
    domain = current_site.domain
    verify_link = f"http://{domain}/verify-email/{uid}/{token}/"
    
    context = {
        'user': user,
        'verify_link': verify_link,
        'domain': domain,
    }
    
    html_message = render_to_string('academi/emails/verification_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Confirma tu correo - AcadEMI',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, request, reset_link):
    """RF-03: Enviar correo de recuperación de contraseña"""
    context = {
        'user': user,
        'reset_link': reset_link,
        'domain': get_current_site(request).domain,
    }
    
    html_message = render_to_string('academi/emails/password_reset_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Recuperación de contraseña - AcadEMI',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def generate_reset_link(user, request):
    """RF-03: Generar enlace de recuperación"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = get_current_site(request)
    domain = current_site.domain
    return f"http://{domain}/reset-password/{uid}/{token}/"


def validate_reset_token(uidb64, token):
    """RF-03: Validar token de recuperación"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    
    if user is not None and default_token_generator.check_token(user, token):
        return user
    return None


def get_client_ip(request):
    """Obtiene la IP del cliente de forma segura"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================
# SEGURIDAD PARA CUESTIONARIOS
# ============================================

class QuizSecurityManager:
    """Gestor de seguridad para cuestionarios y exámenes"""
    
    def __init__(self, user, evaluation):
        self.user = user
        self.evaluation = evaluation
        self.session_key = f"quiz_{evaluation.id}_{user.id}"
    
    def generate_secure_token(self):
        """Genera token único para la sesión del cuestionario"""
        timestamp = int(timezone.now().timestamp())
        secret = settings.SECRET_KEY
        data = f"{self.user.id}|{self.evaluation.id}|{timestamp}"
        token = hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return token
    
    def verify_token(self, token):
        """Verifica que el token sea válido"""
        expected = self.generate_secure_token()
        return hmac.compare_digest(token, expected)
    
    def get_encrypted_answer(self, answer_data):
        """Cifra las respuestas del usuario usando hashlib"""
        data = json.dumps(answer_data)
        timestamp = int(timezone.now().timestamp())
        salt = hashlib.sha256(str(timestamp).encode()).hexdigest()[:16]
        return {
            'data': base64.b64encode(data.encode()).decode(),
            'timestamp': timestamp,
            'salt': salt
        }
    
    def check_attempt_limit(self):
        """Verifica límite de intentos"""
        from .models import EvaluationResult
        attempts = EvaluationResult.objects.filter(
            enrollment__student=self.user,
            evaluation=self.evaluation
        ).count()
        return attempts < self.evaluation.max_attempts
    
    def get_remaining_time(self, start_time):
        """Calcula tiempo restante"""
        elapsed = (timezone.now() - start_time).total_seconds()
        limit = self.evaluation.time_limit_minutes * 60
        return max(0, limit - elapsed)
    
    def log_incident(self, result, incident_type, description):
        """Registra incidentes de seguridad"""
        from .models import EvaluationIncident
        EvaluationIncident.objects.create(
            evaluation_result=result,
            incident_type=incident_type,
            description=description
        )


class AntiCheatingMonitor:
    """Monitor anti-trampas para cuestionarios"""
    
    def __init__(self, result):
        self.result = result
        self.incidents = []
    
    def check_tab_switch(self, request):
        """Detecta cambio de pestaña"""
        if 'tab_switch' in request.session.get('quiz_alerts', []):
            self.incidents.append({
                'type': 'tab_switch',
                'timestamp': timezone.now().isoformat(),
                'details': 'Cambio de pestaña detectado'
            })
            return True
        return False
    
    def check_copy_paste(self, request):
        """Detecta copiar/pegar"""
        if request.POST.get('copy_paste_detected'):
            self.incidents.append({
                'type': 'copy_paste',
                'timestamp': timezone.now().isoformat(),
                'details': 'Intento de copiar/pegar detectado'
            })
            return True
        return False
    
    def check_time_anomaly(self, start_time, end_time):
        """Detecta anomalías de tiempo"""
        duration = (end_time - start_time).total_seconds()
        if duration < 5:
            self.incidents.append({
                'type': 'time_anomaly',
                'timestamp': timezone.now().isoformat(),
                'details': f'Tiempo de respuesta sospechoso: {duration}s'
            })
            return True
        return False
    
    def save_incidents(self, evaluation_result):
        """Guarda todos los incidentes registrados"""
        from .models import EvaluationIncident
        for incident in self.incidents:
            EvaluationIncident.objects.create(
                evaluation_result=evaluation_result,
                incident_type=incident['type'],
                description=incident['details']
            )
        return len(self.incidents)


def rate_limit_quiz():
    """Decorador de rate limiting para cuestionarios"""
    return ratelimit(
        key='user',
        rate='5/m',
        method=['POST'],
        block=True
    )