from django.db import models
from django.utils import timezone

from .users import User
from .courses import Course, Lesson

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

class AssignmentSubmission(models.Model):
    """Entrega de una lección de tipo 'assignment' (tarea)."""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assignment_submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    file = models.FileField(upload_to='assignments/')
    comment = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.IntegerField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    graded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['lesson', 'student']

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"


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
    content = models.TextField(blank=True, null=True)
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
