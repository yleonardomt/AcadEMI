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

from ..models import (
    Cart, Coupon, Payment, PaymentItem, Enrollment, Notification,
    ActivityLog, Course, is_eligible_for_emi_first_purchase_discount,
    EMI_STUDENT_DISCOUNT_PERCENT,
)
from ..utils import get_client_ip, send_purchase_confirmation_email, render_invoice_pdf
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

    items = cart.items.select_related('course').all()
    if not items.exists():
        return JsonResponse({
            'success': False,
            'message': 'El carrito está vacío'
        })

    # CALCULAR TOTALES
    subtotal = Decimal('0.00')
    for item in items:
        if not item.course.is_free:
            subtotal += Decimal(str(item.course.price))

    # APLICAR CUPÓN
    discount = Decimal('0.00')
    coupon_code = data.get('coupon_code')
    coupon = None
    discount_label = None

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code.upper(), is_active=True)
            if coupon.is_valid():
                if coupon.discount_type == 'percentage':
                    discount = subtotal * (Decimal(str(coupon.discount_value)) / Decimal('100'))
                else:
                    discount = Decimal(str(coupon.discount_value))
                if discount > subtotal:
                    discount = subtotal
                discount_label = f'Cupón {coupon.code}'
        except Coupon.DoesNotExist:
            pass

    # DESCUENTO AUTOMÁTICO POR PRIMERA COMPRA DE ESTUDIANTE EMI: no se
    # acumula con un cupón manual, se queda el que dé mayor descuento.
    if is_eligible_for_emi_first_purchase_discount(request.user):
        emi_discount = subtotal * (EMI_STUDENT_DISCOUNT_PERCENT / Decimal('100'))
        if emi_discount > subtotal:
            emi_discount = subtotal
        if emi_discount > discount:
            discount = emi_discount
            coupon = None  # el descuento EMI no está ligado a un Coupon
            discount_label = 'Descuento estudiante EMI (primera compra)'

    total = subtotal - discount

    # VALIDAR DATOS DE PAGO
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    payment_method = data.get('payment_method', 'qr')

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

    # RNF-20: el navegador/app valida la tarjeta y solo envía los últimos
    # 4 dígitos; el servidor nunca recibe ni guarda el número completo.
    card_last_four = ''
    if payment_method == 'card':
        card_last_four = ''.join(ch for ch in str(data.get('card_last_four') or '') if ch.isdigit())[-4:]
        if len(card_last_four) != 4:
            return JsonResponse({
                'success': False,
                'message': 'Número de tarjeta inválido'
            })

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
                payment_details={
                    'card_last_four': card_last_four or None,
                    'card_brand': 'Visa/Mastercard' if payment_method == 'card' else None,
                },
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
                    price=Decimal(str(course.price)) if not course.is_free else Decimal('0.00'),
                    discount_applied=discount if items.count() == 1 else Decimal('0.00'),
                    final_price=Decimal(str(course.price)) if not course.is_free else Decimal('0.00')
                )

                enrollment, created = Enrollment.objects.get_or_create(
                    student=request.user,
                    course=course,
                    defaults={
                        'status': 'enrolled',
                        'payment_amount': Decimal(str(course.price)) if not course.is_free else Decimal('0.00'),
                        'payment_status': 'paid',
                        'payment_method': payment_method,
                        'transaction_id': payment.transaction_id,
                        'payment_date': timezone.now(),
                    }
                )

                if not created:
                    enrollment.payment_status = 'paid'
                    enrollment.payment_amount = Decimal(str(course.price)) if not course.is_free else Decimal('0.00')
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
                    message=f'Has comprado el curso "{course.title}" exitosamente. Factura: {payment.invoice_number}',
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
        try:
            send_purchase_confirmation_email(payment, payment.items.select_related('course'), request)
        except Exception:
            logger.exception('No se pudo enviar el correo de confirmación de compra')

        return JsonResponse({
            'success': True,
            'message': f'Compra realizada con éxito. {len(created_courses)} curso(s) adquirido(s).',
            'invoice_number': payment.invoice_number,
            'total': str(total),
            'discount_label': discount_label,
            'courses': created_courses
        })

    except Exception as e:
        logger.error(f"Error en checkout: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error al procesar la compra: {str(e)}'
        }, status=500)


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
        code = data.get('code', '').upper().strip()
        subtotal = Decimal(str(data.get('subtotal', 0)))

        if not code:
            return JsonResponse({
                'success': False,
                'message': 'Ingresa un código de cupón'
            })

        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Cupón inválido'
            })

        if not coupon.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'Cupón expirado o sin usos disponibles'
            })

        if coupon.course:
            cart = Cart.objects.filter(student=request.user).first()
            if not cart:
                return JsonResponse({
                    'success': False,
                    'message': 'El cupón es para un curso específico'
                })

            has_course = cart.items.filter(course=coupon.course).exists()
            if not has_course:
                return JsonResponse({
                    'success': False,
                    'message': f'Este cupón es solo para el curso "{coupon.course.title}"'
                })

        if coupon.discount_type == 'percentage':
            discount_amount = subtotal * (Decimal(str(coupon.discount_value)) / Decimal('100'))
        else:
            discount_amount = Decimal(str(coupon.discount_value))

        if discount_amount > subtotal:
            discount_amount = subtotal

        return JsonResponse({
            'success': True,
            'message': f'Descuento aplicado: {coupon.discount_value}%' if coupon.discount_type == 'percentage' else f'Descuento aplicado: Bs.{coupon.discount_value}',
            'discount_amount': float(discount_amount),
            'coupon': {
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value)
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ============================================
# API: OBTENER CUPÓN ACTIVO
# ============================================
@login_required
def get_active_coupon_api(request):
    coupon_code = request.session.get('active_coupon')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            if not coupon.is_valid():
                request.session.pop('active_coupon', None)
                return JsonResponse({'success': False})

            subtotal = Decimal(str(request.GET.get('subtotal', 0) or 0))
            if coupon.discount_type == 'percentage':
                discount_amount = subtotal * (Decimal(str(coupon.discount_value)) / Decimal('100'))
            else:
                discount_amount = Decimal(str(coupon.discount_value))
            if discount_amount > subtotal:
                discount_amount = subtotal

            return JsonResponse({
                'success': True,
                'code': coupon.code,
                'discount_amount': float(discount_amount),
                'coupon': {
                    'code': coupon.code,
                    'discount_type': coupon.discount_type,
                    'discount_value': float(coupon.discount_value)
                }
            })
        except (Coupon.DoesNotExist, ValueError, TypeError):
            pass
    return JsonResponse({'success': False})


# ============================================
# HISTORIAL DE COMPRAS
# ============================================
@login_required
def purchase_history_view(request):
    payments = Payment.objects.filter(
        student=request.user
    ).select_related('coupon').prefetch_related('items__course').order_by('-created_at')

    total_spent = payments.aggregate(total=Sum('final_amount'))['total'] or 0

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

    teacher_courses = Course.objects.filter(teacher=request.user)

    if request.method == 'POST':
        course_id = request.POST.get('course')
        code = request.POST.get('code', '').strip().upper()
        discount_type = request.POST.get('discount_type', 'percentage')
        discount_value = request.POST.get('discount_value') or 0
        max_uses = request.POST.get('max_uses') or 1
        expires_at = request.POST.get('expires_at')

        course = teacher_courses.filter(id=course_id).first()

        if not course or not code or not expires_at:
            messages.error(request, 'Completa el curso, código y fecha de expiración.')
        else:
            expires_at_dt = timezone.datetime.fromisoformat(expires_at)
            if timezone.is_naive(expires_at_dt):
                expires_at_dt = timezone.make_aware(expires_at_dt)
            Coupon.objects.create(
                code=code,
                course=course,
                discount_type=discount_type,
                discount_value=discount_value,
                max_uses=max_uses,
                expires_at=expires_at_dt,
                created_by=request.user,
            )
            messages.success(request, f'Cupón {code} creado correctamente.')
            return redirect('teacher_coupons')

    coupons = Coupon.objects.filter(course__in=teacher_courses).select_related('course').order_by('-created_at')
    return render(request, 'academi/payments/mis_cupones.html', {
        'coupons': coupons,
        'teacher_courses': teacher_courses,
    })


@login_required
def teacher_coupon_edit(request, coupon_id):
    """RF-60: modificar un cupón de uno de los cursos propios."""
    coupon = get_object_or_404(Coupon, id=coupon_id, course__teacher=request.user)

    if request.method == 'POST':
        discount_type = request.POST.get('discount_type', coupon.discount_type)
        discount_value = request.POST.get('discount_value') or coupon.discount_value
        max_uses = request.POST.get('max_uses') or coupon.max_uses
        expires_at = request.POST.get('expires_at')

        coupon.discount_type = discount_type
        coupon.discount_value = discount_value
        coupon.max_uses = max_uses
        if expires_at:
            expires_at_dt = timezone.datetime.fromisoformat(expires_at)
            if timezone.is_naive(expires_at_dt):
                expires_at_dt = timezone.make_aware(expires_at_dt)
            coupon.expires_at = expires_at_dt
        coupon.save()
        messages.success(request, f'Cupón {coupon.code} actualizado.')

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
