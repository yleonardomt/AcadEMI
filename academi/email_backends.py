"""Envío acotado por SMTP o por la API HTTPS de Brevo."""
import base64
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend


class SafeSMTPBackend(EmailBackend):
    def open(self):
        if settings.ON_RENDER and int(self.port) in (25, 465, 587):
            if self.fail_silently:
                return False
            raise ImproperlyConfigured(
                'Render Free bloquea este puerto SMTP. Configura BREVO_API_KEY y un remitente verificado.')
        return super().open()


class BrevoBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages or []:
            if not message.recipients():
                continue
            try:
                if not settings.BREVO_API_KEY:
                    raise ImproperlyConfigured('Falta BREVO_API_KEY para enviar correo.')
                name, address = parseaddr(message.from_email)
                payload = {
                    'sender': {'email': address, 'name': name or 'AcadEMI'},
                    'to': [{'email': parseaddr(value)[1]} for value in message.to],
                    'subject': message.subject,
                    'textContent': message.body,
                }
                for field in ('cc', 'bcc'):
                    values = getattr(message, field, [])
                    if values:
                        payload[field] = [{'email': parseaddr(value)[1]} for value in values]
                if message.reply_to:
                    payload['replyTo'] = {'email': parseaddr(message.reply_to[0])[1]}
                for content, mime in getattr(message, 'alternatives', []):
                    if mime == 'text/html':
                        payload['htmlContent'] = content
                if message.attachments:
                    payload['attachment'] = []
                    for filename, content, mime in message.attachments:
                        raw = content.encode('utf-8') if isinstance(content, str) else content
                        payload['attachment'].append({
                            'name': filename, 'content': base64.b64encode(raw).decode('ascii')})
                response = requests.post('https://api.brevo.com/v3/smtp/email',
                    headers={'api-key': settings.BREVO_API_KEY, 'accept': 'application/json'},
                    json=payload, timeout=(3, settings.EMAIL_TIMEOUT))
                if response.status_code != 201:
                    raise RuntimeError(f'El proveedor de correo rechazó el envío (HTTP {response.status_code}).')
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent
