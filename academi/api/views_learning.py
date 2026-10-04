from django.core import signing
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import (
    Course, Lesson, Enrollment, LessonProgress, Comment, Question, AssignmentSubmission,
    Evaluation, QuestionEvaluation, QuestionOption, EvaluationResult, EvaluationIncident,
    Certificate,
)
from ..utils import get_client_ip
from .auth import api_view, error, ok, parse_body
from .progress import mark_lesson_done
from .support import validate_upload
from .serializers import (
    ACTIVE_STATUSES, completed_lesson_ids, display_name, enrollment_json, media_url,
    modules_outline, youtube_id, certificate_json,
)

QUIZ_SALT = 'academi.api.quiz'
QUIZ_GRACE_SECONDS = 15


def _enrollment(user, course):
    return Enrollment.objects.filter(student=user, course=course, status__in=ACTIVE_STATUSES).first()


def _is_staff_of(user, course):
    return user == course.teacher or user.role == 'admin'


def _ordered_lessons(course):
    return list(Lesson.objects.filter(module__course=course).order_by('module__order', 'order'))


@api_view(('GET',))
def my_courses(request):
    user = request.user
    if user.role == 'teacher':
        return teacher_courses(request)
    enrollments = (Enrollment.objects.filter(student=user, status__in=ACTIVE_STATUSES + ['pending'])
                   .select_related('course__category', 'course__teacher').order_by('-last_accessed'))
    return ok(enrollments=[enrollment_json(request, e) for e in enrollments])


def teacher_courses(request):
    from .serializers import CourseContext, course_card
    ctx = CourseContext(None)
    courses = (Course.objects.filter(teacher=request.user).select_related('category', 'teacher')
               .order_by('-created_at'))
    rows = []
    for c in courses:
        card = course_card(request, c, ctx)
        card['status'] = c.status
        card['status_label'] = c.get_status_display()
        card['rejection_reason'] = c.rejection_reason or ''
        rows.append(card)
    return ok(courses=rows, role='teacher')


@api_view(('GET',))
def learn(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='published')
    user = request.user

    if _is_staff_of(user, course):
        return ok(course={'id': course.id, 'title': course.title,
                          'image': media_url(request, course.image)},
                  modules=modules_outline(course, set()), progress=0, completed_count=0,
                  total_lessons=course.total_lessons, certificate=None, preview=True)

    enrollment = get_object_or_404(Enrollment, student=user, course=course, status__in=ACTIVE_STATUSES)
    completed = completed_lesson_ids(enrollment)
    total = course.total_lessons
    percent = int(len(completed) / total * 100) if total else 0
    enrollment.progress_percentage = percent
    just_completed = percent == 100 and enrollment.status != 'completed'
    if just_completed:
        enrollment.status = 'completed'
        enrollment.completed_date = timezone.now()
    elif percent > 0 and enrollment.status == 'enrolled':
        enrollment.status = 'in_progress'
    enrollment.save()
    if just_completed:
        from ..utils import issue_certificate
        issue_certificate(enrollment)

    certificate = Certificate.objects.filter(enrollment=enrollment, is_revoked=False).first()
    lessons = _ordered_lessons(course)
    next_lesson = next((l for l in lessons if l.id not in completed), None)
    return ok(
        course={'id': course.id, 'title': course.title, 'image': media_url(request, course.image),
                'teacher': display_name(course.teacher)},
        modules=modules_outline(course, completed),
        progress=percent, completed_count=len(completed), total_lessons=total,
        status=enrollment.status,
        next_lesson_id=next_lesson.id if next_lesson else None,
        certificate=certificate_json(request, certificate) if certificate else None,
        preview=False,
    )


def _comment_json(request, c, me):
    return {
        'id': c.id, 'content': c.content, 'author': display_name(c.student),
        'picture': media_url(request, c.student.profile_picture),
        'is_edited': c.is_edited, 'is_mine': c.student_id == me.id,
        'created_at': c.created_at.isoformat(),
    }


def _question_json(request, q, me):
    return {
        'id': q.id, 'content': q.content, 'author': display_name(q.student),
        'picture': media_url(request, q.student.profile_picture),
        'is_answered': q.is_answered, 'is_mine': q.student_id == me.id,
        'created_at': q.created_at.isoformat(),
        'answers': [{'id': a.id, 'content': a.content or '', 'teacher': display_name(a.teacher),
                     'created_at': a.created_at.isoformat()} for a in q.answers.all()],
    }


@api_view(('GET',))
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
    course = lesson.module.course
    user = request.user
    staff = _is_staff_of(user, course)

    enrollment = None
    if not staff:
        enrollment = _enrollment(user, course)
        if not enrollment and not lesson.is_free:
            return error('Debes inscribirte en el curso para ver esta lección.', 403, code='NOT_ENROLLED')

    progress = 0
    completed = False
    if enrollment:
        row, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        row.save()  # actualiza last_accessed
        completed = row.completed
        done = len(completed_lesson_ids(enrollment))
        total = course.total_lessons
        progress = int(done / total * 100) if total else 0
        if progress > 0 and enrollment.status == 'enrolled':
            enrollment.status = 'in_progress'
        enrollment.progress_percentage = progress
        enrollment.save()

    lessons = _ordered_lessons(course)
    idx = next((i for i, l in enumerate(lessons) if l.id == lesson.id), None)
    next_lesson = lessons[idx + 1] if idx is not None and idx + 1 < len(lessons) else None
    prev_lesson = lessons[idx - 1] if idx else None

    yt = youtube_id(lesson.video_url)
    evaluation = lesson.evaluations.first() if lesson.lesson_type in ('quiz', 'exam') else None
    quiz = None
    if evaluation:
        attempts = 0
        best = None
        if enrollment:
            results = EvaluationResult.objects.filter(enrollment=enrollment, evaluation=evaluation,
                                                      completed_at__isnull=False)
            attempts = results.count()
            best = max((round(r.score / r.total_points * 100) if r.total_points else 0 for r in results),
                       default=None)
        quiz = {
            'title': evaluation.title, 'description': evaluation.description or '',
            'time_limit_minutes': evaluation.time_limit_minutes, 'passing_score': evaluation.passing_score,
            'max_attempts': evaluation.max_attempts, 'attempts': attempts, 'best_score': best,
            'questions_count': evaluation.questions.count(),
        }

    submission = None
    if lesson.lesson_type == 'assignment' and not staff:
        s = AssignmentSubmission.objects.filter(lesson=lesson, student=user).first()
        if s:
            submission = {
                'file': media_url(request, s.file), 'comment': s.comment or '',
                'submitted_at': s.submitted_at.isoformat(), 'grade': s.grade,
                'feedback': s.feedback or '', 'graded_at': s.graded_at.isoformat() if s.graded_at else None,
            }

    comments = Comment.objects.filter(lesson=lesson).select_related('student').order_by('-created_at')
    questions = (Question.objects.filter(lesson=lesson).select_related('student')
                 .prefetch_related('answers__teacher').order_by('-created_at'))

    return ok(lesson={
        'id': lesson.id, 'title': lesson.title, 'description': lesson.description or '',
        'content': lesson.content or '', 'type': lesson.lesson_type,
        'duration_minutes': lesson.duration_minutes or 0, 'is_free': lesson.is_free,
        'video_url': lesson.video_url or None, 'youtube_id': yt,
        'video_file': media_url(request, lesson.video_file),
        'document_file': media_url(request, lesson.document_file),
        'resources': [{'id': r.id, 'title': r.title, 'type': r.file_type,
                       'url': media_url(request, r.file)} for r in lesson.resources.all()],
        'module': lesson.module.title,
        'course_id': course.id, 'course_title': course.title,
        'completed': completed, 'progress': progress,
        'is_enrolled': enrollment is not None, 'is_staff': staff,
        'next_lesson_id': next_lesson.id if next_lesson else None,
        'next_lesson_title': next_lesson.title if next_lesson else None,
        'prev_lesson_id': prev_lesson.id if prev_lesson else None,
        'quiz': quiz, 'submission': submission,
        'assignment_deadline_days': lesson.assignment_deadline_days,
        'comments': [_comment_json(request, c, user) for c in comments],
        'questions': [_question_json(request, q, user) for q in questions],
    })


@api_view(('POST',), roles=('student',))
def lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=lesson.module.course,
                                   status__in=ACTIVE_STATUSES)
    result = mark_lesson_done(enrollment, lesson, request)
    return ok(message='Lección completada', **result)


# ============================================
# CUESTIONARIOS
# ============================================
def _quiz_context(user, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
    evaluation = Evaluation.objects.filter(lesson=lesson).first()
    if not evaluation:
        return lesson, None, None, error('Este cuestionario no está disponible.', 404)
    enrollment = _enrollment(user, lesson.module.course)
    if not enrollment:
        return lesson, evaluation, None, error('No estás inscrito en este curso.', 403, code='NOT_ENROLLED')
    attempts = EvaluationResult.objects.filter(enrollment=enrollment, evaluation=evaluation).count()
    if attempts >= evaluation.max_attempts:
        return lesson, evaluation, enrollment, error(
            'Has alcanzado el límite de intentos para este cuestionario.', 403, code='NO_ATTEMPTS')
    return lesson, evaluation, enrollment, None


@api_view(('POST',), roles=('student',))
def quiz_start(request, lesson_id):
    """Entrega las preguntas (sin las respuestas correctas) y un token firmado
    con la hora de inicio, que sustituye a la sesión del sitio web."""
    lesson, evaluation, enrollment, problem = _quiz_context(request.user, lesson_id)
    if problem:
        return problem
    questions = QuestionEvaluation.objects.filter(evaluation=evaluation).order_by('order').prefetch_related('options')
    token = signing.dumps({'lesson': lesson.id, 'user': request.user.id,
                           'start': timezone.now().isoformat()}, salt=QUIZ_SALT)
    return ok(
        token=token, title=evaluation.title, time_limit_minutes=evaluation.time_limit_minutes,
        passing_score=evaluation.passing_score,
        questions=[{
            'id': q.id, 'text': q.text, 'type': q.question_type, 'points': q.points or 1,
            'options': [{'id': o.id, 'text': o.text} for o in q.options.all()],
        } for q in questions],
    )


@api_view(('POST',), roles=('student',))
def quiz_submit(request, lesson_id):
    lesson, evaluation, enrollment, problem = _quiz_context(request.user, lesson_id)
    if problem:
        return problem
    data = parse_body(request)
    try:
        payload = signing.loads(data.get('token') or '', salt=QUIZ_SALT, max_age=6 * 3600)
    except signing.BadSignature:
        return error('Sesión de cuestionario expirada. Inícialo nuevamente.', 403, code='SESSION_EXPIRED')
    if payload.get('lesson') != lesson.id or payload.get('user') != request.user.id:
        return error('Token de cuestionario inválido.', 403, code='INVALID_TOKEN')

    start = timezone.datetime.fromisoformat(payload['start'])
    elapsed = int((timezone.now() - start).total_seconds())
    if elapsed > evaluation.time_limit_minutes * 60 + QUIZ_GRACE_SECONDS:
        return error('Tiempo límite excedido.', 403, code='TIME_EXCEEDED')

    answers = data.get('answers') or {}
    tab_switches = int(data.get('tab_switches') or 0)
    score = total = 0
    for q in QuestionEvaluation.objects.filter(evaluation=evaluation):
        points = q.points or 1
        total += points
        selected = answers.get(str(q.id))
        if selected:
            option = QuestionOption.objects.filter(id=selected, question=q).first()
            if option and option.is_correct:
                score += points

    percentage = int(score / total * 100) if total else 0
    passed = percentage >= evaluation.passing_score
    result = EvaluationResult.objects.create(
        enrollment=enrollment, evaluation=evaluation, score=score, total_points=total,
        passed=passed, completed_at=timezone.now(), time_spent=elapsed,
        attempt_number=EvaluationResult.objects.filter(enrollment=enrollment, evaluation=evaluation).count() + 1,
        ip_address=get_client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    if tab_switches:
        EvaluationIncident.objects.create(
            evaluation_result=result, incident_type='tab_switch',
            description=f'La app pasó a segundo plano {tab_switches} vez/veces durante el cuestionario.',
        )

    progress = None
    if passed:
        progress = mark_lesson_done(enrollment, lesson, request)

    attempts_left = max(evaluation.max_attempts - result.attempt_number, 0)
    return ok(result={
        'id': result.id, 'score': score, 'total_points': total, 'percentage': percentage,
        'passed': passed, 'passing_score': evaluation.passing_score, 'time_spent': elapsed,
        'attempt_number': result.attempt_number, 'attempts_left': attempts_left,
    }, progress=progress)


# ============================================
# TAREAS, COMENTARIOS, PREGUNTAS
# ============================================
@api_view(('POST',), roles=('student',))
def assignment_submit(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'),
                               id=lesson_id, lesson_type='assignment')
    if not _enrollment(request.user, lesson.module.course):
        return error('Debes estar inscrito en el curso para entregar esta tarea.', 403)
    uploaded = request.FILES.get('file')
    if not uploaded:
        return error('Selecciona un archivo para entregar.')
    problem = validate_upload(uploaded, 'assignment')
    if problem:
        return error(problem)
    comment = (request.POST.get('comment') or '').strip()
    submission, created = AssignmentSubmission.objects.update_or_create(
        lesson=lesson, student=request.user, defaults={'file': uploaded, 'comment': comment})
    if not created:
        submission.grade = None
        submission.feedback = None
        submission.graded_at = None
        submission.save()
    return ok(message='Tarea entregada correctamente.')


def _course_of(lesson):
    return lesson.module.course


@api_view(('POST',))
def comment_add(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
    content = (parse_body(request).get('content') or '').strip()
    if not _enrollment(request.user, _course_of(lesson)) and not _is_staff_of(request.user, _course_of(lesson)):
        return error('Debes estar inscrito en el curso para comentar.', 403)
    if not content:
        return error('Escribe un comentario antes de enviarlo.')
    c = Comment.objects.create(lesson=lesson, student=request.user, content=content)
    return ok(comment=_comment_json(request, c, request.user))


@api_view(('POST',))
def comment_delete(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    if c.student_id != request.user.id and request.user.role != 'admin':
        return error('No puedes eliminar este comentario.', 403)
    c.delete()
    return ok()


@api_view(('POST',))
def question_add(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
    content = (parse_body(request).get('content') or '').strip()
    if not _enrollment(request.user, _course_of(lesson)):
        return error('Debes estar inscrito en el curso para preguntar.', 403)
    if not content:
        return error('Escribe tu pregunta antes de enviarla.')
    q = Question.objects.create(lesson=lesson, student=request.user, content=content)
    return ok(question=_question_json(request, q, request.user))


@api_view(('POST',))
def comment_edit(request, comment_id):
    """RF-25: el autor edita su propio comentario."""
    c = get_object_or_404(Comment, id=comment_id)
    if c.student_id != request.user.id:
        return error('Solo puedes editar tus propios comentarios.', 403)
    content = (parse_body(request).get('content') or '').strip()
    if not content:
        return error('El comentario no puede quedar vacío.')
    c.content = content
    c.is_edited = True
    c.save()
    return ok(comment=_comment_json(request, c, request.user))


@api_view(('GET',), roles=('student',))
def progress_history(request):
    """RF-09: avance por curso e historial de lecciones completadas."""
    enrollments = (Enrollment.objects.filter(student=request.user, status__in=ACTIVE_STATUSES)
                   .select_related('course__category', 'course__teacher').order_by('-last_accessed'))
    courses = []
    for e in enrollments:
        done = LessonProgress.objects.filter(enrollment=e, completed=True).count()
        item = enrollment_json(request, e)
        item.update({'completed_lessons': done, 'total_lessons': e.course.total_lessons,
                     'enrolled_at': e.enrollment_date.isoformat(),
                     'completed_date': e.completed_date.isoformat() if e.completed_date else None})
        courses.append(item)
    recent = (LessonProgress.objects.filter(enrollment__student=request.user, completed=True)
              .select_related('lesson__module__course').order_by('-completed_at')[:30])
    evaluations = (EvaluationResult.objects.filter(enrollment__student=request.user, completed_at__isnull=False)
                   .select_related('evaluation', 'enrollment__course').order_by('-completed_at')[:15])
    return ok(
        courses=courses,
        activity=[{'type': 'lesson', 'title': r.lesson.title, 'course': r.lesson.module.course.title,
                   'at': r.completed_at.isoformat() if r.completed_at else None} for r in recent]
        + [{'type': 'evaluation', 'title': r.evaluation.title, 'course': r.enrollment.course.title,
            'passed': r.passed, 'at': r.completed_at.isoformat()} for r in evaluations],
    )
