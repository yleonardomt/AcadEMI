from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from unittest.mock import patch
from datetime import timedelta
from contextlib import redirect_stdout
from io import StringIO
from urllib.parse import urlsplit
import re

from django.utils import timezone
from django.test import override_settings

from .models import User, Category, Course, Module, Lesson, Evaluation, LessonProgress, Certificate, Coupon, Cart, CartItem, ChatSession, ChatMessage, ChatFeedback, Payment, Enrollment, AssignmentSubmission
from .api.auth import make_token
from .utils.coupons import coupon_discount, find_coupon, save_coupon
from .forms import RegisterForm


@override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver', '192.0.2.10'], SITE_URL='http://192.0.2.10')
class ReviewDeploymentTests(SimpleTestCase):
    def test_health_check_responde_sin_base_de_datos(self):
        self.assertContains(self.client.get('/healthz/'), 'ok')

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

        Course.objects.filter(title=COURSES[-1]['title']).delete()
        with redirect_stdout(StringIO()):
            run(no_images=True, only_if_empty=True)
        self.assertEqual(Course.objects.count(), len(COURSES))
        self.assertEqual(Course.objects.exclude(image='').count(), len(COURSES))
        self.assertFalse(Course.objects.filter(is_free=True).exists())
        self.assertFalse(Course.objects.filter(price__lt=100).exists())
        self.assertFalse(Course.objects.filter(price__gt=150).exists())
        with redirect_stdout(StringIO()):
            run(no_images=True, only_if_empty=True)
        self.assertEqual(Course.objects.count(), len(COURSES))

    def test_mysql_playlist_has_individual_videos_and_survives_repeated_bootstrap(self):
        import json
        from pathlib import Path
        from scripts.load_emi_catalog import run
        videos = json.loads((Path(__file__).resolve().parent.parent / 'scripts/data/mysql_playlist.json').read_text())['videos']
        with redirect_stdout(StringIO()):
            run(no_images=True, only_if_empty=True)
            run(no_images=True, only_if_empty=True)
        course = Course.objects.get(title='Bases de datos MySQL: consultas y modelado')
        self.assertFalse(course.is_free)
        self.assertEqual(course.price, 150)
        lessons = Lesson.objects.filter(module__course=course, lesson_type='video', is_published=True).order_by('module__order', 'order')
        self.assertEqual(lessons.count(), 80)
        self.assertEqual(lessons.filter(is_free=True).count(), 1)
        self.assertEqual(list(lessons.values_list('video_url', flat=True)), [f'https://www.youtube.com/watch?v={v["id"]}' for v in videos])
        self.assertEqual(list(lessons.values_list('title', flat=True)), [v['title'] for v in videos])



class CertificateDownloadTests(TestCase):
    def test_download_is_generated_for_owner_and_denied_to_other_student(self):
        teacher = User.objects.create_user(username='teacher_cert', password='unused', role='teacher')
        owner = User.objects.create_user(username='owner_cert', password='unused', email_verified=True)
        other = User.objects.create_user(username='other_cert', password='unused', email_verified=True)
        course = Course.objects.create(title='Curso de prueba', description='Prueba', teacher=teacher,
                                       status='published', is_free=True)
        enrollment = Enrollment.objects.create(student=owner, course=course, status='completed', progress_percentage=100)
        certificate = Certificate.objects.create(enrollment=enrollment, certificate_code='CERTTEST001')
        self.client.force_login(owner)
        response = self.client.get(reverse('certificate_download', args=[certificate.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse('certificate_download', args=[certificate.pk])).status_code, 404)

    def test_assignment_file_is_available_only_to_student_and_teacher(self):
        teacher = User.objects.create_user(username='teacher_file', password='unused', role='teacher', email_verified=True)
        student = User.objects.create_user(username='student_file', password='unused', email_verified=True)
        stranger = User.objects.create_user(username='stranger_file', password='unused', email_verified=True)
        course = Course.objects.create(title='Curso de archivos', description='Prueba', teacher=teacher,
                                       status='published', is_free=True)
        module = Module.objects.create(course=course, title='Módulo')
        lesson = Lesson.objects.create(module=module, title='Práctica', lesson_type='assignment')
        submission = AssignmentSubmission.objects.create(lesson=lesson, student=student,
            file='assignments/revision-calculo-diferencial-para-ingenieria.pdf')
        for viewer in (student, teacher):
            self.client.force_login(viewer)
            response = self.client.get(reverse('assignment_download', args=[submission.pk]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
        self.client.force_login(stranger)
        self.assertEqual(self.client.get(reverse('assignment_download', args=[submission.pk])).status_code, 404)
        lesson.is_published = True
        lesson.save(update_fields=['is_published'])
        Enrollment.objects.create(student=student, course=course, status='in_progress')
        response = self.client.get(f'/api/v1/lessons/{lesson.pk}/',
                                   HTTP_AUTHORIZATION='Bearer ' + make_token(student))
        self.assertEqual(response.status_code, 200)
        parsed = urlsplit(response.json()['lesson']['submission']['file'])
        self.assertEqual(self.client.get(parsed.path + '?' + parsed.query).status_code, 200)

    def test_mobile_certificate_link_opens_a_pdf_and_expires_for_invalid_token(self):
        teacher = User.objects.create_user(username='teacher_mobile_pdf', password='unused', role='teacher')
        student = User.objects.create_user(username='student_mobile_pdf', password='unused', email_verified=True)
        course = Course.objects.create(title='Curso PDF móvil', description='Prueba', teacher=teacher,
                                       status='published', is_free=True)
        enrollment = Enrollment.objects.create(student=student, course=course, status='completed')
        certificate = Certificate.objects.create(enrollment=enrollment, certificate_code='MOBILEPDF001')
        response = self.client.get('/api/v1/certificates/', HTTP_AUTHORIZATION='Bearer ' + make_token(student))
        self.assertEqual(response.status_code, 200)
        url = response.json()['certificates'][0]['pdf']
        parsed = urlsplit(url)
        pdf = self.client.get(parsed.path + '?' + parsed.query)
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertEqual(self.client.get(f'/api/v1/downloads/certificate/{certificate.pk}/?t=invalid').status_code, 403)


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


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegistrationRegressionTests(TestCase):
    def registration_data(self):
        return {'role': 'student', 'email': 'registro@example.com', 'full_name': 'Ana Pérez',
                'password1': 'ClaveSegura1!', 'password2': 'ClaveSegura1!', 'accept_terms': 'on'}

    def test_registration_redirects_and_verification_link_activates_account(self):
        from django.core import mail
        import re
        response = self.client.post(reverse('register'), self.registration_data())
        self.assertRedirects(response, reverse('verify_pending'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(self.client.session['verification_email_sent'])
        link = re.search(r'https?://[^\s"<>]+/verify-email/[^\s"<>]+', mail.outbox[0].body).group()
        self.client.get(urlsplit(link).path)
        self.assertTrue(User.objects.get(email='registro@example.com').email_verified)

    @patch('academi.views.auth.send_verification_email', side_effect=TimeoutError('Proveedor no disponible'))
    def test_failed_delivery_does_not_break_registration_or_claim_delivery(self, send):
        response = self.client.post(reverse('register'), self.registration_data())
        self.assertRedirects(response, reverse('verify_pending'))
        self.assertFalse(self.client.session['verification_email_sent'])
        page = self.client.get(reverse('verify_pending'))
        self.assertContains(page, 'Reenviar correo de verificación')
        self.assertNotContains(page, 'El servicio de correo aceptó el envío')

    def test_terms_back_link_works_without_history(self):
        self.assertContains(self.client.get(reverse('terms')), 'href="/"')
        self.assertNotContains(self.client.get(reverse('terms')), 'javascript:history')


class EmailTransportTests(SimpleTestCase):
    @override_settings(BREVO_API_KEY='test-only', EMAIL_TIMEOUT=10)
    @patch('academi.email_backends.requests.post')
    def test_https_delivery_carries_html_and_pdf_and_checks_provider(self, post):
        from django.core.mail import EmailMultiAlternatives
        from academi.email_backends import BrevoBackend
        post.return_value.status_code = 201
        message = EmailMultiAlternatives('Prueba', 'Texto', 'AcadEMI <emisor@example.com>', ['destino@example.com'])
        message.attach_alternative('<p>Hola</p>', 'text/html')
        message.attach('certificado.pdf', b'%PDF-test', 'application/pdf')
        self.assertEqual(BrevoBackend().send_messages([message]), 1)
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['htmlContent'], '<p>Hola</p>')
        self.assertEqual(payload['attachment'][0]['name'], 'certificado.pdf')
        self.assertEqual(post.call_args.kwargs['timeout'], (3, 10))
        post.return_value.status_code = 401
        with self.assertRaises(RuntimeError):
            BrevoBackend().send_messages([message])
        self.assertEqual(BrevoBackend(fail_silently=True).send_messages([message]), 0)

    @override_settings(ON_RENDER=True)
    @patch('django.core.mail.backends.smtp.EmailBackend.open')
    def test_blocked_render_smtp_port_fails_without_waiting_for_network(self, smtp_open):
        from academi.email_backends import SafeSMTPBackend
        from django.core.exceptions import ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured):
            SafeSMTPBackend(port=587).open()
        smtp_open.assert_not_called()


class NavigationRegressionTests(TestCase):
    def test_public_student_teacher_and_admin_pages_render(self):
        from scripts.load_emi_catalog import run
        with redirect_stdout(StringIO()):
            run(no_images=True, only_if_empty=True)
        for name in ['home', 'catalog', 'categories', 'search_courses', 'login', 'register', 'terms', 'password_reset_request']:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        for role in ['student', 'teacher', 'admin']:
            user = User.objects.create_user(username=f'navigation_{role}', role=role, email_verified=True)
            self.client.force_login(user)
            pages = ['dashboard', 'profile', 'notifications', 'change_password', 'chatbot']
            if role == 'student':
                pages += ['my_courses', 'my_progress', 'my_grades', 'my_certificates', 'my_favorites', 'purchase_history', 'cart']
            elif role == 'teacher':
                pages += ['my_courses', 'create_course', 'mis_estudiantes', 'mis_resenas', 'teacher_coupons']
            else:
                pages += ['admin_users', 'admin_courses', 'admin_categories', 'admin_reports', 'admin_coupons', 'admin_payments', 'admin_certificates', 'admin_reports_generate']
            for name in pages:
                with self.subTest(role=role, page=name):
                    self.assertEqual(self.client.get(reverse(name)).status_code, 200)
            self.client.logout()


class CatalogPricingMigrationTests(TestCase):
    def test_new_catalog_prices_preserve_previous_orders_and_learning_progress(self):
        import importlib
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection
        from .models import PaymentItem
        teacher = User.objects.create_user(username='pricing_teacher', role='teacher')
        student = User.objects.create_user(username='pricing_student')
        course = Course.objects.create(title='Bases de datos MySQL: consultas y modelado',
            teacher=teacher, price=59, is_free=False, status='published')
        enrollment = Enrollment.objects.create(student=student, course=course,
            status='in_progress', progress_percentage=25)
        payment = Payment.objects.create(student=student, amount=59, final_amount=59,
            payment_method='demo', status='completed')
        line = PaymentItem.objects.create(payment=payment, course=course, price=59, final_price=59)
        migration = importlib.import_module('academi.migrations.0013_catalog_prices_range')
        migration.update_prices(apps, SimpleNamespace(connection=connection))
        course.refresh_from_db(); payment.refresh_from_db(); line.refresh_from_db(); enrollment.refresh_from_db()
        self.assertEqual(course.price, 150)
        self.assertEqual(payment.final_amount, 59)
        self.assertEqual(line.final_price, 59)
        self.assertEqual(enrollment.progress_percentage, 25)


class CatalogConsistencyTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='catalog_teacher', role='teacher',
            teacher_full_name='Marcela Valdez', email_verified=True)
        self.student = User.objects.create_user(username='catalog_student', email_verified=True)
        self.category = Category.objects.create(name='Sistemas digitales')
        self.other_category = Category.objects.create(name='Mecánica aplicada')
        self.featured = Course.objects.create(title='Bases de datos', teacher=self.teacher,
            category=self.category, status='published', is_featured=True, price=150)
        self.second = Course.objects.create(title='Redes', teacher=self.teacher,
            category=self.category, status='published', price=100)
        self.third = Course.objects.create(title='Termodinámica', teacher=self.teacher,
            category=self.other_category, status='published', price=120)
        self.draft = Course.objects.create(title='Curso privado', teacher=self.teacher,
            category=self.category, status='draft', price=130)
        Enrollment.objects.create(student=self.student, course=self.featured, status='in_progress')

    def test_catalog_renders_each_course_once_including_featured_and_popular(self):
        self.client.force_login(self.student)
        page = self.client.get(reverse('catalog'))
        ids = re.findall(r'data-course-id="(\d+)"', page.content.decode())
        self.assertCountEqual(ids, [str(c.pk) for c in [self.featured, self.second, self.third]])
        self.assertEqual(len(ids), len(set(ids)))
        controls = re.findall(r'\bid="([^"]+)"', page.content.decode())
        self.assertEqual(len(controls), len(set(controls)))
        self.assertEqual(page.context['total_courses'], len(ids))
        self.assertContains(page, 'Destacado')
        self.assertContains(page, 'Adquirido')
        self.assertNotContains(page, self.draft.title)

    def test_home_catalog_api_and_chatbot_use_current_published_total(self):
        from .views.chatbot import match_knowledge_base, build_platform_context
        for status, expected in [('draft', 3), ('published', 4), ('archived', 3)]:
            self.draft.status = status
            self.draft.save(update_fields=['status'])
            with self.subTest(status=status):
                self.assertEqual(self.client.get(reverse('home')).context['total_courses'], expected)
                self.assertEqual(self.client.get(reverse('catalog')).context['total_courses'], expected)
                self.assertEqual(self.client.get('/api/v1/courses/').json()['total'], expected)
                self.assertEqual(self.client.get('/api/v1/home/').json()['total_courses'], expected)
                self.assertEqual(build_platform_context()['total_courses'], expected)
                self.assertIn(f'Hay {expected} cursos publicados', match_knowledge_base('¿Cuántos cursos hay en total?'))

    def test_category_filter_keeps_global_total_and_shows_only_matching_courses(self):
        page = self.client.get(reverse('catalog'), {'category': self.category.pk})
        self.assertEqual(page.context['total_courses'], 3)
        self.assertEqual(page.context['courses'].count(), 2)
        self.assertCountEqual(re.findall(r'data-course-id="(\d+)"', page.content.decode()),
                              [str(self.featured.pk), str(self.second.pk)])
        self.assertEqual(self.client.get('/api/v1/courses/', {'category': self.category.pk}).json()['total'], 2)

    def test_invalid_category_never_returns_server_error(self):
        for value in ['abc', '-1', '0', '999999', '١٢', '1e3', '9' * 100]:
            with self.subTest(category=value):
                self.assertEqual(self.client.get(reverse('catalog'), {'category': value}).status_code, 404)
                self.assertIn(self.client.get('/api/v1/courses/', {'category': value}).status_code, [400, 404])

    def test_web_and_api_search_match_category_and_teacher_display_name(self):
        for term, expected in [(' Sistemas digitales ', [self.featured.pk, self.second.pk]),
                               ('Marcela Valdez', [self.featured.pk, self.second.pk, self.third.pk])]:
            with self.subTest(term=term):
                page = self.client.get(reverse('search_courses'), {'q': term})
                self.assertCountEqual(page.context['courses'].values_list('pk', flat=True), expected)
                api = self.client.get('/api/v1/courses/', {'q': term}).json()
                self.assertCountEqual([c['id'] for c in api['courses']], expected)

    def test_pending_and_cancelled_enrollments_do_not_make_course_popular(self):
        Enrollment.objects.create(student=self.student, course=self.second, status='pending')
        Enrollment.objects.create(student=self.student, course=self.third, status='cancelled')
        page = self.client.get(reverse('catalog'))
        self.assertEqual(page.context['bestseller_ids'], [self.featured.pk])
        self.assertEqual([c['id'] for c in self.client.get('/api/v1/home/').json()['bestsellers']], [self.featured.pk])

    def test_catalog_purchase_controls_are_available_only_to_students(self):
        for user, can_buy in [(self.student, True), (self.teacher, False),
                               (User.objects.create_user(username='catalog_admin', role='admin', email_verified=True), False)]:
            self.client.force_login(user)
            page = self.client.get(reverse('catalog'))
            self.assertEqual(f'id="cartBtn{self.second.pk}"' in page.content.decode(), can_buy)

    def test_mobile_pagination_does_not_repeat_courses_with_equal_sort_values(self):
        Course.objects.bulk_create([Course(title=f'Curso {i}', teacher=self.teacher,
            status='published', price=100) for i in range(25)])
        Course.objects.filter(status='published').update(created_at=timezone.now(), is_featured=False)
        expected = set(Course.objects.filter(status='published').values_list('pk', flat=True))
        for sort in ['featured', 'recent', 'popular', 'rating', 'price_asc', 'price_desc']:
            ids = []
            for page in [1, 2, 3]:
                data = self.client.get('/api/v1/courses/', {'sort': sort, 'page': page}).json()
                ids.extend(c['id'] for c in data['courses'])
            with self.subTest(sort=sort):
                self.assertEqual(set(ids), expected)
                self.assertEqual(len(ids), len(expected))

    def test_subject_recommendation_and_course_without_category_do_not_fail(self):
        from .views.chatbot import match_knowledge_base
        self.assertIn('Sistemas digitales', match_knowledge_base('Quiero cursos de sistemas'))
        uncategorized = Course.objects.create(title='Robótica autónoma', teacher=self.teacher,
                                              status='published', price=140)
        self.assertIn(uncategorized.title, match_knowledge_base('Quiero aprender robótica'))

    def test_web_and_mobile_promote_same_best_coupon_in_bolivianos(self):
        common = {'created_by': self.teacher, 'expires_at': timezone.now() + timedelta(days=3), 'max_uses': 100}
        Coupon.objects.create(code='FIXED40', course=self.featured, discount_type='fixed', discount_value=40, **common)
        percentage = Coupon.objects.create(code='PERCENT30', course=self.featured,
            discount_type='percentage', discount_value=30, **common)
        global_coupon = Coupon.objects.create(code='GLOBAL50', discount_type='fixed', discount_value=50, **common)
        for expected in [global_coupon, percentage]:
            web = self.client.get(reverse('catalog'))
            course = next(c for c in web.context['courses'] if c.pk == self.featured.pk)
            self.assertEqual(course.active_coupon.pk, expected.pk)
            api = self.client.get(f'/api/v1/courses/{self.featured.pk}/').json()
            self.assertEqual(api['course']['coupon']['code'], expected.code)
            global_coupon.is_active = False
            global_coupon.save(update_fields=['is_active'])
        self.featured.is_free = True
        self.featured.save(update_fields=['is_free'])
        api = self.client.get(f'/api/v1/courses/{self.featured.pk}/').json()
        self.assertIsNone(api['course']['coupon'])


class ReviewReadinessTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='review_teacher', role='teacher', email_verified=True)
        self.student = User.objects.create_user(username='review_student', email_verified=True)
        self.other = User.objects.create_user(username='review_other', email_verified=True)
        self.course = Course.objects.create(title='Álgebra', teacher=self.teacher, status='published', price=120)

    def test_chatbot_purchases_and_grades_belong_only_to_current_user(self):
        from .models import EvaluationResult
        from .views.chatbot import personal_answer
        Payment.objects.create(student=self.student, amount=120, final_amount=120,
                               status='completed', payment_method='demo', invoice_number='OWN-001')
        Payment.objects.create(student=self.other, amount=150, final_amount=150,
                               status='completed', payment_method='demo', invoice_number='OTHER-002')
        module = Module.objects.create(course=self.course, title='Módulo')
        lesson = Lesson.objects.create(module=module, title='Examen', lesson_type='exam')
        evaluation = Evaluation.objects.create(lesson=lesson, title='Examen de álgebra')
        own = Enrollment.objects.create(student=self.student, course=self.course, status='in_progress')
        other = Enrollment.objects.create(student=self.other, course=self.course, status='in_progress')
        EvaluationResult.objects.create(enrollment=own, evaluation=evaluation,
            score=8, total_points=10, passed=True, completed_at=timezone.now())
        EvaluationResult.objects.create(enrollment=other, evaluation=evaluation,
            score=3, total_points=10, passed=False, completed_at=timezone.now())
        purchases = personal_answer(self.student, '¿Cuál es el estado de mis compras?')
        self.assertIn('OWN-001', purchases)
        self.assertNotIn('OTHER-002', purchases)
        grades = personal_answer(self.student, 'Quiero consultar mis calificaciones')
        self.assertIn('8/10 puntos', grades)
        self.assertNotIn('3/10', grades)

    def test_evaluation_with_attempts_cannot_lose_answers_when_edited_on_web_or_api(self):
        from .models import EvaluationResult, QuestionEvaluation, QuestionOption, UserAnswer
        module = Module.objects.create(course=self.course, title='Módulo')
        lesson = Lesson.objects.create(module=module, title='Examen original', lesson_type='exam')
        evaluation = Evaluation.objects.create(lesson=lesson, title='Examen original')
        question = QuestionEvaluation.objects.create(evaluation=evaluation, text='2 + 2 = ?')
        option = QuestionOption.objects.create(question=question, text='4', is_correct=True)
        enrollment = Enrollment.objects.create(student=self.student, course=self.course, status='in_progress')
        result = EvaluationResult.objects.create(enrollment=enrollment, evaluation=evaluation,
            score=1, total_points=1, passed=True, completed_at=timezone.now())
        answer = UserAnswer.objects.create(evaluation_result=result, question=question,
            selected_option=option, is_correct=True, points_obtained=1)
        self.client.force_login(self.teacher)
        url = reverse('edit_lesson', args=[lesson.pk])
        self.assertContains(self.client.get(url), 'crea una nueva evaluación')
        self.assertRedirects(self.client.post(url, {'title': 'Reemplazo', 'lesson_type': 'exam'}), url)
        api = self.client.post(f'/api/v1/manage/lessons/{lesson.pk}/update/',
            data='{"title":"Reemplazo","type":"exam","questions":[]}', content_type='application/json',
            HTTP_AUTHORIZATION='Bearer ' + make_token(self.teacher))
        self.assertEqual(api.status_code, 409)
        lesson.refresh_from_db()
        answer.refresh_from_db()
        self.assertEqual(lesson.title, 'Examen original')
        self.assertEqual(answer.question_id, question.pk)
        self.assertEqual(answer.selected_option_id, option.pk)
        self.assertEqual(result.user_answers.count(), 1)

    def test_admin_has_working_course_edit_and_content_links(self):
        admin = User.objects.create_user(username='review_admin', role='admin', email_verified=True)
        self.client.force_login(admin)
        page = self.client.get(reverse('admin_courses'))
        for name in ['edit_course', 'manage_course']:
            url = reverse(name, args=[self.course.pk])
            self.assertContains(page, f'href="{url}"')
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_unverified_account_can_read_help_but_cannot_enter_protected_pages(self):
        pending = User.objects.create_user(username='review_pending', email_verified=False)
        self.client.force_login(pending)
        self.assertEqual(self.client.get(reverse('chatbot')).status_code, 200)
        self.assertEqual(self.client.get(reverse('terms')).status_code, 200)
        response = self.client.post(reverse('chatbot_send'), {'message': '¿Cuántos cursos hay en total?'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hay 1 curso publicado', response.json()['response'])
        for name in ['dashboard', 'profile', 'cart']:
            self.assertRedirects(self.client.get(reverse(name)), reverse('verify_pending'))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', SITE_URL='https://academi.example')
    def test_authentication_emails_have_real_navigation_instead_of_placeholder_links(self):
        from django.core import mail
        from .utils.email import send_verification_email, send_password_reset_email
        self.student.email = 'review@example.com'
        request = RequestFactory().get('/')
        send_verification_email(self.student, request)
        send_password_reset_email(self.student, request, 'https://academi.example/reset-password/token/')
        for message in mail.outbox:
            html = message.alternatives[0].content
            self.assertNotIn('href="#"', html)
            self.assertNotIn('soporte@academi.com', html)
            self.assertIn('https://academi.example/terminos/#privacidad', html)
            self.assertIn('https://academi.example/chatbot/', html)


class EvaluationAttemptJourneyTests(TestCase):
    def setUp(self):
        from .models import QuestionEvaluation, QuestionOption
        from django.core.cache import cache
        cache.clear()
        teacher = User.objects.create_user(username='attempt_teacher', role='teacher', email_verified=True)
        self.student = User.objects.create_user(username='attempt_student', email_verified=True)
        course = Course.objects.create(title='Curso de evaluación', teacher=teacher, status='published')
        module = Module.objects.create(course=course, title='Módulo')
        self.lesson = Lesson.objects.create(module=module, title='Examen', lesson_type='exam')
        self.evaluation = Evaluation.objects.create(lesson=self.lesson, title='Examen', max_attempts=2)
        self.enrollment = Enrollment.objects.create(student=self.student, course=course, status='enrolled')
        self.first = QuestionEvaluation.objects.create(evaluation=self.evaluation, text='Pregunta 1', points=2)
        self.second = QuestionEvaluation.objects.create(evaluation=self.evaluation, text='Pregunta 2', points=3)
        self.correct = QuestionOption.objects.create(question=self.first, text='Correcta', is_correct=True)
        self.wrong = QuestionOption.objects.create(question=self.second, text='Incorrecta', is_correct=False)
        self.client.force_login(self.student)

    def test_web_attempt_keeps_selected_answers_score_and_attempt_number(self):
        import json
        from .models import EvaluationResult
        self.client.get(reverse('quiz_view', args=[self.lesson.pk]))
        response = self.client.post(reverse('quiz_view', args=[self.lesson.pk]),
            json.dumps({'token': self.client.session['quiz_token'], 'answers': {
                f'q_{self.first.pk}': str(self.correct.pk), f'q_{self.second.pk}': str(self.wrong.pk)}}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        result = EvaluationResult.objects.get(pk=response.json()['result_id'])
        self.assertEqual((result.score, result.total_points, result.attempt_number), (2, 5, 1))
        self.assertFalse(result.passed)
        self.assertEqual(result.user_answers.count(), 2)
        first = result.user_answers.get(question=self.first)
        self.assertEqual(first.selected_option_id, self.correct.pk)
        self.assertEqual(first.points_obtained, 2)
        self.assertTrue(first.is_correct)
        self.assertFalse(result.user_answers.get(question=self.second).is_correct)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.progress_percentage, 0)

    def test_mobile_attempt_keeps_answers_and_cannot_exceed_attempt_limit(self):
        import json
        from .models import EvaluationResult
        auth = {'HTTP_AUTHORIZATION': 'Bearer ' + make_token(self.student)}
        for attempt in [1, 2]:
            start = self.client.post(f'/api/v1/quizzes/{self.lesson.pk}/start/', **auth).json()
            response = self.client.post(f'/api/v1/quizzes/{self.lesson.pk}/submit/', json.dumps({
                'token': start['token'], 'answers': {str(self.first.pk): self.correct.pk}}),
                content_type='application/json', **auth)
            self.assertEqual(response.status_code, 200)
            result = EvaluationResult.objects.get(pk=response.json()['result']['id'])
            self.assertEqual(result.attempt_number, attempt)
            self.assertEqual(result.user_answers.count(), 2)
            skipped = result.user_answers.get(question=self.second)
            self.assertIsNone(skipped.selected_option)
            self.assertEqual(skipped.points_obtained, 0)
        self.assertEqual(self.client.post(f'/api/v1/quizzes/{self.lesson.pk}/start/', **auth).status_code, 403)

    def test_wrong_question_option_never_earns_points(self):
        from .utils.evaluation_attempts import record_attempt
        result = record_attempt(self.enrollment, self.evaluation, {str(self.second.pk): self.correct.pk},
                                completed_at=timezone.now())
        self.assertEqual(result.score, 0)
        self.assertIsNone(result.user_answers.get(question=self.second).selected_option)

    def test_invalid_answer_payload_does_not_leave_partial_result(self):
        from .models import EvaluationResult
        from .utils.evaluation_attempts import record_attempt
        with self.assertRaises(ValueError):
            record_attempt(self.enrollment, self.evaluation, {str(self.first.pk): [self.correct.pk]},
                           completed_at=timezone.now())
        self.assertFalse(EvaluationResult.objects.filter(enrollment=self.enrollment).exists())

    def test_teacher_edit_keeps_actual_options_and_correct_answer(self):
        from .models import QuestionOption
        teacher = self.lesson.module.course.teacher
        self.client.force_login(teacher)
        response = self.client.post(reverse('edit_lesson', args=[self.lesson.pk]), {
            'title': 'Examen editado', 'description': 'Descripción actualizada', 'content': 'Selecciona una respuesta.',
            'time_limit': 15, 'passing_score': 70, 'max_attempts': 2,
            'question_1_text': '¿Qué instrucción consulta registros?',
            'question_1_option_0': 'SELECT', 'question_1_option_1': 'DELETE',
            'question_1_option_2': 'DROP', 'question_1_option_3': 'TRUNCATE',
            'question_1_correct_0': 'on',
        })
        self.assertRedirects(response, reverse('manage_course', args=[self.lesson.module.course_id]))
        question = self.evaluation.questions.get()
        options = list(QuestionOption.objects.filter(question=question).order_by('pk'))
        self.assertEqual([o.text for o in options], ['SELECT', 'DELETE', 'DROP', 'TRUNCATE'])
        self.assertEqual([o.is_correct for o in options], [True, False, False, False])


class ProfileJourneyConsistencyTests(TestCase):
    def test_long_combined_profile_name_is_rejected_without_changing_stored_name(self):
        user = User.objects.create_user(username='profile_length', email='length@example.com',
            email_verified=True, first_name='Ana', last_name='Quispe', full_name='Ana Quispe')
        self.client.force_login(user)
        response = self.client.post(reverse('profile'), {
            'username': user.username, 'email': user.email, 'first_name': 'A' * 150, 'last_name': 'B' * 60,
        })
        self.assertContains(response, 'El nombre completo no puede superar 200 caracteres.')
        user.refresh_from_db()
        self.assertEqual(user.full_name, 'Ana Quispe')
        import json
        response = self.client.patch('/api/v1/me/', data=json.dumps({'first_name': 'A' * 150, 'last_name': 'B' * 60}),
            content_type='application/json', HTTP_AUTHORIZATION='Bearer '+make_token(user))
        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.full_name, 'Ana Quispe')

    def test_updating_other_profile_fields_does_not_erase_name(self):
        user = User.objects.create_user(username='profile_phone', email='profile@example.com',
            email_verified=True, first_name='Ana', last_name='Quispe', full_name='Ana Quispe')
        self.client.force_login(user)
        response = self.client.post(reverse('profile'), {
            'username': user.username, 'email': user.email, 'phone': '79123456', 'bio': 'Otra biografía',
        })
        self.assertRedirects(response, reverse('profile'))
        user.refresh_from_db()
        self.assertEqual(user.get_full_name(), 'Ana Quispe')
        self.assertEqual(user.full_name, 'Ana Quispe')

    def test_web_profile_changes_name_consistently_for_student_and_teacher(self):
        for role in ['student', 'teacher']:
            with self.subTest(role=role):
                user = User.objects.create_user(username='profile_'+role, role=role,
                    email=role+'@example.com', email_verified=True, first_name='Nombre anterior',
                    full_name='Nombre anterior', teacher_full_name='Nombre anterior')
                self.client.force_login(user)
                page = self.client.get(reverse('profile'))
                self.assertContains(page, 'name="first_name"')
                self.assertContains(page, 'name="last_name"')
                response = self.client.post(reverse('profile'), {
                    'username': user.username, 'email': user.email,
                    'first_name': 'Ana María', 'last_name': 'Quispe', 'phone': '79123456', 'bio': 'Perfil actualizado',
                })
                self.assertRedirects(response, reverse('profile'))
                user.refresh_from_db()
                self.assertEqual(user.get_full_name(), 'Ana María Quispe')
                canonical = user.teacher_full_name if role == 'teacher' else user.full_name
                self.assertEqual(canonical, 'Ana María Quispe')
                mobile = self.client.get('/api/v1/me/', HTTP_AUTHORIZATION='Bearer '+make_token(user))
                self.assertEqual(mobile.json()['user']['name'], 'Ana María Quispe')

    def test_mobile_name_change_does_not_duplicate_previous_surname_in_web(self):
        user = User.objects.create_user(username='profile_mobile', email_verified=True,
            first_name='Ana', last_name='Anterior', full_name='Ana Anterior')
        response = self.client.patch('/api/v1/me/', data='{"name":"Lucía Nueva"}',
            content_type='application/json', HTTP_AUTHORIZATION='Bearer '+make_token(user))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['name'], 'Lucía Nueva')
        user.refresh_from_db()
        self.assertEqual(user.get_full_name(), 'Lucía Nueva')
        response = self.client.patch('/api/v1/me/', data='{"first_name":"Ana","last_name":""}',
            content_type='application/json', HTTP_AUTHORIZATION='Bearer '+make_token(user))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['name'], 'Ana')

    def test_legacy_full_name_is_available_for_editing_and_role_name_is_respected(self):
        from .api.serializers import display_name
        user = User.objects.create_user(username='profile_legacy', email_verified=True,
                                       full_name='Nombre vigente', teacher_full_name='Antiguo docente')
        self.client.force_login(user)
        page = self.client.get(reverse('profile'))
        self.assertEqual(page.context['form'].initial['first_name'], 'Nombre vigente')
        self.assertEqual(display_name(user), 'Nombre vigente')
