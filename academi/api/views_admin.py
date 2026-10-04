"""Módulo de administración para la app móvil (RF-43 a RF-49)."""
from datetime import datetime

from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import (
    User, Course, Category, Report, Coupon, Payment, Certificate, Comment, Question, Review,
    Notification,
)
from .auth import api_view, error, ok, parse_body
from .serializers import display_name, media_url, money
from .support import log_action

ADMIN = ('admin',)


def _dt(value):
    """Acepta 'YYYY-MM-DD' o ISO completo y devuelve un datetime con zona horaria."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


# ============================================
# USUARIOS (RF-43)
# ============================================
def _user_row(request, u):
    return {
        'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role,
        'role_label': u.get_role_display(), 'name': display_name(u), 'first_name': u.first_name,
        'phone': u.phone or '', 'is_active': u.is_active, 'email_verified': u.email_verified,
        'picture': media_url(request, u.profile_picture),
        'joined': u.date_joined.isoformat(),
    }


@api_view(('GET',), roles=ADMIN)
def users(request):
    q = (request.GET.get('q') or '').strip()
    role = request.GET.get('role')
    qs = User.objects.all().order_by('-date_joined')
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q)
                       | Q(full_name__icontains=q) | Q(teacher_full_name__icontains=q))
    if role in ('student', 'teacher', 'admin'):
        qs = qs.filter(role=role)
    return ok(
        users=[_user_row(request, u) for u in qs[:150]],
        totals={'all': User.objects.count(), 'students': User.objects.filter(role='student').count(),
                'teachers': User.objects.filter(role='teacher').count(),
                'admins': User.objects.filter(role='admin').count(),
                'active': User.objects.filter(is_active=True).count(),
                'inactive': User.objects.filter(is_active=False).count()},
    )


@api_view(('POST',), roles=ADMIN)
def user_create(request):
    data = parse_body(request)
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = data.get('role') or 'student'
    if not username or not email:
        return error('Usuario y correo son obligatorios.')
    if role not in ('student', 'teacher', 'admin'):
        return error('Rol inválido.')
    if len(password) < 8:
        return error('La contraseña debe tener al menos 8 caracteres.')
    if User.objects.filter(username=username).exists():
        return error('El nombre de usuario ya existe.')
    if User.objects.filter(email__iexact=email).exists():
        return error('El email ya está registrado.')
    user = User.objects.create_user(
        username=username, email=email, password=password, role=role,
        first_name=(data.get('first_name') or '').strip(), phone=(data.get('phone') or '').strip(),
        is_active=True, email_verified=True)
    log_action(request, request.user, 'other', f'Admin creó al usuario {user.username} ({role})')
    return ok(message=f'Usuario {username} creado correctamente.', user=_user_row(request, user))


@api_view(('POST',), roles=ADMIN)
def user_update(request, user_id):
    user = get_object_or_404(User, id=user_id)
    data = parse_body(request)
    username = (data.get('username') or user.username).strip()
    email = (data.get('email') or user.email).strip().lower()
    role = data.get('role') or user.role
    if role not in ('student', 'teacher', 'admin'):
        return error('Rol inválido.')
    if User.objects.filter(username=username).exclude(pk=user.pk).exists():
        return error('El nombre de usuario ya existe.')
    if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
        return error('El email ya está registrado.')
    if user == request.user and role != 'admin':
        return error('No puedes quitarte tu propio rol de administrador.')
    user.username, user.email, user.role = username, email, role
    user.first_name = (data.get('first_name') or '').strip()
    user.phone = (data.get('phone') or '').strip() or None
    user.save()
    log_action(request, request.user, 'other', f'Admin editó al usuario {user.username}')
    return ok(message=f'Usuario {user.username} actualizado correctamente.', user=_user_row(request, user))


@api_view(('POST',), roles=ADMIN)
def user_toggle(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        return error('No puedes desactivar tu propia cuenta.')
    user.is_active = not user.is_active
    user.save()
    log_action(request, request.user, 'user_block' if not user.is_active else 'user_unblock',
               f'Admin {"desactivó" if not user.is_active else "activó"} a {user.username}')
    return ok(message=f'Usuario {user.username} {"activado" if user.is_active else "desactivado"}.',
              user=_user_row(request, user))


@api_view(('POST',), roles=ADMIN)
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        return error('No puedes eliminar tu propia cuenta.')
    name = user.username
    user.delete()
    log_action(request, request.user, 'user_delete', f'Admin eliminó al usuario {name}')
    return ok(message=f'Usuario {name} eliminado correctamente.')


@api_view(('POST',), roles=ADMIN)
def user_reset_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    password = parse_body(request).get('new_password') or ''
    if len(password) < 8:
        return error('La contraseña debe tener al menos 8 caracteres.')
    user.set_password(password)
    user.save()
    log_action(request, request.user, 'password_change', f'Admin restableció la contraseña de {user.username}')
    return ok(message=f'Contraseña de {user.username} restablecida correctamente.')


# ============================================
# CURSOS Y CATEGORÍAS (RF-44)
# ============================================
@api_view(('GET',), roles=ADMIN)
def courses(request):
    status = request.GET.get('status')
    qs = Course.objects.all().select_related('teacher', 'category').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    counts = {row['status']: row['n'] for row in Course.objects.values('status').annotate(n=Count('id'))}
    return ok(counts=counts, courses=[{
        'id': c.id, 'title': c.title, 'image': media_url(request, c.image),
        'teacher': display_name(c.teacher), 'category': c.category.name if c.category_id else None,
        'status': c.status, 'status_label': c.get_status_display(), 'price': money(c.price),
        'is_free': c.is_free, 'students': c.total_students, 'lessons': c.total_lessons,
        'rejection_reason': c.rejection_reason or '', 'is_reported': c.is_reported,
        'created_at': c.created_at.isoformat(),
    } for c in qs[:150]])


@api_view(('POST',), roles=ADMIN)
def course_moderate(request, course_id, action):
    course = get_object_or_404(Course, id=course_id)
    if action == 'approve':
        course.status = 'published'
        course.approved_at = timezone.now()
        course.approved_by = request.user
        course.published_at = course.published_at or timezone.now()
        course.rejection_reason = ''
        message = f'Curso "{course.title}" aprobado y publicado.'
        kind, notice = 'course_approve', 'Tu curso fue aprobado'
    elif action == 'reject':
        course.status = 'rejected'
        course.rejection_reason = (parse_body(request).get('reason') or '').strip()
        message = f'Curso "{course.title}" rechazado.'
        kind, notice = 'course_reject', 'Tu curso fue rechazado'
    elif action == 'retire':
        course.status = 'archived'
        message = f'Curso "{course.title}" retirado del catálogo.'
        kind, notice = 'other', 'Tu curso fue retirado del catálogo'
    else:
        return error('Acción no válida.')
    course.save()
    log_action(request, request.user, kind, f'{message}')
    Notification.objects.create(user=course.teacher, type='course', title=notice,
                                message=f'{message} {course.rejection_reason if action == "reject" else ""}'.strip())
    return ok(message=message, status=course.status)


def _category_row(c):
    return {'id': c.id, 'name': c.name, 'description': c.description or '', 'courses_count': c.course_count}


@api_view(('GET',), roles=ADMIN)
def categories(request):
    rows = Category.objects.annotate(course_count=Count('courses')).order_by('name')
    return ok(categories=[_category_row(c) for c in rows])


@api_view(('POST',), roles=ADMIN)
def category_save(request, category_id=None):
    data = parse_body(request)
    name = (data.get('name') or '').strip()
    if not name:
        return error('El nombre de la categoría es obligatorio.')
    description = (data.get('description') or '').strip()
    if category_id:
        cat = get_object_or_404(Category, id=category_id)
        cat.name, cat.description = name, description
        cat.save()
        message = 'Categoría actualizada correctamente.'
    else:
        Category.objects.create(name=name, description=description)
        message = f'Categoría "{name}" creada correctamente.'
    return ok(message=message)


@api_view(('POST',), roles=ADMIN)
def category_delete(request, category_id):
    cat = get_object_or_404(Category, id=category_id)
    if cat.courses.exists():
        return error('No se puede eliminar: hay cursos asociados a esta categoría.')
    cat.delete()
    return ok(message='Categoría eliminada correctamente.')


# ============================================
# CONTENIDO REPORTADO (RF-45)
# ============================================
def _reported_content(report):
    model = {'comment': Comment, 'question': Question, 'review': Review, 'course': Course}.get(report.report_type)
    obj = model.objects.filter(id=report.content_id).first() if model else None
    if obj is None:
        return None
    if report.report_type == 'course':
        return obj.title
    return getattr(obj, 'content', None) or getattr(obj, 'comment', '') or ''


@api_view(('GET',), roles=ADMIN)
def reports(request):
    status = request.GET.get('status')
    qs = Report.objects.select_related('reporter', 'resolved_by').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    return ok(
        pending=Report.objects.filter(status='pending').count(),
        reports=[{
            'id': r.id, 'type': r.report_type, 'type_label': r.get_report_type_display(),
            'reason': r.reason, 'status': r.status, 'status_label': r.get_status_display(),
            'reporter': display_name(r.reporter), 'content_id': r.content_id,
            'content': _reported_content(r), 'created_at': r.created_at.isoformat(),
            'resolved_by': display_name(r.resolved_by) if r.resolved_by_id else None,
        } for r in qs[:150]],
    )


@api_view(('POST',), roles=ADMIN)
def report_resolve(request, report_id, action):
    report = get_object_or_404(Report, id=report_id)
    if action not in ('resolve', 'dismiss', 'remove'):
        return error('Acción no válida.')
    if action == 'remove':
        # Acción sobre el contenido: eliminar el comentario/pregunta/reseña reportada.
        model = {'comment': Comment, 'question': Question, 'review': Review}.get(report.report_type)
        if model:
            model.objects.filter(id=report.content_id).delete()
        action = 'resolve'
    report.status = 'resolved' if action == 'resolve' else 'dismissed'
    report.resolved_at = timezone.now()
    report.resolved_by = request.user
    report.save()
    log_action(request, request.user, 'other', f'Admin {report.status} el reporte #{report.id}')
    return ok(message='Reporte actualizado correctamente.')


# ============================================
# CUPONES Y PROMOCIONES (RF-46)
# ============================================
def coupon_row(c):
    return {
        'id': c.id, 'code': c.code, 'type': c.discount_type, 'value': money(c.discount_value),
        'course_id': c.course_id, 'course': c.course.title if c.course_id else None,
        'max_uses': c.max_uses, 'used_count': c.used_count, 'is_active': c.is_active,
        'is_valid': c.is_valid(), 'expires_at': c.expires_at.isoformat(),
        'created_by': display_name(c.created_by),
    }


def save_coupon(request, coupon=None, course=None):
    """Crea o modifica un cupón. Lo comparten administrador y docente."""
    data = parse_body(request)
    discount_type = data.get('discount_type') or (coupon.discount_type if coupon else 'percentage')
    if discount_type not in ('percentage', 'fixed'):
        return None, error('Tipo de descuento inválido.')
    try:
        value = float(data.get('discount_value')) if data.get('discount_value') not in (None, '') \
            else (float(coupon.discount_value) if coupon else 0)
        max_uses = int(data.get('max_uses')) if data.get('max_uses') not in (None, '') \
            else (coupon.max_uses if coupon else 1)
    except (TypeError, ValueError):
        return None, error('Valor o usos máximos inválidos.')
    if value <= 0 or (discount_type == 'percentage' and value > 100):
        return None, error('El descuento debe ser mayor a 0 (y hasta 100% si es porcentaje).')
    if max_uses < 1:
        return None, error('Los usos máximos deben ser al menos 1.')
    expires = _dt(data.get('expires_at'))
    if coupon is None:
        code = (data.get('code') or '').strip().upper()
        if not code or not expires:
            return None, error('Código y fecha de expiración son obligatorios.')
        if Coupon.objects.filter(code=code).exists():
            return None, error('Ya existe un cupón con ese código.')
        coupon = Coupon(code=code, created_by=request.user, course=course)
    coupon.discount_type, coupon.discount_value, coupon.max_uses = discount_type, value, max_uses
    if expires:
        coupon.expires_at = expires
    coupon.save()
    return coupon, None


@api_view(('GET',), roles=ADMIN)
def coupons(request):
    rows = Coupon.objects.select_related('course', 'created_by').order_by('-created_at')
    return ok(coupons=[coupon_row(c) for c in rows[:150]])


@api_view(('POST',), roles=ADMIN)
def coupon_save(request, coupon_id=None):
    coupon = get_object_or_404(Coupon, id=coupon_id) if coupon_id else None
    saved, problem = save_coupon(request, coupon)
    if problem:
        return problem
    log_action(request, request.user, 'other', f'Admin guardó el cupón {saved.code}')
    return ok(message=f'Cupón {saved.code} guardado.', coupon=coupon_row(saved))


@api_view(('POST',), roles=ADMIN)
def coupon_toggle(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()
    return ok(message=f'Cupón {coupon.code} {"activado" if coupon.is_active else "desactivado"}.',
              coupon=coupon_row(coupon))


# ============================================
# COMPRAS E INGRESOS (RF-47)
# ============================================
@api_view(('GET',), roles=ADMIN)
def payments(request):
    status = request.GET.get('status')
    qs = Payment.objects.select_related('student', 'coupon').prefetch_related('items__course').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    completed = Payment.objects.filter(status='completed')
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return ok(
        total_revenue=money(completed.aggregate(t=Sum('final_amount'))['t']),
        monthly_revenue=money(completed.filter(created_at__gte=month_start).aggregate(t=Sum('final_amount'))['t']),
        completed_count=completed.count(),
        payments=[{
            'id': p.id, 'invoice_number': p.invoice_number, 'student': display_name(p.student),
            'email': p.student.email, 'total': money(p.final_amount), 'discount': money(p.discount_applied),
            'method_label': p.get_payment_method_display(), 'status': p.status,
            'status_label': p.get_status_display(), 'created_at': p.created_at.isoformat(),
            'courses': [i.course.title for i in p.items.all()],
        } for p in qs[:150]],
    )


# ============================================
# CERTIFICADOS EMITIDOS (RF-48)
# ============================================
@api_view(('GET',), roles=ADMIN)
def certificates(request):
    rows = (Certificate.objects.select_related('enrollment__student', 'enrollment__course')
            .order_by('-issued_at')[:150])
    return ok(certificates=[{
        'id': c.id, 'code': c.certificate_code, 'student': display_name(c.enrollment.student),
        'course': c.enrollment.course.title, 'issued_at': c.issued_at.isoformat(),
        'is_revoked': c.is_revoked, 'verification_count': c.verification_count,
        'pdf': media_url(request, c.pdf_file),
    } for c in rows])


@api_view(('POST',), roles=ADMIN)
def certificate_toggle(request, certificate_id):
    c = get_object_or_404(Certificate, id=certificate_id)
    if c.is_revoked:
        c.reactivate()
        message = f'Certificado {c.certificate_code} reactivado.'
    else:
        c.revoke()
        message = f'Certificado {c.certificate_code} revocado.'
    log_action(request, request.user, 'certificate', message)
    return ok(message=message, is_revoked=c.is_revoked)


# ============================================
# REPORTES (RF-49)
# ============================================
@api_view(('POST',), roles=ADMIN)
def generate_report(request):
    """Resumen de usuarios, cursos, ventas y rendimiento académico en un rango de fechas."""
    from ..models import Enrollment, EvaluationResult
    data = parse_body(request)
    date_from, date_to = data.get('date_from') or None, data.get('date_to') or None

    users_qs, courses_qs = User.objects.all(), Course.objects.all()
    pay_qs = Payment.objects.filter(status='completed')
    enroll_qs = Enrollment.objects.all()
    eval_qs = EvaluationResult.objects.filter(completed_at__isnull=False)
    try:
        if date_from:
            users_qs = users_qs.filter(created_at__date__gte=date_from)
            courses_qs = courses_qs.filter(created_at__date__gte=date_from)
            pay_qs = pay_qs.filter(created_at__date__gte=date_from)
            enroll_qs = enroll_qs.filter(enrollment_date__date__gte=date_from)
            eval_qs = eval_qs.filter(completed_at__date__gte=date_from)
        if date_to:
            users_qs = users_qs.filter(created_at__date__lte=date_to)
            courses_qs = courses_qs.filter(created_at__date__lte=date_to)
            pay_qs = pay_qs.filter(created_at__date__lte=date_to)
            enroll_qs = enroll_qs.filter(enrollment_date__date__lte=date_to)
            eval_qs = eval_qs.filter(completed_at__date__lte=date_to)
    except Exception:
        return error('Rango de fechas inválido (usa AAAA-MM-DD).')

    scores = [r.score / r.total_points * 100 for r in eval_qs if r.total_points]
    top_courses = (pay_qs.values('items__course__title').annotate(n=Count('items'), total=Sum('items__final_price'))
                   .order_by('-n')[:5])
    return ok(report={
        'date_from': date_from, 'date_to': date_to,
        'users': users_qs.count(), 'students': users_qs.filter(role='student').count(),
        'teachers': users_qs.filter(role='teacher').count(),
        'courses': courses_qs.count(), 'published': courses_qs.filter(status='published').count(),
        'sales': pay_qs.count(), 'revenue': money(pay_qs.aggregate(t=Sum('final_amount'))['t']),
        'enrollments': enroll_qs.count(), 'completed_enrollments': enroll_qs.filter(status='completed').count(),
        'evaluations': eval_qs.count(), 'passed_evaluations': eval_qs.filter(passed=True).count(),
        'avg_score': round(sum(scores) / len(scores)) if scores else 0,
        'top_courses': [{'title': r['items__course__title'], 'sales': r['n'], 'revenue': money(r['total'])}
                        for r in top_courses if r['items__course__title']],
    })
