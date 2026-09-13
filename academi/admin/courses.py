from django.contrib import admin

from ..models import Category, Course, Module, Lesson, Enrollment, LessonProgress, Favorite, Review


# ============================================
# ADMIN - CATEGORÍAS
# ============================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')


# ============================================
# ADMIN - CURSOS
# ============================================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'level', 'price', 'status', 'is_featured', 'created_at')
    list_filter = ('status', 'level', 'is_free', 'is_featured', 'category')
    search_fields = ('title', 'description', 'teacher__username', 'teacher__email')
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'approved_at')
    raw_id_fields = ('teacher', 'approved_by')

    fieldsets = (
        ('Información básica', {
            'fields': ('title', 'description', 'category', 'teacher')
        }),
        ('Nivel y precio', {
            'fields': ('level', 'price', 'is_free')
        }),
        ('Estado', {
            'fields': ('status', 'is_featured', 'published_at', 'approved_at', 'approved_by', 'rejection_reason')
        }),
        ('Multimedia', {
            'fields': ('image', 'video_promo')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ============================================
# ADMIN - MÓDULOS
# ============================================
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')
    ordering = ('course', 'order')


# ============================================
# ADMIN - LECCIONES
# ============================================
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'lesson_type', 'is_free', 'is_published', 'order')
    list_filter = ('lesson_type', 'is_free', 'is_published', 'module__course')
    search_fields = ('title', 'description', 'content')
    ordering = ('module', 'order')
    readonly_fields = ('created_at', 'updated_at')


# ============================================
# ADMIN - INSCRIPCIONES
# ============================================
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'progress_percentage', 'enrollment_date')
    list_filter = ('status', 'payment_status', 'course')
    search_fields = ('student__username', 'student__email', 'course__title')
    readonly_fields = ('enrollment_date', 'completed_date', 'last_accessed')


# ============================================
# ADMIN - PROGRESO DE LECCIONES
# ============================================
@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'completed', 'completed_at')
    list_filter = ('completed',)


# ============================================
# ADMIN - FAVORITOS
# ============================================
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'created_at')
    search_fields = ('student__username', 'course__title')


# ============================================
# ADMIN - RESEÑAS
# ============================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'is_reported', 'created_at')
    list_filter = ('rating', 'is_reported')
    search_fields = ('student__username', 'course__title', 'comment')
