import json

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ActivityLog, Cart, CartItem, Course, Enrollment, Payment, User
from .models import Coupon
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from .utils.invoice_pdf import render_invoice_pdf


@override_settings(DEMO_CHECKOUT=True)
class DebitCardCheckoutTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='card_student', email='card@example.com', email_verified=True)
        teacher = User.objects.create_user(username='card_teacher', role='teacher')
        self.course = Course.objects.create(title='Curso con tarjeta', status='published', price=120, teacher=teacher)
        self.cart = Cart.objects.create(student=self.student)
        CartItem.objects.create(cart=self.cart, course=self.course)
        self.client.force_login(self.student)

    def checkout(self, **changes):
        payload = {'full_name': 'Ana Tarjeta', 'email': 'card@example.com',
                   'payment_method': 'debit_card', 'test_card': 'visa_debit', **changes}
        return self.client.post(reverse('checkout'), data=json.dumps(payload), content_type='application/json')

    def test_success_records_only_masked_test_card_and_grants_access(self):
        response = self.checkout(card_number='4000056655665556', cvc='123', expiry='12/35')
        self.assertTrue(response.json()['success'])
        payment = Payment.objects.get()
        self.assertEqual(payment.payment_details, {'mode': 'demo', 'method': 'debit_card',
                                                  'card_brand': 'Visa', 'card_last_four': '5556'})
        self.assertEqual(payment.payment_method, 'demo')
        self.assertEqual(payment.final_amount, 120)
        self.assertEqual(payment.commission_amount, 0)
        self.assertEqual(self.cart.items.count(), 0)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())
        self.assertNotIn('4000056655665556', json.dumps(list(ActivityLog.objects.values()), default=str))
        self.assertNotIn('card_number', json.dumps(payment.payment_details))
        self.assertContains(self.client.get(reverse('purchase_history')), payment.display_payment_method)
        self.assertContains(self.client.get(reverse('invoice', args=[payment.pk])), payment.display_payment_method)
        self.assertTrue(render_invoice_pdf(payment).read().startswith(b'%PDF'))

    def test_unknown_card_or_missing_method_leaves_cart_and_access_unchanged(self):
        for changes in [{'test_card': ''}, {'test_card': '4242424242424242'},
                        {'test_card': {'number': '4000056655665556'}}, {'payment_method': 'card'}]:
            with self.subTest(changes=changes):
                response = self.checkout(**changes)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(Payment.objects.exists())
                self.assertFalse(Enrollment.objects.exists())
                self.assertEqual(self.cart.items.count(), 1)

    def test_mastercard_uses_server_metadata_not_browser_last_four(self):
        self.assertTrue(self.checkout(test_card='mastercard_debit', card_last_four='9999').json()['success'])
        self.assertEqual(Payment.objects.get().display_payment_method, 'Tarjeta de débito · Mastercard •••• 8210')

    def test_bad_email_cannot_complete_order(self):
        self.assertEqual(self.checkout(email='invalid').status_code, 400)
        self.assertFalse(Payment.objects.exists())

    def test_free_order_needs_no_card(self):
        self.course.is_free, self.course.price = True, 0
        self.course.save()
        self.assertTrue(self.checkout(payment_method='free', test_card=None).json()['success'])
        self.assertEqual(Payment.objects.get().payment_method, 'free')

    @override_settings(DEMO_CHECKOUT=False)
    def test_test_card_never_enables_real_payments(self):
        self.assertEqual(self.checkout().status_code, 503)
        self.assertFalse(Payment.objects.exists())
        self.assertNotContains(self.client.get(reverse('cart')), 'id="cardNumber"')

    def test_duplicate_submit_does_not_create_second_purchase(self):
        self.assertTrue(self.checkout().json()['success'])
        self.assertFalse(self.checkout().json()['success'])
        self.assertEqual(Payment.objects.count(), 1)

    def test_non_object_payload_returns_400(self):
        for payload in ['[]', 'null', '"test"']:
            response = self.client.post(reverse('checkout'), data=payload, content_type='application/json')
            self.assertEqual(response.status_code, 400)

    def test_coupon_rounds_to_cents_before_recording_order_and_lines(self):
        self.course.price = Decimal('120.50')
        self.course.save()
        Coupon.objects.create(created_by=self.course.teacher, code='CENTAVOS', discount_type='percentage',
                              discount_value=25, max_uses=10, expires_at=timezone.now() + timedelta(days=1))
        response = self.checkout(coupon_code='CENTAVOS')
        self.assertEqual(response.json()['total'], '90.37')
        payment = Payment.objects.get()
        self.assertEqual(payment.discount_applied, Decimal('30.13'))
        self.assertEqual(payment.final_amount, Decimal('90.37'))
        self.assertEqual(payment.items.get().final_price, payment.final_amount)
