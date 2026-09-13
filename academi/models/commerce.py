from decimal import Decimal

from django.db import models
from django.utils import timezone

from .users import User
from .courses import Course
from .learning import Enrollment

# ============================================
# MÓDULO 7: CARRITO, COMPRAS, PAGOS Y CUPONES (RF-54 al RF-63)
# ============================================

class Cart(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.student.username}"

    @property
    def total(self):
        return sum(item.course.price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'course']

    def __str__(self):
        return f"{self.cart.student.username} - {self.course.title}"


class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Porcentaje'),
        ('fixed', 'Monto fijo'),
    )

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='coupons')
    max_uses = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_coupons')

    def __str__(self):
        return self.code

    def is_valid(self):
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.expires_at < timezone.now():
            return False
        return True

    def apply_discount(self, amount):
        if self.discount_type == 'percentage':
            return amount * (1 - self.discount_value / 100)
        return max(0, amount - self.discount_value)


class Payment(models.Model):
    """
    Modelo de pagos con facturación y seguimiento completo
    """

    PAYMENT_STATUS = (
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
        ('cancelled', 'Cancelado'),
        ('expired', 'Expirado'),
    )

    PAYMENT_METHODS = (
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Transferencia bancaria'),
        ('pago_efectivo', 'Pago Efectivo'),
        ('qr', 'Pago QR'),
        ('card', 'Tarjeta'),
        ('cart', 'Carrito'),
        ('mobile', 'Pago Móvil'),
    )

    # RELACIONES
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )

    # DATOS DEL PAGO
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    teacher_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='stripe')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')

    # DATOS DE TRANSACCIÓN
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    receipt_url = models.URLField(blank=True, null=True)

    # FACTURACIÓN
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    billing_name = models.CharField(max_length=255, blank=True, null=True)
    billing_email = models.EmailField(blank=True, null=True)
    billing_phone = models.CharField(max_length=50, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    billing_ci = models.CharField(max_length=20, blank=True, null=True)
    billing_company = models.CharField(max_length=255, blank=True, null=True)
    billing_nit = models.CharField(max_length=50, blank=True, null=True)

    # DATOS DE PAGO
    payment_details = models.JSONField(default=dict, blank=True)

    # FECHAS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    # METADATOS
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.invoice_number or 'Pago'} - {self.student.username} - Bs.{self.final_amount}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        if self.final_amount > 0:
            self.commission_amount = self.final_amount * Decimal('0.10')
            self.teacher_amount = self.final_amount - self.commission_amount

        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        year = timezone.now().year
        last_payment = Payment.objects.filter(
            created_at__year=year
        ).order_by('-created_at').first()

        if last_payment and last_payment.invoice_number:
            try:
                last_num = int(last_payment.invoice_number.split('-')[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1

        return f"FAC-{year}-{str(next_num).zfill(5)}"

    def complete(self):
        self.status = 'completed'
        self.confirmed_at = timezone.now()
        self.save()

    def refund(self):
        self.status = 'refunded'
        self.refunded_at = timezone.now()
        self.save()

    def cancel(self):
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()


class PaymentItem(models.Model):
    """Items individuales de un pago (cursos comprados)"""

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='items'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    teacher_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Item de pago'
        verbose_name_plural = 'Items de pago'
        indexes = [
            models.Index(fields=['payment', 'course']),
        ]

    def __str__(self):
        return f"{self.payment.invoice_number} - {self.course.title}"

    def save(self, *args, **kwargs):
        if self.final_price == 0:
            self.final_price = self.price - self.discount_applied

        if self.final_price > 0:
            self.platform_commission = self.final_price * Decimal('0.10')
            self.teacher_commission = self.final_price - self.platform_commission

        super().save(*args, **kwargs)


# ============================================
# MÓDULO 8: CERTIFICADOS (RF-64 al RF-67)
# ============================================

class Certificate(models.Model):  # RF-64, RF-65, RF-66, RF-67
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_code = models.CharField(max_length=50, unique=True)  # RF-67
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='certificates/', blank=True, null=True)  # RF-65
    is_verified = models.BooleanField(default=False)
    verification_count = models.IntegerField(default=0)  # RF-67
    last_verified_at = models.DateTimeField(blank=True, null=True)  # RF-67

    def __str__(self):
        return f"Certificado - {self.enrollment.student.username} - {self.enrollment.course.title}"

    def generate_code(self):  # RF-67
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        self.certificate_code = code
        return code

    def verify(self):  # RF-67
        self.is_verified = True
        self.verification_count += 1
        self.last_verified_at = timezone.now()
        self.save()
        return True
