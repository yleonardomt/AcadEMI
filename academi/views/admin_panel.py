from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Sum
from django.utils import timezone

from ..models import Course, Category, Report, Coupon, Payment, Certificate

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
    total_revenue = payments.filter(status='completed').aggregate(total=Sum('final_amount'))['total'] or 0
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
def admin_course_moderate(request, course_id, action):
    """RF70: aprobar, rechazar o retirar un curso del catálogo."""
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    course = get_object_or_404(Course, id=course_id)

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
    else:
        messages.error(request, 'Acción no válida.')

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
            Category.objects.create(name=name, description=description)
            messages.success(request, f'Categoría "{name}" creada correctamente.')
        else:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
        return redirect('admin_categories')

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
            category.name = name
            category.description = description
            category.save()
            messages.success(request, 'Categoría actualizada correctamente.')
        else:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
    return redirect('admin_categories')


@login_required
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
        code = request.POST.get('code', '').strip().upper()
        discount_type = request.POST.get('discount_type', 'percentage')
        discount_value = request.POST.get('discount_value') or 0
        max_uses = request.POST.get('max_uses') or 1
        expires_at = request.POST.get('expires_at')
        if code and expires_at:
            expires_at_dt = timezone.datetime.fromisoformat(expires_at)
            if timezone.is_naive(expires_at_dt):
                expires_at_dt = timezone.make_aware(expires_at_dt)
            Coupon.objects.create(
                code=code,
                discount_type=discount_type,
                discount_value=discount_value,
                max_uses=max_uses,
                expires_at=expires_at_dt,
                created_by=request.user,
            )
            messages.success(request, f'Cupón "{code}" creado correctamente.')
        else:
            messages.error(request, 'Código y fecha de expiración son obligatorios.')
        return redirect('admin_coupons')

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
        coupon.discount_type = request.POST.get('discount_type', coupon.discount_type)
        coupon.discount_value = request.POST.get('discount_value') or coupon.discount_value
        coupon.max_uses = request.POST.get('max_uses') or coupon.max_uses
        expires_at = request.POST.get('expires_at')
        if expires_at:
            expires_at_dt = timezone.datetime.fromisoformat(expires_at)
            if timezone.is_naive(expires_at_dt):
                expires_at_dt = timezone.make_aware(expires_at_dt)
            coupon.expires_at = expires_at_dt
        coupon.save()
        messages.success(request, f'Cupón {coupon.code} actualizado.')

    return redirect('admin_coupons')


@login_required
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
def admin_reports_generate_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    context = {}
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')

        payments = Payment.objects.filter(status='completed')
        if date_from:
            payments = payments.filter(created_at__date__gte=date_from)
        if date_to:
            payments = payments.filter(created_at__date__lte=date_to)

        context['generated'] = True
        context['report_type'] = report_type
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['total_users'] = User.objects.count()
        context['total_courses'] = Course.objects.count()
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
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        first_name = request.POST.get('first_name', '')
        phone = request.POST.get('phone', '')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return redirect('admin_users')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado.')
            return redirect('admin_users')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            role=role,
            phone=phone,
            is_active=True
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
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.first_name = request.POST.get('first_name', '')
        user.phone = request.POST.get('phone', '')
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        messages.success(request, f'Usuario {user.username} actualizado correctamente.')
        return redirect('admin_users')

    return render(request, 'academi/users/admin_editar_usuario.html', {'edit_user': user})


@login_required
def admin_user_delete(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('admin_users')

    username = user.username
    user.delete()
    messages.success(request, f'Usuario {username} eliminado correctamente.')
    return redirect('admin_users')


@login_required
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
        new_password = request.POST.get('new_password')
        if len(new_password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return redirect('admin_users')

        user.set_password(new_password)
        user.save()
        messages.success(request, f'Contraseña de {user.username} restablecida correctamente.')
        return redirect('admin_users')

    return render(request, 'academi/users/admin_reset_password.html', {'reset_user': user})
