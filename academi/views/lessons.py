import json
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from ..models import (
    Module, Lesson, LessonResource, Evaluation, QuestionEvaluation,
    QuestionOption, Enrollment, LessonProgress, Comment, Question,
    AssignmentSubmission,
)
from ..utils import send_certificate_email, issue_certificate


# ============================================
# CRUD DE LECCIONES (desde la vista de gestión de curso)
# ============================================
@login_required
def add_lesson_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        lesson_type = request.POST.get('lesson_type')
        content = request.POST.get('content')
        is_free = request.POST.get('is_free') == 'on'

        if not title:
            messages.error(request, 'El título de la lección es obligatorio.')
            return render(request, 'academi/courses/crear_leccion.html', {'module': module})

        last_order = module.lessons.count()
        Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            lesson_type=lesson_type or 'text',
            content=content,
            is_free=is_free,
            order=last_order + 1
        )
        messages.success(request, 'Lección creada correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/courses/crear_leccion.html', {'module': module})


@login_required
def edit_lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    # ============================================
    # DETERMINAR TEMPLATE
    # ============================================
    template_map = {
        'text': 'academi/courses/lecciones/crear_texto.html',
        'video': 'academi/courses/lecciones/crear_video.html',
        'document': 'academi/courses/lecciones/crear_documento.html',
        'quiz': 'academi/courses/lecciones/crear_cuestionario.html',
        'exam': 'academi/courses/lecciones/crear_cuestionario.html',
        'assignment': 'academi/courses/lecciones/crear_tarea.html',
    }

    template = template_map.get(lesson.lesson_type, 'academi/courses/lecciones/crear_texto.html')

    # ============================================
    # POST - GUARDAR CAMBIOS
    # ============================================
    if request.method == 'POST':
        lesson.title = request.POST.get('title', lesson.title)
        lesson.description = request.POST.get('description', lesson.description)
        lesson.content = request.POST.get('content', lesson.content)
        lesson.is_free = request.POST.get('is_free') == 'on'
        lesson.lesson_type = request.POST.get('lesson_type', lesson.lesson_type)
        lesson.duration_minutes = request.POST.get('duration', lesson.duration_minutes)

        if lesson.lesson_type == 'video':
            lesson.video_url = request.POST.get('video_url', lesson.video_url)
            if request.FILES.get('video_file'):
                lesson.video_file = request.FILES.get('video_file')

        if lesson.lesson_type == 'document':
            if request.FILES.get('document_file'):
                lesson.document_file = request.FILES.get('document_file')

        if lesson.lesson_type == 'assignment':
            lesson.assignment_deadline_days = request.POST.get('assignment_deadline_days', 7)
            lesson.assignment_deadline_hours = request.POST.get('assignment_deadline_hours', 0)

        lesson.save()

        # Si es cuestionario/examen, actualizar evaluación
        if lesson.lesson_type in ['quiz', 'exam']:
            evaluation = Evaluation.objects.filter(lesson=lesson).first()
            if evaluation:
                evaluation.title = f'{lesson.get_lesson_type_display()}: {lesson.title}'
                evaluation.description = lesson.content
                evaluation.time_limit_minutes = request.POST.get('time_limit', 30)
                evaluation.passing_score = request.POST.get('passing_score', 70)
                evaluation.max_attempts = request.POST.get('max_attempts', 1)
                evaluation.save()

                # Eliminar preguntas y opciones existentes
                QuestionEvaluation.objects.filter(evaluation=evaluation).delete()

                # Recrear preguntas y opciones
                question_count = 0
                for key, value in request.POST.items():
                    if key.startswith('question_') and key.endswith('_text'):
                        parts = key.split('_')
                        if len(parts) >= 3:
                            q_num = parts[1]
                            if q_num.isdigit():
                                question_text = value.strip()
                                if question_text:
                                    question_count += 1
                                    question = QuestionEvaluation.objects.create(
                                        evaluation=evaluation,
                                        question_type='multiple',
                                        text=question_text,
                                        points=1,
                                        order=question_count
                                    )

                                    option_count = 0
                                    for opt_key, opt_value in request.POST.items():
                                        if opt_key.startswith(f'question_{q_num}_option_'):
                                            opt_parts = opt_key.split('_')
                                            if len(opt_parts) >= 5:
                                                opt_index = opt_parts[3]
                                                if opt_index.isdigit() and opt_value.strip():
                                                    correct_key = f'question_{q_num}_correct_{opt_index}'
                                                    is_correct = correct_key in request.POST
                                                    QuestionOption.objects.create(
                                                        question=question,
                                                        text=opt_value.strip(),
                                                        is_correct=is_correct
                                                    )
                                                    option_count += 1

                                    if option_count == 0:
                                        default_options = ['Opción A', 'Opción B', 'Opción C', 'Opción D']
                                        for i, opt_text in enumerate(default_options):
                                            QuestionOption.objects.create(
                                                question=question,
                                                text=opt_text,
                                                is_correct=(i == 0)
                                            )

        messages.success(request, f'Lección "{lesson.title}" actualizada correctamente.')
        return redirect('manage_course', course_id=course.id)

    # ============================================
    # GET - PREPARAR DATOS PARA EL TEMPLATE
    # ============================================

    form_data = {
        'title': lesson.title,
        'description': lesson.description,
        'content': lesson.content,
        'is_free': lesson.is_free,
        'duration': lesson.duration_minutes,
        'video_url': lesson.video_url,
        'time_limit': 30,
        'passing_score': 70,
        'max_attempts': 1,
        'assignment_deadline_days': 7,
        'assignment_deadline_hours': 0,
    }

    # ============================================
    # OBTENER PREGUNTAS EXISTENTES
    # ============================================
    preguntas = []

    if lesson.lesson_type in ['quiz', 'exam']:
        evaluation = Evaluation.objects.filter(lesson=lesson).first()

        if evaluation:
            form_data['time_limit'] = evaluation.time_limit_minutes
            form_data['passing_score'] = evaluation.passing_score
            form_data['max_attempts'] = evaluation.max_attempts

            questions = QuestionEvaluation.objects.filter(evaluation=evaluation).order_by('order')

            for q in questions:
                options = QuestionOption.objects.filter(question=q)
                preguntas.append({
                    'id': q.id,
                    'text': q.text,
                    'question_type': q.question_type,
                    'points': q.points,
                    'order': q.order,
                    'options': [
                        {
                            'id': opt.id,
                            'text': opt.text,
                            'is_correct': opt.is_correct
                        } for opt in options
                    ]
                })

    # ============================================
    # CONVERTIR A JSON PARA EL JAVASCRIPT
    # ============================================
    preguntas_json = json.dumps(preguntas, default=str)

    # Obtener datos de tarea
    if lesson.lesson_type == 'assignment':
        form_data['assignment_deadline_days'] = lesson.assignment_deadline_days or 7
        form_data['assignment_deadline_hours'] = lesson.assignment_deadline_hours or 0

    # Configurar según tipo
    if lesson.lesson_type == 'exam':
        titulo_pagina = 'Editar examen'
        icono = 'fas fa-clipboard-list'
        tiempo_limite_default = form_data['time_limit']
        intentos_default = form_data['max_attempts']
        max_intentos = 5
        nota = 'Los exámenes son más extensos que los cuestionarios.'
    elif lesson.lesson_type == 'quiz':
        titulo_pagina = 'Editar cuestionario'
        icono = 'fas fa-tasks'
        tiempo_limite_default = form_data['time_limit']
        intentos_default = form_data['max_attempts']
        max_intentos = 10
        nota = 'Las preguntas y opciones se guardan al editar el cuestionario.'
    else:
        titulo_pagina = f'Editar lección de {lesson.get_lesson_type_display()}'
        icono = 'fas fa-edit'
        tiempo_limite_default = 30
        intentos_default = 1
        max_intentos = 10
        nota = ''

    # ============================================
    # RENDERIZAR CON TODOS LOS DATOS
    # ============================================
    return render(request, template, {
        'module': lesson.module,
        'lesson': lesson,
        'form_data': form_data,
        'preguntas': preguntas,  # Para el template (si se usa)
        'preguntas_json': preguntas_json,  # Para el JavaScript
        'titulo_pagina': titulo_pagina,
        'icono': icono,
        'tiempo_limite_default': tiempo_limite_default,
        'intentos_default': intentos_default,
        'max_intentos': max_intentos,
        'nota': nota,
        'es_edicion': True,
    })


@login_required
def delete_lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = lesson.title
        lesson.delete()
        messages.success(request, f'Lección "{title}" eliminada correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/courses/eliminar_leccion.html', {'lesson': lesson})


@login_required
def reorder_lesson_view(request, lesson_id, direction):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    module = lesson.module
    course = module.course

    if request.user != course.teacher and request.user.role != 'admin':
        return JsonResponse({'error': 'Sin permisos'}, status=403)

    lessons = list(module.lessons.all())
    current_index = lessons.index(lesson)

    if direction == 'up' and current_index > 0:
        lessons[current_index], lessons[current_index - 1] = lessons[current_index - 1], lessons[current_index]
    elif direction == 'down' and current_index < len(lessons) - 1:
        lessons[current_index], lessons[current_index + 1] = lessons[current_index + 1], lessons[current_index]
    else:
        return JsonResponse({'error': 'Movimiento inválido'}, status=400)

    for i, l in enumerate(lessons, start=1):
        l.order = i
        l.save()

    return JsonResponse({'success': True})


@login_required
def upload_video_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    if request.method == 'POST':
        video = request.FILES.get('video')
        if video:
            lesson.video_file = video
            lesson.lesson_type = 'video'
            lesson.save()
            messages.success(request, 'Video subido correctamente.')
        else:
            messages.error(request, 'No se seleccionó ningún video.')
        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/courses/subir_video.html', {'lesson': lesson})


@login_required
def upload_document_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    if request.method == 'POST':
        document = request.FILES.get('document')
        if document:
            LessonResource.objects.create(
                lesson=lesson,
                title=document.name,
                file=document,
                file_type='other'
            )
            lesson.lesson_type = 'document'
            lesson.save()
            messages.success(request, 'Documento subido correctamente.')
        else:
            messages.error(request, 'No se seleccionó ningún documento.')
        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/courses/subir_documento.html', {'lesson': lesson})


# ============================================
# APRENDIZAJE - VISTA DE LECCIÓN
# ============================================
@login_required
def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    is_teacher_of_course = request.user == course.teacher or request.user.role == 'admin'

    enrollment = None
    if not is_teacher_of_course:
        enrollment = get_object_or_404(
            Enrollment,
            student=request.user,
            course=course,
            status__in=['enrolled', 'in_progress', 'completed']
        )

    # ============================================
    # PROCESAR URL DE YOUTUBE
    # ============================================
    youtube_embed_url = None
    youtube_video_id = None
    youtube_thumbnail = None
    is_youtube = False

    if lesson.video_url:
        video_url = lesson.video_url.strip()

        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)',
            r'youtube\.com\/shorts\/([^&\n?#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                youtube_video_id = match.group(1)
                youtube_video_id = youtube_video_id.split('?')[0].split('&')[0]
                is_youtube = True
                break

        if youtube_video_id:
            youtube_embed_url = (
                f'https://www.youtube-nocookie.com/embed/{youtube_video_id}'
                f'?autoplay=0&rel=0&modestbranding=1&enablejsapi=1'
                f'&origin={request.build_absolute_uri("/")[:-1]}'
                f'&iv_load_policy=3'
            )
            youtube_thumbnail = f'https://img.youtube.com/vi/{youtube_video_id}/maxresdefault.jpg'

    # ============================================
    # MARCAR LECCIÓN COMO VISTA Y CALCULAR PROGRESO
    # (solo aplica al estudiante inscrito, no al
    # docente/admin que solo consulta la lección)
    # ============================================
    progress = 0
    completed_count = 0
    total_lessons = 0

    if enrollment:
        lesson_progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={
                'completed': False,
                'completed_at': None,
                'last_accessed': timezone.now()
            }
        )
        lesson_progress.last_accessed = timezone.now()
        lesson_progress.save()

        modules = course.modules.all()
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
        if progress == 100 and enrollment.status != 'completed':
            enrollment.status = 'completed'
            enrollment.completed_date = timezone.now()
        elif progress > 0 and enrollment.status == 'enrolled':
            enrollment.status = 'in_progress'
        enrollment.save()

    # ============================================
    # OBTENER SIGUIENTE LECCIÓN
    # ============================================
    next_lesson = None
    lessons = list(Lesson.objects.filter(
        module__course=course
    ).order_by('module__order', 'order'))

    for i, l in enumerate(lessons):
        if l.id == lesson.id and i < len(lessons) - 1:
            next_lesson = lessons[i + 1]
            break

    # ============================================
    # VERIFICAR SI ES CUESTIONARIO
    # ============================================
    is_quiz = lesson.lesson_type in ['quiz', 'exam']
    has_evaluation = False
    evaluation = None

    if is_quiz:
        evaluation = lesson.evaluations.first()
        if evaluation:
            has_evaluation = True

    # ============================================
    # COMENTARIOS Y PREGUNTAS (RF-35 al RF-39)
    # ============================================
    comments = Comment.objects.filter(lesson=lesson).select_related('student').order_by('-created_at')
    questions = Question.objects.filter(lesson=lesson).select_related('student').prefetch_related('answers__teacher').order_by('-created_at')

    # ============================================
    # ENTREGA DE TAREA (solo lecciones tipo 'assignment')
    # ============================================
    my_submission = None
    if lesson.lesson_type == 'assignment' and not is_teacher_of_course:
        my_submission = AssignmentSubmission.objects.filter(lesson=lesson, student=request.user).first()

    # ============================================
    # CONTEXTO
    # ============================================
    context = {
        'lesson': lesson,
        'course': course,
        'enrollment': enrollment,
        'next_lesson': next_lesson,
        'progress': progress,
        'completed_count': completed_count,
        'total_lessons': total_lessons,
        'youtube_embed_url': youtube_embed_url,
        'youtube_video_id': youtube_video_id,
        'youtube_thumbnail': youtube_thumbnail,
        'is_youtube': is_youtube,
        'is_quiz': is_quiz,
        'has_evaluation': has_evaluation,
        'evaluation': evaluation,
        'comments': comments,
        'questions': questions,
        'is_teacher_of_course': is_teacher_of_course,
        'my_submission': my_submission,
    }

    return render(request, 'academi/courses/leccion_detalle.html', context)


@login_required
def mark_lesson_complete(request, lesson_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=course,
        status__in=['enrolled', 'in_progress', 'completed']
    )

    lesson_progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
        defaults={'completed': True, 'completed_at': timezone.now()}
    )

    if not lesson_progress.completed:
        lesson_progress.completed = True
        lesson_progress.completed_at = timezone.now()
        lesson_progress.save()

    modules = course.modules.all()
    total_lessons = 0
    completed_count = 0

    for module in modules:
        for l in module.lessons.all():
            total_lessons += 1
            if LessonProgress.objects.filter(enrollment=enrollment, lesson=l, completed=True).exists():
                completed_count += 1

    progress = int((completed_count / total_lessons * 100)) if total_lessons > 0 else 0
    enrollment.progress_percentage = progress
    just_completed = False
    if progress == 100 and enrollment.status != 'completed':
        enrollment.status = 'completed'
        enrollment.completed_date = timezone.now()
        just_completed = True
    elif progress > 0 and enrollment.status == 'enrolled':
        enrollment.status = 'in_progress'
    enrollment.save()

    certificate_id = None
    if just_completed:
        certificate, _ = issue_certificate(enrollment)
        certificate_id = certificate.id

        # RF-66: enviar el certificado al correo automáticamente al emitirse.
        try:
            send_certificate_email(certificate, request)
        except Exception:
            pass  # La emisión del certificado no debe fallar si el correo falla.

    return JsonResponse({
        'success': True,
        'progress': progress,
        'completed_count': completed_count,
        'total_lessons': total_lessons,
        'message': 'Lección completada',
        'course_completed': just_completed,
        'certificate_id': certificate_id,
    })


# ============================================
# CREAR LECCIONES POR TIPO
# ============================================
def get_module_and_check_permission(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course
    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para crear lecciones en este curso.')
        return None, None
    return module, course


def render_lesson_form(request, module, template, form_data=None):
    return render(request, template, {
        'module': module,
        'form_data': form_data or {}
    })


@login_required
def create_lesson_text_view(request, module_id):
    module, course = get_module_and_check_permission(request, module_id)
    if not module:
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        content = request.POST.get('content', '').strip()
        is_free = request.POST.get('is_free') == 'on'
        duration = request.POST.get('duration', 0)

        if not title or len(title) < 3:
            messages.error(request, 'El título es obligatorio y debe tener al menos 3 caracteres.')
            return render_lesson_form(request, module, 'academi/courses/lecciones/crear_texto.html', request.POST)

        if not content:
            messages.error(request, 'El contenido es obligatorio.')
            return render_lesson_form(request, module, 'academi/courses/lecciones/crear_texto.html', request.POST)

        try:
            duration = int(duration) if duration else 0
        except ValueError:
            duration = 0

        last_order = module.lessons.count()
        lesson = Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            lesson_type='text',
            content=content,
            is_free=is_free,
            duration_minutes=duration,
            order=last_order + 1
        )

        messages.success(request, f'Lección de texto "{title}" creada correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render_lesson_form(request, module, 'academi/courses/lecciones/crear_texto.html')


@login_required
def create_lesson_video_view(request, module_id):
    module, course = get_module_and_check_permission(request, module_id)
    if not module:
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        content = request.POST.get('content', '').strip()
        is_free = request.POST.get('is_free') == 'on'
        duration = request.POST.get('duration', 0)
        video_url = request.POST.get('video_url', '').strip()
        video_file = request.FILES.get('video_file')

        if not title or len(title) < 3:
            messages.error(request, 'El título es obligatorio y debe tener al menos 3 caracteres.')
            return render_lesson_form(request, module, 'academi/courses/lecciones/crear_video.html', request.POST)

        if not video_url and not video_file:
            messages.error(request, 'Debes proporcionar una URL de video o subir un archivo.')
            return render_lesson_form(request, module, 'academi/courses/lecciones/crear_video.html', request.POST)

        try:
            duration = int(duration) if duration else 0
        except ValueError:
            duration = 0

        last_order = module.lessons.count()
        lesson = Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            lesson_type='video',
            content=content,
            is_free=is_free,
            duration_minutes=duration,
            video_url=video_url,
            order=last_order + 1
        )

        if video_file:
            lesson.video_file = video_file
            lesson.save()

        messages.success(request, f'Lección de video "{title}" creada correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render_lesson_form(request, module, 'academi/courses/lecciones/crear_video.html')


@login_required
def create_lesson_document_view(request, module_id):
    module, course = get_module_and_check_permission(request, module_id)
    if not module:
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        content = request.POST.get('content', '').strip()
        is_free = request.POST.get('is_free') == 'on'
        duration = request.POST.get('duration', 0)
        document_file = request.FILES.get('document_file')

        if not title or len(title) < 3:
            messages.error(request, 'El título es obligatorio y debe tener al menos 3 caracteres.')
            return render_lesson_form(request, module, 'academi/courses/lecciones/crear_documento.html', request.POST)

        if not document_file:
            messages.error(request, 'Debes subir un archivo de documento.')
            return render_lesson_form(request, module, 'academi/courses/lecciones/crear_documento.html', request.POST)

        try:
            duration = int(duration) if duration else 0
        except ValueError:
            duration = 0

        last_order = module.lessons.count()
        lesson = Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            lesson_type='document',
            content=content,
            is_free=is_free,
            duration_minutes=duration,
            order=last_order + 1
        )

        lesson.document_file = document_file
        lesson.save()

        messages.success(request, f'Lección de documento "{title}" creada correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render_lesson_form(request, module, 'academi/courses/lecciones/crear_documento.html')


@login_required
def create_lesson_quiz_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    tipo = request.GET.get('tipo', 'cuestionario')
    es_examen = tipo == 'examen'

    if es_examen:
        tiempo_limite_default = 60
        intentos_default = 1
        max_intentos = 5
        titulo_pagina = 'Crear examen'
        icono = 'fas fa-clipboard-list'
        nota = 'Los exámenes son más extensos que los cuestionarios y cubren todo el módulo.'
        tipo_evaluacion = 'exam'
    else:
        tiempo_limite_default = 30
        intentos_default = 1
        max_intentos = 10
        titulo_pagina = 'Crear cuestionario'
        icono = 'fas fa-tasks'
        nota = 'Las preguntas y opciones se guardan al crear el cuestionario.'
        tipo_evaluacion = 'quiz'

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        content = request.POST.get('content', '').strip()
        is_free = request.POST.get('is_free') == 'on'
        duration = request.POST.get('duration', 0)
        time_limit = request.POST.get('time_limit', tiempo_limite_default)
        passing_score = request.POST.get('passing_score', 70)
        max_attempts = request.POST.get('max_attempts', intentos_default)

        if not title or len(title) < 3:
            messages.error(request, 'El título es obligatorio y debe tener al menos 3 caracteres.')
            return render(request, 'academi/courses/lecciones/crear_cuestionario.html', {
                'module': module,
                'form_data': request.POST,
                'titulo_pagina': titulo_pagina,
                'icono': icono,
                'tiempo_limite_default': tiempo_limite_default,
                'intentos_default': intentos_default,
                'max_intentos': max_intentos,
                'nota': nota,
            })

        if not content:
            messages.error(request, 'Las instrucciones son obligatorias.')
            return render(request, 'academi/courses/lecciones/crear_cuestionario.html', {
                'module': module,
                'form_data': request.POST,
                'titulo_pagina': titulo_pagina,
                'icono': icono,
                'tiempo_limite_default': tiempo_limite_default,
                'intentos_default': intentos_default,
                'max_intentos': max_intentos,
                'nota': nota,
            })

        try:
            duration = int(duration) if duration else 0
            time_limit = int(time_limit) if time_limit else tiempo_limite_default
            passing_score = int(passing_score) if passing_score else 70
            max_attempts = int(max_attempts) if max_attempts else intentos_default
        except ValueError:
            time_limit = tiempo_limite_default
            passing_score = 70
            max_attempts = intentos_default

        last_order = module.lessons.count()
        lesson = Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            lesson_type=tipo_evaluacion,
            content=content,
            is_free=is_free,
            duration_minutes=duration,
            order=last_order + 1
        )

        evaluation = Evaluation.objects.create(
            lesson=lesson,
            title=f'{titulo_pagina}: {title}',
            description=content,
            evaluation_type=tipo_evaluacion,
            time_limit_minutes=time_limit,
            passing_score=passing_score,
            max_attempts=max_attempts,
            is_active=True
        )

        # ============================================
        # PROCESAR PREGUNTAS Y OPCIONES
        # ============================================
        question_count = 0

        preguntas_data = {}
        for key, value in request.POST.items():
            if key.startswith('question_') and key.endswith('_text'):
                parts = key.split('_')
                if len(parts) >= 3:
                    q_num = parts[1]
                    if q_num.isdigit():
                        preguntas_data[q_num] = value.strip()

        for q_num, question_text in preguntas_data.items():
            if not question_text:
                continue

            question_count += 1

            question = QuestionEvaluation.objects.create(
                evaluation=evaluation,
                question_type='multiple',
                text=question_text,
                points=1,
                order=question_count
            )

            option_count = 0

            for opt_key, opt_value in request.POST.items():
                prefix = f'question_{q_num}_option_'
                if opt_key.startswith(prefix):
                    opt_index = opt_key[len(prefix):]

                    if opt_index.isdigit() and opt_value.strip():
                        correct_key = f'question_{q_num}_correct_{opt_index}'
                        is_correct = correct_key in request.POST

                        QuestionOption.objects.create(
                            question=question,
                            text=opt_value.strip(),
                            is_correct=is_correct
                        )
                        option_count += 1

            if option_count == 0:
                default_options = ['Opción A', 'Opción B', 'Opción C', 'Opción D']
                for i, opt_text in enumerate(default_options):
                    QuestionOption.objects.create(
                        question=question,
                        text=opt_text,
                        is_correct=(i == 0)
                    )

        if question_count == 0:
            messages.warning(request, f'No se agregaron preguntas al {titulo_pagina.lower()}. Puedes editarlo después.')
        else:
            messages.success(request, f'{titulo_pagina} "{title}" creado con {question_count} preguntas.')

        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/courses/lecciones/crear_cuestionario.html', {
        'module': module,
        'titulo_pagina': titulo_pagina,
        'icono': icono,
        'tiempo_limite_default': tiempo_limite_default,
        'intentos_default': intentos_default,
        'max_intentos': max_intentos,
        'nota': nota,
        'es_edicion': False,
    })


@login_required
def create_lesson_assignment_view(request, module_id):
    module, course = get_module_and_check_permission(request, module_id)
    if not module:
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        content = request.POST.get('content', '').strip()
        is_free = request.POST.get('is_free') == 'on'
        duration = request.POST.get('duration', 0)
        assignment_deadline_days = request.POST.get('assignment_deadline_days', 7)
        assignment_deadline_hours = request.POST.get('assignment_deadline_hours', 0)

        if not title or len(title) < 3:
            messages.error(request, 'El título es obligatorio y debe tener al menos 3 caracteres.')
            return render(request, 'academi/courses/lecciones/crear_tarea.html', {
                'module': module,
                'form_data': request.POST
            })

        if not content:
            messages.error(request, 'La descripción de la tarea es obligatoria.')
            return render(request, 'academi/courses/lecciones/crear_tarea.html', {
                'module': module,
                'form_data': request.POST
            })

        try:
            duration = int(duration) if duration else 0
            assignment_deadline_days = int(assignment_deadline_days) if assignment_deadline_days else 7
            assignment_deadline_hours = int(assignment_deadline_hours) if assignment_deadline_hours else 0
        except ValueError:
            assignment_deadline_days = 7
            assignment_deadline_hours = 0

        last_order = module.lessons.count()
        lesson = Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            lesson_type='assignment',
            content=content,
            is_free=is_free,
            duration_minutes=duration,
            order=last_order + 1,
            assignment_deadline_days=assignment_deadline_days,
            assignment_deadline_hours=assignment_deadline_hours
        )

        messages.success(request, f'Tarea "{title}" creada correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/courses/lecciones/crear_tarea.html', {'module': module})


# ============================================
# ENTREGA DE TAREAS (lecciones tipo 'assignment')
# ============================================
@login_required
def submit_assignment_view(request, lesson_id):
    """El estudiante sube (o vuelve a subir) su entrega de una tarea."""
    lesson = get_object_or_404(Lesson, id=lesson_id, lesson_type='assignment')
    course = lesson.module.course

    if not Enrollment.objects.filter(
        student=request.user, course=course, status__in=['enrolled', 'in_progress', 'completed']
    ).exists():
        messages.error(request, 'Debes estar inscrito en el curso para entregar esta tarea.')
        return redirect('lesson_view', lesson_id=lesson.id)

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        comment = request.POST.get('comment', '').strip()

        if not uploaded_file:
            messages.error(request, 'Selecciona un archivo para entregar.')
        else:
            submission, created = AssignmentSubmission.objects.update_or_create(
                lesson=lesson, student=request.user,
                defaults={'file': uploaded_file, 'comment': comment},
            )
            if not created:
                submission.grade = None
                submission.feedback = None
                submission.graded_at = None
                submission.save()
            messages.success(request, 'Tarea entregada correctamente.')

    return redirect('lesson_view', lesson_id=lesson.id)


@login_required
def assignment_submissions_view(request, lesson_id):
    """RF-19: el docente consulta y califica las entregas de una tarea."""
    lesson = get_object_or_404(Lesson, id=lesson_id, lesson_type='assignment')
    course = lesson.module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    submissions = AssignmentSubmission.objects.filter(lesson=lesson).select_related('student').order_by('-submitted_at')

    return render(request, 'academi/courses/lecciones/entregas_tarea.html', {
        'lesson': lesson,
        'course': course,
        'submissions': submissions,
    })


@login_required
def grade_assignment_view(request, submission_id):
    """RF-19: el docente califica una entrega de tarea."""
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    course = submission.lesson.module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            grade = int(request.POST.get('grade', ''))
        except ValueError:
            grade = None
        feedback = request.POST.get('feedback', '').strip()

        if grade is None or not (0 <= grade <= 100):
            messages.error(request, 'La calificación debe ser un número entre 0 y 100.')
        else:
            submission.grade = grade
            submission.feedback = feedback
            submission.graded_at = timezone.now()
            submission.save()
            messages.success(request, f'Entrega de {submission.student.username} calificada.')

    return redirect('assignment_submissions', lesson_id=submission.lesson_id)
