from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model

User = get_user_model()


def send_verification_email(user, request):
    """RF-07: Enviar correo de verificación"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = get_current_site(request)
    domain = current_site.domain
    verify_link = f"http://{domain}/verify-email/{uid}/{token}/"

    context = {
        'user': user,
        'verify_link': verify_link,
        'domain': domain,
    }

    html_message = render_to_string('academi/emails/verification_email.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject='Confirma tu correo - AcadEMI',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, request, reset_link):
    """RF-03: Enviar correo de recuperación de contraseña"""
    context = {
        'user': user,
        'reset_link': reset_link,
        'domain': get_current_site(request).domain,
    }

    html_message = render_to_string('academi/emails/password_reset_email.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject='Recuperación de contraseña - AcadEMI',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_certificate_email(certificate, request):
    """RF-66: Enviar certificado por correo electrónico"""
    user = certificate.enrollment.student
    current_site = get_current_site(request)
    domain = current_site.domain
    certificate_link = f"http://{domain}/my-certificates/{certificate.id}/"

    context = {
        'user': user,
        'certificate': certificate,
        'certificate_link': certificate_link,
        'domain': domain,
    }

    html_message = render_to_string('academi/emails/certificate_email.html', context)
    plain_message = strip_tags(html_message)

    email = EmailMultiAlternatives(
        subject=f'Tu certificado de "{certificate.enrollment.course.title}" - AcadEMI',
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_message, 'text/html')
    if certificate.pdf_file:
        email.attach(
            f'certificado-{certificate.certificate_code}.pdf',
            certificate.pdf_file.read(),
            'application/pdf',
        )
    email.send(fail_silently=False)


def send_purchase_confirmation_email(payment, items, request):
    """RF-58, RF-62: enviar confirmación de compra y comprobante por correo."""
    current_site = get_current_site(request)
    domain = current_site.domain
    invoice_link = f"http://{domain}/purchase-history/invoice/{payment.id}/"

    context = {
        'payment': payment,
        'items': items,
        'invoice_link': invoice_link,
        'domain': domain,
    }

    html_message = render_to_string('academi/emails/purchase_confirmation_email.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject=f'Confirmación de compra - Factura {payment.invoice_number} - AcadEMI',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[payment.billing_email or payment.student.email],
        html_message=html_message,
        fail_silently=True,
    )


def generate_reset_link(user, request):
    """RF-03: Generar enlace de recuperación"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = get_current_site(request)
    domain = current_site.domain
    return f"http://{domain}/reset-password/{uid}/{token}/"


def validate_reset_token(uidb64, token):
    """RF-03: Validar token de recuperación"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None

    if user is not None and default_token_generator.check_token(user, token):
        return user
    return None
