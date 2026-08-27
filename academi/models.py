from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal

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


# ============================================
# MÓDULO 3: GESTIÓN DE CURSOS (RF-15 al RF-24)
# ============================================

class Category(models.Model):  # RF-71
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"


class Course(models.Model):  # RF-15, RF-16, RF-17, RF-21
    LEVEL_CHOICES = (
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
        ('expert', 'Experto'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Borrador'),
        ('pending', 'Pendiente de aprobación'),  # RF-70
        ('published', 'Publicado'),
        ('rejected', 'Rechazado'),
        ('archived', 'Archivado'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='courses/', blank=True, null=True)
    video_promo = models.FileField(upload_to='courses/promo/', blank=True, null=True)  # RF-30
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_free = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)  # RF-21
    approved_at = models.DateTimeField(blank=True, null=True)  # RF-70
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_courses')
    rejection_reason = models.TextField(blank=True, null=True)  # RF-70
    
    def __str__(self):
        return self.title
    
    @property
    def total_modules(self):
        return self.modules.count()
    
    @property
    def total_lessons(self):
        return sum(module.lessons.count() for module in self.modules.all())
    
    @property
    def total_students(self):  # RF-22
        return self.enrollments.filter(status='enrolled').count()
    
    @property
    def total_duration(self):
        total = 0
        for module in self.modules.all():
            for lesson in module.lessons.all():
                total += lesson.duration_minutes or 0
        return total
    
    @property
    def average_rating(self):  # RF-24, RF-29, RF-40
        ratings = self.reviews.all()
        if ratings:
            return sum(r.rating for r in ratings) / len(ratings)
        return 0
    
    @property
    def total_reviews(self):
        return self.reviews.count()
    
    def get_price_display(self):
        if self.is_free:
            return "Gratis"
        return f"Bs. {self.price}"


class Module(models.Model):  # RF-18, RF-20
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):  # RF-18, RF-19, RF-20
    LESSON_TYPES = (
        ('video', 'Video'),
        ('document', 'Documento'),
        ('text', 'Texto'),
        ('quiz', 'Cuestionario'),
        ('assignment', 'Tarea'),
    )
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='video')
    video_url = models.URLField(blank=True, null=True)  # RF-33
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)  # RF-19
    document_file = models.FileField(upload_to='documents/', blank=True, null=True)  # RF-19
    order = models.IntegerField(default=0)  # RF-20
    is_free = models.BooleanField(default=False)  # RF-30
    is_published = models.BooleanField(default=False)
    duration_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"


class LessonResource(models.Model):  # RF-19
    RESOURCE_TYPES = (
        ('pdf', 'PDF'),
        ('doc', 'Documento'),
        ('ppt', 'Presentación'),
        ('xls', 'Excel'),
        ('zip', 'ZIP'),
        ('image', 'Imagen'),
        ('other', 'Otro'),
    )
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='resources/')
    file_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


# ============================================
# MÓDULO 2: PERFIL Y GESTIÓN DEL ESTUDIANTE (Continuación)
# ============================================

class Favorite(models.Model):  # RF-13, RF-31
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"


class Enrollment(models.Model):  # RF-09, RF-56, RF-63
    """Inscripción de un estudiante a un curso (compra única)"""
    
    STATUS_CHOICES = (
        ('pending', 'Pendiente de pago'),
        ('enrolled', 'Inscrito'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)  # RF-10, RF-34
    completed_date = models.DateTimeField(blank=True, null=True)
    last_accessed = models.DateTimeField(auto_now=True)  # RF-34
    
    # Datos de compra
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=(
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    ), default='pending')
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.get_status_display()}"
    
    def is_completed(self):
        return self.status == 'completed'
    
    def is_enrolled(self):
        return self.status in ['enrolled', 'in_progress']
    
    def complete_course(self):  # RF-64
        self.status = 'completed'
        self.progress_percentage = 100
        self.completed_date = timezone.now()
        self.save()


class LessonProgress(models.Model):  # RF-10, RF-34
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_accessed = models.DateTimeField(auto_now=True)
    time_spent = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['enrollment', 'lesson']
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.lesson.title}"


# ============================================
# MÓDULO 5: APRENDIZAJE Y PARTICIPACIÓN (RF-32 al RF-43)
# ============================================

class Comment(models.Model):  # RF-35, RF-36, RF-42
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    is_edited = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)  # RF-42
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"


class Question(models.Model):  # RF-37, RF-38, RF-39, RF-42
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    content = models.TextField()
    is_answered = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)  # RF-42
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    content = models.TextField(blank=True, null=True)  # <--- AGREGAR null=True
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.teacher.username} - {self.question.content[:30]}"


class Review(models.Model):  # RF-24, RF-29, RF-40, RF-41, RF-42
    RATING_CHOICES = (
        (1, '1 - Muy malo'),
        (2, '2 - Malo'),
        (3, '3 - Regular'),
        (4, '4 - Bueno'),
        (5, '5 - Excelente'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)  # RF-42
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.rating}"


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
# MÓDULO 6: EVALUACIONES (RF-44 al RF-53)
# ============================================

class Evaluation(models.Model):  # RF-44, RF-46
    EVALUATION_TYPES = (
        ('quiz', 'Cuestionario'),
        ('exam', 'Examen'),
        ('assignment', 'Tarea'),
        ('practical', 'Práctico'),
    )
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='evaluations')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    evaluation_type = models.CharField(max_length=20, choices=EVALUATION_TYPES, default='quiz')
    time_limit_minutes = models.IntegerField(default=30)  # RF-46
    passing_score = models.IntegerField(default=70)  # RF-46
    max_attempts = models.IntegerField(default=1)  # RF-46
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class QuestionEvaluation(models.Model):  # RF-45
    QUESTION_TYPES = (
        ('multiple', 'Opción múltiple'),
        ('single', 'Opción única'),
        ('true_false', 'Verdadero/Falso'),
        ('open', 'Respuesta abierta'),
    )
    
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single')
    text = models.TextField()
    points = models.IntegerField(default=1)  # RF-46
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.evaluation.title} - {self.text[:50]}"


class QuestionOption(models.Model):  # RF-45
    question = models.ForeignKey(QuestionEvaluation, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.text


class EvaluationResult(models.Model):  # RF-50, RF-51, RF-52
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='evaluation_results')
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)  # RF-47
    completed_at = models.DateTimeField(blank=True, null=True)
    time_spent = models.IntegerField(default=0)  # RF-48
    attempt_number = models.IntegerField(default=1)
    ip_address = models.GenericIPAddressField(blank=True, null=True)  # RF-53
    user_agent = models.TextField(blank=True, null=True)  # RF-53
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.evaluation.title}"


class UserAnswer(models.Model):  # RF-49
    evaluation_result = models.ForeignKey(EvaluationResult, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(QuestionEvaluation, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, blank=True, null=True)
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_obtained = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.evaluation_result} - {self.question.text[:30]}"


class EvaluationIncident(models.Model):  # RF-53
    INCIDENT_TYPES = (
        ('copy_paste', 'Copiar y pegar'),
        ('tab_switch', 'Cambio de pestaña'),
        ('timeout', 'Tiempo agotado'),
        ('other', 'Otro'),
    )
    
    evaluation_result = models.ForeignKey(EvaluationResult, on_delete=models.CASCADE, related_name='incidents')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.evaluation_result} - {self.incident_type}"


# ============================================
# MÓDULO 7: CARRITO, COMPRAS, PAGOS Y CUPONES (RF-54 al RF-63)
# ============================================

class Cart(models.Model):  # RF-54, RF-55
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Carrito de {self.student.username}"
    
    @property
    def total(self):
        return sum(item.course.price for item in self.items.all())


class CartItem(models.Model):  # RF-54
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cart', 'course']
    
    def __str__(self):
        return f"{self.cart.student.username} - {self.course.title}"


class Coupon(models.Model):  # RF-59, RF-60, RF-73
    DISCOUNT_TYPES = (
        ('percentage', 'Porcentaje'),
        ('fixed', 'Monto fijo'),
    )
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='coupons')
    max_uses = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_coupons')
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.expires_at < timezone.now():
            return False
        return True
    
    def apply_discount(self, amount):
        if self.discount_type == 'percentage':
            return amount * (1 - self.discount_value / 100)
        return max(0, amount - self.discount_value)


class Payment(models.Model):  # RF-56, RF-57, RF-58, RF-61, RF-62
    PAYMENT_STATUS = (
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
        ('cancelled', 'Cancelado'),
    )
    
    PAYMENT_METHODS = (
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Transferencia bancaria'),
        ('pago_efectivo', 'Pago Efectivo'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')  # RF-59
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='stripe')  # RF-57
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')  # RF-61
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    receipt_url = models.URLField(blank=True, null=True)  # RF-62
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.username} - Bs.{self.final_amount} - {self.status}"
    
    def confirm_payment(self):  # RF-58, RF-63
        self.status = 'completed'
        self.confirmed_at = timezone.now()
        self.save()
        
        # Crear inscripciones para los cursos
        for item in self.cart_items.all():
            enrollment = Enrollment.objects.create(
                student=self.student,
                course=item.course,
                status='enrolled',
                payment_amount=item.price,
                payment_status='paid',
                payment_method=self.payment_method,
                transaction_id=self.transaction_id,
                payment_date=self.confirmed_at
            )
            # Crear notificación
            Notification.objects.create(
                user=self.student,
                type='purchase',
                title=f'¡Curso adquirido!',
                message=f'Has comprado el curso "{item.course.title}" exitosamente.',
                link=f'/course/{item.course.id}/'
            )


class PaymentItem(models.Model):  # RF-56
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='cart_items')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.payment.student.username} - {self.course.title}"


# ============================================
# MÓDULO 8: CERTIFICADOS (RF-64 al RF-67)
# ============================================

class Certificate(models.Model):  # RF-64, RF-65, RF-66, RF-67
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_code = models.CharField(max_length=50, unique=True)  # RF-67
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='certificates/', blank=True, null=True)  # RF-65
    is_verified = models.BooleanField(default=False)
    verification_count = models.IntegerField(default=0)  # RF-67
    last_verified_at = models.DateTimeField(blank=True, null=True)  # RF-67
    
    def __str__(self):
        return f"Certificado - {self.enrollment.student.username} - {self.enrollment.course.title}"
    
    def generate_code(self):  # RF-67
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        self.certificate_code = code
        return code
    
    def verify(self):  # RF-67
        self.is_verified = True
        self.verification_count += 1
        self.last_verified_at = timezone.now()
        self.save()
        return True


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


# ============================================
# MÓDULO 10: ASISTENTE VIRTUAL - CHATBOT (RF-77 al RF-82)
# ============================================

class ChatSession(models.Model):  # RF-77
    """Sesión de chat del usuario con el asistente virtual"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Chat de {self.user.username} - {self.started_at}"
    
    def end_session(self):
        self.is_active = False
        self.ended_at = timezone.now()
        self.save()


class ChatMessage(models.Model):  # RF-78, RF-79, RF-80, RF-81, RF-82
    """Mensaje intercambiado en el chat"""
    
    SENDER_TYPES = (
        ('user', 'Usuario'),
        ('bot', 'Asistente Virtual'),
    )
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_TYPES)
    message = models.TextField()
    response_time = models.FloatField(blank=True, null=True)  # Tiempo de respuesta en segundos
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_sender_display()} - {self.message[:50]}"


class ChatIntent(models.Model):  # RF-78
    """Intenciones reconocidas por el chatbot"""
    
    INTENT_TYPES = (
        ('greeting', 'Saludo'),
        ('course', 'Información de cursos'),
        ('purchase', 'Información de compras'),
        ('academic', 'Información académica'),
        ('help', 'Ayuda de plataforma'),
        ('other', 'Otro'),
    )
    
    name = models.CharField(max_length=50, unique=True)
    intent_type = models.CharField(max_length=20, choices=INTENT_TYPES)
    keywords = models.TextField(help_text="Palabras clave separadas por comas")
    response_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class ChatKnowledgeBase(models.Model):  # RF-82
    """Base de conocimiento del chatbot"""
    
    CATEGORIES = (
        ('general', 'General'),
        ('courses', 'Cursos'),
        ('payments', 'Pagos'),
        ('academic', 'Académico'),
        ('support', 'Soporte'),
        ('technical', 'Técnico'),
    )
    
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORIES, default='general')
    keywords = models.TextField(help_text="Palabras clave separadas por comas")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kb_entries')
    
    def __str__(self):
        return f"{self.category} - {self.question[:50]}"


class ChatFeedback(models.Model):  # RF-82
    """Feedback del usuario sobre las respuestas del chatbot"""
    
    RATING_CHOICES = (
        (1, 'Muy mala'),
        (2, 'Mala'),
        (3, 'Regular'),
        (4, 'Buena'),
        (5, 'Excelente'),
    )
    
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.rating} - {self.message.message[:30]}"


class ChatAnalytics(models.Model):  # RF-79, RF-80, RF-81
    """Analíticas del chatbot"""
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='analytics')
    total_messages = models.IntegerField(default=0)
    user_messages = models.IntegerField(default=0)
    bot_messages = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analytics - {self.session.user.username} - {self.created_at}"