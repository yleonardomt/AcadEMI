"""Panel del docente (y resumen del administrador) para la app móvil."""
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import (
    User, Course, Enrollment, Review, Question, Answer, Payment, EvaluationResult,
    Report, AssignmentSubmission, Notification,
)
from .auth import api_view, error, ok, parse_body
from .serializers import ACTIVE_STATUSES, display_name, media_url, money, review_json

TEACHER = ('teacher', 'admin')


def _own_courses(user):
    qs = Course.objects.all() if user.role == 'admin' else Course.objects.filter(teacher=user)
    return qs


@api_view(('GET',), roles=TEACHER)
def dashboard(request):
    user = request.user
    courses = _own_courses(user)
    enrollments = Enrollment.objects.filter(course__in=courses, status__in=ACTIVE_STATUSES)
    reviews = Review.objects.filter(course__in=courses)
    payload = {
        'courses': courses.count(),
        'published': courses.filter(status='published').count(),
        'drafts': courses.filter(status='draft').count(),
        'pending': courses.filter(status='pending').count(),
        'rejected': courses.filter(status='rejected').count(),
        'students': enrollments.count(),
        'active_students': enrollments.filter(progress_percentage__gt=0).exclude(status='completed')
        .values('student').distinct().count(),
        'completed_students': enrollments.filter(status='completed').count(),
        'reviews': reviews.count(),
        'rating': round(reviews.aggregate(a=Avg('rating'))['a'] or 0, 1),
        'pending_questions': Question.objects.filter(lesson__module__course__in=courses, is_answered=False).count(),
        'pending_assignments': AssignmentSubmission.objects.filter(
            lesson__module__course__in=courses, grade__isnull=True).count(),
    }
    top = (courses.filter(status='published').order_by('-created_at')[:5])
    payload['recent_courses'] = [{
        'id': c.id, 'title': c.title, 'image': media_url(request, c.image),
        'students': c.total_students, 'status': c.status, 'status_label': c.get_status_display(),
    } for c in top]

    if user.role == 'admin':
        completed = Payment.objects.filter(status='completed')
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        payload['admin'] = {
            'users': User.objects.count(), 'students': User.objects.filter(role='student').count(),
            'teachers': User.objects.filter(role='teacher').count(),
            'courses_pending_approval': Course.objects.filter(status='pending').count(),
            'payments': completed.count(),
            'revenue': money(completed.aggregate(t=Sum('final_amount'))['t']),
            'monthly_revenue': money(completed.filter(created_at__gte=month_start)
                                     .aggregate(t=Sum('final_amount'))['t']),
            'open_reports': Report.objects.filter(status='pending').count(),
        }
    return ok(**payload)


@api_view(('GET',), roles=TEACHER)
def course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user != course.teacher and request.user.role != 'admin':
        return error('No tienes permisos.', 403)
    rows = []
    for e in Enrollment.objects.filter(course=course).select_related('student').order_by('-enrollment_date'):
        results = list(EvaluationResult.objects.filter(enrollment=e, completed_at__isnull=False))
        avg = int(sum((r.score / r.total_points * 100) if r.total_points else 0 for r in results)
                  / len(results)) if results else None
        rows.append({
            'id': e.id, 'student': display_name(e.student), 'email': e.student.email,
            'picture': media_url(request, e.student.profile_picture),
            'status': e.status, 'status_label': e.get_status_display(),
            'progress': e.progress_percentage, 'evaluations': len(results), 'average_score': avg,
            'enrolled_at': e.enrollment_date.isoformat(),
        })
    return ok(course={'id': course.id, 'title': course.title}, students=rows)


@api_view(('GET',), roles=TEACHER)
def all_students(request):
    rows = (Enrollment.objects.filter(course__in=_own_courses(request.user), status__in=ACTIVE_STATUSES)
            .select_related('student', 'course').order_by('-enrollment_date')[:200])
    return ok(students=[{
        'id': e.id, 'student': display_name(e.student), 'email': e.student.email,
        'picture': media_url(request, e.student.profile_picture), 'course': e.course.title,
        'course_id': e.course_id, 'progress': e.progress_percentage, 'status_label': e.get_status_display(),
    } for e in rows])


@api_view(('GET',), roles=TEACHER)
def questions(request):
    rows = (Question.objects.filter(lesson__module__course__in=_own_courses(request.user))
            .select_related('student', 'lesson__module__course').prefetch_related('answers__teacher')
            .order_by('is_answered', '-created_at')[:100])
    return ok(questions=[{
        'id': q.id, 'content': q.content, 'author': display_name(q.student),
        'picture': media_url(request, q.student.profile_picture),
        'lesson': q.lesson.title, 'lesson_id': q.lesson_id, 'course': q.lesson.module.course.title,
        'is_answered': q.is_answered, 'created_at': q.created_at.isoformat(),
        'answers': [{'id': a.id, 'content': a.content or '', 'teacher': display_name(a.teacher)}
                    for a in q.answers.all()],
    } for q in rows])


@api_view(('POST',), roles=TEACHER)
def question_answer(request, question_id):
    question = get_object_or_404(Question.objects.select_related('lesson__module__course'), id=question_id)
    course = question.lesson.module.course
    if request.user != course.teacher and request.user.role != 'admin':
        return error('No tienes permisos para responder esta pregunta.', 403)
    content = (parse_body(request).get('content') or '').strip()
    if not content:
        return error('Escribe una respuesta antes de enviarla.')
    answer = Answer.objects.filter(question=question).first()
    if answer:
        answer.content = content
        answer.save()
    else:
        Answer.objects.create(question=question, teacher=request.user, content=content)
        Notification.objects.create(
            user=question.student, type='answer', title='Tu pregunta fue respondida',
            message=f'El docente respondió tu pregunta en "{question.lesson.title}".')
    question.is_answered = True
    question.save()
    return ok(message='Respuesta publicada.')


@api_view(('GET',), roles=TEACHER)
def reviews(request):
    rows = (Review.objects.filter(course__in=_own_courses(request.user))
            .select_related('student', 'course').order_by('-created_at')[:100])
    data = []
    for r in rows:
        item = review_json(request, r)
        item['course'] = r.course.title
        data.append(item)
    return ok(reviews=data)
