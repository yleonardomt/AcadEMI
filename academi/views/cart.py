from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ..models import (
    Cart, CartItem, Course, Enrollment,
    EMI_STUDENT_DISCOUNT_PERCENT, is_eligible_for_emi_first_purchase_discount,
)


# ============================================
# MÓDULO 7: CARRITO
# ============================================
@login_required
def cart_add_view(request, course_id):
    """Agregar un curso al carrito"""
    try:
        if request.user.role != 'student':
            return JsonResponse({
                'success': False,
                'message': 'Solo estudiantes pueden comprar.'
            })

        course = get_object_or_404(Course, id=course_id, status='published')

        # Verificar si ya está inscrito
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return JsonResponse({
                'success': False,
                'message': 'Ya has comprado este curso.'
            })

        # Obtener o crear carrito
        cart, created = Cart.objects.get_or_create(student=request.user)

        # Verificar si ya está en el carrito
        if CartItem.objects.filter(cart=cart, course=course).exists():
            return JsonResponse({
                'success': False,
                'message': 'El curso ya está en el carrito.'
            })

        # Agregar al carrito
        CartItem.objects.create(cart=cart, course=course)
        items_count = cart.items.count()

        return JsonResponse({
            'success': True,
            'message': 'Curso agregado al carrito',
            'items_count': items_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def cart_remove_view(request, course_id):
    """Eliminar un curso del carrito"""
    try:
        cart = get_object_or_404(Cart, student=request.user)
        item = get_object_or_404(CartItem, cart=cart, course_id=course_id)
        item.delete()

        items_count = cart.items.count()

        return JsonResponse({
            'success': True,
            'message': 'Curso eliminado del carrito',
            'items_count': items_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def cart_items_view(request):
    """Obtener los items del carrito (API)"""
    try:
        cart, created = Cart.objects.get_or_create(student=request.user)
        items = list(cart.items.values_list('course_id', flat=True))

        return JsonResponse({
            'success': True,
            'items': items,
            'items_count': cart.items.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'items': [],
            'items_count': 0
        })


@login_required
def cart_view(request):
    """Vista principal del carrito"""
    cart, created = Cart.objects.get_or_create(student=request.user)
    items = cart.items.select_related('course').all()

    total = 0
    for item in items:
        if not item.course.is_free:
            total += item.course.price

    context = {
        'cart': cart,
        'items': items,
        'items_count': items.count(),
        'total': total,
        'emi_discount_eligible': is_eligible_for_emi_first_purchase_discount(request.user),
        'emi_discount_percent': EMI_STUDENT_DISCOUNT_PERCENT,
    }
    return render(request, 'academi/payments/carrito.html', context)
