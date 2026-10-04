"""Conversión de modelos a dicts JSON para la API móvil."""
import re

from django.db.models import Avg, Count

from ..models import (
    Coupon, Enrollment, Favorite, LessonProgress, Certificate,
)

YOUTUBE_PATTERNS = [
    r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
    r'youtube\.com/embed/([^&\n?#]+)',
    r'youtube\.com/v/([^&\n?#]+)',
    r'youtube\.com/shorts/([^&\n?#]+)',
]

ACTIVE_STATUSES = ['enrolled', 'in_progress', 'completed']


def media_url(request, f):
    if not f:
        return None
    try:
        return request.build_absolute_uri(f.url)
    except ValueError:
        return None


def money(value):
    return float(value or 0)


def youtube_id(url):
    if not url:
        return None
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url.strip())
        if match:
            return match.group(1).split('?')[0].split('&')[0]
    return None


def display_name(user):
    return (user.teacher_full_name or user.full_name or user.get_full_name()
            or user.first_name or user.username)


def user_json(request, user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'name': display_name(user),
        'email_verified': user.email_verified,
        'phone': user.phone or user.teacher_phone or '',
        'bio': user.bio or '',
        'city': user.city or '',
        'university': user.university or '',
        'career': user.career or '',
        'semester': user.semester or '',
        'education_level': user.education_level or '',
        'interests': user.interests or '',
        'specialty': user.specialty or '',
        'institution': user.institution or '',
        'experience_years': user.experience_years or '',
        'teacher_bio': user.teacher_bio or '',
        'linkedin': user.linkedin or '',
        'website': user.website or '',
        'picture': media_url(request, user.profile_picture),
    }


def teacher_json(request, teacher, with_stats=False):
    data = {
        'id': teacher.id,
        'name': display_name(teacher),
        'specialty': teacher.specialty or '',
        'institution': teacher.institution or '',
        'bio': teacher.teacher_bio or teacher.bio or '',
        'experience_years': teacher.experience_years or '',
        'linkedin': teacher.linkedin or '',
        'website': teacher.website or '',
        'picture': media_url(request, teacher.profile_picture),
    }
    if with_stats:
        from ..models import Course, Review
        courses = Course.objects.filter(teacher=teacher, status='published')
        data['courses_count'] = courses.count()
        data['students_count'] = Enrollment.objects.filter(
            course__in=courses, status__in=ACTIVE_STATUSES
        ).count()
        data['rating'] = round(
            Review.objects.filter(course__in=courses).aggregate(a=Avg('rating'))['a'] or 0, 1
        )
    return data


def active_coupons_map():
    """Mejor promoción vigente por curso (o global), como el catálogo web."""
    candidates = [
        c for c in Coupon.objects.filter(is_active=True).select_related('course').order_by('-discount_value')
        if c.is_valid()
    ]
    global_coupon = next((c for c in candidates if c.course_id is None), None)
    per_course = {}
    for c in candidates:
        if c.course_id is not None:
            per_course.setdefault(c.course_id, c)
    return per_course, global_coupon


def coupon_json(coupon):
    if not coupon:
        return None
    return {
        'code': coupon.code,
        'type': coupon.discount_type,
        'value': money(coupon.discount_value),
        'expires_at': coupon.expires_at.isoformat(),
    }


class CourseContext:
    """Agrupa lo que hace falta para marcar favoritos/inscripciones/cupones
    de muchos cursos con un puñado de consultas."""

    def __init__(self, user):
        self.enrolled = set()
        self.favorites = set()
        if user is not None:
            self.enrolled = set(Enrollment.objects.filter(
                student=user, status__in=ACTIVE_STATUSES).values_list('course_id', flat=True))
            self.favorites = set(Favorite.objects.filter(student=user).values_list('course_id', flat=True))
        self.per_course_coupon, self.global_coupon = active_coupons_map()

    def coupon_for(self, course):
        return self.per_course_coupon.get(course.id) or self.global_coupon


def course_card(request, course, ctx):
    ratings = getattr(course, '_rating_cache', None)
    if ratings is None:
        ratings = course.reviews.aggregate(avg=Avg('rating'), n=Count('id'))
    return {
        'id': course.id,
        'title': course.title,
        'description': course.description[:220],
        'image': media_url(request, course.image),
        'category': course.category.name if course.category_id else None,
        'category_id': course.category_id,
        'level': course.level,
        'level_label': course.get_level_display(),
        'price': money(course.price),
        'is_free': course.is_free,
        'price_label': course.get_price_display(),
        'is_featured': course.is_featured,
        'teacher': display_name(course.teacher),
        'rating': round(ratings['avg'] or 0, 1),
        'reviews_count': ratings['n'],
        'students_count': course.total_students,
        'lessons_count': course.total_lessons,
        'duration_minutes': course.total_duration,
        'is_enrolled': course.id in ctx.enrolled,
        'is_favorite': course.id in ctx.favorites,
        'coupon': coupon_json(ctx.coupon_for(course)),
    }


def enrollment_json(request, enrollment):
    course = enrollment.course
    certificate = Certificate.objects.filter(enrollment=enrollment, is_revoked=False).first()
    return {
        'id': enrollment.id,
        'course_id': course.id,
        'title': course.title,
        'image': media_url(request, course.image),
        'category': course.category.name if course.category_id else None,
        'teacher': display_name(course.teacher),
        'status': enrollment.status,
        'progress': enrollment.progress_percentage,
        'last_accessed': enrollment.last_accessed.isoformat() if enrollment.last_accessed else None,
        'certificate_id': certificate.id if certificate else None,
    }


def lesson_outline(lesson, completed_ids=None):
    return {
        'id': lesson.id,
        'title': lesson.title,
        'type': lesson.lesson_type,
        'duration_minutes': lesson.duration_minutes or 0,
        'is_free': lesson.is_free,
        'completed': lesson.id in completed_ids if completed_ids is not None else False,
    }


def modules_outline(course, completed_ids=None):
    return [{
        'id': m.id,
        'title': m.title,
        'description': m.description or '',
        'lessons': [lesson_outline(l, completed_ids) for l in m.lessons.all()],
    } for m in course.modules.all().prefetch_related('lessons')]


def completed_lesson_ids(enrollment):
    return set(LessonProgress.objects.filter(enrollment=enrollment, completed=True).values_list('lesson_id', flat=True))


def review_json(request, review):
    return {
        'id': review.id,
        'student': display_name(review.student),
        'picture': media_url(request, review.student.profile_picture),
        'rating': review.rating,
        'comment': review.comment or '',
        'is_edited': review.is_edited,
        'created_at': review.created_at.isoformat(),
    }


def certificate_json(request, certificate):
    enrollment = certificate.enrollment
    return {
        'id': certificate.id,
        'code': certificate.certificate_code,
        'course_id': enrollment.course_id,
        'course': enrollment.course.title,
        'student': display_name(enrollment.student),
        'issued_at': certificate.issued_at.isoformat(),
        'is_revoked': certificate.is_revoked,
        'pdf': media_url(request, certificate.pdf_file),
    }
