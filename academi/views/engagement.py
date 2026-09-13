from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..models import Lesson, Comment, Question, Answer, Course, Review, Enrollment, Report

# ============================================
# MÓDULO 5: APRENDIZAJE Y PARTICIPACIÓN (RF-35 al RF-42)
# ============================================


def _is_enrolled(user, course):
    return Enrollment.objects.filter(
        student=user, course=course, status__in=['enrolled', 'in_progress', 'completed']
    ).exists()


@login_required
def add_comment_view(request, lesson_id):
    """RF-35: comentar en una lección."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not _is_enrolled(request.user, course):
            messages.error(request, 'Debes estar inscrito en el curso para comentar.')
        elif not content:
            messages.error(request, 'Escribe un comentario antes de enviarlo.')
        else:
            Comment.objects.create(lesson=lesson, student=request.user, content=content)
            messages.success(request, 'Comentario publicado.')

    return redirect('lesson_view', lesson_id=lesson.id)


@login_required
def edit_comment_view(request, comment_id):
    """RF-36: gestionar (editar) comentarios propios."""
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.student != request.user:
        messages.error(request, 'No puedes editar el comentario de otro usuario.')
        return redirect('lesson_view', lesson_id=comment.lesson_id)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, 'El comentario no puede quedar vacío.')
        else:
            comment.content = content
            comment.is_edited = True
            comment.save()
            messages.success(request, 'Comentario actualizado.')

    return redirect('lesson_view', lesson_id=comment.lesson_id)


@login_required
def delete_comment_view(request, comment_id):
    """RF-36: gestionar (eliminar) comentarios propios."""
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.student != request.user and request.user.role != 'admin':
        messages.error(request, 'No puedes eliminar el comentario de otro usuario.')
        return redirect('lesson_view', lesson_id=comment.lesson_id)

    lesson_id = comment.lesson_id
    comment.delete()
    messages.success(request, 'Comentario eliminado.')
    return redirect('lesson_view', lesson_id=lesson_id)


@login_required
def add_question_view(request, lesson_id):
    """RF-37: realizar preguntas sobre las lecciones."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not _is_enrolled(request.user, course):
            messages.error(request, 'Debes estar inscrito en el curso para preguntar.')
        elif not content:
            messages.error(request, 'Escribe tu pregunta antes de enviarla.')
        else:
            Question.objects.create(lesson=lesson, student=request.user, content=content)
            messages.success(request, 'Pregunta enviada al docente.')

    return redirect('lesson_view', lesson_id=lesson.id)


@login_required
def answer_question_view(request, question_id):
    """RF-38: el docente responde preguntas sobre sus cursos."""
    question = get_object_or_404(Question, id=question_id)
    course = question.lesson.module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para responder esta pregunta.')
        return redirect('lesson_view', lesson_id=question.lesson_id)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, 'Escribe una respuesta antes de enviarla.')
        else:
            answer = Answer.objects.filter(question=question).first()
            if answer:
                answer.content = content
                answer.save()
            else:
                Answer.objects.create(question=question, teacher=request.user, content=content)
            question.is_answered = True
            question.save()
            messages.success(request, 'Respuesta publicada.')

    return redirect('lesson_view', lesson_id=question.lesson_id)


@login_required
def add_review_view(request, course_id):
    """RF-40: valorar y reseñar un curso adquirido."""
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        if not _is_enrolled(request.user, course):
            messages.error(request, 'Debes haber adquirido el curso para reseñarlo.')
        elif Review.objects.filter(student=request.user, course=course).exists():
            messages.error(request, 'Ya reseñaste este curso. Edita tu reseña existente.')
        else:
            try:
                rating = int(request.POST.get('rating', 0))
            except ValueError:
                rating = 0
            comment = request.POST.get('comment', '').strip()

            if rating not in (1, 2, 3, 4, 5):
                messages.error(request, 'Selecciona una valoración entre 1 y 5.')
            else:
                Review.objects.create(student=request.user, course=course, rating=rating, comment=comment)
                messages.success(request, 'Reseña publicada. ¡Gracias por tu opinión!')

    return redirect('course_detail', course_id=course.id)


@login_required
def edit_review_view(request, review_id):
    """RF-41: gestionar (editar) reseñas propias."""
    review = get_object_or_404(Review, id=review_id)
    if review.student != request.user:
        messages.error(request, 'No puedes editar la reseña de otro usuario.')
        return redirect('course_detail', course_id=review.course_id)

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 0))
        except ValueError:
            rating = 0
        comment = request.POST.get('comment', '').strip()

        if rating not in (1, 2, 3, 4, 5):
            messages.error(request, 'Selecciona una valoración entre 1 y 5.')
        else:
            review.rating = rating
            review.comment = comment
            review.is_edited = True
            review.save()
            messages.success(request, 'Reseña actualizada.')

    return redirect('course_detail', course_id=review.course_id)


@login_required
def delete_review_view(request, review_id):
    """RF-41: gestionar (eliminar) reseñas propias."""
    review = get_object_or_404(Review, id=review_id)
    if review.student != request.user and request.user.role != 'admin':
        messages.error(request, 'No puedes eliminar la reseña de otro usuario.')
        return redirect('course_detail', course_id=review.course_id)

    course_id = review.course_id
    review.delete()
    messages.success(request, 'Reseña eliminada.')
    return redirect('course_detail', course_id=course_id)


REPORTABLE_MODELS = {
    'comment': Comment,
    'question': Question,
    'review': Review,
}


@login_required
def report_content_view(request):
    """RF-42: reportar comentarios, preguntas o reseñas inapropiadas."""
    if request.method != 'POST':
        return redirect('dashboard')

    report_type = request.POST.get('report_type', '')
    content_id = request.POST.get('content_id', '')
    reason = request.POST.get('reason', '').strip()

    model = REPORTABLE_MODELS.get(report_type)
    obj = model.objects.filter(id=content_id).first() if model and content_id else None

    if not obj or not reason:
        messages.error(request, 'Datos de reporte incompletos.')
        return redirect('dashboard')

    Report.objects.create(
        reporter=request.user,
        report_type=report_type,
        content_id=obj.id,
        reason=reason,
    )
    obj.is_reported = True
    obj.save(update_fields=['is_reported'])
    messages.success(request, 'Reporte enviado. Un administrador lo revisará.')

    if report_type == 'review':
        return redirect('course_detail', course_id=obj.course_id)
    return redirect('lesson_view', lesson_id=obj.lesson_id)
