"""Reseñas, reportes, notificaciones, certificados, calificaciones y chatbot."""
import time

from django.shortcuts import get_object_or_404

from ..models import (
    Course, Comment, Question, Review, Report, Notification, Certificate, EvaluationResult,
    Enrollment, ChatSession, ChatMessage, ChatAnalytics,
)
from ..utils.ai_chatbot import get_ai_response
from ..utils import send_certificate_email
from ..views.chatbot import build_platform_context, get_chat_history, match_knowledge_base
from .auth import api_view, error, ok, parse_body
from .serializers import ACTIVE_STATUSES, certificate_json, review_json

REPORTABLE = {'comment': Comment, 'question': Question, 'review': Review, 'course': Course}


# ============================================
# RESEÑAS Y REPORTES
# ============================================
def _valid_rating(value):
    try:
        rating = int(value)
    except (TypeError, ValueError):
        return None
    return rating if rating in (1, 2, 3, 4, 5) else None


@api_view(('POST',), roles=('student',))
def review_save(request, course_id):
    """Crea la reseña del estudiante o actualiza la que ya tenía."""
    course = get_object_or_404(Course, id=course_id, status='published')
    if not Enrollment.objects.filter(student=request.user, course=course, status__in=ACTIVE_STATUSES).exists():
        return error('Debes haber adquirido el curso para reseñarlo.', 403)
    data = parse_body(request)
    rating = _valid_rating(data.get('rating'))
    if rating is None:
        return error('Selecciona una valoración entre 1 y 5.')
    comment = (data.get('comment') or '').strip()

    review = Review.objects.filter(student=request.user, course=course).first()
    if review:
        review.rating, review.comment, review.is_edited = rating, comment, True
        review.save()
    else:
        review = Review.objects.create(student=request.user, course=course, rating=rating, comment=comment)
    return ok(review=review_json(request, review), message='Reseña publicada. ¡Gracias por tu opinión!')


@api_view(('POST',))
def review_delete(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if review.student_id != request.user.id and request.user.role != 'admin':
        return error('No puedes eliminar la reseña de otro usuario.', 403)
    review.delete()
    return ok(message='Reseña eliminada.')


@api_view(('POST',))
def report_content(request):
    data = parse_body(request)
    report_type = data.get('report_type', '')
    reason = (data.get('reason') or '').strip()
    model = REPORTABLE.get(report_type)
    obj = model.objects.filter(id=data.get('content_id') or 0).first() if model else None
    if not obj or not reason:
        return error('Datos de reporte incompletos.')
    Report.objects.create(reporter=request.user, report_type=report_type, content_id=obj.id, reason=reason)
    obj.is_reported = True
    obj.save(update_fields=['is_reported'])
    return ok(message='Reporte enviado. Un administrador lo revisará.')


# ============================================
# NOTIFICACIONES
# ============================================
def _notification_json(n):
    return {'id': n.id, 'type': n.type, 'title': n.title, 'message': n.message,
            'is_read': n.is_read, 'created_at': n.created_at.isoformat()}


@api_view(('GET',))
def notifications(request):
    rows = Notification.objects.filter(user=request.user).order_by('-created_at')[:100]
    return ok(notifications=[_notification_json(n) for n in rows],
              unread=Notification.objects.filter(user=request.user, is_read=False).count())


@api_view(('POST',))
def notifications_read_all(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return ok()


@api_view(('POST',))
def notification_read(request, notification_id):
    Notification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
    return ok()


# ============================================
# CERTIFICADOS Y CALIFICACIONES
# ============================================
@api_view(('GET',), roles=('student',))
def certificates(request):
    rows = (Certificate.objects.filter(enrollment__student=request.user)
            .select_related('enrollment__course', 'enrollment__student').order_by('-issued_at'))
    return ok(certificates=[certificate_json(request, c) for c in rows])


@api_view(('GET',), roles=('student',))
def certificate_detail(request, certificate_id):
    c = get_object_or_404(Certificate.objects.select_related('enrollment__course', 'enrollment__student'),
                          id=certificate_id, enrollment__student=request.user)
    return ok(certificate=certificate_json(request, c))


@api_view(('POST',), roles=('student',))
def certificate_email(request, certificate_id):
    """RF-41: envía el certificado al correo registrado del estudiante."""
    c = get_object_or_404(Certificate.objects.select_related('enrollment__course', 'enrollment__student'),
                          id=certificate_id, enrollment__student=request.user)
    if c.is_revoked:
        return error('Este certificado fue revocado y no puede enviarse.')
    try:
        send_certificate_email(c, request)
    except Exception:
        return error('No pudimos enviar el correo. Intenta nuevamente.', 500)
    return ok(message=f'Te enviamos el certificado a {request.user.email}.')


@api_view(('GET',), auth='none')
def certificate_verify(request, code):
    """RF-67: verificación pública por código."""
    c = (Certificate.objects.filter(certificate_code=code.strip().upper())
         .select_related('enrollment__student', 'enrollment__course').first())
    if not c:
        return ok(valid=False)
    c.verify()
    return ok(valid=not c.is_revoked, certificate=certificate_json(request, c))


@api_view(('GET',), roles=('student',))
def grades(request):
    results = (EvaluationResult.objects.filter(enrollment__student=request.user, completed_at__isnull=False)
               .select_related('evaluation', 'enrollment__course').order_by('-completed_at'))
    return ok(results=[{
        'id': r.id, 'course': r.enrollment.course.title, 'course_id': r.enrollment.course_id,
        'evaluation': r.evaluation.title, 'score': r.score, 'total_points': r.total_points,
        'percentage': round(r.score / r.total_points * 100) if r.total_points else 0,
        'passed': r.passed, 'attempt': r.attempt_number,
        'completed_at': r.completed_at.isoformat(),
    } for r in results])


# ============================================
# CHATBOT
# ============================================
def _message_json(m):
    return {'id': m.id, 'sender': m.sender, 'message': m.message, 'created_at': m.created_at.isoformat()}


@api_view(('GET',))
def chatbot_history(request):
    session = ChatSession.objects.filter(user=request.user, is_active=True).first()
    if not session:
        return ok(messages=[])
    rows = session.messages.order_by('-created_at')[:40][::-1]
    return ok(messages=[_message_json(m) for m in rows])


@api_view(('POST',))
def chatbot_send(request):
    text = (parse_body(request).get('message') or '').strip()
    if not text:
        return error('Escribe un mensaje.')

    session, _ = ChatSession.objects.get_or_create(user=request.user, is_active=True, defaults={})
    history = get_chat_history(session)

    start = time.time()
    reply = get_ai_response(text, build_platform_context(request.user), history)
    used_ai = reply is not None
    if not reply:
        reply = match_knowledge_base(text)
    elapsed = round(time.time() - start, 3)

    ChatMessage.objects.create(session=session, sender='user', message=text)
    bot = ChatMessage.objects.create(session=session, sender='bot', message=reply, response_time=elapsed)
    analytics, _ = ChatAnalytics.objects.get_or_create(session=session)
    analytics.total_messages = session.messages.count()
    analytics.user_messages = session.messages.filter(sender='user').count()
    analytics.bot_messages = session.messages.filter(sender='bot').count()
    analytics.save()
    return ok(reply=_message_json(bot), ai=used_ai)
