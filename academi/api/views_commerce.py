import logging
import secrets
from decimal import Decimal

from django.core import signing
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import (
    Cart, CartItem, Coupon, Course, Enrollment, Notification, ActivityLog,
    Payment, PaymentItem, EMI_STUDENT_DISCOUNT_PERCENT,
    is_eligible_for_emi_first_purchase_discount,
)
from ..utils import get_client_ip, send_purchase_confirmation_email, render_invoice_pdf
from .auth import api_view, error, ok, parse_body
from .support import log_action
from .serializers import ACTIVE_STATUSES, media_url, money, display_name

logger = logging.getLogger(__name__)
D = Decimal


def _cart_items(user):
    cart, _ = Cart.objects.get_or_create(student=user)
    return cart, list(cart.items.select_related('course__category', 'course__teacher'))


def _course_price(course):
    return D('0.00') if course.is_free else D(str(course.price))


def _coupon_discount(coupon, items):
    """Descuento del cupón. Si es de un curso específico, solo descuenta
    sobre ese curso; si es global, sobre todo el carrito."""
    base = sum((_course_price(i.course) for i in items
                if coupon.course_id is None or i.course_id == coupon.course_id), D('0.00'))
    if coupon.discount_type == 'percentage':
        discount = base * (D(str(coupon.discount_value)) / D('100'))
    else:
        discount = D(str(coupon.discount_value))
    return min(discount, base)


def _find_coupon(code, items):
    """Devuelve (coupon, mensaje_de_error)."""
    code = (code or '').upper().strip()
    if not code:
        return None, 'Ingresa un código de cupón'
    coupon = Coupon.objects.filter(code=code, is_active=True).first()
    if not coupon:
        return None, 'Cupón inválido'
    if not coupon.is_valid():
        return None, 'Cupón expirado o sin usos disponibles'
    if coupon.course_id and not any(i.course_id == coupon.course_id for i in items):
        return None, f'Este cupón es solo para el curso "{coupon.course.title}"'
    return coupon, None


def _pricing(user, items, coupon=None):
    subtotal = sum((_course_price(i.course) for i in items), D('0.00'))
    discount = D('0.00')
    label = None
    if coupon:
        discount = _coupon_discount(coupon, items)
        label = f'Cupón {coupon.code}'
    # El descuento EMI no se acumula con un cupón: se aplica el mayor.
    if is_eligible_for_emi_first_purchase_discount(user):
        emi = min(subtotal * (EMI_STUDENT_DISCOUNT_PERCENT / D('100')), subtotal)
        if emi > discount:
            discount, coupon, label = emi, None, 'Descuento estudiante EMI (primera compra)'
    return {'subtotal': subtotal, 'discount': discount, 'total': subtotal - discount,
            'label': label, 'coupon': coupon}


def _cart_json(request, cart, items, pricing):
    return {
        'items': [{
            'course_id': i.course_id, 'title': i.course.title,
            'image': media_url(request, i.course.image),
            'teacher': display_name(i.course.teacher),
            'category': i.course.category.name if i.course.category_id else None,
            'price': money(_course_price(i.course)), 'is_free': i.course.is_free,
            'level_label': i.course.get_level_display(),
        } for i in items],
        'items_count': len(items),
        'subtotal': money(pricing['subtotal']), 'discount': money(pricing['discount']),
        'total': money(pricing['total']), 'discount_label': pricing['label'],
        'coupon_code': pricing['coupon'].code if pricing['coupon'] else None,
    }


@api_view(('GET',), roles=('student',))
def cart(request):
    cart_obj, items = _cart_items(request.user)
    return ok(cart=_cart_json(request, cart_obj, items, _pricing(request.user, items)),
              emi_discount=float(EMI_STUDENT_DISCOUNT_PERCENT)
              if is_eligible_for_emi_first_purchase_discount(request.user) else None)


@api_view(('POST',), roles=('student',))
def cart_add(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='published')
    if Enrollment.objects.filter(student=request.user, course=course, status__in=ACTIVE_STATUSES).exists():
        return error('Ya has comprado este curso.')
    cart_obj, _ = Cart.objects.get_or_create(student=request.user)
    _, created = CartItem.objects.get_or_create(cart=cart_obj, course=course)
    if not created:
        return error('El curso ya está en el carrito.')
    return ok(message='Curso agregado al carrito', items_count=cart_obj.items.count())


@api_view(('POST',), roles=('student',))
def cart_remove(request, course_id):
    cart_obj, _ = Cart.objects.get_or_create(student=request.user)
    CartItem.objects.filter(cart=cart_obj, course_id=course_id).delete()
    return ok(message='Curso eliminado del carrito', items_count=cart_obj.items.count())


@api_view(('POST',), roles=('student',))
def coupon_validate(request):
    cart_obj, items = _cart_items(request.user)
    coupon, problem = _find_coupon(parse_body(request).get('code'), items)
    if problem:
        return error(problem)
    pricing = _pricing(request.user, items, coupon)
    applied = pricing['coupon'] is not None
    message = (f'Cupón {coupon.code} aplicado.' if applied else
               'Tu descuento EMI es mayor que el cupón, se aplicará ese.')
    return ok(message=message, applied=applied, cart=_cart_json(request, cart_obj, items, pricing))


@api_view(('POST',), roles=('student',))
def checkout(request):
    data = parse_body(request)
    user = request.user
    cart_obj, items = _cart_items(user)
    if not items:
        return error('El carrito está vacío')

    coupon = None
    if data.get('coupon_code'):
        coupon, problem = _find_coupon(data['coupon_code'], items)
        if problem:
            return error(problem)
    pricing = _pricing(user, items, coupon)
    coupon = pricing['coupon']

    full_name = (data.get('full_name') or '').strip()
    email = (data.get('email') or '').strip()
    method = data.get('payment_method', 'qr')
    if not full_name:
        return error('El nombre completo es obligatorio')
    if not email:
        return error('El correo electrónico es obligatorio')
    if method not in ('qr', 'card'):
        return error('Método de pago inválido')

    last_four = None
    if method == 'card':
        # La app valida el número y solo envía los 4 últimos dígitos: el
        # número completo nunca viaja al servidor.
        last_four = ''.join(ch for ch in str(data.get('card_last_four') or '') if ch.isdigit())[-4:]
        if len(last_four) != 4:
            return error('Número de tarjeta inválido')

    try:
        with transaction.atomic():
            payment = Payment.objects.create(
                student=user, coupon=coupon, amount=pricing['subtotal'],
                discount_applied=pricing['discount'], final_amount=pricing['total'],
                payment_method=method, status='completed',
                transaction_id=f'TXN-{secrets.token_hex(8).upper()}',
                billing_name=full_name, billing_email=email,
                billing_phone=(data.get('phone') or '').strip(),
                billing_address=(data.get('address') or '').strip(),
                payment_details={'card_last_four': last_four,
                                 'card_brand': 'Visa/Mastercard' if last_four else None, 'source': 'mobile'},
                confirmed_at=timezone.now(), ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''), notes=pricing['label'] or '',
            )
            titles = []
            for item in items:
                course = item.course
                price = _course_price(course)
                PaymentItem.objects.create(
                    payment=payment, course=course, price=price,
                    discount_applied=pricing['discount'] if len(items) == 1 else D('0.00'),
                    final_price=price,
                )
                enrollment, created = Enrollment.objects.get_or_create(
                    student=user, course=course,
                    defaults={'status': 'enrolled', 'payment_amount': price, 'payment_status': 'paid',
                              'payment_method': method, 'transaction_id': payment.transaction_id,
                              'payment_date': timezone.now()})
                if not created:
                    enrollment.payment_status = 'paid'
                    enrollment.payment_amount = price
                    enrollment.payment_method = method
                    enrollment.transaction_id = payment.transaction_id
                    enrollment.payment_date = timezone.now()
                    enrollment.status = 'enrolled'
                    enrollment.save()
                titles.append(course.title)

                Notification.objects.create(
                    user=user, type='purchase', title=f'Curso adquirido: {course.title}',
                    message=f'Has comprado el curso "{course.title}" exitosamente. Factura: {payment.invoice_number}')
                if course.teacher:
                    Notification.objects.create(
                        user=course.teacher, type='course', title=f'Nuevo estudiante en {course.title}',
                        message=f'{user.username} se ha inscrito en tu curso "{course.title}"')

            if coupon:
                coupon.used_count += 1
                if coupon.used_count >= coupon.max_uses:
                    coupon.is_active = False
                coupon.save()
            cart_obj.items.all().delete()
            ActivityLog.objects.create(
                user=user, action_type='payment',
                description=f'Compra móvil - Factura: {payment.invoice_number} - {len(titles)} cursos - '
                            f'Total: Bs.{pricing["total"]}',
                ip_address=get_client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', ''))
    except Exception:
        logger.exception('Error en checkout móvil')
        return error('Error al procesar la compra. Intenta nuevamente.', 500)

    try:
        send_purchase_confirmation_email(payment, payment.items.select_related('course'), request)
    except Exception:
        logger.exception('No se pudo enviar el correo de confirmación de compra')

    return ok(message=f'Compra realizada con éxito. {len(titles)} curso(s) adquirido(s).',
              payment_id=payment.id, invoice_number=payment.invoice_number,
              total=money(pricing['total']), discount_label=pricing['label'], courses=titles)


INVOICE_SALT = 'academi.api.invoice'


def _payment_json(payment, with_items=False, request=None):
    data = {
        'id': payment.id, 'invoice_number': payment.invoice_number,
        'amount': money(payment.amount), 'discount': money(payment.discount_applied),
        'total': money(payment.final_amount), 'method': payment.payment_method,
        'method_label': payment.get_payment_method_display(),
        'status': payment.status, 'status_label': payment.get_status_display(),
        'created_at': payment.created_at.isoformat(), 'transaction_id': payment.transaction_id,
        'courses_count': payment.items.count(),
        'coupon': payment.coupon.code if payment.coupon_id else None,
    }
    if with_items:
        if request is not None:
            token = signing.dumps({'payment': payment.id}, salt=INVOICE_SALT)
            data['pdf_url'] = request.build_absolute_uri(f'/api/v1/purchases/{payment.id}/pdf/?t={token}')
        data.update({
            'billing_name': payment.billing_name or '', 'billing_email': payment.billing_email or '',
            'billing_phone': payment.billing_phone or '', 'billing_address': payment.billing_address or '',
            'notes': payment.notes or '',
            'card_last_four': (payment.payment_details or {}).get('card_last_four'),
            'items': [{'course_id': i.course_id, 'title': i.course.title,
                       'price': money(i.price), 'final_price': money(i.final_price)}
                      for i in payment.items.select_related('course')],
        })
    return data


@api_view(('GET',), roles=('student',))
def purchases(request):
    payments = (Payment.objects.filter(student=request.user).select_related('coupon')
                .prefetch_related('items').order_by('-created_at'))
    rows = list(payments)
    total = sum((p.final_amount for p in rows if p.status == 'completed'), D('0.00'))
    return ok(payments=[_payment_json(p) for p in rows], total_spent=money(total))


@api_view(('GET',), roles=('student',))
def purchase_detail(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related('coupon'), id=payment_id, student=request.user)
    return ok(payment=_payment_json(payment, with_items=True, request=request))


@api_view(('GET',), auth='none')
def purchase_pdf(request, payment_id):
    """RF-38: PDF del comprobante. Se abre desde el navegador del teléfono, que no
    puede enviar el token Bearer, así que se protege con un enlace firmado de 10 minutos."""
    try:
        data = signing.loads(request.GET.get('t', ''), salt=INVOICE_SALT, max_age=600)
    except signing.BadSignature:
        return error('El enlace del comprobante expiró. Vuelve a abrirlo desde la app.', 403)
    if data.get('payment') != payment_id:
        return error('Enlace inválido.', 403)
    payment = get_object_or_404(Payment, id=payment_id)
    response = HttpResponse(render_invoice_pdf(payment).read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprobante-{payment.invoice_number or payment.id}.pdf"'
    return response
