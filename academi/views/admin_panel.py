from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q, Count, Sum
from django.utils import timezone

from ..models import Course, Category, Report, Coupon, Payment, Certificate, Notification
from ..utils.coupons import save_coupon as save_coupon_record
from ..utils.demo_sales import visible_sales

User = get_user_model()


# ============================================
# ADMIN - LISTA DE PAGOS
# ============================================
@login_required
def admin_payments_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    payments = Payment.objects.all().order_by('-created_at')
    total_revenue = visible_sales(payments.filter(status='completed')).aggregate(total=Sum('final_amount'))['total'] or 0
    return render(request, 'academi/admin/admin_pagos.html', {
        'payments': payments,
        'total_revenue': total_revenue,
    })


# ============================================
# MÓDULO 9: ADMINISTRACIÓN
# ============================================
@login_required
def admin_courses_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    courses = Course.objects.all().select_related('teacher', 'category').order_by('-created_at')
    return render(request, 'academi/admin/admin_cursos.html', {'courses': courses})


@login_required
@require_POST
def admin_course_moderate(request, course_id, action):
    """RF70: aprobar, rechazar o retirar un curso del catálogo."""
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    course = get_object_or_404(Course, id=course_id)

    allowed_states = {'approve': ('pending',), 'reject': ('pending',), 'retire': ('published',)}
    if action not in allowed_states or course.status not in allowed_states[action]:
        messages.error(request, 'La acción no corresponde al estado actual del curso.')
        return redirect('admin_courses')
    if action == 'approve' and course.total_lessons == 0:
        messages.error(request, 'El curso necesita al menos una lección para ser aprobado.')
        return redirect('admin_courses')

    if action == 'approve':
        course.status = 'published'
        course.approved_at = timezone.now()
        course.approved_by = request.user
        course.published_at = course.published_at or timezone.now()
        course.rejection_reason = ''
        course.save()
        messages.success(request, f'Curso "{course.title}" aprobado y publicado.')
    elif action == 'reject':
        reason = request.POST.get('reason', '')
        course.status = 'rejected'
        course.rejection_reason = reason
        course.save()
        messages.success(request, f'Curso "{course.title}" rechazado.')
    elif action == 'retire':
        course.status = 'archived'
        course.save()
        messages.success(request, f'Curso "{course.title}" retirado del catálogo.')
    Notification.objects.create(
        user=course.teacher, type='course', title='Revisión de tu curso',
        message=f'El curso "{course.title}" ahora está {course.get_status_display().lower()}.'
    )

    return redirect('admin_courses')


@login_required
def admin_categories_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            if Category.objects.filter(name__iexact=name).exists():
                messages.error(request, 'Ya existe una categoría con ese nombre.')
            else:
                Category.objects.create(name=name, description=description)
                messages.success(request, f'Categoría "{name}" creada correctamente.')
                return redirect('admin_categories')
        else:
            messages.error(request, 'El nombre de la categoría es obligatorio.')

    categories = Category.objects.all().annotate(course_count=Count('courses')).order_by('name')
    return render(request, 'academi/admin/admin_categorias.html', {'categories': categories})


@login_required
def admin_category_edit(request, category_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            if Category.objects.filter(name__iexact=name).exclude(pk=category.pk).exists():
                messages.error(request, 'Ya existe una categoría con ese nombre.')
            else:
                category.name = name
                category.description = description
                category.save()
                messages.success(request, 'Categoría actualizada correctamente.')
        else:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
    return redirect('admin_categories')


@login_required
@require_POST
def admin_category_delete(request, category_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    category = get_object_or_404(Category, id=category_id)
    if category.courses.exists():
        messages.error(request, 'No se puede eliminar: hay cursos asociados a esta categoría.')
    else:
        category.delete()
        messages.success(request, 'Categoría eliminada correctamente.')
    return redirect('admin_categories')


@login_required
def admin_reports_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    reports = Report.objects.all().select_related('reporter', 'resolved_by').order_by('-created_at')
    return render(request, 'academi/admin/admin_reportes.html', {
        'reports': reports,
        'pending_count': reports.filter(status='pending').count(),
    })


@login_required
@require_POST
def admin_report_resolve(request, report_id, action):
    """RF43, RF72: revisar y gestionar contenido reportado."""
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    report = get_object_or_404(Report, id=report_id)

    if action in ('resolve', 'dismiss'):
        report.status = 'resolved' if action == 'resolve' else 'dismissed'
        report.resolved_at = timezone.now()
        report.resolved_by = request.user
        report.save()
        messages.success(request, 'Reporte actualizado correctamente.')
    else:
        messages.error(request, 'Acción no válida.')

    return redirect('admin_reports')


@login_required
def admin_coupons_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    if request.method == 'POST':
        coupon, problem = save_coupon_record(request.user, request.POST)
        if not problem:
            messages.success(request, f'Cupón "{coupon.code}" creado correctamente.')
            return redirect('admin_coupons')
        messages.error(request, problem)

    coupons = Coupon.objects.all().select_related('course', 'created_by').order_by('-created_at')
    return render(request, 'academi/admin/admin_cupones.html', {'coupons': coupons})


@login_required
def admin_coupon_edit(request, coupon_id):
    """RF-73: modificar un cupón existente."""
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        saved, problem = save_coupon_record(request.user, request.POST, coupon)
        messages.error(request, problem) if problem else messages.success(request, f'Cupón {saved.code} actualizado.')

    return redirect('admin_coupons')


@login_required
@require_POST
def admin_coupon_toggle(request, coupon_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()
    estado = 'activado' if coupon.is_active else 'desactivado'
    messages.success(request, f'Cupón {coupon.code} {estado}.')
    return redirect('admin_coupons')


@login_required
def admin_certificates_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    certificates = Certificate.objects.all().select_related('enrollment__student', 'enrollment__course').order_by('-issued_at')
    return render(request, 'academi/admin/admin_certificados.html', {'certificates': certificates})


@login_required
@require_POST
def admin_certificate_toggle(request, certificate_id):
    """Revoca o reactiva un certificado (p. ej. si se emitió por error o hubo fraude)."""
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    certificate = get_object_or_404(Certificate, id=certificate_id)
    if certificate.is_revoked:
        certificate.reactivate()
        messages.success(request, f'Certificado {certificate.certificate_code} reactivado.')
    else:
        certificate.revoke()
        messages.success(request, f'Certificado {certificate.certificate_code} revocado.')
    return redirect('admin_certificates')


@login_required
def admin_reports_generate_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    context = {}
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')

        # El rango de fechas se aplica a los 3 tipos de reporte (antes
        # solo filtraba las ventas; usuarios y cursos ignoraban el
        # rango elegido aunque el formulario lo pedía).
        users = User.objects.all()
        courses = Course.objects.all()
        payments = visible_sales(Payment.objects.filter(status='completed', amount__gt=0))
        if date_from:
            users = users.filter(created_at__date__gte=date_from)
            courses = courses.filter(created_at__date__gte=date_from)
            payments = payments.filter(created_at__date__gte=date_from)
        if date_to:
            users = users.filter(created_at__date__lte=date_to)
            courses = courses.filter(created_at__date__lte=date_to)
            payments = payments.filter(created_at__date__lte=date_to)

        context['generated'] = True
        context['report_type'] = report_type
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['total_users'] = users.count()
        context['total_courses'] = courses.count()
        context['total_sales'] = payments.count()
        context['total_revenue'] = payments.aggregate(total=Sum('final_amount'))['total'] or 0

    return render(request, 'academi/admin/admin_generar_reportes.html', context)


# ============================================
# ADMIN - CRUD USUARIOS
# ============================================
@login_required
def admin_users_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard')

    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query)
        ).order_by('-date_joined')
    else:
        users = User.objects.all().order_by('-date_joined')

    context = {
        'users': users,
        'query': query,
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role='student').count(),
        'total_teachers': User.objects.filter(role='teacher').count(),
        'total_admins': User.objects.filter(role='admin').count(),
        'total_active': User.objects.filter(is_active=True).count(),
        'total_inactive': User.objects.filter(is_active=False).count(),
    }
    return render(request, 'academi/users/admin_usuarios.html', context)


@login_required
def admin_user_create(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password') or ''
        role = request.POST.get('role', 'student')
        first_name = request.POST.get('first_name', '')
        phone = request.POST.get('phone', '')

        if not username or role not in ('student', 'teacher', 'admin'):
            messages.error(request, 'Nombre de usuario o rol inválido.')
            return render(request, 'academi/users/admin_crear_usuario.html')
        try:
            validate_email(email)
            validate_password(password)
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
            return render(request, 'academi/users/admin_crear_usuario.html')

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'academi/users/admin_crear_usuario.html')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'El email ya está registrado.')
            return render(request, 'academi/users/admin_crear_usuario.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            role=role,
            phone=phone,
            is_active=True,
            email_verified=True,
        )
        messages.success(request, f'Usuario {username} creado correctamente.')
        return redirect('admin_users')

    return render(request, 'academi/users/admin_crear_usuario.html')


@login_required
def admin_user_edit(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        role = request.POST.get('role', '')
        active = request.POST.get('is_active') == 'on'
        if not username or role not in ('student', 'teacher', 'admin'):
            messages.error(request, 'Nombre de usuario o rol inválido.')
            return redirect('admin_users')
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Correo electrónico inválido.')
            return redirect('admin_users')
        if User.objects.filter(username__iexact=username).exclude(pk=user.pk).exists() or User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            messages.error(request, 'El usuario o correo ya está registrado.')
            return redirect('admin_users')
        if user == request.user and (role != 'admin' or not active):
            messages.error(request, 'No puedes quitarte el rol de administrador ni desactivar tu cuenta.')
            return redirect('admin_users')
        user.username = username
        user.email = email
        user.role = role
        user.first_name = request.POST.get('first_name', '')
        user.phone = request.POST.get('phone', '')
        user.is_active = active
        user.save()
        messages.success(request, f'Usuario {user.username} actualizado correctamente.')
        return redirect('admin_users')

    return render(request, 'academi/users/admin_editar_usuario.html', {'edit_user': user})


@login_required
@require_POST
def admin_user_delete(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('admin_users')

    if user.courses_taught.exists() or user.enrollments.exists() or user.payments.exists() or user.created_coupons.exists():
        messages.error(request, 'Este usuario tiene cursos, inscripciones, pagos o cupones. Desactiva la cuenta para conservar los datos.')
        return redirect('admin_users')

    username = user.username
    user.delete()
    messages.success(request, f'Usuario {username} eliminado correctamente.')
    return redirect('admin_users')


@login_required
@require_POST
def admin_user_toggle_active(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
        return redirect('admin_users')

    user.is_active = not user.is_active
    user.save()

    estado = 'activado' if user.is_active else 'desactivado'
    messages.success(request, f'Usuario {user.username} {estado} correctamente.')
    return redirect('admin_users')


@login_required
def admin_user_reset_password(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        new_password = request.POST.get('new_password') or ''
        try:
            validate_password(new_password, user)
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
            return render(request, 'academi/users/admin_reset_password.html', {'reset_user': user})

        user.set_password(new_password)
        user.save()
        messages.success(request, f'Contraseña de {user.username} restablecida correctamente.')
        return redirect('admin_users')

    return render(request, 'academi/users/admin_reset_password.html', {'reset_user': user})
