import json
import secrets

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit

from ..models import (
    Lesson, QuestionEvaluation, QuestionOption, EvaluationResult,
    EvaluationIncident, LessonProgress,
)
from ..utils import get_client_ip, issue_certificate
from ..decorators.quiz_decorators import quiz_required, prevent_cheating


# ============================================
# MÓDULO 6: EVALUACIONES / CUESTIONARIOS
# ============================================
@login_required
@ratelimit(key='user', rate='5/m', method=['POST'], block=True)
@quiz_required
@prevent_cheating
def quiz_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    evaluation = request.quiz_evaluation
    enrollment = request.quiz_enrollment

    # Generar token
    token = secrets.token_urlsafe(32)

    # GET - Iniciar sesión
    if request.method == 'GET':
        request.session['quiz_active'] = True
        request.session['quiz_start_time'] = timezone.now().isoformat()
        request.session['quiz_token'] = token
        request.session['quiz_ip'] = get_client_ip(request)
        request.session['quiz_user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        request.session['quiz_alerts'] = []

    # Obtener preguntas
    questions = QuestionEvaluation.objects.filter(evaluation=evaluation).order_by('order')

    # POST - Procesar respuestas
    if request.method == 'POST':
        try:
            body = request.body.decode('utf-8')
            data = json.loads(body)
            token_recibido = data.get('token', '')
            answers = data.get('answers', {})

            # Verificar token
            token_sesion = request.session.get('quiz_token', '')
            if not token_recibido or token_recibido != token_sesion:
                return JsonResponse({
                    'error': 'Token de seguridad inválido',
                    'code': 'INVALID_TOKEN'
                }, status=403)

            # Calcular puntaje
            score = 0
            total_points = 0

            for question in questions:
                total_points += question.points or 1
                answer_key = f'q_{question.id}'

                if answer_key in answers:
                    selected_option_id = answers[answer_key]
                    option = QuestionOption.objects.filter(
                        id=selected_option_id,
                        question=question
                    ).first()

                    if option and option.is_correct:
                        score += question.points or 1

            percentage = int((score / total_points) * 100) if total_points > 0 else 0
            passed = percentage >= evaluation.passing_score

            # Calcular tiempo
            start_time_str = request.session.get('quiz_start_time')
            time_spent = 0
            if start_time_str:
                try:
                    start_time = timezone.datetime.fromisoformat(start_time_str)
                    time_spent = int((timezone.now() - start_time).total_seconds())
                except:
                    pass

            # Crear resultado
            result = EvaluationResult.objects.create(
                enrollment=enrollment,
                evaluation=evaluation,
                score=score,
                total_points=total_points,
                passed=passed,
                completed_at=timezone.now(),
                time_spent=time_spent,
                attempt_number=EvaluationResult.objects.filter(
                    enrollment=enrollment,
                    evaluation=evaluation
                ).count() + 1,
                ip_address=request.session.get('quiz_ip'),
                user_agent=request.session.get('quiz_user_agent')
            )

            # ============================================
            # MARCAR LECCIÓN COMO COMPLETADA
            # ============================================
            if passed:
                # Marcar la lección como completada
                lesson_progress, created = LessonProgress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=lesson,
                    defaults={'completed': True, 'completed_at': timezone.now()}
                )
                if not lesson_progress.completed:
                    lesson_progress.completed = True
                    lesson_progress.completed_at = timezone.now()
                    lesson_progress.save()

                # Actualizar progreso del curso
                modules = lesson.module.course.modules.all()
                total_lessons = 0
                completed_count = 0
                for module in modules:
                    for l in module.lessons.all():
                        total_lessons += 1
                        if LessonProgress.objects.filter(
                            enrollment=enrollment,
                            lesson=l,
                            completed=True
                        ).exists():
                            completed_count += 1

                progress = int((completed_count / total_lessons * 100)) if total_lessons > 0 else 0
                enrollment.progress_percentage = progress
                just_completed = progress == 100 and enrollment.status != 'completed'
                if just_completed:
                    enrollment.status = 'completed'
                    enrollment.completed_date = timezone.now()
                elif progress > 0 and enrollment.status == 'enrolled':
                    enrollment.status = 'in_progress'
                enrollment.save()

                if just_completed:
                    issue_certificate(enrollment)

            # Registrar incidentes (RF-53)
            valid_incident_types = {'copy_paste', 'tab_switch', 'timeout', 'other'}
            alerts = request.session.get('quiz_alerts', [])
            for alert in alerts:
                if isinstance(alert, dict):
                    alert_type = alert.get('type', 'other')
                    detail = alert.get('detail', '')
                else:
                    alert_type = alert
                    detail = ''
                if alert_type not in valid_incident_types:
                    alert_type = 'other'
                EvaluationIncident.objects.create(
                    evaluation_result=result,
                    incident_type=alert_type,
                    description=detail or f'Incidente detectado: {alert_type}'
                )

            # Limpiar sesión
            request.session['quiz_active'] = False
            request.session.pop('quiz_start_time', None)
            request.session.pop('quiz_token', None)
            request.session.pop('quiz_alerts', None)
            request.session.pop('quiz_kicked', None)

            return JsonResponse({
                'success': True,
                'score': score,
                'total_points': total_points,
                'percentage': percentage,
                'passed': passed,
                'result_id': result.id
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Datos inválidos',
                'code': 'INVALID_DATA'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'code': 'SERVER_ERROR'
            }, status=500)

    # Contexto para GET
    attempts_used = EvaluationResult.objects.filter(
        enrollment=enrollment,
        evaluation=evaluation
    ).count()

    context = {
        'lesson': lesson,
        'course': lesson.module.course,
        'evaluation': evaluation,
        'questions': questions,
        'token': token,
        'enrollment': enrollment,
        'time_limit': evaluation.time_limit_minutes,
        'max_attempts': evaluation.max_attempts,
        'attempts_used': attempts_used,
        'passing_score': evaluation.passing_score,
    }
    return render(request, 'academi/courses/quiz.html', context)


@login_required
def quiz_result_view(request, result_id):
    result = get_object_or_404(EvaluationResult, id=result_id)

    if result.enrollment.student != request.user:
        messages.error(request, 'No tienes permiso para ver este resultado.')
        return redirect('dashboard')

    # ============================================
    # CALCULAR INTENTOS
    # ============================================
    attempts_used = EvaluationResult.objects.filter(
        enrollment=result.enrollment,
        evaluation=result.evaluation
    ).count()

    max_attempts = result.evaluation.max_attempts
    remaining_attempts = max_attempts - attempts_used

    incidents = EvaluationIncident.objects.filter(evaluation_result=result)
    has_incidents = incidents.exists()

    percentage = int((result.score / result.total_points) * 100) if result.total_points > 0 else 0

    context = {
        'result': result,
        'percentage': percentage,
        'evaluation': result.evaluation,
        'course': result.enrollment.course,
        'lesson': result.evaluation.lesson,  # Para el botón "reintentar"
        'has_incidents': has_incidents,
        'incidents': incidents,
        'attempts_used': attempts_used,
        'max_attempts': max_attempts,
        'remaining_attempts': remaining_attempts,
    }
    return render(request, 'academi/courses/quiz_resultado.html', context)


@login_required
def quiz_tab_switch_alert(request):
    """RF-53: registra incidentes de seguridad durante un cuestionario
    (cambio de pestaña, intento de captura de pantalla, atajo de
    inspección, etc.). Solo el cambio de pestaña bloquea el envío al
    superar el límite; los demás tipos quedan registrados como
    advertencia sin impedir que el estudiante termine el examen."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            incident_type = data.get('type', 'tab_switch')
            detail = data.get('detail', '')
            count = data.get('count', 0)

            alerts = request.session.get('quiz_alerts', [])
            alerts.append({'type': incident_type, 'detail': detail})
            request.session['quiz_alerts'] = alerts
            # Reasignar la clave (en vez de mutar la lista en el lugar) es
            # necesario para que Django detecte el cambio y guarde la sesión:
            # session.modified no se activa solo con list.append().

            if incident_type == 'tab_switch' and count >= 3:
                request.session['quiz_kicked'] = True
                return JsonResponse({'kicked': True, 'message': 'Demasiados cambios de pestaña'})

            return JsonResponse({'success': True})
        except:
            return JsonResponse({'error': 'Datos inválidos'}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)
