from django.core.files.base import ContentFile

from ..models import Certificate
from .certificate_pdf import render_certificate_pdf


def issue_certificate(enrollment):
    """RF-64: emite el certificado de un enrollment completado (idempotente)."""
    certificate = Certificate.objects.filter(enrollment=enrollment).first()
    if certificate:
        return certificate, False

    certificate = Certificate(enrollment=enrollment)
    while True:
        code = certificate.generate_code()
        if not Certificate.objects.filter(certificate_code=code).exists():
            break
    certificate.save()

    # RF-65: el certificado debe poder descargarse como PDF real, no solo
    # imprimirse desde el navegador.
    pdf_buffer = render_certificate_pdf(certificate)
    certificate.pdf_file.save(
        f'certificado-{certificate.certificate_code}.pdf',
        ContentFile(pdf_buffer.read()),
        save=True,
    )

    return certificate, True
