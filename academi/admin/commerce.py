from django.contrib import admin

from ..models import Payment, Certificate, Coupon, Cart, CartItem


# ============================================
# ADMIN - PAGOS
# ============================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'final_amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('student__username', 'student__email', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')


# ============================================
# ADMIN - CERTIFICADOS
# ============================================
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_code', 'enrollment', 'issued_at', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('certificate_code', 'enrollment__student__username')


# ============================================
# ADMIN - CUPONES
# ============================================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'course', 'is_active', 'used_count', 'expires_at')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)


# ============================================
# ADMIN - CARRITO
# ============================================
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('student', 'created_at', 'updated_at')
    search_fields = ('student__username',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'course', 'added_at')
    search_fields = ('cart__student__username', 'course__title')
