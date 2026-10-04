"""Gestión de cursos para el docente desde la app móvil: cursos, módulos,
lecciones, evaluaciones, cupones y estadísticas (RF-13, RF-14, RF-16, RF-28,
RF-32 y RF-36). Aplica los mismos permisos que las vistas web: solo el
docente dueño del curso (o un administrador)."""
import json

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import (
    Category, Course, Module, Lesson, Coupon, Evaluation, QuestionEvaluation, QuestionOption,
    Enrollment, EvaluationResult, AssignmentSubmission, Notification,
)
from ..utils import compute_course_stats
from .auth import api_view, error, ok, parse_body
from .serializers import display_name, media_url, money
from .support import log_action, validate_upload
from .views_admin import coupon_row, save_coupon

TEACHER = ('teacher', 'admin')
LEVELS = {'beginner', 'intermediate', 'advanced', 'expert'}
LESSON_TYPES = {'text', 'video', 'document', 'assignment', 'quiz', 'exam'}


def _flag(value):
    return str(value).lower() in ('true', '1', 'on', 'yes')


def _own_course(user, course_id):
    course = get_object_or_404(Course, id=course_id)
    if user != course.teacher and user.role != 'admin':
        return None, error('No tienes permisos sobre este curso.', 403)
    return course, None


def _own_module(user, module_id):
    module = get_object_or_404(Module.objects.select_related('course'), id=module_id)
    if user != module.course.teacher and user.role != 'admin':
        return None, error('No tienes permisos sobre este curso.', 403)
    return module, None


def _own_lesson(user, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
    if user != lesson.module.course.teacher and user.role != 'admin':
        return None, error('No tienes permisos sobre este curso.', 403)
    return lesson, None


# ============================================
# CURSOS (RF-13)
# ============================================
def _course_admin_json(request, c):
    return {
        'id': c.id, 'title': c.title, 'description': c.description, 'category_id': c.category_id,
        'category': c.category.name if c.category_id else None, 'level': c.level,
        'level_label': c.get_level_display(), 'price': money(c.price), 'is_free': c.is_free,
        'is_featured': c.is_featured, 'status': c.status, 'status_label': c.get_status_display(),
        'rejection_reason': c.rejection_reason or '', 'image': media_url(request, c.image),
        'video_promo': media_url(request, c.video_promo),
        'modules': [{
            'id': m.id, 'title': m.title, 'description': m.description or '', 'order': m.order,
            'lessons': [{
                'id': l.id, 'title': l.title, 'type': l.lesson_type, 'order': l.order,
                'is_free': l.is_free, 'duration_minutes': l.duration_minutes or 0,
            } for l in m.lessons.all()],
        } for m in c.modules.all().prefetch_related('lessons')],
    }


@api_view(('GET',), roles=TEACHER)
def course_detail(request, course_id):
    course, problem = _own_course(request.user, course_id)
    if problem:
        return problem
    return ok(course=_course_admin_json(request, course))


@api_view(('POST',), roles=('teacher',))
def course_create(request):
    return _save_course(request, None)


@api_view(('POST',), roles=TEACHER)
def course_update(request, course_id):
    course, problem = _own_course(request.user, course_id)
    if problem:
        return problem
    return _save_course(request, course)


def _save_course(request, course):
    data = parse_body(request)
    title = (data.get('title') or (course.title if course else '')).strip()
    description = (data.get('description') or (course.description if course else '')).strip()
    if len(title) < 3:
        return error('El título es obligatorio (mínimo 3 caracteres).')
    if not description:
        return error('La descripción es obligatoria.')
    level = data.get('level') or (course.level if course else 'beginner')
    if level not in LEVELS:
        return error('Nivel inválido.')
    is_free = _flag(data['is_free']) if 'is_free' in data else (course.is_free if course else False)
    try:
        price = float(data['price']) if data.get('price') not in (None, '') else (float(course.price) if course else 0)
    except ValueError:
        return error('Precio inválido.')
    if price < 0:
        return error('El precio no puede ser negativo.')
    if is_free:
        price = 0
    category = None
    category_id = data.get('category') or data.get('category_id')
    if category_id not in (None, ''):
        category = Category.objects.filter(id=category_id).first()
        if not category:
            return error('La categoría no existe.')

    image = request.FILES.get('image')
    promo = request.FILES.get('video_promo')
    for f, kind in ((image, 'image'), (promo, 'video')):
        if f:
            problem = validate_upload(f, kind)
            if problem:
                return error(problem)

    creating = course is None
    if creating:
        course = Course(teacher=request.user, status='draft')
    course.title, course.description, course.level = title, description, level
    course.price, course.is_free = price, is_free
    if 'is_featured' in data:
        course.is_featured = _flag(data['is_featured'])
    if category:
        course.category = category
    if image:
        course.image = image
    if promo:
        course.video_promo = promo
    course.save()
    log_action(request, request.user, 'course_create' if creating else 'course_edit',
               f'{"Creó" if creating else "Editó"} el curso "{course.title}"')
    return ok(message=f'Curso "{title}" {"creado" if creating else "actualizado"} correctamente.',
              course=_course_admin_json(request, course))


@api_view(('POST',), roles=TEACHER)
def course_delete(request, course_id):
    course, problem = _own_course(request.user, course_id)
    if problem:
        return problem
    title = course.title
    course.delete()
    log_action(request, request.user, 'course_delete', f'Eliminó el curso "{title}"')
    return ok(message=f'Curso "{title}" eliminado correctamente.')


@api_view(('POST',), roles=TEACHER)
def course_publish(request, course_id):
    course, problem = _own_course(request.user, course_id)
    if problem:
        return problem
    if course.total_lessons == 0:
        return error('El curso debe tener al menos una lección para publicarse.')
    course.status = 'published'
    course.published_at = timezone.now()
    course.save()
    log_action(request, request.user, 'course_edit', f'Publicó el curso "{course.title}"')
    return ok(message=f'Curso "{course.title}" publicado exitosamente.', status=course.status)


@api_view(('GET',), roles=TEACHER)
def course_stats(request, course_id):
    """RF-16: estadísticas de estudiantes, progreso, evaluaciones, valoraciones y ventas."""
    course, problem = _own_course(request.user, course_id)
    if problem:
        return problem
    return ok(course={'id': course.id, 'title': course.title}, stats=compute_course_stats(course))


# ============================================
# MÓDULOS Y LECCIONES (RF-14)
# ============================================
@api_view(('POST',), roles=TEACHER)
def module_save(request, course_id=None, module_id=None):
    data = parse_body(request)
    title = (data.get('title') or '').strip()
    if not title:
        return error('El título del módulo es obligatorio.')
    if module_id:
        module, problem = _own_module(request.user, module_id)
        if problem:
            return problem
        module.title, module.description = title, (data.get('description') or '').strip()
        module.save()
        return ok(message='Módulo actualizado correctamente.')
    course, problem = _own_course(request.user, course_id)
    if problem:
        return problem
    Module.objects.create(course=course, title=title, description=(data.get('description') or '').strip(),
                          order=course.modules.count() + 1)
    return ok(message='Módulo creado correctamente.')


@api_view(('POST',), roles=TEACHER)
def module_delete(request, module_id):
    module, problem = _own_module(request.user, module_id)
    if problem:
        return problem
    title = module.title
    module.delete()
    return ok(message=f'Módulo "{title}" eliminado correctamente.')


def _swap(items, target, direction):
    items = list(items)
    idx = items.index(target)
    if direction == 'up' and idx > 0:
        items[idx], items[idx - 1] = items[idx - 1], items[idx]
    elif direction == 'down' and idx < len(items) - 1:
        items[idx], items[idx + 1] = items[idx + 1], items[idx]
    else:
        return False
    for i, item in enumerate(items, start=1):
        if item.order != i:
            item.order = i
            item.save(update_fields=['order'])
    return True


@api_view(('POST',), roles=TEACHER)
def module_move(request, module_id, direction):
    module, problem = _own_module(request.user, module_id)
    if problem:
        return problem
    if not _swap(module.course.modules.all(), module, direction):
        return error('Movimiento inválido.')
    return ok(message='Módulo reordenado.')


@api_view(('POST',), roles=TEACHER)
def lesson_move(request, lesson_id, direction):
    lesson, problem = _own_lesson(request.user, lesson_id)
    if problem:
        return problem
    if not _swap(lesson.module.lessons.all(), lesson, direction):
        return error('Movimiento inválido.')
    return ok(message='Lección reordenada.')


@api_view(('POST',), roles=TEACHER)
def lesson_delete(request, lesson_id):
    lesson, problem = _own_lesson(request.user, lesson_id)
    if problem:
        return problem
    title = lesson.title
    lesson.delete()
    return ok(message=f'Lección "{title}" eliminada correctamente.')


def _lesson_admin_json(request, lesson):
    data = {
        'id': lesson.id, 'title': lesson.title, 'description': lesson.description or '',
        'content': lesson.content or '', 'type': lesson.lesson_type, 'is_free': lesson.is_free,
        'duration_minutes': lesson.duration_minutes or 0, 'video_url': lesson.video_url or '',
        'video_file': media_url(request, lesson.video_file),
        'document_file': media_url(request, lesson.document_file),
        'deadline_days': lesson.assignment_deadline_days, 'deadline_hours': lesson.assignment_deadline_hours,
        'module_id': lesson.module_id, 'course_id': lesson.module.course_id, 'quiz': None,
    }
    evaluation = lesson.evaluations.first() if lesson.lesson_type in ('quiz', 'exam') else None
    if evaluation:
        data['quiz'] = {
            'time_limit_minutes': evaluation.time_limit_minutes, 'passing_score': evaluation.passing_score,
            'max_attempts': evaluation.max_attempts,
            'questions': [{
                'id': q.id, 'text': q.text, 'points': q.points,
                'options': [{'id': o.id, 'text': o.text, 'is_correct': o.is_correct} for o in q.options.all()],
            } for q in evaluation.questions.all().order_by('order').prefetch_related('options')],
        }
    return data


@api_view(('GET',), roles=TEACHER)
def lesson_detail(request, lesson_id):
    lesson, problem = _own_lesson(request.user, lesson_id)
    if problem:
        return problem
    return ok(lesson=_lesson_admin_json(request, lesson))


def _parse_questions(raw):
    """Acepta lista o texto JSON. Valida cada pregunta y devuelve (lista, error)."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw or '[]')
        except json.JSONDecodeError:
            return None, 'Formato de preguntas inválido.'
    questions = []
    for i, q in enumerate(raw or [], start=1):
        text = (q.get('text') or '').strip()
        options = [{'text': (o.get('text') or '').strip(), 'is_correct': bool(o.get('is_correct'))}
                   for o in (q.get('options') or []) if (o.get('text') or '').strip()]
        if not text:
            return None, f'La pregunta {i} no tiene enunciado.'
        if len(options) < 2:
            return None, f'La pregunta {i} necesita al menos 2 opciones.'
        if not any(o['is_correct'] for o in options):
            return None, f'Marca la respuesta correcta de la pregunta {i}.'
        try:
            points = max(int(q.get('points') or 1), 1)
        except (TypeError, ValueError):
            points = 1
        questions.append({'text': text, 'points': points, 'options': options})
    return questions, None


@api_view(('POST',), roles=TEACHER)
def lesson_save(request, module_id=None, lesson_id=None):
    """Crea (módulo) o modifica (lección) una lección de cualquier tipo, con su
    evaluación y preguntas si es cuestionario/examen (RF-14, RF-28)."""
    lesson = None
    if lesson_id:
        lesson, problem = _own_lesson(request.user, lesson_id)
        if problem:
            return problem
        module = lesson.module
    else:
        module, problem = _own_module(request.user, module_id)
        if problem:
            return problem

    data = parse_body(request)
    lesson_type = (data.get('type') or (lesson.lesson_type if lesson else 'text'))
    if lesson_type not in LESSON_TYPES:
        return error('Tipo de lección inválido.')
    title = (data.get('title') or '').strip()
    if len(title) < 3:
        return error('El título es obligatorio y debe tener al menos 3 caracteres.')
    content = (data.get('content') if 'content' in data else (lesson.content if lesson else '')) or ''
    content = content.strip()
    description = (data.get('description') or '').strip()
    try:
        duration = int(data.get('duration_minutes') or 0)
    except ValueError:
        duration = 0

    video_url = (data.get('video_url') or '').strip()
    video_file = request.FILES.get('video_file')
    document_file = request.FILES.get('document_file')
    if video_file:
        if (problem := validate_upload(video_file, 'video')):
            return error(problem)
    if document_file:
        if (problem := validate_upload(document_file, 'document')):
            return error(problem)

    if lesson_type == 'text' and not content:
        return error('El contenido es obligatorio.')
    if lesson_type == 'video' and not (video_url or video_file or (lesson and (lesson.video_url or lesson.video_file))):
        return error('Debes proporcionar una URL de video o subir un archivo.')
    if lesson_type == 'document' and not (document_file or (lesson and lesson.document_file)):
        return error('Debes subir el documento de la lección.')
    if lesson_type in ('quiz', 'exam') and not content:
        return error('Las instrucciones son obligatorias.')

    questions = None
    if lesson_type in ('quiz', 'exam'):
        raw = data.get('questions')
        if raw is not None:
            questions, problem = _parse_questions(raw)
            if problem:
                return error(problem)
        elif lesson is None:
            return error('Agrega al menos una pregunta.')
        if lesson is None and not questions:
            return error('Agrega al menos una pregunta.')

    with transaction.atomic():
        creating = lesson is None
        if creating:
            lesson = Lesson(module=module, order=module.lessons.count() + 1)
        lesson.title, lesson.description, lesson.content = title, description, content
        lesson.lesson_type = lesson_type
        lesson.is_free = _flag(data.get('is_free'))
        lesson.duration_minutes = duration
        if lesson_type == 'video':
            lesson.video_url = video_url
            if video_file:
                lesson.video_file = video_file
        if lesson_type == 'document' and document_file:
            lesson.document_file = document_file
        if lesson_type == 'assignment':
            lesson.assignment_deadline_days = int(data.get('deadline_days') or 7)
            lesson.assignment_deadline_hours = int(data.get('deadline_hours') or 0)
        lesson.save()

        if lesson_type in ('quiz', 'exam'):
            evaluation = lesson.evaluations.first()
            defaults = (60, 5) if lesson_type == 'exam' else (30, 10)
            try:
                time_limit = int(data.get('time_limit_minutes') or (evaluation.time_limit_minutes if evaluation else defaults[0]))
                passing = int(data.get('passing_score') or (evaluation.passing_score if evaluation else 70))
                attempts = int(data.get('max_attempts') or (evaluation.max_attempts if evaluation else 1))
            except ValueError:
                transaction.set_rollback(True)
                return error('Tiempo, puntaje o intentos inválidos.')
            if not (1 <= time_limit <= 600 and 1 <= passing <= 100 and 1 <= attempts <= defaults[1]):
                transaction.set_rollback(True)
                return error(f'Tiempo (1-600 min), puntaje (1-100) e intentos (1-{defaults[1]}) fuera de rango.')
            if evaluation is None:
                evaluation = Evaluation(lesson=lesson)
            evaluation.title = f'{"Examen" if lesson_type == "exam" else "Cuestionario"}: {title}'
            evaluation.description = content
            evaluation.evaluation_type = lesson_type
            evaluation.time_limit_minutes, evaluation.passing_score = time_limit, passing
            evaluation.max_attempts, evaluation.is_active = attempts, True
            evaluation.save()
            if questions is not None:
                evaluation.questions.all().delete()
                for n, q in enumerate(questions, start=1):
                    correct = sum(1 for o in q['options'] if o['is_correct'])
                    question = QuestionEvaluation.objects.create(
                        evaluation=evaluation, question_type='single' if correct == 1 else 'multiple',
                        text=q['text'], points=q['points'], order=n)
                    QuestionOption.objects.bulk_create([
                        QuestionOption(question=question, text=o['text'], is_correct=o['is_correct'])
                        for o in q['options']])
    log_action(request, request.user, 'course_edit',
               f'{"Creó" if creating else "Editó"} la lección "{title}" del curso "{module.course.title}"')
    return ok(message=f'Lección "{title}" {"creada" if creating else "actualizada"} correctamente.',
              lesson=_lesson_admin_json(request, lesson))


# ============================================
# RESULTADOS E INCIDENCIAS (RF-32)
# ============================================
@api_view(('GET',), roles=TEACHER)
def course_results(request, course_id):
    course, problem = _own_course(request.user, course_id)
    if problem:
        return problem
    results = (EvaluationResult.objects.filter(enrollment__course=course, completed_at__isnull=False)
               .select_related('evaluation__lesson', 'enrollment__student')
               .prefetch_related('incidents').order_by('-completed_at')[:200])
    return ok(course={'id': course.id, 'title': course.title}, results=[{
        'id': r.id, 'student': display_name(r.enrollment.student), 'evaluation': r.evaluation.lesson.title,
        'score': r.score, 'total_points': r.total_points,
        'percentage': round(r.score / r.total_points * 100) if r.total_points else 0,
        'passed': r.passed, 'attempt': r.attempt_number, 'time_spent': r.time_spent,
        'completed_at': r.completed_at.isoformat(),
        'incidents': [{'type': i.incident_type, 'type_label': i.get_incident_type_display(),
                       'description': i.description, 'at': i.created_at.isoformat()} for i in r.incidents.all()],
    } for r in results])


# ============================================
# TAREAS (calificación por el docente)
# ============================================
@api_view(('GET',), roles=TEACHER)
def assignment_submissions(request, lesson_id):
    lesson, problem = _own_lesson(request.user, lesson_id)
    if problem:
        return problem
    rows = AssignmentSubmission.objects.filter(lesson=lesson).select_related('student').order_by('-submitted_at')
    return ok(lesson={'id': lesson.id, 'title': lesson.title}, submissions=[{
        'id': s.id, 'student': display_name(s.student), 'file': media_url(request, s.file),
        'comment': s.comment or '', 'submitted_at': s.submitted_at.isoformat(), 'grade': s.grade,
        'feedback': s.feedback or '',
    } for s in rows])


@api_view(('POST',), roles=TEACHER)
def assignment_grade(request, submission_id):
    submission = get_object_or_404(AssignmentSubmission.objects.select_related('lesson__module__course', 'student'),
                                   id=submission_id)
    course = submission.lesson.module.course
    if request.user != course.teacher and request.user.role != 'admin':
        return error('No tienes permisos.', 403)
    data = parse_body(request)
    try:
        grade = int(data.get('grade'))
    except (TypeError, ValueError):
        return error('La nota debe ser un número entre 0 y 100.')
    if not 0 <= grade <= 100:
        return error('La nota debe estar entre 0 y 100.')
    submission.grade = grade
    submission.feedback = (data.get('feedback') or '').strip()
    submission.graded_at = timezone.now()
    submission.save()
    Notification.objects.create(user=submission.student, type='evaluation',
                                title=f'Tarea calificada: {submission.lesson.title}',
                                message=f'Recibiste {grade}/100 en la tarea "{submission.lesson.title}".')
    return ok(message='Tarea calificada.')


# ============================================
# CUPONES DEL DOCENTE (RF-36)
# ============================================
def _teacher_coupons(user):
    courses = Course.objects.all() if user.role == 'admin' else Course.objects.filter(teacher=user)
    return Coupon.objects.filter(course__in=courses)


@api_view(('GET',), roles=TEACHER)
def coupons(request):
    courses = Course.objects.all() if request.user.role == 'admin' else Course.objects.filter(teacher=request.user)
    rows = _teacher_coupons(request.user).select_related('course', 'created_by').order_by('-created_at')
    return ok(coupons=[coupon_row(c) for c in rows],
              courses=[{'id': c.id, 'title': c.title} for c in courses.filter(status='published')])


@api_view(('POST',), roles=TEACHER)
def coupon_save(request, coupon_id=None):
    if coupon_id:
        coupon = get_object_or_404(_teacher_coupons(request.user), id=coupon_id)
        saved, problem = save_coupon(request, coupon)
    else:
        course, problem = _own_course(request.user, parse_body(request).get('course'))
        if problem:
            return problem
        saved, problem = save_coupon(request, None, course)
    if problem:
        return problem
    return ok(message=f'Cupón {saved.code} guardado.', coupon=coupon_row(saved))


@api_view(('POST',), roles=TEACHER)
def coupon_toggle(request, coupon_id):
    coupon = get_object_or_404(_teacher_coupons(request.user), id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()
    return ok(message=f'Cupón {coupon.code} {"activado" if coupon.is_active else "desactivado"}.',
              coupon=coupon_row(coupon))


@api_view(('POST',), roles=TEACHER)
def coupon_delete(request, coupon_id):
    coupon = get_object_or_404(_teacher_coupons(request.user), id=coupon_id)
    code = coupon.code
    coupon.delete()
    return ok(message=f'Cupón {code} eliminado.')
