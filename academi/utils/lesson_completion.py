"""Reglas de finalización aplicadas en web y en la API móvil."""

from ..models import AssignmentSubmission, EvaluationResult


def completion_blocker(enrollment, lesson):
    """Devuelve el motivo que impide completar la actividad, o None."""
    if lesson.lesson_type in ('quiz', 'exam'):
        if not EvaluationResult.objects.filter(
            enrollment=enrollment, evaluation__lesson=lesson, passed=True,
        ).exists():
            return 'Debes aprobar esta evaluación antes de completar la lección.'
    elif lesson.lesson_type == 'assignment':
        if not AssignmentSubmission.objects.filter(
            lesson=lesson, student=enrollment.student,
        ).exists():
            return 'Debes entregar la tarea antes de completar la lección.'
    return None
