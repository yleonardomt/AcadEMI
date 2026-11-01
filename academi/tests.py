from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from unittest.mock import patch
from datetime import timedelta
from contextlib import redirect_stdout
from io import StringIO

from django.utils import timezone
from django.test import override_settings

from .models import User, Category, Course, Module, Lesson, Evaluation, LessonProgress, Certificate, Coupon, Cart, CartItem, ChatSession, ChatMessage, ChatFeedback, Payment, Enrollment
from .api.auth import make_token
from .utils.coupons import coupon_discount, find_coupon, save_coupon
from .forms import RegisterForm


@override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver', '192.0.2.10'], SITE_URL='http://192.0.2.10')
class ReviewDeploymentTests(SimpleTestCase):
    def test_404_web_y_api_tienen_respuesta_correcta(self):
        web = self.client.get('/pagina-inexistente/')
        api = self.client.get('/api/v1/ruta-inexistente/')
        self.assertEqual(web.status_code, 404)
        self.assertContains(web, 'No encontramos esta página', status_code=404)
        self.assertEqual(api.status_code, 404)
        self.assertEqual(api.json()['message'], 'Página no encontrada.')

    def test_500_no_requiere_sesion_ni_base_de_datos(self):
        from core.error_views import server_error
        response = server_error(RequestFactory().get('/'))
        self.assertContains(response, 'No pudimos cargar la página', status_code=500)

    def test_enlace_de_recuperacion_usa_site_url(self):
        from .utils.email import generate_reset_link
        user = User(pk=1, username='test', email='test@example.com', password='hash')
        link = generate_reset_link(user, RequestFactory().get('/', HTTP_HOST='testserver'))
        self.assertTrue(link.startswith('http://192.0.2.10/reset-password/'))


class CatalogBootstrapTests(TestCase):
    def test_initial_catalog_has_bundled_images_and_is_idempotent(self):
        from scripts.load_emi_catalog import COURSES, run
        with redirect_stdout(StringIO()):
            run(no_images=True, only_if_empty=True)
        self.assertEqual(Course.objects.count(), len(COURSES))
        self.assertEqual(Course.objects.exclude(image='').count(), len(COURSES))
        with redirect_stdout(StringIO()):
            run(no_images=True, only_if_empty=True)
        self.assertEqual(Course.objects.count(), len(COURSES))


@override_settings(DEMO_CHECKOUT=False)
class ChatbotAndCheckoutTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='alumna', password='clave-segura', email='a@example.com', email_verified=True)
        self.teacher = User.objects.create_user(username='profe', password='clave-segura', role='teacher', email_verified=True)
        self.category = Category.objects.create(name='Programación')
        self.course = Course.objects.create(title='Python inicial', description='Curso', category=self.category,
                                            teacher=self.teacher, status='published', price='50.00')

    def test_catalog_answer_uses_published_course_and_current_price(self):
        with patch('academi.views.chatbot.get_ai_response') as ai:
            response = self.client.post(reverse('chatbot_send'), {'message': '¿Qué cursos hay disponibles?'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Python inicial', response.json()['response'])
        self.assertIn('Bs. 50.00', response.json()['response'])
        ai.assert_not_called()

    def test_personal_progress_uses_only_signed_in_user_data(self):
        Enrollment.objects.create(student=self.student, course=self.course, status='in_progress', progress_percentage=35)
        self.client.force_login(self.student)
        with patch('academi.views.chatbot.get_ai_response') as ai:
            response = self.client.post(reverse('chatbot_send'), {'message': '¿Cuál es mi progreso?'})
        self.assertIn('Python inicial: 35%', response.json()['response'])
        ai.assert_not_called()

    def test_payment_question_does_not_promise_an_unverified_charge(self):
        response = self.client.post(reverse('chatbot_send'), {'message': '¿Puedo pagar con QR?'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('aún no están habilitadas', response.json()['response'])

    def test_mobile_chat_uses_same_answer_and_persists_it(self):
        response = self.client.post('/api/v1/chatbot/send/', data='{"message":"¿Qué cursos hay disponibles?"}',
                                    content_type='application/json',
                                    HTTP_AUTHORIZATION='Bearer ' + make_token(self.student))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Python inicial', response.json()['reply']['message'])
        self.assertEqual(ChatMessage.objects.filter(session__user=self.student).count(), 2)

    def test_chat_history_feedback_and_message_limit(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('chatbot_send'), {'message': 'Hola'})
        self.assertEqual(response.status_code, 200)
        message_id = response.json()['message_id']
        self.assertContains(self.client.get(reverse('chatbot')), 'Hola')
        self.assertEqual(self.client.post(reverse('chatbot_feedback'), {'message_id': message_id, 'rating': 5}).status_code, 200)
        self.assertEqual(ChatFeedback.objects.get(message_id=message_id).rating, 5)
        too_long = self.client.post(reverse('chatbot_send'), {'message': 'a' * 1001})
        self.assertEqual(too_long.status_code, 400)
        self.assertEqual(ChatMessage.objects.filter(session__user=self.student).count(), 2)

    def test_feedback_rejects_other_users_message(self):
        session = ChatSession.objects.create(user=self.teacher)
        message = ChatMessage.objects.create(session=session, sender='bot', message='Privado')
        self.client.force_login(self.student)
        response = self.client.post(reverse('chatbot_feedback'), {'message_id': message.id, 'rating': 1})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ChatFeedback.objects.exists())

    def test_paid_checkout_is_blocked_on_web_and_api(self):
        cart = Cart.objects.create(student=self.student)
        CartItem.objects.create(cart=cart, course=self.course)
        self.client.force_login(self.student)
        web = self.client.post(reverse('checkout'), data='{"full_name":"Alumna", "email":"a@example.com"}',
                               content_type='application/json')
        self.assertEqual(web.status_code, 503)
        api = self.client.post('/api/v1/checkout/', data='{"full_name":"Alumna", "email":"a@example.com"}',
                               content_type='application/json', HTTP_AUTHORIZATION='Bearer ' + make_token(self.student))
        self.assertEqual(api.status_code, 503)
        self.assertFalse(Payment.objects.exists())
        self.assertFalse(Enrollment.objects.exists())

    def test_free_course_enrollment_still_works(self):
        self.course.is_free = True
        self.course.price = 0
        self.course.save()
        cart = Cart.objects.create(student=self.student)
        CartItem.objects.create(cart=cart, course=self.course)
        self.client.force_login(self.student)
        with patch('academi.views.payments.send_purchase_confirmation_email'):
            response = self.client.post(reverse('checkout'), data='{"full_name":"Alumna", "email":"a@example.com"}',
                                        content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(Payment.objects.get().payment_method, 'free')
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_teacher_publication_requires_admin_approval(self):
        module = Module.objects.create(course=self.course, title='Inicio')
        Lesson.objects.create(module=module, title='Introducción', content='Contenido')
        self.course.status = 'draft'
        self.course.save()
        self.client.force_login(self.teacher)
        self.client.post(reverse('publish_course', args=[self.course.id]))
        self.course.refresh_from_db()
        self.assertEqual(self.course.status, 'pending')
        admin = User.objects.create_user(username='admin', password='clave-segura', role='admin')
        self.client.force_login(admin)
        self.client.post(reverse('admin_course_moderate', args=[self.course.id, 'approve']))
        self.course.refresh_from_db()
        self.assertEqual(self.course.status, 'published')
        self.assertEqual(self.course.approved_by, admin)

    def test_teacher_edit_returns_published_course_to_review(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('edit_course', args=[self.course.id]), {
            'title': 'Python avanzado', 'description': 'Descripción actualizada',
            'level': 'beginner', 'price': '60.00',
        })
        self.assertEqual(response.status_code, 302)
        self.course.refresh_from_db()
        self.assertEqual(self.course.status, 'pending')
        self.assertFalse(self.course.is_featured)

    def test_course_with_students_is_archived_and_lessons_preserved(self):
        module = Module.objects.create(course=self.course, title='Inicio')
        lesson = Lesson.objects.create(module=module, title='Introducción', content='Contenido')
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('delete_course', args=[self.course.id]))
        self.assertTrue(response.json()['success'])
        self.course.refresh_from_db()
        self.assertEqual(self.course.status, 'archived')
        self.client.post(reverse('delete_lesson', args=[lesson.id]))
        self.assertTrue(Lesson.objects.filter(pk=lesson.id).exists())
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_coupon_code_unique_and_discount_limited_to_its_course(self):
        other = Course.objects.create(title='Otro curso', description='Otro', teacher=self.teacher,
                                      category=self.category, status='published', price='30.00')
        cart = Cart.objects.create(student=self.student)
        item1 = CartItem.objects.create(cart=cart, course=self.course)
        item2 = CartItem.objects.create(cart=cart, course=other)
        data = {'code': 'Python10', 'discount_type': 'percentage', 'discount_value': '10',
                'max_uses': '5', 'expires_at': (timezone.now() + timedelta(days=7)).isoformat()}
        coupon, problem = save_coupon(self.teacher, data, course=self.course)
        self.assertIsNone(problem)
        duplicate, problem = save_coupon(self.teacher, {**data, 'code': 'python10'}, course=other)
        self.assertIsNone(duplicate)
        self.assertIn('existe', problem)
        self.assertEqual(coupon_discount(coupon, [item1, item2]), 5)
        self.assertIsNotNone(find_coupon('PYTHON10', [item2])[1])

    def test_free_enrollment_does_not_consume_first_paid_purchase_discount(self):
        self.student.email = 'alumna@est.emi.edu.bo'
        self.student.save()
        self.course.is_free = True
        self.course.price = 0
        self.course.save()
        CartItem.objects.create(cart=Cart.objects.create(student=self.student), course=self.course)
        self.client.force_login(self.student)
        with patch('academi.views.payments.send_purchase_confirmation_email'):
            self.client.post(reverse('checkout'), data='{"full_name":"Alumna", "email":"alumna@est.emi.edu.bo"}',
                             content_type='application/json')
        from .models import is_eligible_for_emi_first_purchase_discount
        self.assertTrue(is_eligible_for_emi_first_purchase_discount(self.student))

    def test_mobile_checkout_rejects_course_removed_from_catalog(self):
        self.course.is_free = True
        self.course.price = 0
        self.course.status = 'pending'
        self.course.save()
        CartItem.objects.create(cart=Cart.objects.create(student=self.student), course=self.course)
        response = self.client.post('/api/v1/checkout/',
                                    data='{"full_name":"Alumna", "email":"a@example.com"}',
                                    content_type='application/json',
                                    HTTP_AUTHORIZATION='Bearer ' + make_token(self.student))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Enrollment.objects.exists())

    def test_admin_cannot_delete_teacher_with_courses(self):
        admin = User.objects.create_user(username='admin', password='clave-segura', role='admin')
        self.client.force_login(admin)
        self.client.post(reverse('admin_user_delete', args=[self.teacher.id]))
        self.assertTrue(User.objects.filter(pk=self.teacher.id).exists())
        self.assertTrue(Course.objects.filter(pk=self.course.id).exists())

    def test_mobile_teacher_cannot_publish_or_feature_without_admin(self):
        module = Module.objects.create(course=self.course, title='Inicio')
        Lesson.objects.create(module=module, title='Introducción', content='Contenido')
        self.course.status = 'draft'
        self.course.save()
        auth = {'HTTP_AUTHORIZATION': 'Bearer ' + make_token(self.teacher)}
        response = self.client.post(f'/api/v1/manage/courses/{self.course.id}/update/',
                                    data='{"title":"Python nuevo","description":"Contenido","level":"beginner","price":"50","is_featured":true}',
                                    content_type='application/json', **auth)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(f'/api/v1/manage/courses/{self.course.id}/publish/', **auth)
        self.assertEqual(response.status_code, 200)
        self.course.refresh_from_db()
        self.assertEqual(self.course.status, 'pending')
        self.assertFalse(self.course.is_featured)

    @override_settings(DEMO_CHECKOUT=True)
    def test_demo_purchase_records_order_access_and_dashboard_figures(self):
        CartItem.objects.create(cart=Cart.objects.create(student=self.student), course=self.course)
        self.client.force_login(self.student)
        with patch('academi.views.payments.send_purchase_confirmation_email') as email:
            response = self.client.post(reverse('checkout'),
                                        data='{"full_name":"Alumna", "email":"a@example.com"}',
                                        content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['demo'])
        payment = Payment.objects.get()
        self.assertEqual(payment.payment_method, 'demo')
        self.assertEqual(payment.final_amount, 50)
        self.assertTrue(payment.invoice_number.startswith('ORD-'))
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course, payment_status='demo').exists())
        email.assert_not_called()
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse('course_stats', args=[self.course.id])).status_code, 200)
        from .utils.course_stats import compute_course_stats
        self.assertEqual(compute_course_stats(self.course)['sales'], 1)
        with override_settings(DEMO_CHECKOUT=False):
            self.assertEqual(compute_course_stats(self.course)['sales'], 0)

    @override_settings(DEMO_CHECKOUT=True)
    def test_demo_coupon_updates_usage_and_net_line_amount(self):
        coupon, problem = save_coupon(self.teacher, {
            'code': 'OFERTA10', 'discount_type': 'percentage', 'discount_value': '10',
            'max_uses': '1', 'expires_at': (timezone.now() + timedelta(days=1)).isoformat(),
        }, course=self.course)
        self.assertIsNone(problem)
        CartItem.objects.create(cart=Cart.objects.create(student=self.student), course=self.course)
        self.client.force_login(self.student)
        response = self.client.post(reverse('checkout'),
                                    data='{"full_name":"Alumna", "email":"a@example.com", "coupon_code":"OFERTA10"}',
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        coupon.refresh_from_db()
        self.assertEqual(coupon.demo_used_count, 1)
        self.assertEqual(coupon.used_count, 0)
        self.assertFalse(coupon.is_valid())
        payment = Payment.objects.get()
        self.assertEqual(payment.final_amount, 45)
        self.assertEqual(payment.items.get().final_price, 45)

    @override_settings(DEMO_CHECKOUT=True)
    def test_mobile_demo_purchase_grants_course_access(self):
        CartItem.objects.create(cart=Cart.objects.create(student=self.student), course=self.course)
        response = self.client.post('/api/v1/checkout/',
                                    data='{"full_name":"Alumna", "email":"a@example.com"}',
                                    content_type='application/json',
                                    HTTP_AUTHORIZATION='Bearer ' + make_token(self.student))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['demo'])
        self.assertEqual(Payment.objects.get().payment_method, 'demo')
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    @override_settings(DEMO_CHECKOUT=True)
    def test_fully_discounted_paid_order_counts_as_sale(self):
        coupon, problem = save_coupon(self.teacher, {
            'code': 'TOTAL', 'discount_type': 'percentage', 'discount_value': '100',
            'max_uses': '1', 'expires_at': (timezone.now() + timedelta(days=1)).isoformat(),
        }, course=self.course)
        self.assertIsNone(problem)
        CartItem.objects.create(cart=Cart.objects.create(student=self.student), course=self.course)
        self.client.force_login(self.student)
        response = self.client.post(reverse('checkout'),
                                    data='{"full_name":"Alumna", "email":"a@example.com", "coupon_code":"TOTAL"}',
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        from .utils.course_stats import compute_course_stats
        self.assertEqual(Payment.objects.get().final_amount, 0)
        self.assertEqual(compute_course_stats(self.course)['sales'], 1)

# Create your tests here.


class AuthExperienceTests(TestCase):
    def test_login_and_register_show_password_controls(self):
        self.assertContains(self.client.get(reverse('login')), 'data-password-toggle="id_password"')
        response = self.client.get(reverse('register'))
        self.assertContains(response, 'data-password-toggle="id_password1"')
        self.assertContains(response, '8 caracteres como mínimo')
        self.assertContains(response, 'Una mayúscula')

    def test_student_registration_saves_profile_information(self):
        form = RegisterForm(data={
            'role': 'student', 'email': 'Nueva@Example.com', 'full_name': 'Ana Pérez',
            'university': 'EMI', 'career': 'Ingeniería Civil', 'city': 'La Paz',
            'password1': 'ClaveSegura1!', 'password2': 'ClaveSegura1!', 'accept_terms': 'on',
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, 'nueva@example.com')
        self.assertEqual(user.full_name, 'Ana Pérez')
        self.assertEqual(user.university, 'EMI')
        self.assertEqual(user.career, 'Ingeniería Civil')
        self.assertEqual(user.city, 'La Paz')

    def test_teacher_registration_saves_professional_information(self):
        form = RegisterForm(data={
            'role': 'teacher', 'email': 'profe@example.com', 'teacher_full_name': 'Luis Rojas',
            'specialty': 'Ingeniería Mecatrónica', 'experience_years': '5-10',
            'institution': 'AcadEMI', 'teacher_bio': 'Docente de automatización.',
            'password1': 'ClaveSegura1!', 'password2': 'ClaveSegura1!', 'accept_terms': 'on',
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.teacher_full_name, 'Luis Rojas')
        self.assertEqual(user.specialty, 'Ingeniería Mecatrónica')
        self.assertEqual(user.experience_years, '5-10')
        self.assertEqual(user.institution, 'AcadEMI')
        self.assertEqual(user.teacher_bio, 'Docente de automatización.')


class LearningCompletionTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='alumno', password='clave-segura', role='student', email_verified=True)
        teacher = User.objects.create_user(username='docente', password='clave-segura', role='teacher', email_verified=True)
        category = Category.objects.create(name='Ingeniería Civil')
        self.course = Course.objects.create(title='Resistencia de materiales', description='Curso', category=category,
                                            teacher=teacher, status='published', is_free=True)
        module = Module.objects.create(course=self.course, title='Módulo 1')
        self.quiz = Lesson.objects.create(module=module, title='Examen final', lesson_type='exam', is_published=True)
        self.assignment = Lesson.objects.create(module=module, title='Práctica', lesson_type='assignment', is_published=True)
        Evaluation.objects.create(lesson=self.quiz, title='Examen final')
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course, status='enrolled')

    def test_examen_no_se_completa_sin_aprobar_en_web_y_api(self):
        self.client.force_login(self.student)
        web = self.client.post(reverse('mark_lesson_complete', args=[self.quiz.id]))
        api = self.client.post(f'/api/v1/lessons/{self.quiz.id}/complete/',
                               HTTP_AUTHORIZATION='Bearer ' + make_token(self.student))
        self.assertEqual((web.status_code, api.status_code), (403, 403))
        self.assertFalse(LessonProgress.objects.filter(lesson=self.quiz, completed=True).exists())
        self.assertFalse(Certificate.objects.exists())

    def test_tarea_no_se_completa_sin_entregar_en_web_y_api(self):
        self.client.force_login(self.student)
        web = self.client.post(reverse('mark_lesson_complete', args=[self.assignment.id]))
        api = self.client.post(f'/api/v1/lessons/{self.assignment.id}/complete/',
                               HTTP_AUTHORIZATION='Bearer ' + make_token(self.student))
        self.assertEqual((web.status_code, api.status_code), (403, 403))
        self.assertFalse(LessonProgress.objects.filter(lesson=self.assignment, completed=True).exists())
        self.assertFalse(Certificate.objects.exists())
