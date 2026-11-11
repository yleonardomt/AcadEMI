"""Calificación y conservación de respuestas compartidas por web y móvil."""

from django.db import transaction

from ..models import Enrollment, EvaluationResult, UserAnswer


@transaction.atomic
def record_attempt(enrollment, evaluation, answers, *, key_prefix='', **metadata):
    if not isinstance(answers, dict):
        raise ValueError('Las respuestas deben enviarse como un objeto.')

    # El mismo estudiante no puede consumir el último intento dos veces
    # mediante envíos simultáneos desde web y móvil.
    Enrollment.objects.select_for_update().get(pk=enrollment.pk)
    used = EvaluationResult.objects.filter(enrollment=enrollment, evaluation=evaluation).count()
    if used >= evaluation.max_attempts:
        raise ValueError('Has alcanzado el límite de intentos para esta evaluación.')

    score = total = 0
    rows = []
    for question in evaluation.questions.prefetch_related('options').order_by('order', 'pk'):
        points = question.points or 1
        total += points
        selected = answers.get(f'{key_prefix}{question.pk}')
        if selected is not None and (isinstance(selected, bool) or not isinstance(selected, (str, int))):
            raise ValueError('La opción seleccionada no es válida.')
        option = next((o for o in question.options.all() if str(o.pk) == str(selected)), None)
        correct = bool(option and option.is_correct)
        awarded = points if correct else 0
        score += awarded
        rows.append(UserAnswer(question=question, selected_option=option,
                               is_correct=correct, points_obtained=awarded))

    percentage = int(score / total * 100) if total else 0
    result = EvaluationResult.objects.create(
        enrollment=enrollment, evaluation=evaluation, score=score, total_points=total,
        passed=percentage >= evaluation.passing_score, attempt_number=used + 1, **metadata,
    )
    for answer in rows:
        answer.evaluation_result = result
    UserAnswer.objects.bulk_create(rows)
    return result
