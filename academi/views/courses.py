from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.http import JsonResponse

from ..models import Category, Course, Module, Enrollment, LessonProgress, Favorite, Review, EvaluationResult, Certificate, Coupon
from ..utils import issue_certificate, compute_course_stats


# ============================================
# MÓDULO 3: GESTIÓN DE CURSOS
# ============================================
@login_required
def create_course_view(request):
    if request.user.role != 'teacher':
        messages.error(request, 'No tienes permisos para crear cursos.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        level = request.POST.get('level')
        price = request.POST.get('price')
        is_free = request.POST.get('is_free') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        image = request.FILES.get('image')
        video_promo = request.FILES.get('video_promo')

        if not title or not description:
            messages.error(request, 'El título y la descripción son obligatorios.')
            return render(request, 'academi/courses/crear_curso.html', {'categories': Category.objects.all()})

        course = Course.objects.create(
            title=title,
            description=description,
            teacher=request.user,
            level=level or 'beginner',
            price=price or 0.00,
            is_free=is_free,
            is_featured=is_featured,
            image=image,
            video_promo=video_promo,
            status='draft'
        )

        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                course.category = category
                course.save()
            except Category.DoesNotExist:
                pass

        messages.success(request, f'Curso "{title}" creado exitosamente.')
        return redirect('manage_course', course_id=course.id)

    categories = Category.objects.all()
    return render(request, 'academi/courses/crear_curso.html', {'categories': categories})


@login_required
def manage_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para gestionar este curso.')
        return redirect('dashboard')

    modules = course.modules.all().prefetch_related('lessons')
    return render(request, 'academi/courses/gestionar_curso.html', {
        'course': course,
        'modules': modules
    })


@login_required
def edit_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para editar este curso.')
        return redirect('dashboard')

    if request.method == 'POST':
        course.title = request.POST.get('title')
        course.description = request.POST.get('description')
        course.level = request.POST.get('level')
        course.price = request.POST.get('price') or 0.00
        course.is_free = request.POST.get('is_free') == 'on'
        course.is_featured = request.POST.get('is_featured') == 'on'

        if request.FILES.get('image'):
            course.image = request.FILES.get('image')
        if request.FILES.get('video_promo'):
            course.video_promo = request.FILES.get('video_promo')

        category_id = request.POST.get('category')
        if category_id:
            try:
                course.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass

        course.save()
        messages.success(request, 'Curso actualizado correctamente.')
        return redirect('manage_course', course_id=course.id)

    categories = Category.objects.all()
    return render(request, 'academi/courses/editar_curso.html', {
        'course': course,
        'categories': categories
    })


@login_required
def delete_course_view(request, course_id):
    """Se llama vía AJAX desde el botón "Eliminar" de mis_cursos.html
    (ver static/js/mis-cursos.js), que espera una respuesta JSON — no
    redirige a una página de confirmación aparte."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher and request.user.role != 'admin':
        return JsonResponse({'success': False, 'message': 'No tienes permisos para eliminar este curso.'}, status=403)

    title = course.title
    course.delete()
    return JsonResponse({'success': True, 'message': f'Curso "{title}" eliminado correctamente.'})


@login_required
def publish_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para publicar este curso.')
        return redirect('dashboard')

    if request.method == 'POST':
        if course.total_lessons == 0:
            messages.error(request, 'El curso debe tener al menos una lección para publicarse.')
            return redirect('manage_course', course_id=course.id)

        course.status = 'published'
        course.published_at = timezone.now()
        course.save()
        messages.success(request, f'Curso "{course.title}" publicado exitosamente.')
        return redirect('my_courses')

    return render(request, 'academi/courses/publicar_curso.html', {'course': course})


@login_required
def add_module_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')

        if not title:
            messages.error(request, 'El título del módulo es obligatorio.')
            return render(request, 'academi/courses/crear_modulo.html', {'course': course})

        last_order = course.modules.count()
        Module.objects.create(
            course=course,
            title=title,
            description=description,
            order=last_order + 1
        )
        messages.success(request, 'Módulo creado correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/courses/crear_modulo.html', {'course': course})


@login_required
def edit_module_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    if request.method == 'POST':
        module.title = request.POST.get('title')
        module.description = request.POST.get('description')
        module.save()
        messages.success(request, 'Módulo actualizado correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/courses/editar_modulo.html', {'module': module})


@login_required
def delete_module_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = module.title
        module.delete()
        messages.success(request, f'Módulo "{title}" eliminado correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/courses/eliminar_modulo.html', {'module': module})


@login_required
def reorder_module_view(request, module_id, direction):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    module = get_object_or_404(Module, id=module_id)
    course = module.course

    if request.user != course.teacher and request.user.role != 'admin':
        return JsonResponse({'error': 'Sin permisos'}, status=403)

    modules = list(course.modules.all())
    current_index = modules.index(module)

    if direction == 'up' and current_index > 0:
        modules[current_index], modules[current_index - 1] = modules[current_index - 1], modules[current_index]
    elif direction == 'down' and current_index < len(modules) - 1:
        modules[current_index], modules[current_index + 1] = modules[current_index + 1], modules[current_index]
    else:
        return JsonResponse({'error': 'Movimiento inválido'}, status=400)

    for i, m in enumerate(modules, start=1):
        m.order = i
        m.save()

    return JsonResponse({'success': True})


@login_required
def course_stats_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    stats = compute_course_stats(course)
    context = {
        'course': course,
        'stats': stats,
        'distribution': [(star, stats['rating_distribution'][star]) for star in range(5, 0, -1)],
    }
    return render(request, 'academi/courses/estadisticas_curso.html', context)


@login_required
def course_students_view(request, course_id):
    """RF-22, RF-52: consultar estudiantes inscritos y sus calificaciones."""
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')

    enrollments = Enrollment.objects.filter(course=course).select_related('student').prefetch_related(
        Prefetch(
            'evaluation_results',
            queryset=EvaluationResult.objects.select_related('evaluation__lesson').prefetch_related('incidents').order_by('-completed_at'),
            to_attr='results_list',
        )
    )

    for enrollment in enrollments:
        results = enrollment.results_list
        enrollment.results_count = len(results)
        if results:
            enrollment.average_score = int(
                sum((r.score / r.total_points * 100) if r.total_points else 0 for r in results) / len(results)
            )
        else:
            enrollment.average_score = None

    return render(request, 'academi/courses/estudiantes_curso.html', {
        'course': course,
        'enrollments': enrollments
    })


# ============================================
# MÓDULO 4: CATÁLOGO Y EXPLORACIÓN
# ============================================
def attach_active_coupons(*course_lists):
    """Le pone a cada curso un atributo .active_coupon (o None) con la
    mejor promoción vigente (global o específica del curso), para que
    _course_card.html pueda mostrar el badge de descuento y "válido
    hasta" sin tener que hacer lookups por id en el template. Reutiliza
    Coupon.is_valid() en vez de repetir sus reglas acá."""
    candidates = [
        c for c in Coupon.objects.filter(is_active=True).select_related('course').order_by('-discount_value')
        if c.is_valid()
    ]
    global_coupons = [c for c in candidates if c.course_id is None]
    per_course = {}
    for c in candidates:
        if c.course_id is not None:
            per_course.setdefault(c.course_id, c)

    for course_list in course_lists:
        for course in course_list:
            course.active_coupon = per_course.get(course.id) or (global_coupons[0] if global_coupons else None)


def catalog_view(request):
    all_published = Course.objects.filter(status='published')
    courses = all_published.annotate(student_count=Count('enrollments', distinct=True))

    category_id = request.GET.get('category')
    selected_category = None
    selected_category_obj = None
    if category_id:
        courses = courses.filter(category_id=category_id)
        selected_category = int(category_id)
        selected_category_obj = Category.objects.filter(id=category_id).first()

    courses = courses.order_by('-is_featured', '-created_at')

    categories = Category.objects.annotate(
        course_count=Count('courses', filter=Q(courses__status='published'), distinct=True)
    ).filter(course_count__gt=0).order_by('name')

    featured_courses = all_published.filter(is_featured=True).annotate(
        student_count=Count('enrollments', distinct=True)
    ).order_by('-created_at')[:8]

    bestseller_courses = all_published.annotate(
        student_count=Count('enrollments', distinct=True)
    ).filter(student_count__gt=0).order_by('-student_count')[:8]

    user_enrolled_courses = []
    user_favorite_courses = []
    if request.user.is_authenticated and request.user.role == 'student':
        user_enrolled_courses = Enrollment.objects.filter(
            student=request.user,
            status__in=['enrolled', 'in_progress', 'completed']
        ).values_list('course_id', flat=True)
        user_favorite_courses = Favorite.objects.filter(
            student=request.user
        ).values_list('course_id', flat=True)

    attach_active_coupons(courses, featured_courses, bestseller_courses)

    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': selected_category,
        'selected_category_obj': selected_category_obj,
        'featured_courses': featured_courses,
        'bestseller_courses': bestseller_courses,
        'bestseller_ids': [c.id for c in bestseller_courses],
        'user_enrolled_courses': list(user_enrolled_courses),
        'user_favorite_courses': list(user_favorite_courses),
        'total_courses': all_published.count(),
    }
    return render(request, 'academi/courses/catalogo.html', context)


def search_courses_view(request):
    query = request.GET.get('q', '')
    courses = Course.objects.filter(status='published')
    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(teacher__username__icontains=query)
        )
    return render(request, 'academi/courses/buscar.html', {'courses': courses, 'query': query})


def categories_view(request):
    categories = Category.objects.all().annotate(
        course_count=Count('courses', filter=Q(courses__status='published'))
    )
    return render(request, 'academi/courses/categorias.html', {'categories': categories})


def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='published')
    is_favorite = False
    is_enrolled = False
    user_review = None
    if request.user.is_authenticated:
        if request.user.role == 'student':
            is_favorite = Favorite.objects.filter(student=request.user, course=course).exists()
        is_enrolled = Enrollment.objects.filter(
            student=request.user, course=course,
            status__in=['enrolled', 'in_progress', 'completed']
        ).exists()
        user_review = Review.objects.filter(student=request.user, course=course).first()

    reviews = Review.objects.filter(course=course).exclude(
        student=request.user if request.user.is_authenticated else None
    ).select_related('student').order_by('-created_at')

    return render(request, 'academi/courses/curso_detalle.html', {
        'course': course,
        'is_favorite': is_favorite,
        'is_enrolled': is_enrolled,
        'user_review': user_review,
        'reviews': reviews,
        'user_enrolled_courses': [course.id] if is_enrolled else [],
    })


@login_required
def favorite_toggle_view(request, course_id):
    """RF-13, RF-31: agregar o quitar un curso de favoritos."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    course = get_object_or_404(Course, id=course_id)
    favorite = Favorite.objects.filter(student=request.user, course=course).first()

    if favorite:
        favorite.delete()
        return JsonResponse({'success': True, 'is_favorite': False, 'message': 'Curso quitado de favoritos'})

    Favorite.objects.create(student=request.user, course=course)
    return JsonResponse({'success': True, 'is_favorite': True, 'message': 'Curso agregado a favoritos'})


# ============================================
# MÓDULO 5: APRENDIZAJE
# ============================================
@login_required
def course_learn_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='published')

    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=course,
        status__in=['enrolled', 'in_progress', 'completed']
    )

    modules = course.modules.all().prefetch_related('lessons')

    completed_lessons_ids = LessonProgress.objects.filter(
        enrollment=enrollment,
        completed=True
    ).values_list('lesson_id', flat=True)

    completed_lessons = list(completed_lessons_ids)

    total_lessons = 0
    for module in modules:
        total_lessons += module.lessons.count()

    completed_count = len(completed_lessons)
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

    certificate = Certificate.objects.filter(enrollment=enrollment).first() if enrollment.status == 'completed' else None

    context = {
        'course': course,
        'enrollment': enrollment,
        'modules': modules,
        'completed_lessons': completed_lessons,
        'progress': progress,
        'total_lessons': total_lessons,
        'completed_count': completed_count,
        'certificate': certificate,
    }
    return render(request, 'academi/courses/curso_aprender.html', context)
