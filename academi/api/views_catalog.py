from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404

from ..models import (
    Category, Course, Enrollment, Favorite, Review, Certificate,
    EMI_STUDENT_DISCOUNT_PERCENT, is_eligible_for_emi_first_purchase_discount,
)
from .auth import api_view, error, ok
from .serializers import (
    ACTIVE_STATUSES, CourseContext, course_card, enrollment_json, modules_outline,
    review_json, teacher_json, completed_lesson_ids, coupon_json,
)

PAGE_SIZE = 12


def _published():
    return (Course.objects.filter(status='published')
            .select_related('category', 'teacher')
            .prefetch_related('modules__lessons'))


def _cards(request, queryset, ctx):
    return [course_card(request, c, ctx) for c in queryset]


def _user_or_none(request):
    return request.api_user


@api_view(('GET',), auth='optional')
def home(request):
    user = _user_or_none(request)
    ctx = CourseContext(user)
    published = _published()

    featured = published.filter(is_featured=True).order_by('-created_at')[:8]
    bestsellers = (published.annotate(n=Count('enrollments', distinct=True))
                   .filter(n__gt=0).order_by('-n')[:8])
    newest = published.order_by('-created_at')[:8]
    categories = (Category.objects
                  .annotate(course_count=Count('courses', filter=Q(courses__status='published'), distinct=True))
                  .filter(course_count__gt=0).order_by('name'))

    payload = {
        'featured': _cards(request, featured, ctx),
        'bestsellers': _cards(request, bestsellers, ctx),
        'newest': _cards(request, newest, ctx),
        'categories': [{'id': c.id, 'name': c.name, 'courses_count': c.course_count} for c in categories],
        'total_courses': published.count(),
        'emi_discount': None,
    }

    if user is not None:
        if is_eligible_for_emi_first_purchase_discount(user):
            payload['emi_discount'] = float(EMI_STUDENT_DISCOUNT_PERCENT)
        enrollments = Enrollment.objects.filter(student=user, status__in=ACTIVE_STATUSES).select_related(
            'course__category', 'course__teacher')
        continuing = enrollments.exclude(status='completed').order_by('-last_accessed')[:5]
        payload['continue_learning'] = [enrollment_json(request, e) for e in continuing]
        all_enrollments = list(enrollments)
        payload['stats'] = {
            'enrolled': len(all_enrollments),
            'completed': sum(1 for e in all_enrollments if e.status == 'completed'),
            'avg_progress': (sum(e.progress_percentage for e in all_enrollments) // len(all_enrollments))
            if all_enrollments else 0,
            'certificates': Certificate.objects.filter(enrollment__student=user, is_revoked=False).count(),
        }
    return ok(**payload)


@api_view(('GET',), auth='optional')
def categories(request):
    rows = (Category.objects
            .annotate(course_count=Count('courses', filter=Q(courses__status='published'), distinct=True))
            .order_by('name'))
    return ok(categories=[
        {'id': c.id, 'name': c.name, 'description': c.description or '', 'courses_count': c.course_count}
        for c in rows
    ])


@api_view(('GET',), auth='optional')
def course_list(request):
    user = _user_or_none(request)
    ctx = CourseContext(user)
    qs = _published()

    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) |
                       Q(teacher__username__icontains=q) | Q(teacher__teacher_full_name__icontains=q) |
                       Q(category__name__icontains=q))
    if request.GET.get('category'):
        qs = qs.filter(category_id=request.GET['category'])
    if request.GET.get('level'):
        qs = qs.filter(level=request.GET['level'])
    price = request.GET.get('price')
    if price == 'free':
        qs = qs.filter(Q(is_free=True) | Q(price=0))
    elif price == 'paid':
        qs = qs.filter(is_free=False, price__gt=0)

    sort = request.GET.get('sort', 'featured')
    qs = qs.annotate(n_students=Count('enrollments', distinct=True), avg_rating=Avg('reviews__rating'))
    order = {
        'featured': ('-is_featured', '-created_at'),
        'recent': ('-created_at',),
        'popular': ('-n_students', '-created_at'),
        'rating': ('-avg_rating', '-n_students'),
        'price_asc': ('price',),
        'price_desc': ('-price',),
    }.get(sort, ('-is_featured', '-created_at'))
    qs = qs.order_by(*order)

    try:
        page = max(int(request.GET.get('page', 1)), 1)
    except ValueError:
        page = 1
    total = qs.count()
    start = (page - 1) * PAGE_SIZE
    items = list(qs[start:start + PAGE_SIZE])
    return ok(
        courses=_cards(request, items, ctx),
        page=page, total=total, has_more=start + PAGE_SIZE < total,
    )


@api_view(('GET',), auth='optional')
def course_detail(request, course_id):
    user = _user_or_none(request)
    course = get_object_or_404(_published(), id=course_id)
    ctx = CourseContext(user)

    enrollment = None
    user_review = None
    if user is not None:
        enrollment = Enrollment.objects.filter(student=user, course=course, status__in=ACTIVE_STATUSES).first()
        user_review = Review.objects.filter(student=user, course=course).select_related('student').first()

    reviews = (Review.objects.filter(course=course).select_related('student')
               .exclude(student=user).order_by('-created_at')[:30]) if user else \
        Review.objects.filter(course=course).select_related('student').order_by('-created_at')[:30]

    completed = completed_lesson_ids(enrollment) if enrollment else None
    ratings = course.reviews.aggregate(avg=Avg('rating'), n=Count('id'))
    distribution = {str(i): course.reviews.filter(rating=i).count() for i in range(1, 6)}

    other_courses = (_published().filter(teacher=course.teacher).exclude(id=course.id)[:6])

    card = course_card(request, course, ctx)
    card.update({
        'description': course.description,
        'video_promo': request.build_absolute_uri(course.video_promo.url) if course.video_promo else None,
        'modules': modules_outline(course, completed),
        'modules_count': course.total_modules,
        'rating_distribution': distribution,
        'rating': round(ratings['avg'] or 0, 1),
        'reviews_count': ratings['n'],
        'reviews': [review_json(request, r) for r in reviews],
        'user_review': review_json(request, user_review) if user_review else None,
        'teacher_info': teacher_json(request, course.teacher, with_stats=True),
        'teacher_courses': _cards(request, other_courses, ctx),
        'progress': enrollment.progress_percentage if enrollment else None,
        'in_cart': bool(user) and user.cart.filter(items__course=course).exists(),
        'emi_discount': float(EMI_STUDENT_DISCOUNT_PERCENT)
        if user and is_eligible_for_emi_first_purchase_discount(user) else None,
        'created_at': course.created_at.isoformat(),
        'updated_at': course.updated_at.isoformat(),
    })
    return ok(course=card)


@api_view(('POST',), roles=('student',))
def favorite_toggle(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='published')
    favorite = Favorite.objects.filter(student=request.user, course=course).first()
    if favorite:
        favorite.delete()
        return ok(is_favorite=False, message='Curso quitado de favoritos')
    Favorite.objects.create(student=request.user, course=course)
    return ok(is_favorite=True, message='Curso agregado a favoritos')


@api_view(('GET',), roles=('student',))
def favorites(request):
    ctx = CourseContext(request.user)
    rows = (Favorite.objects.filter(student=request.user, course__status='published')
            .select_related('course__category', 'course__teacher').order_by('-created_at'))
    return ok(courses=_cards(request, [f.course for f in rows], ctx))
