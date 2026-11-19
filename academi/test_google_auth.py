import json
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from google.auth import crypt, jwt

from .models import Course, Enrollment, GoogleIdentity, User
from .utils.google_oauth import GoogleLoginError, exchange_code
from .views.google_auth import FLOW_KEY, SIGNUP_KEY

CONFIG = {'GOOGLE_OAUTH_CLIENT_ID': 'test-client.apps.googleusercontent.com',
          'GOOGLE_OAUTH_CLIENT_SECRET': 'test-oauth-secret', 'SITE_URL': 'https://academi.example',
          'EMAIL_BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}


@override_settings(**CONFIG)
class GoogleTokenTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
        cls.signer = crypt.RSASigner.from_string(pem, key_id='test-key')
        cls.public = key.public_key().public_bytes(serialization.Encoding.PEM,
                                                  serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    def claims(self, **changes):
        return {'iss': 'https://accounts.google.com', 'aud': CONFIG['GOOGLE_OAUTH_CLIENT_ID'],
                'sub': 'google-subject', 'email': 'student@gmail.com', 'email_verified': True,
                'name': 'Ana Quispe', 'nonce': 'nonce-test', 'iat': int(time.time()) - 5,
                'exp': int(time.time()) + 300, **changes}

    def exchange(self, claims, nonce='nonce-test', signer=None):
        token = jwt.encode(signer or self.signer, claims).decode()
        certificates = SimpleNamespace(status=200, data=json.dumps({'test-key': self.public}).encode())
        with patch('academi.utils.google_oauth.requests.post') as post, \
                patch('academi.utils.google_oauth._BoundedRequest', return_value=Mock(return_value=certificates)):
            post.return_value.json.return_value = {'id_token': token}
            result = exchange_code('one-time-code', nonce, 'pkce-verifier', 'https://academi.example/auth/google/callback/')
            self.assertEqual(post.call_args.args[0], 'https://oauth2.googleapis.com/token')
            self.assertEqual(post.call_args.kwargs['data']['code_verifier'], 'pkce-verifier')
            self.assertEqual(post.call_args.kwargs['timeout'], 10)
            return result

    def test_real_signature_audience_issuer_and_nonce_are_verified(self):
        identity = self.exchange(self.claims())
        self.assertEqual(identity['subject'], 'google-subject')
        self.assertTrue(identity['authoritative'])
        for changes in [{'aud': 'other-client'}, {'iss': 'https://fake.example'},
                        {'exp': int(time.time()) - 120}, {'nonce': 'wrong-nonce'},
                        {'azp': 'another-client'}, {'email_verified': False}, {'email': 'invalid-address'}]:
            with self.subTest(changes=changes), self.assertRaises(GoogleLoginError):
                self.exchange(self.claims(**changes))

    def test_signature_from_another_key_is_rejected(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
        signer = crypt.RSASigner.from_string(pem, key_id='test-key')
        with self.assertRaises(GoogleLoginError):
            self.exchange(self.claims(), signer=signer)

    def test_external_email_requires_local_verification_but_workspace_does_not(self):
        self.assertFalse(self.exchange(self.claims(email='student@external.example'))['authoritative'])
        self.assertTrue(self.exchange(self.claims(email='student@school.example', hd='school.example'))['authoritative'])

    def test_google_timeout_and_missing_token_have_controlled_error(self):
        with patch('academi.utils.google_oauth.requests.post', side_effect=requests.Timeout), self.assertRaises(GoogleLoginError):
            exchange_code('code', 'nonce', 'verifier', 'https://academi.example/auth/google/callback/')
        with patch('academi.utils.google_oauth.requests.post') as post, self.assertRaises(GoogleLoginError):
            post.return_value.json.return_value = {}
            exchange_code('code', 'nonce', 'verifier', 'https://academi.example/auth/google/callback/')


@override_settings(**CONFIG)
class GoogleFlowTests(TestCase):
    def setUp(self):
        cache.clear()

    def start(self, **data):
        response = self.client.post(reverse('google_start'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.url).hostname, 'accounts.google.com')
        return self.client.session[FLOW_KEY], parse_qs(urlsplit(response.url).query)

    def callback(self, identity=None, **start):
        flow, _ = self.start(**start)
        identity = identity or {'subject': 'new-google-subject', 'email': 'new@gmail.com',
                                'name': 'Ana Quispe', 'authoritative': True}
        with patch('academi.views.google_auth.exchange_code', return_value=identity) as exchange:
            response = self.client.get(reverse('google_callback'), {'state': flow['state'], 'code': 'code'})
        exchange.assert_called_once_with('code', flow['nonce'], flow['verifier'], flow['redirect_uri'])
        return response

    def complete(self, **changes):
        data = {'role': 'student', 'full_name': 'Ana Quispe', 'accept_terms': 'on', **changes}
        return self.client.post(reverse('google_complete'), data)

    def test_google_buttons_are_present_without_exposing_secret(self):
        for page in ['login', 'register']:
            response = self.client.get(reverse(page))
            self.assertContains(response, 'Continuar con Google')
            self.assertContains(response, reverse('google_start'))
            self.assertContains(response, 'Al continuar, aceptas los')
            self.assertNotContains(response, CONFIG['GOOGLE_OAUTH_CLIENT_SECRET'])

    @override_settings(GOOGLE_OAUTH_CLIENT_ID='', GOOGLE_OAUTH_CLIENT_SECRET='')
    def test_missing_configuration_does_not_break_password_login(self):
        self.assertNotContains(self.client.get(reverse('login')), 'Continuar con Google')
        self.assertRedirects(self.client.post(reverse('google_start')), reverse('login'))

    def test_start_requires_post_and_csrf_and_uses_pkce(self):
        self.assertEqual(self.client.get(reverse('google_start')).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(reverse('google_start')).status_code, 403)
        flow, params = self.start(intent='register', role='teacher', next='https://attacker.example/')
        self.assertEqual(params['scope'], ['openid email profile'])
        self.assertEqual(params['code_challenge_method'], ['S256'])
        self.assertEqual(params['redirect_uri'], ['https://academi.example/auth/google/callback/'])
        self.assertEqual(flow['next'], '')
        self.assertEqual(flow['role'], 'teacher')
        self.assertEqual(params['state'], [flow['state']])
        self.assertNotIn('client_secret', params)

    def test_oauth_session_cookie_allows_top_level_cross_site_callback(self):
        response = self.client.post(reverse('google_start'), {'intent': 'login'})
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertEqual(cookie['samesite'], 'Lax')
        self.assertTrue(cookie['httponly'])
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Strict')

    def test_invalid_expired_or_replayed_state_cannot_authenticate(self):
        flow, _ = self.start()
        with patch('academi.views.google_auth.exchange_code') as exchange:
            self.assertEqual(self.client.get(reverse('google_callback'), {'state': 'wrong', 'code': 'code'}).url, reverse('login'))
            exchange.assert_not_called()
        session = self.client.session
        session[FLOW_KEY] = {**flow, 'issued': time.time() - 601}
        session.save()
        with patch('academi.views.google_auth.exchange_code') as exchange:
            self.client.get(reverse('google_callback'), {'state': flow['state'], 'code': 'code'})
            exchange.assert_not_called()
        self.callback(intent='register', role='teacher')
        self.assertNotIn(FLOW_KEY, self.client.session)
        with patch('academi.views.google_auth.exchange_code') as exchange:
            self.client.get(reverse('google_callback'), {'state': flow['state'], 'code': 'code'})
            exchange.assert_not_called()
        self.assertFalse(User.objects.filter(email='new@gmail.com').exists())

    def test_google_cancellation_and_provider_error_return_to_working_forms(self):
        flow, _ = self.start(intent='register')
        self.assertRedirects(self.client.get(reverse('google_callback'), {'state': flow['state'], 'error': 'access_denied'}), reverse('register'))
        flow, _ = self.start()
        with patch('academi.views.google_auth.exchange_code', side_effect=GoogleLoginError('No pudimos verificar tu cuenta.')):
            self.assertRedirects(self.client.get(reverse('google_callback'), {'state': flow['state'], 'code': 'code'}), reverse('login'))

    def test_new_google_student_enters_directly_without_captcha_or_second_form(self):
        self.assertRedirects(self.callback(next='/my-courses/'), reverse('my_courses'))
        user = User.objects.get(email='new@gmail.com')
        self.assertEqual(user.role, 'student')
        self.assertEqual(user.full_name, 'Ana Quispe')
        self.assertTrue(user.email_verified)
        self.assertFalse(user.has_usable_password())
        self.assertIsNotNone(user.google_identity.terms_accepted_at)
        self.assertNotIn(SIGNUP_KEY, self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertEqual(self.client.post(reverse('google_complete'), {}).status_code, 302)
        self.assertEqual(User.objects.filter(email='new@gmail.com').count(), 1)
        self.client.logout()
        self.assertRedirects(self.callback(), reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertEqual(User.objects.filter(email='new@gmail.com').count(), 1)

    def test_student_registration_also_enters_directly_and_handles_missing_name(self):
        response = self.callback({'subject': 'nameless', 'email': 'nameless@gmail.com',
                                   'name': '', 'authoritative': True}, intent='register', role='student')
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(User.objects.get(email='nameless@gmail.com').full_name, 'nameless')

    def test_automatic_signup_does_not_create_admin_or_reuse_taken_username(self):
        existing = User.objects.create_user(username='new', email='someone@example.com')
        self.assertRedirects(self.callback(role='admin'), reverse('dashboard'))
        user = User.objects.get(email='new@gmail.com')
        self.assertNotEqual(user.username, existing.username)
        self.assertEqual(user.role, 'student')
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_automatic_signup_rolls_back_user_if_identity_creation_conflicts(self):
        with patch('academi.views.google_auth.GoogleIdentity.objects.create', side_effect=IntegrityError):
            self.assertEqual(self.callback().url, reverse('login'))
        self.assertFalse(User.objects.filter(email='new@gmail.com').exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_teacher_requires_specialty_and_admin_signup_is_rejected(self):
        self.callback(intent='register', role='teacher')
        self.assertContains(self.client.get(reverse('google_complete')), 'teacher_full_name')
        self.assertEqual(self.complete(accept_terms='').status_code, 200)
        self.assertFalse(User.objects.filter(email='new@gmail.com').exists())
        self.assertEqual(self.complete(role='admin').status_code, 200)
        response = self.complete(role='teacher', teacher_full_name='Docente Google', specialty='')
        self.assertContains(response, 'Ingresa tu especialidad.')
        self.assertRedirects(self.complete(role='teacher', teacher_full_name='Docente Google', specialty='Sistemas'), reverse('dashboard'))
        user = User.objects.get(email='new@gmail.com')
        self.assertEqual((user.role, user.teacher_full_name, user.specialty), ('teacher', 'Docente Google', 'Sistemas'))
        self.assertFalse(user.is_staff)

    def test_external_email_uses_existing_verification_flow(self):
        from django.core import mail
        self.callback({'subject': 'external', 'email': 'person@example.com', 'authoritative': False, 'name': 'Ana'})
        self.assertRedirects(self.complete(), reverse('verify_pending'))
        self.assertFalse(User.objects.get(email='person@example.com').email_verified)
        self.assertTrue(self.client.session['verification_email_sent'])
        self.assertEqual(len(mail.outbox), 1)

    def test_expired_signup_and_email_registered_during_signup_do_not_duplicate(self):
        self.callback(intent='register', role='teacher')
        session = self.client.session
        session[SIGNUP_KEY] = {**session[SIGNUP_KEY], 'issued': time.time() - 601}
        session.save()
        self.assertRedirects(self.complete(), reverse('register'))
        self.callback(intent='register', role='teacher')
        User.objects.create_user(username='existing', email='new@gmail.com')
        self.assertRedirects(self.complete(), reverse('login'))
        self.assertEqual(User.objects.filter(email='new@gmail.com').count(), 1)

    def test_existing_verified_student_keeps_purchases_and_existing_teacher_keeps_role(self):
        teacher = User.objects.create_user(username='course_owner', role='teacher')
        course = Course.objects.create(teacher=teacher, title='Curso adquirido', status='published')
        student = User.objects.create_user(username='existing_student', email='student@gmail.com',
                                           password='old-password', email_verified=True)
        enrollment = Enrollment.objects.create(student=student, course=course, status='in_progress', progress_percentage=35)
        self.assertRedirects(self.callback({'subject': 'student-sub', 'email': student.email,
                                            'name': 'Google Name', 'authoritative': True}, next='/my-courses/'), reverse('my_courses'))
        self.assertEqual(int(self.client.session['_auth_user_id']), student.pk)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.progress_percentage, 35)
        student.refresh_from_db()
        self.assertTrue(student.check_password('old-password'))
        self.client.logout()
        teacher.email, teacher.email_verified = 'teacher@gmail.com', True
        teacher.save()
        self.callback({'subject': 'teacher-sub', 'email': teacher.email, 'name': 'Docente', 'authoritative': True})
        teacher.refresh_from_db()
        self.assertEqual(teacher.role, 'teacher')
        self.assertEqual(int(self.client.session['_auth_user_id']), teacher.pk)

    def test_unverified_duplicate_or_admin_email_requires_explicit_link(self):
        for role, verified in [('student', False), ('admin', True)]:
            user = User.objects.create_user(username='existing_'+role, email=role+'@gmail.com', role=role, email_verified=verified)
            response = self.callback({'subject': role, 'email': user.email, 'name': 'Name', 'authoritative': True})
            self.assertEqual(response.url, reverse('login'))
            self.assertNotIn('_auth_user_id', self.client.session)
            self.assertFalse(GoogleIdentity.objects.filter(user=user).exists())
        User.objects.create_user(username='duplicate1', email='same@gmail.com', email_verified=True)
        User.objects.create_user(username='duplicate2', email='SAME@gmail.com', email_verified=True)
        self.assertEqual(self.callback({'subject': 'dup', 'email': 'same@gmail.com', 'name': 'Name', 'authoritative': True}).url, reverse('login'))

    def test_disabled_linked_user_cannot_log_in(self):
        user = User.objects.create_user(username='disabled', email='inactive@gmail.com', is_active=False, email_verified=True)
        GoogleIdentity.objects.create(user=user, subject='disabled-sub', google_email=user.email)
        response = self.callback({'subject': 'disabled-sub', 'email': user.email, 'name': 'Name', 'authoritative': True})
        self.assertEqual(response.url, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_explicit_link_requires_password_and_supports_later_google_admin_login(self):
        user = User.objects.create_user(username='administrator', email='local@example.com', role='admin',
                                        password='my-existing-password', email_verified=True)
        self.client.force_login(user, backend='academi.auth_backends.UsernameOrEmailBackend')
        self.assertRedirects(self.client.post(reverse('google_start'), {'intent': 'link', 'password': 'wrong'}), reverse('profile'))
        self.assertNotIn(FLOW_KEY, self.client.session)
        identity = {'subject': 'admin-sub', 'email': 'mygoogle@gmail.com', 'name': 'Admin', 'authoritative': True}
        self.assertRedirects(self.callback(identity, intent='link', password='my-existing-password'), reverse('profile'))
        self.client.logout()
        self.assertRedirects(self.callback(identity), reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        user.refresh_from_db()
        self.assertEqual((user.role, user.email), ('admin', 'local@example.com'))

    def test_linked_identity_cannot_be_moved_to_another_user(self):
        owner = User.objects.create_user(username='google_owner', email_verified=True)
        GoogleIdentity.objects.create(user=owner, subject='owned-sub', google_email='owned@gmail.com')
        other = User.objects.create_user(username='other_user', password='existing-password', email_verified=True)
        self.client.force_login(other, backend='academi.auth_backends.UsernameOrEmailBackend')
        response = self.callback({'subject': 'owned-sub', 'email': 'owned@gmail.com', 'name': 'Name', 'authoritative': True},
                                 intent='link', password='existing-password')
        self.assertEqual(response.url, reverse('profile'))
        self.assertEqual(GoogleIdentity.objects.get(subject='owned-sub').user_id, owner.pk)
        self.assertFalse(GoogleIdentity.objects.filter(user=other).exists())

    def test_google_only_account_can_create_password_without_losing_google_login(self):
        self.callback()
        user = User.objects.get(email='new@gmail.com')
        response = self.client.get(reverse('change_password'))
        self.assertNotIn('old_password', response.context['form'].fields)
        response = self.client.post(reverse('change_password'), {'new_password1': 'NuevaClaveSegura2026!',
                                                               'new_password2': 'NuevaClaveSegura2026!'})
        self.assertRedirects(response, reverse('dashboard'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('NuevaClaveSegura2026!'))
        self.assertEqual(user.google_identity.subject, 'new-google-subject')
        self.assertIn('old_password', self.client.get(reverse('change_password')).context['form'].fields)
