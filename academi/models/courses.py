from django.db import models

from .users import User

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
    is_reported = models.BooleanField(default=False)  # RF-42: un estudiante puede reportar el curso completo

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
        return self.enrollments.filter(status__in=['enrolled', 'in_progress', 'completed']).count()

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


class Lesson(models.Model):
    LESSON_TYPES = (
        ('video', 'Video'),
        ('document', 'Documento'),
        ('text', 'Texto'),
        ('quiz', 'Cuestionario'),
        ('exam', 'Examen'),
        ('assignment', 'Tarea'),
    )

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='video')
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    document_file = models.FileField(upload_to='documents/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_free = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    duration_minutes = models.IntegerField(default=0)

    # ===== PARA TAREAS =====
    assignment_deadline_days = models.IntegerField(default=7, null=True, blank=True)
    assignment_deadline_hours = models.IntegerField(default=0, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class LessonResource(models.Model):
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
