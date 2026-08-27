from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.http import JsonResponse

from .forms import (
    RegisterForm, LoginForm, UserProfileForm, 
    PasswordResetRequestForm, PasswordResetConfirmForm,
    CustomPasswordChangeForm
)
from .models import (
    User, Category, Course, Module, Lesson, Enrollment, 
    LessonProgress, Favorite, Notification, Comment, 
    Question, Answer, Review, Report, Evaluation,
    QuestionEvaluation, QuestionOption, EvaluationResult,
    UserAnswer, EvaluationIncident, Cart, CartItem,
    Coupon, Payment, PaymentItem, Certificate,
    SystemReport, ActivityLog, SystemSetting,
    ChatSession, ChatMessage, ChatIntent, ChatKnowledgeBase,
    ChatFeedback, ChatAnalytics, LessonResource
)
from .utils import send_verification_email, send_password_reset_email, generate_reset_link

User = get_user_model()


# ============================================
# HOME
# ============================================
def home_view(request):
    return render(request, 'academi/index.html')


# ============================================
# RF-01: REGISTRARSE
# ============================================
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # RF-07: Enviar email de verificación
            try:
                send_verification_email(user, request)
                messages.success(request, 'Registro exitoso. Te hemos enviado un correo de verificación.')
            except:
                messages.warning(request, 'Registro exitoso, pero no pudimos enviar el correo de verificación.')
            
            return redirect('dashboard')
    else:
        form = RegisterForm()
    
    return render(request, 'academi/register.html', {'form': form})


# ============================================
# RF-02: INICIAR SESIÓN
# ============================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Bienvenido de vuelta, {user.username}.')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
    else:
        form = LoginForm()
    
    return render(request, 'academi/login.html', {'form': form})


# ============================================
# RF-04: CERRAR SESIÓN
# ============================================
def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


# ============================================
# RF-05: CAMBIAR CONTRASEÑA
# ============================================
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña cambiada correctamente.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Error al cambiar la contraseña. Revisa los campos.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'academi/change_password.html', {'form': form})


# ============================================
# RF-03: RECUPERAR CONTRASEÑA - SOLICITAR
# ============================================
def password_reset_request_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'No existe un usuario con este email.')
                return render(request, 'academi/password_reset_request.html', {'form': form})
            
            reset_link = generate_reset_link(user, request)
            
            try:
                send_password_reset_email(user, request, reset_link)
                messages.success(request, 'Se ha enviado un enlace de recuperación a tu email.')
                return render(request, 'academi/password_reset_done.html')
            except:
                messages.error(request, 'Error al enviar el email. Intenta nuevamente.')
    
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'academi/password_reset_request.html', {'form': form})


# ============================================
# RF-03: RECUPERAR CONTRASEÑA - CONFIRMAR
# ============================================
def password_reset_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                new_password = form.cleaned_data['new_password']
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
                return redirect('login')
        else:
            form = PasswordResetConfirmForm()
        
        return render(request, 'academi/password_reset_confirm.html', {'form': form, 'valid': True})
    else:
        messages.error(request, 'El enlace de recuperación es inválido o ha expirado.')
        return redirect('password_reset_request')


# ============================================
# RF-07: CONFIRMAR CORREO ELECTRÓNICO
# ============================================
def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if not user.email_verified:
            user.verify_email()
            messages.success(request, 'Tu correo ha sido verificado correctamente.')
        else:
            messages.info(request, 'Tu correo ya estaba verificado.')
        return redirect('dashboard')
    else:
        messages.error(request, 'El enlace de verificación es inválido o ha expirado.')
        return redirect('login')


# ============================================
# RF-08: PERFIL
# ============================================
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('profile')
        else:
            messages.error(request, 'Error al actualizar el perfil. Revisa los campos.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'academi/perfil.html', {'form': form})


# ============================================
# DASHBOARD
# ============================================
@login_required
def dashboard_view(request):
    user = request.user
    
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    
    enrollments = Enrollment.objects.filter(student=user)
    total_enrollments = enrollments.count()
    completed_courses = enrollments.filter(status='completed').count()
    in_progress_courses = enrollments.filter(status='in_progress').count()
    
    avg_progress = 0
    if total_enrollments > 0:
        avg_progress = sum(e.progress_percentage for e in enrollments) // total_enrollments
    
    completed_percentage = 0
    in_progress_percentage = 0
    pending_percentage = 100
    if total_enrollments > 0:
        completed_percentage = (completed_courses / total_enrollments) * 100
        in_progress_percentage = (in_progress_courses / total_enrollments) * 100
        pending_percentage = 100 - completed_percentage - in_progress_percentage
    
    total_certificates = Certificate.objects.filter(enrollment__student=user).count()
    enrollments_in_progress = enrollments.filter(status='in_progress')[:5]
    
    teacher_courses = Course.objects.filter(teacher=user)
    teacher_courses_count = teacher_courses.count()
    teacher_published_courses = teacher_courses.filter(status='published').count()
    teacher_draft_courses = teacher_courses.filter(status='draft').count()
    
    teacher_students_total = Enrollment.objects.filter(course__in=teacher_courses, status='enrolled').count()
    recent_courses = teacher_courses.order_by('-created_at')[:5]
    
    total_users = User.objects.count()
    total_courses = Course.objects.count()
    total_payments = Payment.objects.filter(status='completed').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(total=Sum('final_amount'))['total'] or 0
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    
    context = {
        'user': user,
        'is_student': user.role == 'student',
        'is_teacher': user.role == 'teacher',
        'is_admin': user.role == 'admin',
        'now': timezone.now(),
        
        'total_enrollments': total_enrollments,
        'completed_courses': completed_courses,
        'in_progress_courses': in_progress_courses,
        'avg_progress': avg_progress,
        'completed_percentage': int(completed_percentage),
        'in_progress_percentage': int(in_progress_percentage),
        'pending_percentage': int(pending_percentage),
        'total_certificates': total_certificates,
        'enrollments_in_progress': enrollments_in_progress,
        
        'teacher_courses_count': teacher_courses_count,
        'teacher_published_courses': teacher_published_courses,
        'teacher_draft_courses': teacher_draft_courses,
        'teacher_students_total': teacher_students_total,
        'recent_courses': recent_courses,
        
        'total_users': total_users,
        'total_courses': total_courses,
        'total_payments': total_payments,
        'total_revenue': total_revenue,
        'recent_users': recent_users,
        
        'notifications': notifications,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'academi/dashboard.html', context)


# ============================================
# MÓDULO 2: PERFIL Y GESTIÓN DEL ESTUDIANTE
# ============================================

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'academi/notificaciones.html', {'notifications': notifications})


@login_required
def my_courses_view(request):
    if request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
        return render(request, 'academi/mis_cursos.html', {'courses': courses})
    else:
        enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
        return render(request, 'academi/mis_cursos.html', {'enrollments': enrollments})


@login_required
def my_progress_view(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    return render(request, 'academi/mi_progreso.html', {'enrollments': enrollments})


@login_required
def my_grades_view(request):
    results = EvaluationResult.objects.filter(enrollment__student=request.user).select_related('evaluation', 'enrollment__course')
    return render(request, 'academi/mis_calificaciones.html', {'results': results})


@login_required
def my_certificates_view(request):
    certificates = Certificate.objects.filter(enrollment__student=request.user).select_related('enrollment__course')
    return render(request, 'academi/mis_certificados.html', {'certificates': certificates})


@login_required
def my_favorites_view(request):
    favorites = Favorite.objects.filter(student=request.user).select_related('course')
    return render(request, 'academi/mis_favoritos.html', {'favorites': favorites})


@login_required
def purchase_history_view(request):
    payments = Payment.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'academi/historial_compras.html', {'payments': payments})


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(student=request.user)
    return render(request, 'academi/carrito.html', {'cart': cart})


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
            return render(request, 'academi/crear_curso.html', {'categories': Category.objects.all()})
        
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
    return render(request, 'academi/crear_curso.html', {'categories': categories})


@login_required
def manage_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para gestionar este curso.')
        return redirect('dashboard')
    
    modules = course.modules.all().prefetch_related('lessons')
    return render(request, 'academi/gestionar_curso.html', {
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
    return render(request, 'academi/editar_curso.html', {
        'course': course,
        'categories': categories
    })


@login_required
def delete_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para eliminar este curso.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = course.title
        course.delete()
        messages.success(request, f'Curso "{title}" eliminado correctamente.')
        return redirect('my_courses')
    
    return render(request, 'academi/eliminar_curso.html', {'course': course})


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
    
    return render(request, 'academi/publicar_curso.html', {'course': course})


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
            return render(request, 'academi/crear_modulo.html', {'course': course})
        
        last_order = course.modules.count()
        Module.objects.create(
            course=course,
            title=title,
            description=description,
            order=last_order + 1
        )
        messages.success(request, 'Módulo creado correctamente.')
        return redirect('manage_course', course_id=course.id)
    
    return render(request, 'academi/crear_modulo.html', {'course': course})


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
    
    return render(request, 'academi/editar_modulo.html', {'module': module})


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
    
    return render(request, 'academi/eliminar_modulo.html', {'module': module})


@login_required
def reorder_module_view(request, module_id, direction):
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
            return render(request, 'academi/crear_leccion.html', {'module': module})
        
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
    
    return render(request, 'academi/crear_leccion.html', {'module': module})


@login_required
def edit_lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    
    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        lesson.title = request.POST.get('title')
        lesson.description = request.POST.get('description')
        lesson.lesson_type = request.POST.get('lesson_type')
        lesson.content = request.POST.get('content')
        lesson.is_free = request.POST.get('is_free') == 'on'
        lesson.save()
        messages.success(request, 'Lección actualizada correctamente.')
        return redirect('manage_course', course_id=course.id)
    
    return render(request, 'academi/editar_leccion.html', {'lesson': lesson})


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
    
    return render(request, 'academi/eliminar_leccion.html', {'lesson': lesson})


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
    
    return render(request, 'academi/subir_video.html', {'lesson': lesson})


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
            resource = LessonResource.objects.create(
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
    
    return render(request, 'academi/subir_documento.html', {'lesson': lesson})


@login_required
def course_stats_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    
    enrollments = Enrollment.objects.filter(course=course)
    total_students = enrollments.count()
    completed = enrollments.filter(status='completed').count()
    in_progress = enrollments.filter(status='in_progress').count()
    
    context = {
        'course': course,
        'total_students': total_students,
        'completed': completed,
        'in_progress': in_progress,
        'total_lessons': course.total_lessons,
        'total_modules': course.total_modules,
    }
    return render(request, 'academi/estadisticas_curso.html', context)


@login_required
def course_students_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    return render(request, 'academi/estudiantes_curso.html', {
        'course': course,
        'enrollments': enrollments
    })


# ============================================
# MÓDULO 4: CATÁLOGO Y EXPLORACIÓN
# ============================================

def catalog_view(request):
    courses = Course.objects.filter(status='published')
    return render(request, 'academi/catalogo.html', {'courses': courses})


def search_courses_view(request):
    query = request.GET.get('q', '')
    courses = Course.objects.filter(status='published')
    if query:
        courses = courses.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(teacher__username__icontains=query)
        )
    return render(request, 'academi/buscar.html', {'courses': courses, 'query': query})


def categories_view(request):
    categories = Category.objects.all()
    return render(request, 'academi/categorias.html', {'categories': categories})


# ============================================
# MÓDULO 10: ASISTENTE VIRTUAL
# ============================================

def chatbot_view(request):
    return render(request, 'academi/chatbot.html')


# ============================================
# MÓDULO 9: ADMINISTRACIÓN
# ============================================

@login_required
def admin_courses_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    courses = Course.objects.all().order_by('-created_at')
    return render(request, 'academi/admin_cursos.html', {'courses': courses})


@login_required
def admin_categories_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    categories = Category.objects.all()
    return render(request, 'academi/admin_categorias.html', {'categories': categories})


@login_required
def admin_reports_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    reports = Report.objects.filter(status='pending')
    return render(request, 'academi/admin_reportes.html', {'reports': reports})


@login_required
def admin_coupons_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    coupons = Coupon.objects.all()
    return render(request, 'academi/admin_cupones.html', {'coupons': coupons})


@login_required
def admin_payments_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    payments = Payment.objects.all().order_by('-created_at')
    return render(request, 'academi/admin_pagos.html', {'payments': payments})


@login_required
def admin_certificates_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    certificates = Certificate.objects.all().order_by('-issued_at')
    return render(request, 'academi/admin_certificados.html', {'certificates': certificates})


@login_required
def admin_reports_generate_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    return render(request, 'academi/admin_generar_reportes.html')


# ============================================
# ADMIN - CRUD USUARIOS
# ============================================

@login_required
def admin_users_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard')
    
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query) | 
            Q(first_name__icontains=query)
        ).order_by('-date_joined')
    else:
        users = User.objects.all().order_by('-date_joined')
    
    context = {
        'users': users,
        'query': query,
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role='student').count(),
        'total_teachers': User.objects.filter(role='teacher').count(),
        'total_admins': User.objects.filter(role='admin').count(),
        'total_active': User.objects.filter(is_active=True).count(),
        'total_inactive': User.objects.filter(is_active=False).count(),
    }
    return render(request, 'academi/admin_usuarios.html', context)


@login_required
def admin_user_create(request):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        first_name = request.POST.get('first_name', '')
        phone = request.POST.get('phone', '')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return redirect('admin_users')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado.')
            return redirect('admin_users')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            role=role,
            phone=phone,
            is_active=True
        )
        messages.success(request, f'Usuario {username} creado correctamente.')
        return redirect('admin_users')
    
    return render(request, 'academi/admin_crear_usuario.html')


@login_required
def admin_user_edit(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.first_name = request.POST.get('first_name', '')
        user.phone = request.POST.get('phone', '')
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        messages.success(request, f'Usuario {user.username} actualizado correctamente.')
        return redirect('admin_users')
    
    return render(request, 'academi/admin_editar_usuario.html', {'edit_user': user})


@login_required
def admin_user_delete(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('admin_users')
    
    username = user.username
    user.delete()
    messages.success(request, f'Usuario {username} eliminado correctamente.')
    return redirect('admin_users')


@login_required
def admin_user_toggle_active(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
        return redirect('admin_users')
    
    user.is_active = not user.is_active
    user.save()
    
    estado = 'activado' if user.is_active else 'desactivado'
    messages.success(request, f'Usuario {user.username} {estado} correctamente.')
    return redirect('admin_users')


@login_required
def admin_user_reset_password(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        if len(new_password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return redirect('admin_users')
        
        user.set_password(new_password)
        user.save()
        messages.success(request, f'Contraseña de {user.username} restablecida correctamente.')
        return redirect('admin_users')
    
    return render(request, 'academi/admin_reset_password.html', {'reset_user': user})


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
            return render_lesson_form(request, module, 'academi/lecciones/crear_texto.html', request.POST)

        if not content:
            messages.error(request, 'El contenido es obligatorio.')
            return render_lesson_form(request, module, 'academi/lecciones/crear_texto.html', request.POST)

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

    return render_lesson_form(request, module, 'academi/lecciones/crear_texto.html')


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
            return render_lesson_form(request, module, 'academi/lecciones/crear_video.html', request.POST)

        if not video_url and not video_file:
            messages.error(request, 'Debes proporcionar una URL de video o subir un archivo.')
            return render_lesson_form(request, module, 'academi/lecciones/crear_video.html', request.POST)

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

    return render_lesson_form(request, module, 'academi/lecciones/crear_video.html')


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
            return render_lesson_form(request, module, 'academi/lecciones/crear_documento.html', request.POST)

        if not document_file:
            messages.error(request, 'Debes subir un archivo de documento.')
            return render_lesson_form(request, module, 'academi/lecciones/crear_documento.html', request.POST)

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

    return render_lesson_form(request, module, 'academi/lecciones/crear_documento.html')


@login_required
def create_lesson_quiz_view(request, module_id):
    module, course = get_module_and_check_permission(request, module_id)
    if not module:
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        content = request.POST.get('content', '').strip()
        is_free = request.POST.get('is_free') == 'on'
        duration = request.POST.get('duration', 0)
        quiz_time_limit = request.POST.get('quiz_time_limit', 30)
        quiz_passing_score = request.POST.get('quiz_passing_score', 70)
        quiz_max_attempts = request.POST.get('quiz_max_attempts', 1)

        if not title or len(title) < 3:
            messages.error(request, 'El título es obligatorio y debe tener al menos 3 caracteres.')
            return render(request, 'academi/lecciones/crear_cuestionario.html', {
                'module': module,
                'form_data': request.POST
            })

        if not content:
            messages.error(request, 'Las instrucciones del cuestionario son obligatorias.')
            return render(request, 'academi/lecciones/crear_cuestionario.html', {
                'module': module,
                'form_data': request.POST
            })

        try:
            duration = int(duration) if duration else 0
            quiz_time_limit = int(quiz_time_limit) if quiz_time_limit else 30
            quiz_passing_score = int(quiz_passing_score) if quiz_passing_score else 70
            quiz_max_attempts = int(quiz_max_attempts) if quiz_max_attempts else 1
        except ValueError:
            quiz_time_limit = 30
            quiz_passing_score = 70
            quiz_max_attempts = 1

        # Crear la lección
        last_order = module.lessons.count()
        lesson = Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            lesson_type='quiz',
            content=content,
            is_free=is_free,
            duration_minutes=duration,
            order=last_order + 1
        )

        # Crear evaluación asociada
        from .models import Evaluation, QuestionEvaluation, QuestionOption
        evaluation = Evaluation.objects.create(
            lesson=lesson,
            title=f'Cuestionario: {title}',
            description=content,
            evaluation_type='quiz',
            time_limit_minutes=quiz_time_limit,
            passing_score=quiz_passing_score,
            max_attempts=quiz_max_attempts,
            is_active=True
        )

        # Procesar preguntas
        question_count = 0
        for key, value in request.POST.items():
            if key.startswith('question_') and key.endswith('_text'):
                # Extraer el número de la pregunta
                parts = key.split('_')
                if len(parts) >= 3:
                    q_num = parts[1]
                    if q_num.isdigit():
                        question_text = value.strip()
                        if question_text:
                            question_count += 1
                            # Crear la pregunta
                            question = QuestionEvaluation.objects.create(
                                evaluation=evaluation,
                                question_type='multiple',
                                text=question_text,
                                points=1,
                                order=question_count
                            )
                            
                            # Buscar opciones de esta pregunta
                            option_count = 0
                            for opt_key, opt_value in request.POST.items():
                                if opt_key.startswith(f'question_{q_num}_option_'):
                                    opt_parts = opt_key.split('_')
                                    if len(opt_parts) >= 5:
                                        opt_index = opt_parts[3]
                                        if opt_index.isdigit() and opt_value.strip():
                                            option_count += 1
                                            # Verificar si es correcta
                                            correct_key = f'question_{q_num}_correct_{opt_index}'
                                            is_correct = correct_key in request.POST
                                            
                                            QuestionOption.objects.create(
                                                question=question,
                                                text=opt_value.strip(),
                                                is_correct=is_correct
                                            )

        if question_count == 0:
            messages.warning(request, 'No se agregaron preguntas al cuestionario. Puedes editarlo después.')
        else:
            messages.success(request, f'Cuestionario "{title}" creado con {question_count} preguntas.')

        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/lecciones/crear_cuestionario.html', {'module': module})


@login_required
def create_lesson_exam_view(request, module_id):
    module, course = get_module_and_check_permission(request, module_id)
    if not module:
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        content = request.POST.get('content', '').strip()
        is_free = request.POST.get('is_free') == 'on'
        duration = request.POST.get('duration', 0)
        exam_time_limit = request.POST.get('exam_time_limit', 60)
        exam_passing_score = request.POST.get('exam_passing_score', 70)
        exam_max_attempts = request.POST.get('exam_max_attempts', 1)

        if not title or len(title) < 3:
            messages.error(request, 'El título es obligatorio y debe tener al menos 3 caracteres.')
            return render(request, 'academi/lecciones/crear_examen.html', {
                'module': module,
                'form_data': request.POST
            })

        if not content:
            messages.error(request, 'Las instrucciones del examen son obligatorias.')
            return render(request, 'academi/lecciones/crear_examen.html', {
                'module': module,
                'form_data': request.POST
            })

        try:
            duration = int(duration) if duration else 0
            exam_time_limit = int(exam_time_limit) if exam_time_limit else 60
            exam_passing_score = int(exam_passing_score) if exam_passing_score else 70
            exam_max_attempts = int(exam_max_attempts) if exam_max_attempts else 1
        except ValueError:
            exam_time_limit = 60
            exam_passing_score = 70
            exam_max_attempts = 1

        # Crear la lección
        last_order = module.lessons.count()
        lesson = Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            lesson_type='exam',
            content=content,
            is_free=is_free,
            duration_minutes=duration,
            order=last_order + 1
        )

        # Crear evaluación asociada
        from .models import Evaluation, QuestionEvaluation, QuestionOption
        evaluation = Evaluation.objects.create(
            lesson=lesson,
            title=f'Examen: {title}',
            description=content,
            evaluation_type='exam',
            time_limit_minutes=exam_time_limit,
            passing_score=exam_passing_score,
            max_attempts=exam_max_attempts,
            is_active=True
        )

        # Procesar preguntas
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
                                            option_count += 1
                                            correct_key = f'question_{q_num}_correct_{opt_index}'
                                            is_correct = correct_key in request.POST
                                            
                                            QuestionOption.objects.create(
                                                question=question,
                                                text=opt_value.strip(),
                                                is_correct=is_correct
                                            )

        if question_count == 0:
            messages.warning(request, 'No se agregaron preguntas al examen. Puedes editarlo después.')
        else:
            messages.success(request, f'Examen "{title}" creado con {question_count} preguntas.')

        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/lecciones/crear_examen.html', {'module': module})


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
        assignment_deadline = request.POST.get('assignment_deadline', '')

        if not title or len(title) < 3:
            messages.error(request, 'El título es obligatorio y debe tener al menos 3 caracteres.')
            return render_lesson_form(request, module, 'academi/lecciones/crear_tarea.html', request.POST)

        if not content:
            messages.error(request, 'La descripción de la tarea es obligatoria.')
            return render_lesson_form(request, module, 'academi/lecciones/crear_tarea.html', request.POST)

        if not assignment_deadline:
            messages.error(request, 'Debes establecer una fecha de entrega.')
            return render_lesson_form(request, module, 'academi/lecciones/crear_tarea.html', request.POST)

        try:
            duration = int(duration) if duration else 0
        except ValueError:
            duration = 0

        last_order = module.lessons.count()
        lesson = Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            lesson_type='assignment',
            content=content,
            is_free=is_free,
            duration_minutes=duration,
            order=last_order + 1
        )

        messages.success(request, f'Tarea "{title}" creada correctamente.')
        return redirect('manage_course', course_id=course.id)

    return render_lesson_form(request, module, 'academi/lecciones/crear_tarea.html')