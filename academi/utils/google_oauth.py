"""Intercambio OAuth y validación de identidad con la biblioteca oficial de Google."""

import secrets
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token

AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
FLOW_TTL = 600


class GoogleLoginError(Exception):
    pass


class _BoundedRequest(GoogleRequest):
    def __call__(self, *args, **kwargs):
        kwargs['timeout'] = 10
        return super().__call__(*args, **kwargs)


def available():
    return bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)


def callback_uri(request):
    origin = settings.SITE_URL or request.build_absolute_uri('/')
    return urljoin(origin.rstrip('/') + '/', reverse('google_callback').lstrip('/'))


def verified_identity(claims, nonce):
    if not secrets.compare_digest(str(claims.get('nonce', '')), nonce):
        raise ValueError('Invalid nonce')
    if claims.get('azp', settings.GOOGLE_OAUTH_CLIENT_ID) != settings.GOOGLE_OAUTH_CLIENT_ID:
        raise ValueError('Invalid authorized party')
    subject, email = claims.get('sub'), claims.get('email')
    if (not isinstance(subject, str) or not subject or len(subject) > 255
            or not isinstance(email, str) or len(email) > 254 or claims.get('email_verified') is not True):
        raise ValueError('Invalid identity')
    email = email.strip().lower()
    validate_email(email)
    # Para correos externos a Gmail/Workspace, se mantiene la verificación
    # de AcadEMI: Google no garantiza su titularidad actual.
    authoritative = email.endswith('@gmail.com') or bool(claims.get('hd'))
    return {'subject': subject, 'email': email, 'authoritative': authoritative,
            'name': str(claims.get('name') or '')[:150]}


def exchange_code(code, nonce, verifier, redirect_uri):
    try:
        response = requests.post(TOKEN_URL, data={
            'code': code, 'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'redirect_uri': redirect_uri, 'grant_type': 'authorization_code',
            'code_verifier': verifier,
        }, timeout=10)
        response.raise_for_status()
        token = response.json().get('id_token')
        if not isinstance(token, str) or not token:
            raise ValueError('Missing ID token')
        with requests.Session() as session:
            claims = id_token.verify_oauth2_token(
                token, _BoundedRequest(session=session), settings.GOOGLE_OAUTH_CLIENT_ID,
                clock_skew_in_seconds=30,
            )
        return verified_identity(claims, nonce)
    except (requests.RequestException, GoogleAuthError, ValueError, TypeError, AttributeError, ValidationError) as exc:
        # No registrar códigos, tokens ni respuestas del proveedor.
        raise GoogleLoginError('No pudimos verificar tu cuenta de Google. Inténtalo de nuevo.') from exc
