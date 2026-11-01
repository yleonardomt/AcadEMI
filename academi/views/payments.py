import json
import logging
import secrets
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings

from ..models import (
    Cart, Coupon, Payment, PaymentItem, Enrollment, Notification,
    ActivityLog, Course, is_eligible_for_emi_first_purchase_discount,
    EMI_STUDENT_DISCOUNT_PERCENT,
)
from ..utils import get_client_ip, send_purchase_confirmation_email, render_invoice_pdf
from ..utils.coupons import save_coupon as save_coupon_record
from ..utils.demo_sales import visible_sales
from ..api.views_commerce import _find_coupon, _pricing, _line_amounts
from django.http import HttpResponse

logger = logging.getLogger(__name__)


# ============================================
# CHECKOUT COMPLETO
# ============================================
@login_required
def checkout_view(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método no permitido'
        }, status=405)

    if request.user.role != 'student':
        return JsonResponse({
            'success': False,
            'message': 'Solo estudiantes pueden comprar'
        }, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos inválidos'
        }, status=400)

    # OBTENER CARRITO
    cart = Cart.objects.filter(student=request.user).first()
    if not cart:
        return JsonResponse({
            'success': False,
            'message': 'No tienes cursos en el carrito'
        })

    items = list(cart.items.select_related('course'))
    if not items:
        return JsonResponse({
            'success': False,
            'message': 'El carrito está vacío'
        })

    if any(item.course.status != 'published' for item in items):
        return JsonResponse({'success': False, 'message': 'Hay un curso que ya no está publicado. Quítalo del carrito.'}, status=400)

    coupon = None
    if data.get('coupon_code'):
        coupon, problem = _find_coupon(data['coupon_code'], items)
        if problem:
            return JsonResponse({'success': False, 'message': problem}, status=400)
    pricing = _pricing(request.user, items, coupon)
    lines = _line_amounts(items, pricing)
    subtotal, discount, total = pricing['subtotal'], pricing['discount'], pricing['total']
    coupon, discount_label = pricing['coupon'], pricing['label']

    # No existe integración con un proveedor que confirme el cobro.
    # Nunca conceder acceso a un curso de pago basándose en datos del navegador.
    demo = subtotal > 0 and settings.DEMO_CHECKOUT
    if subtotal > 0 and not demo:
        return JsonResponse({
            'success': False,
            'message': 'Las compras de cursos pagos aún no están habilitadas. Estamos integrando un cobro verificable.'
        }, status=503)

    # VALIDAR DATOS DE PAGO
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    payment_method = 'demo' if demo else 'free'

    if not full_name:
        return JsonResponse({
            'success': False,
            'message': 'El nombre completo es obligatorio'
        })

    if not email:
        return JsonResponse({
            'success': False,
            'message': 'El correo electrónico es obligatorio'
        })
    if any(Enrollment.objects.filter(student=request.user, course=item.course).exists() for item in items):
        return JsonResponse({'success': False, 'message': 'Ya estás inscrito en uno de estos cursos. Quítalo del carrito.'}, status=400)

    # CREAR PAGO CON TRANSACCIÓN
    try:
        with transaction.atomic():
            payment = Payment.objects.create(
                student=request.user,
                coupon=coupon,
                amount=subtotal,
                discount_applied=discount,
                final_amount=total,
                payment_method=payment_method,
                status='completed',
                transaction_id=f"TXN-{secrets.token_hex(8).upper()}",
                billing_name=full_name,
                billing_email=email,
                billing_phone=phone,
                billing_address=address,
                payment_details={'mode': 'demo'} if demo else {},
                confirmed_at=timezone.now(),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes=discount_label or ''
            )

            # CREAR ENROLLMENTS Y PAYMENT ITEMS
            created_courses = []

            for item in items:
                course = item.course

                PaymentItem.objects.create(
                    payment=payment,
                    course=course,
                    price=lines[course.id][0],
                    discount_applied=lines[course.id][1],
                    final_price=lines[course.id][2]
                )

                enrollment, created = Enrollment.objects.get_or_create(
                    student=request.user,
                    course=course,
                    defaults={
                        'status': 'enrolled',
                        'payment_amount': Decimal('0.00') if demo else (Decimal(str(course.price)) if not course.is_free else Decimal('0.00')),
                        'payment_status': 'demo' if demo else 'paid',
                        'payment_method': payment_method,
                        'transaction_id': payment.transaction_id,
                        'payment_date': timezone.now(),
                    }
                )

                if not created:
                    enrollment.payment_status = 'demo' if demo else 'paid'
                    enrollment.payment_amount = Decimal('0.00') if demo else (Decimal(str(course.price)) if not course.is_free else Decimal('0.00'))
                    enrollment.payment_method = payment_method
                    enrollment.transaction_id = payment.transaction_id
                    enrollment.payment_date = timezone.now()
                    enrollment.status = 'enrolled'
                    enrollment.save()

                created_courses.append(course.title)

                # NOTIFICACIÓN AL ESTUDIANTE
                Notification.objects.create(
                    user=request.user,
                    type='purchase',
                    title=f'Curso adquirido: {course.title}',
                    message=f'Ya tienes acceso al curso "{course.title}". Pedido: {payment.invoice_number}' if demo else f'Has comprado el curso "{course.title}" exitosamente. Factura: {payment.invoice_number}',
                    link=f'/course/{course.id}/'
                )

                # NOTIFICACIÓN AL DOCENTE
                if course.teacher:
                    Notification.objects.create(
                        user=course.teacher,
                        type='course',
                        title=f'Nuevo estudiante en {course.title}',
                        message=f'{request.user.username} se ha inscrito en tu curso "{course.title}"',
                        link=f'/course/{course.id}/students/'
                    )

            # ACTUALIZAR CUPÓN
            if coupon:
                if demo:
                    coupon.demo_used_count += 1
                    coupon.save(update_fields=['demo_used_count'])
                else:
                    coupon.used_count += 1
                    if coupon.used_count >= coupon.max_uses:
                        coupon.is_active = False
                    coupon.save()

            # LIMPIAR CARRITO
            cart.items.all().delete()

            # GUARDAR CUPÓN EN SESIÓN
            if coupon:
                request.session['active_coupon'] = coupon.code
            else:
                request.session.pop('active_coupon', None)

            # REGISTRAR ACTIVIDAD
            ActivityLog.objects.create(
                user=request.user,
                action_type='payment',
                description=f'Compra realizada - Factura: {payment.invoice_number} - {len(created_courses)} cursos - Total: Bs.{total}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

        # RF-58, RF-62: correo de confirmación con el comprobante, enviado
        # después de confirmar la transacción (si falla el envío, la compra
        # ya quedó registrada de todos modos: fail_silently=True).
        if not demo:
            try:
                send_purchase_confirmation_email(payment, payment.items.select_related('course'), request)
            except Exception:
                logger.exception('No se pudo enviar el correo de confirmación de compra')

        return JsonResponse({
            'success': True,
            'message': f'Compra registrada. {len(created_courses)} curso(s) disponibles.' if demo else f'Inscripción realizada. {len(created_courses)} curso(s) disponibles.',
            'demo': demo,
            'invoice_number': payment.invoice_number,
            'total': str(total),
            'discount_label': discount_label,
            'courses': created_courses
        })

    except Exception as e:
        logger.error(f"Error en checkout: {str(e)}")
        logger.exception('Error en checkout web')
        return JsonResponse({'success': False, 'message': 'No se pudo procesar la inscripción. Intenta nuevamente.'}, status=500)


# ============================================
# API: VALIDAR CUPÓN
# ============================================
@login_required
def validate_coupon_api(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'message': 'Datos inválidos.'}, status=400)
    cart = Cart.objects.filter(student=request.user).first()
    items = list(cart.items.select_related('course')) if cart else []
    if not items:
        return JsonResponse({'success': False, 'message': 'El carrito está vacío.'}, status=400)
    coupon, problem = _find_coupon(data.get('code') if isinstance(data, dict) else '', items)
    if problem:
        return JsonResponse({'success': False, 'message': problem}, status=400)
    pricing = _pricing(request.user, items, coupon)
    applied = pricing['coupon'] is not None
    return JsonResponse({
        'success': True, 'applied': applied, 'message': pricing['label'] or 'Descuento calculado.',
        'code': coupon.code, 'discount_amount': float(pricing['discount']),
        'coupon': {'code': coupon.code, 'discount_type': coupon.discount_type,
                   'discount_value': float(coupon.discount_value)},
    })


# ============================================
# API: OBTENER CUPÓN ACTIVO
# ============================================
@login_required
def get_active_coupon_api(request):
    coupon_code = request.session.get('active_coupon')
    if coupon_code:
        cart = Cart.objects.filter(student=request.user).first()
        items = list(cart.items.select_related('course')) if cart else []
        coupon, problem = _find_coupon(coupon_code, items)
        if not problem:
            pricing = _pricing(request.user, items, coupon)
            if pricing['coupon']:
                return JsonResponse({
                    'success': True, 'code': coupon.code,
                    'discount_amount': float(pricing['discount']),
                    'coupon': {'code': coupon.code, 'discount_type': coupon.discount_type,
                               'discount_value': float(coupon.discount_value)},
                })
        request.session.pop('active_coupon', None)
    return JsonResponse({'success': False})


# ============================================
# HISTORIAL DE COMPRAS
# ============================================
@login_required
def purchase_history_view(request):
    payments = Payment.objects.filter(
        student=request.user
    ).select_related('coupon').prefetch_related('items__course').order_by('-created_at')

    total_spent = visible_sales(payments.filter(status='completed')).aggregate(total=Sum('final_amount'))['total'] or 0

    return render(request, 'academi/payments/historial_compras.html', {
        'payments': payments,
        'total_payments': payments.count(),
        'total_spent': total_spent,
    })


# ============================================
# FACTURA
# ============================================
@login_required
def invoice_view(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, student=request.user)
    items = PaymentItem.objects.filter(payment=payment).select_related('course')

    return render(request, 'academi/payments/factura.html', {
        'payment': payment,
        'items': items,
        'subtotal': payment.amount,
        'discount': payment.discount_applied,
        'total': payment.final_amount
    })


@login_required
def invoice_pdf_view(request, payment_id):
    """RF-38: descarga el comprobante de pago como PDF."""
    payment = get_object_or_404(Payment, id=payment_id, student=request.user)
    response = HttpResponse(render_invoice_pdf(payment).read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprobante-{payment.invoice_number or payment.id}.pdf"'
    return response


# ============================================
# CUPONES DEL DOCENTE (RF-60)
# ============================================
@login_required
def teacher_coupons_view(request):
    """RF-60: el docente crea, modifica, activa y desactiva cupones de sus cursos."""
    if request.user.role != 'teacher':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    owned_courses = Course.objects.filter(teacher=request.user)
    teacher_courses = owned_courses.filter(status='published', is_free=False)

    if request.method == 'POST':
        course_id = request.POST.get('course')
        course = teacher_courses.filter(id=course_id).first()
        if not course:
            messages.error(request, 'Selecciona un curso pago publicado.')
        else:
            coupon, problem = save_coupon_record(request.user, request.POST, course=course)
            if problem:
                messages.error(request, problem)
            else:
                messages.success(request, f'Cupón {coupon.code} creado correctamente.')
                return redirect('teacher_coupons')

    coupons = Coupon.objects.filter(course__in=owned_courses).select_related('course').order_by('-created_at')
    return render(request, 'academi/payments/mis_cupones.html', {
        'coupons': coupons,
        'teacher_courses': teacher_courses,
    })


@login_required
def teacher_coupon_edit(request, coupon_id):
    """RF-60: modificar un cupón de uno de los cursos propios."""
    coupon = get_object_or_404(Coupon, id=coupon_id, course__teacher=request.user)

    if request.method == 'POST':
        saved, problem = save_coupon_record(request.user, request.POST, coupon)
        messages.error(request, problem) if problem else messages.success(request, f'Cupón {saved.code} actualizado.')

    return redirect('teacher_coupons')


@login_required
@require_POST
def teacher_coupon_toggle(request, coupon_id):
    """RF-60: activar/desactivar un cupón de uno de los cursos propios."""
    coupon = get_object_or_404(Coupon, id=coupon_id, course__teacher=request.user)
    coupon.is_active = not coupon.is_active
    coupon.save()
    estado = 'activado' if coupon.is_active else 'desactivado'
    messages.success(request, f'Cupón {coupon.code} {estado}.')
    return redirect('teacher_coupons')


@login_required
def teacher_coupon_delete(request, coupon_id):
    """RF-60: eliminar definitivamente un cupón de uno de los cursos propios."""
    coupon = get_object_or_404(Coupon, id=coupon_id, course__teacher=request.user)
    if request.method == 'POST':
        code = coupon.code
        coupon.delete()
        messages.success(request, f'Cupón {code} eliminado.')
    return redirect('teacher_coupons')
