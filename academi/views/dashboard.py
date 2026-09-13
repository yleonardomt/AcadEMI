from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Sum, Avg
from django.utils import timezone

from ..models import (
    Notification, Enrollment, Certificate, Course, Review, Payment,
    Coupon, Report, EvaluationResult, Favorite,
)

User = get_user_model()


# ============================================
# DASHBOARD - VERSIÓN MEJORADA
# ============================================
@login_required
def dashboard_view(request):
    user = request.user
    now = timezone.now()
    today = now.date()

    # ============================================
    # NOTIFICACIONES
    # ============================================
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()

    # ============================================
    # MÉTRICAS DEL ESTUDIANTE (si es estudiante)
    # ============================================
    enrollments = Enrollment.objects.filter(student=user)
    total_enrollments = enrollments.count()
    completed_courses = enrollments.filter(status='completed').count()
    in_progress_courses = enrollments.filter(status='in_progress').count()
    pending_courses = enrollments.filter(status='pending').count()

    avg_progress = 0
    if total_enrollments > 0:
        avg_progress = sum(e.progress_percentage for e in enrollments) // total_enrollments

    completed_percentage = 0
    in_progress_percentage = 0
    pending_percentage = 100
    if total_enrollments > 0:
        completed_percentage = (completed_courses / total_enrollments) * 100
        in_progress_percentage = (in_progress_courses / total_enrollments) * 100
        pending_percentage = 100 - completed_percentage - in_progress_percentage

    total_certificates = Certificate.objects.filter(enrollment__student=user).count()
    enrollments_in_progress = enrollments.filter(status='in_progress').select_related('course')[:5]

    # Últimos cursos iniciados
    recent_enrollments = enrollments.order_by('-enrollment_date').select_related('course')[:5]

    # ============================================
    # MÉTRICAS DEL DOCENTE (si es docente)
    # ============================================
    teacher_courses = Course.objects.filter(teacher=user)
    teacher_courses_count = teacher_courses.count()
    teacher_published_courses = teacher_courses.filter(status='published').count()
    teacher_draft_courses = teacher_courses.filter(status='draft').count()
    teacher_pending_courses = teacher_courses.filter(status='pending').count()
    teacher_rejected_courses = teacher_courses.filter(status='rejected').count()

    # Estudiantes totales en cursos del docente
    teacher_students_total = Enrollment.objects.filter(
        course__in=teacher_courses,
        status__in=['enrolled', 'in_progress', 'completed']
    ).count()

    # Estudiantes activos (con progreso > 0)
    teacher_active_students = Enrollment.objects.filter(
        course__in=teacher_courses,
        progress_percentage__gt=0,
        status__in=['enrolled', 'in_progress']
    ).values('student').distinct().count()

    recent_courses = teacher_courses.order_by('-created_at').select_related('category')[:5]

    # Reseñas de cursos del docente
    teacher_reviews = Review.objects.filter(course__in=teacher_courses)
    teacher_total_reviews = teacher_reviews.count()
    teacher_avg_rating = teacher_reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    # ============================================
    # MÉTRICAS GLOBALES (para admin)
    # ============================================
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_admins = User.objects.filter(role='admin').count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()

    # Usuarios nuevos en los últimos 7 días
    week_ago = now - timezone.timedelta(days=7)
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()

    total_courses = Course.objects.count()
    published_courses = Course.objects.filter(status='published').count()
    draft_courses = Course.objects.filter(status='draft').count()
    pending_approval_courses = Course.objects.filter(status='pending').count()
    featured_courses = Course.objects.filter(is_featured=True).count()
    free_courses = Course.objects.filter(is_free=True).count()

    total_payments = Payment.objects.filter(status='completed').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(total=Sum('final_amount'))['total'] or 0

    # Ingresos del mes actual
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = Payment.objects.filter(
        status='completed',
        confirmed_at__gte=month_start
    ).aggregate(total=Sum('final_amount'))['total'] or 0

    # Ingresos del mes pasado
    last_month_start = (month_start - timezone.timedelta(days=1)).replace(day=1)
    last_month_revenue = Payment.objects.filter(
        status='completed',
        confirmed_at__gte=last_month_start,
        confirmed_at__lt=month_start
    ).aggregate(total=Sum('final_amount'))['total'] or 0

    # Porcentaje de crecimiento
    revenue_growth = 0
    if last_month_revenue > 0:
        revenue_growth = ((monthly_revenue - last_month_revenue) / last_month_revenue) * 100

    total_enrollments_global = Enrollment.objects.count()
    completed_enrollments = Enrollment.objects.filter(status='completed').count()
    in_progress_enrollments = Enrollment.objects.filter(status='in_progress').count()

    total_certificates_global = Certificate.objects.count()
    verified_certificates = Certificate.objects.filter(is_verified=True).count()

    pending_reports = Report.objects.filter(status='pending').count()
    total_reports = Report.objects.count()

    total_coupons = Coupon.objects.count()
    active_coupons = Coupon.objects.filter(is_active=True, expires_at__gte=now).count()

    # ============================================
    # ACTIVIDAD RECIENTE
    # ============================================
    recent_users = User.objects.all().order_by('-date_joined')[:10]

    # Últimos pagos
    recent_payments = Payment.objects.filter(status='completed').order_by('-confirmed_at').select_related('student')[:5]

    # Últimas inscripciones
    recent_enrollments_global = Enrollment.objects.order_by('-enrollment_date').select_related('student', 'course')[:5]

    # Últimos cursos creados
    recent_courses_global = Course.objects.order_by('-created_at').select_related('teacher', 'category')[:5]

    # Últimas reseñas
    recent_reviews = Review.objects.order_by('-created_at').select_related('student', 'course')[:5]

    # ============================================
    # CONTEXTO COMPLETO
    # ============================================
    context = {
        # Usuario y roles
        'user': user,
        'is_student': user.role == 'student',
        'is_teacher': user.role == 'teacher',
        'is_admin': user.role == 'admin',
        'now': now,
        'today': today,

        # ===== MÉTRICAS ESTUDIANTE =====
        'total_enrollments': total_enrollments,
        'completed_courses': completed_courses,
        'in_progress_courses': in_progress_courses,
        'pending_courses': pending_courses,
        'avg_progress': avg_progress,
        'completed_percentage': int(completed_percentage),
        'in_progress_percentage': int(in_progress_percentage),
        'pending_percentage': int(pending_percentage),
        'total_certificates': total_certificates,
        'enrollments_in_progress': enrollments_in_progress,
        'recent_enrollments': recent_enrollments,

        # ===== MÉTRICAS DOCENTE =====
        'teacher_courses_count': teacher_courses_count,
        'teacher_published_courses': teacher_published_courses,
        'teacher_draft_courses': teacher_draft_courses,
        'teacher_pending_courses': teacher_pending_courses,
        'teacher_rejected_courses': teacher_rejected_courses,
        'teacher_students_total': teacher_students_total,
        'teacher_active_students': teacher_active_students,
        'recent_courses': recent_courses,
        'teacher_total_reviews': teacher_total_reviews,
        'teacher_avg_rating': round(teacher_avg_rating, 1),

        # ===== MÉTRICAS GLOBALES =====
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_admins': total_admins,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'new_users_week': new_users_week,

        'total_courses': total_courses,
        'published_courses': published_courses,
        'draft_courses': draft_courses,
        'pending_approval_courses': pending_approval_courses,
        'featured_courses': featured_courses,
        'free_courses': free_courses,

        'total_payments': total_payments,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'last_month_revenue': last_month_revenue,
        'revenue_growth': round(revenue_growth, 1),

        'total_enrollments_global': total_enrollments_global,
        'completed_enrollments': completed_enrollments,
        'in_progress_enrollments': in_progress_enrollments,

        'total_certificates_global': total_certificates_global,
        'verified_certificates': verified_certificates,

        'pending_reports': pending_reports,
        'total_reports': total_reports,

        'total_coupons': total_coupons,
        'active_coupons': active_coupons,

        # ===== ACTIVIDAD RECIENTE =====
        'recent_users': recent_users,
        'recent_payments': recent_payments,
        'recent_enrollments_global': recent_enrollments_global,
        'recent_courses_global': recent_courses_global,
        'recent_reviews': recent_reviews,

        # ===== NOTIFICACIONES =====
        'notifications': notifications,
        'unread_notifications': unread_notifications,
    }

    return render(request, 'academi/dashboard/dashboard.html', context)


# ============================================
# MÓDULO 2: PERFIL Y GESTIÓN DEL ESTUDIANTE
# ============================================
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'academi/pages/notificaciones.html', {'notifications': notifications})


@login_required
def my_courses_view(request):
    if request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
        return render(request, 'academi/courses/mis_cursos.html', {'courses': courses})
    else:
        enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
        courses = [enrollment.course for enrollment in enrollments]
        return render(request, 'academi/courses/mis_cursos.html', {'courses': courses})


@login_required
def my_progress_view(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    return render(request, 'academi/dashboard/mi_progreso.html', {'enrollments': enrollments})


@login_required
def my_grades_view(request):
    results = EvaluationResult.objects.filter(enrollment__student=request.user).select_related('evaluation', 'enrollment__course')
    return render(request, 'academi/dashboard/mis_calificaciones.html', {'results': results})


@login_required
def my_certificates_view(request):
    certificates = Certificate.objects.filter(enrollment__student=request.user).select_related('enrollment__course')
    return render(request, 'academi/dashboard/mis_certificados.html', {'certificates': certificates})


@login_required
def certificate_detail_view(request, certificate_id):
    """RF-65: consultar y descargar (imprimir) un certificado."""
    certificate = get_object_or_404(
        Certificate, id=certificate_id, enrollment__student=request.user
    )
    return render(request, 'academi/dashboard/certificado_detalle.html', {'certificate': certificate})


@login_required
def certificate_send_email_view(request, certificate_id):
    """RF-66: enviar el certificado al correo registrado."""
    certificate = get_object_or_404(
        Certificate, id=certificate_id, enrollment__student=request.user
    )
    from ..utils import send_certificate_email
    try:
        send_certificate_email(certificate, request)
        messages.success(request, f'Certificado enviado a {request.user.email}.')
    except Exception:
        messages.error(request, 'No se pudo enviar el correo. Intenta más tarde.')
    return redirect('my_certificates')


def verify_certificate_view(request, code):
    """RF-67: verificar la autenticidad de un certificado por su código."""
    certificate = Certificate.objects.filter(certificate_code=code).select_related(
        'enrollment__student', 'enrollment__course'
    ).first()
    if certificate:
        certificate.verify()
    return render(request, 'academi/pages/verificar_certificado.html', {
        'certificate': certificate,
        'code': code,
    })


@login_required
def my_favorites_view(request):
    favorites = Favorite.objects.filter(student=request.user).select_related('course')
    return render(request, 'academi/dashboard/mis_favoritos.html', {'favorites': favorites})


@login_required
def mis_estudiantes_view(request):
    if request.user.role != 'teacher' and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    courses = Course.objects.filter(teacher=request.user)
    enrollments = Enrollment.objects.filter(
        course__in=courses,
        status__in=['enrolled', 'in_progress', 'completed']
    ).select_related('student', 'course')

    return render(request, 'academi/courses/mis_estudiantes.html', {
        'enrollments': enrollments,
        'total_students': enrollments.count(),
        'courses': courses,
    })


@login_required
def mis_resenas_view(request):
    if request.user.role != 'teacher' and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    courses = Course.objects.filter(teacher=request.user)
    reviews = Review.objects.filter(course__in=courses).select_related('student', 'course')

    return render(request, 'academi/courses/mis_resenas.html', {
        'reviews': reviews,
        'total_reviews': reviews.count(),
        'courses': courses,
    })
