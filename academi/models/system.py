from django.db import models

from .users import User

# ============================================
# MÓDULO 5 (continuación): MODERACIÓN DE CONTENIDO (RF-42, RF-43, RF-72)
# ============================================

class Report(models.Model):  # RF-42, RF-43, RF-72
    REPORT_TYPES = (
        ('comment', 'Comentario'),
        ('question', 'Pregunta'),
        ('review', 'Reseña'),
        ('course', 'Curso'),
        ('user', 'Usuario'),
    )

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    content_id = models.IntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=(
        ('pending', 'Pendiente'),
        ('reviewed', 'Revisado'),
        ('resolved', 'Resuelto'),
        ('dismissed', 'Descartado'),
    ), default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')

    def __str__(self):
        return f"{self.reporter.username} - {self.report_type} - {self.status}"


# ============================================
# MÓDULO 9: ADMINISTRACIÓN (RF-68 al RF-76)
# ============================================

class SystemReport(models.Model):  # RF-76
    REPORT_TYPES = (
        ('users', 'Usuarios'),
        ('courses', 'Cursos'),
        ('payments', 'Pagos'),
        ('enrollments', 'Inscripciones'),
        ('revenue', 'Ingresos'),
        ('students', 'Estudiantes'),
        ('teachers', 'Docentes'),
        ('certificates', 'Certificados'),
        ('evaluations', 'Evaluaciones'),
    )

    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    title = models.CharField(max_length=200, blank=True, null=True)
    data = models.JSONField(default=dict)
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporte {self.get_report_type_display()} - {self.created_at}"


class ActivityLog(models.Model):  # RF-68, RF-69
    ACTION_TYPES = (
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('register', 'Registro'),
        ('course_create', 'Creación de curso'),
        ('course_edit', 'Edición de curso'),
        ('course_delete', 'Eliminación de curso'),
        ('course_approve', 'Aprobación de curso'),
        ('course_reject', 'Rechazo de curso'),
        ('enrollment', 'Inscripción'),
        ('payment', 'Pago'),
        ('certificate', 'Certificado'),
        ('profile_update', 'Actualización de perfil'),
        ('password_change', 'Cambio de contraseña'),
        ('user_block', 'Bloqueo de usuario'),
        ('user_unblock', 'Desbloqueo de usuario'),
        ('user_delete', 'Eliminación de usuario'),
        ('other', 'Otro'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.created_at}"


class SystemSetting(models.Model):  # RF-68, RF-73
    SETTING_TYPES = (
        ('general', 'General'),
        ('email', 'Email'),
        ('payment', 'Pagos'),
        ('security', 'Seguridad'),
        ('appearance', 'Apariencia'),
    )

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='general')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} = {self.value[:50]}"
