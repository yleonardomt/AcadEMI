from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Category, Course, Module, Lesson, Enrollment, 
    LessonProgress, Favorite, Notification, Comment, 
    Question, Answer, Review, Report, Evaluation,
    QuestionEvaluation, QuestionOption, EvaluationResult,
    UserAnswer, EvaluationIncident, Cart, CartItem,
    Coupon, Payment, PaymentItem, Certificate,
    SystemReport, ActivityLog, SystemSetting,
    ChatSession, ChatMessage, ChatIntent, ChatKnowledgeBase,
    ChatFeedback, ChatAnalytics, LessonResource
)

# ============================================
# ADMIN - USUARIOS
# ============================================
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'email_verified', 'date_joined')
    list_filter = ('role', 'is_active', 'email_verified', 'is_staff')
    search_fields = ('username', 'email', 'full_name', 'teacher_full_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('role', 'phone', 'bio', 'profile_picture', 
                      'full_name', 'birth_date', 'city', 'education_level',
                      'university', 'career', 'semester', 'interests',
                      'teacher_full_name', 'teacher_phone', 'teacher_email',
                      'specialty', 'experience_years', 'teaching_materials',
                      'teaching_level', 'institution', 'teacher_bio',
                      'linkedin', 'website', 'email_verified', 'verification_token',
                      'reset_password_token', 'reset_password_expires', 'last_login_ip')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {
            'fields': ('role', 'phone', 'full_name')
        }),
    )

admin.site.register(User, CustomUserAdmin)

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
# ADMIN - NOTIFICACIONES
# ============================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__username', 'title', 'message')

# ============================================
# ADMIN - RESEÑAS
# ============================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'is_reported', 'created_at')
    list_filter = ('rating', 'is_reported')
    search_fields = ('student__username', 'course__title', 'comment')

# ============================================
# ADMIN - PAGOS
# ============================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'final_amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('student__username', 'student__email', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')

# ============================================
# ADMIN - CERTIFICADOS
# ============================================
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_code', 'enrollment', 'issued_at', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('certificate_code', 'enrollment__student__username')

# ============================================
# ADMIN - CUPONES
# ============================================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'course', 'is_active', 'used_count', 'expires_at')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)

# ============================================
# ADMIN - CARRITO
# ============================================
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('student', 'created_at', 'updated_at')
    search_fields = ('student__username',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'course', 'added_at')
    search_fields = ('cart__student__username', 'course__title')

# ============================================
# ADMIN - EVALUACIONES
# ============================================
@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'evaluation_type', 'is_active', 'created_at')
    list_filter = ('evaluation_type', 'is_active')

@admin.register(QuestionEvaluation)
class QuestionEvaluationAdmin(admin.ModelAdmin):
    list_display = ('text', 'evaluation', 'question_type', 'points', 'order')
    list_filter = ('question_type',)

@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'evaluation', 'score', 'passed', 'completed_at')
    list_filter = ('passed',)

# ============================================
# ADMIN - CHATBOT
# ============================================
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'started_at', 'ended_at')
    list_filter = ('is_active',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'message', 'created_at')
    list_filter = ('sender',)

@admin.register(ChatIntent)
class ChatIntentAdmin(admin.ModelAdmin):
    list_display = ('name', 'intent_type', 'is_active')
    list_filter = ('intent_type', 'is_active')

@admin.register(ChatKnowledgeBase)
class ChatKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active')
    list_filter = ('category', 'is_active')

# ============================================
# ADMIN - REPORTES
# ============================================
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'report_type', 'status', 'created_at')
    list_filter = ('report_type', 'status')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'created_at')
    list_filter = ('action_type',)
    search_fields = ('user__username', 'description')

# ============================================
# ADMIN - SISTEMA
# ============================================
@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'setting_type')
    list_filter = ('setting_type',)
    search_fields = ('key', 'value', 'description')

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