"""Descargas temporales para la app cuando abre el navegador del dispositivo."""

from django.core import signing
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404

from ..models import AssignmentSubmission, Certificate, User
from ..utils.certificate_pdf import render_certificate_pdf
from .auth import api_view, error
from .serializers import DOWNLOAD_SALT


@api_view(('GET',), auth='none')
def download(request, kind, object_id):
    try:
        data = signing.loads(request.GET.get('t', ''), salt=DOWNLOAD_SALT, max_age=1800)
    except signing.BadSignature:
        return error('El enlace expiró. Abre el archivo nuevamente desde la app.', 403)
    if data.get('kind') != kind or data.get('id') != object_id:
        return error('Enlace inválido.', 403)
    user = User.objects.filter(pk=data.get('user'), is_active=True).first()
    if user is None:
        return error('La cuenta ya no está disponible.', 403)
    if user.password[-12:] != data.get('pw'):
        return error('El enlace ya no es válido. Abre el archivo desde la app.', 403)

    if kind == 'certificate':
        certificate = get_object_or_404(
            Certificate.objects.select_related('enrollment__student', 'enrollment__course'),
            pk=object_id, is_revoked=False,
        )
        if user.pk != certificate.enrollment.student_id and user.role != 'admin':
            return error('No tienes permisos para este certificado.', 403)
        response = HttpResponse(render_certificate_pdf(certificate).getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificado-{certificate.certificate_code}.pdf"'
        return response

    if kind == 'assignment':
        submission = get_object_or_404(
            AssignmentSubmission.objects.select_related('lesson__module__course'), pk=object_id,
        )
        course = submission.lesson.module.course
        if user.pk not in (submission.student_id, course.teacher_id) and user.role != 'admin':
            return error('No tienes permisos para este archivo.', 403)
        try:
            return FileResponse(submission.file.open('rb'), as_attachment=True,
                                filename=submission.file.name.rsplit('/', 1)[-1])
        except (FileNotFoundError, OSError):
            raise Http404('El archivo ya no está disponible.')

    raise Http404
