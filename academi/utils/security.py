import base64
import hashlib
import hmac
import json

from django.conf import settings
from django.utils import timezone


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
        from ..models import EvaluationResult
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
        from ..models import EvaluationIncident
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
        from ..models import EvaluationIncident
        for incident in self.incidents:
            EvaluationIncident.objects.create(
                evaluation_result=evaluation_result,
                incident_type=incident['type'],
                description=incident['details']
            )
        return len(self.incidents)
