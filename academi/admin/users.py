from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from ..models import User


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
