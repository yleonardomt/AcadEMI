from django.db.models import Avg, Count, Sum

from ..models import (
    Enrollment, EvaluationResult, EvaluationIncident, PaymentItem, Review,
)

ACTIVE = ['enrolled', 'in_progress', 'completed']


def compute_course_stats(course):
    """RF-16: estadísticas de un curso (estudiantes, progreso, evaluaciones,
    valoraciones y ventas). La usan la vista web y la API móvil."""
    enrollments = Enrollment.objects.filter(course=course, status__in=ACTIVE)
    total = enrollments.count()
    completed = enrollments.filter(status='completed').count()
    in_progress = enrollments.filter(status='in_progress').count()
    avg_progress = enrollments.aggregate(a=Avg('progress_percentage'))['a'] or 0

    results = EvaluationResult.objects.filter(
        enrollment__course=course, completed_at__isnull=False)
    results_count = results.count()
    passed = results.filter(passed=True).count()
    scores = [r.score / r.total_points * 100 for r in results if r.total_points]
    incidents = EvaluationIncident.objects.filter(evaluation_result__enrollment__course=course).count()

    reviews = Review.objects.filter(course=course)
    review_agg = reviews.aggregate(a=Avg('rating'), n=Count('id'))
    distribution = {i: reviews.filter(rating=i).count() for i in range(1, 6)}

    sales = PaymentItem.objects.filter(course=course, payment__status='completed')
    revenue = sales.aggregate(t=Sum('final_price'))['t'] or 0

    return {
        'total_students': total,
        'completed': completed,
        'in_progress': in_progress,
        'not_started': max(total - completed - in_progress, 0),
        'avg_progress': round(avg_progress),
        'completion_rate': round(completed / total * 100) if total else 0,
        'total_lessons': course.total_lessons,
        'total_modules': course.total_modules,
        'evaluations_taken': results_count,
        'evaluations_passed': passed,
        'pass_rate': round(passed / results_count * 100) if results_count else 0,
        'avg_score': round(sum(scores) / len(scores)) if scores else 0,
        'incidents': incidents,
        'reviews': review_agg['n'] or 0,
        'avg_rating': round(review_agg['a'] or 0, 1),
        'rating_distribution': distribution,
        'sales': sales.count(),
        'revenue': float(revenue),
    }
