from django.utils import timezone

from ..models import LessonProgress
from ..utils import issue_certificate, send_certificate_email


def mark_lesson_done(enrollment, lesson, request=None):
    """Marca la lección como completada y recalcula el progreso del curso
    (mismas reglas que la vista web mark_lesson_complete). Devuelve un dict
    con el progreso y, si acaba de terminar el curso, el certificado."""
    progress_row, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment, lesson=lesson,
        defaults={'completed': True, 'completed_at': timezone.now()},
    )
    if not progress_row.completed:
        progress_row.completed = True
        progress_row.completed_at = timezone.now()
        progress_row.save()

    course = enrollment.course
    total = 0
    done = 0
    for module in course.modules.all():
        for l in module.lessons.all():
            total += 1
            if LessonProgress.objects.filter(enrollment=enrollment, lesson=l, completed=True).exists():
                done += 1

    percent = int(done / total * 100) if total else 0
    enrollment.progress_percentage = percent
    just_completed = False
    if percent == 100 and enrollment.status != 'completed':
        enrollment.status = 'completed'
        enrollment.completed_date = timezone.now()
        just_completed = True
    elif percent > 0 and enrollment.status == 'enrolled':
        enrollment.status = 'in_progress'
    enrollment.save()

    certificate_id = None
    if just_completed:
        certificate, _ = issue_certificate(enrollment)
        certificate_id = certificate.id
        if request is not None:
            try:
                send_certificate_email(certificate, request)
            except Exception:
                pass  # emitir el certificado no debe fallar si el correo falla

    return {
        'progress': percent,
        'completed_count': done,
        'total_lessons': total,
        'course_completed': just_completed,
        'certificate_id': certificate_id,
    }
