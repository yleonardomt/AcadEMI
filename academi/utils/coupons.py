"""Reglas compartidas por los cupones de web y API móvil."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from ..models import Coupon


def save_coupon(owner, data, coupon=None, course=None):
    code = (data.get('code') or '').strip().upper() if coupon is None else coupon.code
    if not code or len(code) > 50:
        return None, 'El código debe tener entre 1 y 50 caracteres.'
    if coupon is None and Coupon.objects.filter(code__iexact=code).exists():
        return None, 'Ya existe un cupón con ese código.'

    discount_type = data.get('discount_type') or (coupon.discount_type if coupon else 'percentage')
    if discount_type not in ('percentage', 'fixed'):
        return None, 'Tipo de descuento inválido.'
    try:
        value = Decimal(str(data.get('discount_value') or (coupon.discount_value if coupon else '0')))
        max_uses = int(data.get('max_uses') or (coupon.max_uses if coupon else 1))
    except (InvalidOperation, TypeError, ValueError):
        return None, 'Valor o usos máximos inválidos.'
    if not value.is_finite() or value <= 0 or value.as_tuple().exponent < -2:
        return None, 'El descuento debe ser positivo y tener como máximo dos decimales.'
    if discount_type == 'percentage' and value > 100:
        return None, 'El porcentaje no puede superar 100%.'
    minimum_uses = max(1, coupon.used_count, coupon.demo_used_count) if coupon else 1
    if max_uses < minimum_uses:
        return None, 'Los usos máximos no pueden ser menores que los ya utilizados.'

    expires_raw = data.get('expires_at')
    if expires_raw:
        try:
            expires = datetime.fromisoformat(str(expires_raw).replace('Z', '+00:00'))
            if timezone.is_naive(expires):
                expires = timezone.make_aware(expires)
        except (TypeError, ValueError):
            return None, 'Fecha de expiración inválida.'
    elif coupon:
        expires = coupon.expires_at
    else:
        return None, 'La fecha de expiración es obligatoria.'
    if expires <= timezone.now():
        return None, 'La fecha de expiración debe ser futura.'
    target_course = course if coupon is None else coupon.course
    if target_course and (target_course.status != 'published' or target_course.is_free):
        return None, 'El cupón debe corresponder a un curso pago publicado.'

    if coupon is None:
        coupon = Coupon(code=code, created_by=owner, course=course)
    coupon.discount_type = discount_type
    coupon.discount_value = value
    coupon.max_uses = max_uses
    coupon.expires_at = expires
    try:
        coupon.full_clean()
        coupon.save()
    except ValidationError as exc:
        return None, '; '.join(exc.messages)
    except IntegrityError:
        return None, 'Ya existe un cupón con ese código.'
    return coupon, None


def coupon_discount(coupon, items):
    base = sum((Decimal('0') if item.course.is_free else Decimal(str(item.course.price))
                for item in items if coupon.course_id is None or item.course_id == coupon.course_id), Decimal('0'))
    discount = base * coupon.discount_value / Decimal('100') if coupon.discount_type == 'percentage' else coupon.discount_value
    return min(max(discount, Decimal('0')), base)


def find_coupon(code, items):
    code = (code or '').strip().upper()
    if not code:
        return None, 'Ingresa un código de cupón.'
    if not any(not item.course.is_free for item in items):
        return None, 'Los cupones se aplican solo a cursos pagos.'
    coupon = Coupon.objects.filter(code=code).select_related('course').first()
    if not coupon or not coupon.is_valid():
        return None, 'Cupón inválido, agotado o vencido.'
    if coupon.course_id and not any(item.course_id == coupon.course_id for item in items):
        return None, f'Este cupón es solo para el curso "{coupon.course.title}".'
    return coupon, None
