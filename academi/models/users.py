from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# ============================================
# MÓDULO 1: AUTENTICACIÓN Y REGISTRO (RF-01 al RF-07)
# ============================================

class User(AbstractUser):
    ROLES = (
        ('student', 'Estudiante'),
        ('teacher', 'Docente'),
        ('admin', 'Administrador'),
    )

    role = models.CharField(max_length=20, choices=ROLES, default='student')
    email_verified = models.BooleanField(default=False)  # RF-07
    verification_token = models.CharField(max_length=255, blank=True, null=True)
    reset_password_token = models.CharField(max_length=255, blank=True, null=True)  # RF-03
    reset_password_expires = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    # Campos para estudiantes (RF-01)
    full_name = models.CharField(max_length=200, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    education_level = models.CharField(max_length=50, blank=True, null=True)
    university = models.CharField(max_length=200, blank=True, null=True)
    career = models.CharField(max_length=200, blank=True, null=True)
    semester = models.CharField(max_length=50, blank=True, null=True)
    interests = models.TextField(blank=True, null=True)

    # Campos para docentes (RF-01)
    teacher_full_name = models.CharField(max_length=200, blank=True, null=True)
    teacher_phone = models.CharField(max_length=20, blank=True, null=True)
    teacher_email = models.EmailField(blank=True, null=True)
    specialty = models.CharField(max_length=200, blank=True, null=True)
    experience_years = models.CharField(max_length=20, blank=True, null=True)
    teaching_materials = models.TextField(blank=True, null=True)
    teaching_level = models.TextField(blank=True, null=True)
    institution = models.CharField(max_length=200, blank=True, null=True)
    teacher_bio = models.TextField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

    def is_student(self):
        return self.role == 'student'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_admin_user(self):
        return self.role == 'admin'

    def verify_email(self):
        """RF-07: Confirmar correo electrónico"""
        self.email_verified = True
        self.verification_token = None
        self.save()

    def set_reset_token(self, token):
        """RF-03: Generar token para recuperar contraseña"""
        self.reset_password_token = token
        self.reset_password_expires = timezone.now() + timezone.timedelta(hours=24)
        self.save()

    def is_reset_token_valid(self, token):
        """RF-03: Validar token de recuperación"""
        if self.reset_password_token != token:
            return False
        if self.reset_password_expires < timezone.now():
            return False
        return True


# ============================================
# MÓDULO 2: PERFIL Y GESTIÓN DEL ESTUDIANTE (RF-08 al RF-14)
# ============================================

class Notification(models.Model):  # RF-14
    NOTIFICATION_TYPES = (
        ('course', 'Curso'),
        ('evaluation', 'Evaluación'),
        ('purchase', 'Compra'),
        ('certificate', 'Certificado'),
        ('comment', 'Comentario'),
        ('question', 'Pregunta'),
        ('answer', 'Respuesta'),
        ('system', 'Sistema'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"
