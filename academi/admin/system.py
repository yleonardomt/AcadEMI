from django.contrib import admin

from ..models import Notification, Report, ActivityLog, SystemSetting


# ============================================
# ADMIN - NOTIFICACIONES
# ============================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__username', 'title', 'message')


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
# ADMIN - CONFIGURACIÓN DEL SISTEMA
# ============================================
@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'setting_type')
    list_filter = ('setting_type',)
    search_fields = ('key', 'value', 'description')
