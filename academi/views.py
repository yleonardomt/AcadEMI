from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit

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
from .utils import (
    send_verification_email, 
    send_password_reset_email, 
    generate_reset_link,
    get_client_ip,
    QuizSecurityManager,
    AntiCheatingMonitor,
    rate_limit_quiz
)
from .decorators.quiz_decorators import quiz_required, prevent_cheating, validate_quiz_token

import secrets
import json
import re
import logging

logger = logging.getLogger(__name__)
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
        courses = [enrollment.course for enrollment in enrollments]
        return render(request, 'academi/mis_cursos.html', {'courses': courses})


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
    items = cart.items.select_related('course').all()
    total = sum(item.course.price for item in items if not item.course.is_free)
    
    context = {
        'cart': cart,
        'items': items,
        'items_count': items.count(),
        'total': total,
    }
    return render(request, 'academi/carrito.html', context)


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
    from .models import Lesson, Evaluation, QuestionEvaluation, QuestionOption
    from django.shortcuts import get_object_or_404, redirect, render
    from django.contrib import messages
    import json
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    
    if request.user != course.teacher and request.user.role != 'admin':
        messages.error(request, 'No tienes permisos.')
        return redirect('dashboard')
    
    # ============================================
    # DETERMINAR TEMPLATE
    # ============================================
    template_map = {
        'text': 'academi/lecciones/crear_texto.html',
        'video': 'academi/lecciones/crear_video.html',
        'document': 'academi/lecciones/crear_documento.html',
        'quiz': 'academi/lecciones/crear_cuestionario.html',
        'exam': 'academi/lecciones/crear_cuestionario.html',
        'assignment': 'academi/lecciones/crear_tarea.html',
    }
    
    template = template_map.get(lesson.lesson_type, 'academi/lecciones/crear_texto.html')
    
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
    # 🔥 OBTENER PREGUNTAS EXISTENTES
    # ============================================
    preguntas = []
    
    if lesson.lesson_type in ['quiz', 'exam']:
        evaluation = Evaluation.objects.filter(lesson=lesson).first()
        print(f"🔍 Evaluación encontrada: {evaluation}")  # DEBUG
        
        if evaluation:
            form_data['time_limit'] = evaluation.time_limit_minutes
            form_data['passing_score'] = evaluation.passing_score
            form_data['max_attempts'] = evaluation.max_attempts
            
            questions = QuestionEvaluation.objects.filter(evaluation=evaluation).order_by('order')
            print(f"📝 Preguntas encontradas: {questions.count()}")  # DEBUG
            
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
                print(f"  ✅ Pregunta: {q.text} - {len(options)} opciones")  # DEBUG
        else:
            print("❌ NO hay evaluación para esta lección")
    
    print(f"📊 Total preguntas en contexto: {len(preguntas)}")  # DEBUG
    
    # ============================================
    # 🔥 CONVERTIR A JSON PARA EL JAVASCRIPT
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
    # 🔥 RENDERIZAR CON TODOS LOS DATOS
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
    categories = Category.objects.all()
    
    q = request.GET.get('q', '')
    if q:
        courses = courses.filter(
            Q(title__icontains=q) | 
            Q(description__icontains=q) |
            Q(teacher__username__icontains=q)
        )
    
    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    level = request.GET.get('level')
    if level:
        courses = courses.filter(level=level)
    
    price = request.GET.get('price')
    if price == 'free':
        courses = courses.filter(is_free=True)
    elif price == 'paid':
        courses = courses.filter(is_free=False)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'newest':
        courses = courses.order_by('-created_at')
    elif sort == 'popular':
        courses = courses.annotate(student_count=Count('enrollments')).order_by('-student_count')
    elif sort == 'price_low':
        courses = courses.order_by('price')
    elif sort == 'price_high':
        courses = courses.order_by('-price')
    elif sort == 'rating':
        courses = courses.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    
    user_enrolled_courses = []
    if request.user.is_authenticated and request.user.role == 'student':
        user_enrolled_courses = Enrollment.objects.filter(
            student=request.user,
            status__in=['enrolled', 'in_progress', 'completed']
        ).values_list('course_id', flat=True)
    
    context = {
        'courses': courses,
        'categories': categories,
        'user_enrolled_courses': list(user_enrolled_courses),
    }
    return render(request, 'academi/catalogo.html', context)


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


def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='published')
    return render(request, 'academi/curso_detalle.html', {'course': course})


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
    if progress == 100 and enrollment.status != 'completed':
        enrollment.status = 'completed'
        enrollment.completed_date = timezone.now()
    elif progress > 0 and enrollment.status == 'enrolled':
        enrollment.status = 'in_progress'
    enrollment.save()
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'modules': modules,
        'completed_lessons': completed_lessons,
        'progress': progress,
        'total_lessons': total_lessons,
        'completed_count': completed_count,
    }
    return render(request, 'academi/curso_aprender.html', context)


@login_required
def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    
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
    # MARCAR LECCIÓN COMO VISTA
    # ============================================
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
    
    # ============================================
    # CALCULAR PROGRESO
    # ============================================
    modules = course.modules.all()
    total_lessons = 0
    completed_count = 0
    
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
    }
    
    return render(request, 'academi/leccion_detalle.html', context)


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
    if progress == 100 and enrollment.status != 'completed':
        enrollment.status = 'completed'
        enrollment.completed_date = timezone.now()
    elif progress > 0 and enrollment.status == 'enrolled':
        enrollment.status = 'in_progress'
    enrollment.save()
    
    return JsonResponse({
        'success': True,
        'progress': progress,
        'completed_count': completed_count,
        'total_lessons': total_lessons,
        'message': 'Lección completada'
    })


# ============================================
# MÓDULO 6: EVALUACIONES / CUESTIONARIOS
# ============================================
@login_required
@ratelimit(key='user', rate='5/m', method=['POST'], block=True)
@quiz_required
@prevent_cheating
def quiz_view(request, lesson_id):
    from django.shortcuts import get_object_or_404, render
    from django.http import JsonResponse
    from django.utils import timezone
    from .models import Lesson, QuestionEvaluation, QuestionOption, EvaluationResult, EvaluationIncident, LessonProgress
    from .utils import get_client_ip
    import json
    import secrets
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    evaluation = request.quiz_evaluation
    enrollment = request.quiz_enrollment
    
    # Generar token
    token = secrets.token_urlsafe(32)
    
    # GET - Iniciar sesión
    if request.method == 'GET':
        request.session['quiz_active'] = True
        request.session['quiz_start_time'] = timezone.now().isoformat()
        request.session['quiz_token'] = token
        request.session['quiz_ip'] = get_client_ip(request)
        request.session['quiz_user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        request.session['quiz_alerts'] = []
    
    # Obtener preguntas
    questions = QuestionEvaluation.objects.filter(evaluation=evaluation).order_by('order')
    
    # POST - Procesar respuestas
    if request.method == 'POST':
        try:
            body = request.body.decode('utf-8')
            data = json.loads(body)
            token_recibido = data.get('token', '')
            answers = data.get('answers', {})
            
            # Verificar token
            token_sesion = request.session.get('quiz_token', '')
            if not token_recibido or token_recibido != token_sesion:
                return JsonResponse({
                    'error': 'Token de seguridad inválido',
                    'code': 'INVALID_TOKEN'
                }, status=403)
            
            # Calcular puntaje
            score = 0
            total_points = 0
            
            for question in questions:
                total_points += question.points or 1
                answer_key = f'q_{question.id}'
                
                if answer_key in answers:
                    selected_option_id = answers[answer_key]
                    option = QuestionOption.objects.filter(
                        id=selected_option_id,
                        question=question
                    ).first()
                    
                    if option and option.is_correct:
                        score += question.points or 1
            
            percentage = int((score / total_points) * 100) if total_points > 0 else 0
            passed = percentage >= evaluation.passing_score
            
            # Calcular tiempo
            start_time_str = request.session.get('quiz_start_time')
            time_spent = 0
            if start_time_str:
                try:
                    start_time = timezone.datetime.fromisoformat(start_time_str)
                    time_spent = int((timezone.now() - start_time).total_seconds())
                except:
                    pass
            
            # Crear resultado
            result = EvaluationResult.objects.create(
                enrollment=enrollment,
                evaluation=evaluation,
                score=score,
                total_points=total_points,
                passed=passed,
                completed_at=timezone.now(),
                time_spent=time_spent,
                attempt_number=EvaluationResult.objects.filter(
                    enrollment=enrollment,
                    evaluation=evaluation
                ).count() + 1,
                ip_address=request.session.get('quiz_ip'),
                user_agent=request.session.get('quiz_user_agent')
            )
            
            # ============================================
            # 🔥 MARCAR LECCIÓN COMO COMPLETADA
            # ============================================
            if passed:
                # Marcar la lección como completada
                lesson_progress, created = LessonProgress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=lesson,
                    defaults={'completed': True, 'completed_at': timezone.now()}
                )
                if not lesson_progress.completed:
                    lesson_progress.completed = True
                    lesson_progress.completed_at = timezone.now()
                    lesson_progress.save()
                
                # Actualizar progreso del curso
                modules = lesson.module.course.modules.all()
                total_lessons = 0
                completed_count = 0
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
            
            # Registrar incidentes
            alerts = request.session.get('quiz_alerts', [])
            for alert in alerts:
                if alert in ['tab_switch', 'copy_paste', 'timeout']:
                    EvaluationIncident.objects.create(
                        evaluation_result=result,
                        incident_type=alert,
                        description=f'Incidente detectado: {alert}'
                    )
            
            # Limpiar sesión
            request.session['quiz_active'] = False
            request.session.pop('quiz_start_time', None)
            request.session.pop('quiz_token', None)
            request.session.pop('quiz_alerts', None)
            request.session.pop('quiz_kicked', None)
            
            return JsonResponse({
                'success': True,
                'score': score,
                'total_points': total_points,
                'percentage': percentage,
                'passed': passed,
                'result_id': result.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Datos inválidos',
                'code': 'INVALID_DATA'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'code': 'SERVER_ERROR'
            }, status=500)
    
    # Contexto para GET
    attempts_used = EvaluationResult.objects.filter(
        enrollment=enrollment,
        evaluation=evaluation
    ).count()
    
    context = {
        'lesson': lesson,
        'course': lesson.module.course,
        'evaluation': evaluation,
        'questions': questions,
        'token': token,
        'enrollment': enrollment,
        'time_limit': evaluation.time_limit_minutes,
        'max_attempts': evaluation.max_attempts,
        'attempts_used': attempts_used,
        'passing_score': evaluation.passing_score,
    }
    return render(request, 'academi/quiz.html', context)


@login_required
def quiz_result_view(request, result_id):
    from django.shortcuts import get_object_or_404, redirect, render
    from django.contrib import messages
    from .models import EvaluationResult, EvaluationIncident
    
    result = get_object_or_404(EvaluationResult, id=result_id)
    
    if result.enrollment.student != request.user:
        messages.error(request, 'No tienes permiso para ver este resultado.')
        return redirect('dashboard')
    
    # ============================================
    # 🔥 CALCULAR INTENTOS
    # ============================================
    attempts_used = EvaluationResult.objects.filter(
        enrollment=result.enrollment,
        evaluation=result.evaluation
    ).count()
    
    max_attempts = result.evaluation.max_attempts
    remaining_attempts = max_attempts - attempts_used
    
    incidents = EvaluationIncident.objects.filter(evaluation_result=result)
    has_incidents = incidents.exists()
    
    percentage = int((result.score / result.total_points) * 100) if result.total_points > 0 else 0
    
    context = {
        'result': result,
        'percentage': percentage,
        'evaluation': result.evaluation,
        'course': result.enrollment.course,
        'lesson': result.evaluation.lesson,  # <-- PARA EL BOTÓN REINTENTAR
        'has_incidents': has_incidents,
        'incidents': incidents,
        'attempts_used': attempts_used,
        'max_attempts': max_attempts,
        'remaining_attempts': remaining_attempts,
    }
    return render(request, 'academi/quiz_resultado.html', context)


@login_required
def quiz_tab_switch_alert(request):
    import json
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lesson_id = data.get('lesson_id')
            count = data.get('count', 0)
            
            if 'quiz_alerts' not in request.session:
                request.session['quiz_alerts'] = []
            request.session['quiz_alerts'].append('tab_switch')
            
            if count > 3:
                request.session['quiz_kicked'] = True
                return JsonResponse({'kicked': True, 'message': 'Demasiados cambios de pestaña'})
            
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'error': 'Datos inválidos'}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============================================
# MÓDULO 7: CARRITO Y COMPRAS
# ============================================
@login_required
def checkout_view(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'message': 'Metodo no permitido.'
        })
    
    if request.user.role != 'student':
        return JsonResponse({
            'success': False, 
            'message': 'Solo estudiantes pueden comprar.'
        })
    
    cart = get_object_or_404(Cart, student=request.user)
    items = cart.items.all()
    
    if not items:
        return JsonResponse({
            'success': False, 
            'message': 'El carrito esta vacio.'
        })
    
    created_count = 0
    for item in items:
        if Enrollment.objects.filter(student=request.user, course=item.course).exists():
            continue
        
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=item.course,
            status='enrolled',
            payment_status='paid',
            payment_method='cart',
            payment_amount=0 if item.course.is_free else item.course.price,
            payment_date=timezone.now()
        )
        created_count += 1
        
        Notification.objects.create(
            user=request.user,
            type='purchase',
            title='Curso adquirido',
            message=f'Has comprado el curso "{item.course.title}" exitosamente.',
            link=f'/course/{item.course.id}/'
        )
    
    items.delete()
    
    if created_count == 0:
        return JsonResponse({
            'success': False,
            'message': 'No se pudo completar la compra. Los cursos ya están en tu lista.'
        })
    
    return JsonResponse({
        'success': True,
        'message': f'Compra realizada con exito. {created_count} curso(s) adquirido(s).'
    })


@login_required
def cart_add_view(request, course_id):
    try:
        if request.user.role != 'student':
            return JsonResponse({
                'success': False, 
                'message': 'Solo estudiantes pueden comprar.'
            })
        
        course = get_object_or_404(Course, id=course_id, status='published')
        
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return JsonResponse({
                'success': False, 
                'message': 'Ya has comprado este curso.'
            })
        
        cart, created = Cart.objects.get_or_create(student=request.user)
        
        if CartItem.objects.filter(cart=cart, course=course).exists():
            return JsonResponse({
                'success': False, 
                'message': 'El curso ya esta en el carrito.'
            })
        
        CartItem.objects.create(cart=cart, course=course)
        items_count = cart.items.count()
        
        return JsonResponse({
            'success': True,
            'message': 'Curso agregado al carrito',
            'items_count': items_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': str(e)
        })


@login_required
def cart_remove_view(request, course_id):
    try:
        cart = get_object_or_404(Cart, student=request.user)
        item = get_object_or_404(CartItem, cart=cart, course_id=course_id)
        item.delete()
        
        items_count = cart.items.count()
        
        return JsonResponse({
            'success': True,
            'message': 'Curso eliminado del carrito',
            'items_count': items_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def cart_items_view(request):
    try:
        cart, created = Cart.objects.get_or_create(student=request.user)
        items = list(cart.items.values_list('course_id', flat=True))
        
        return JsonResponse({
            'success': True,
            'items': items,
            'items_count': cart.items.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'items': [],
            'items_count': 0
        })


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
    from .models import Lesson, Evaluation, QuestionEvaluation, QuestionOption
    from django.shortcuts import get_object_or_404, redirect, render
    from django.contrib import messages
    
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
            return render(request, 'academi/lecciones/crear_cuestionario.html', {
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
            return render(request, 'academi/lecciones/crear_cuestionario.html', {
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
        print(f"✅ Lección creada: ID {lesson.id} - {lesson.title}")

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
        print(f"✅ Evaluación creada: ID {evaluation.id}")

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
                        print(f"📝 Pregunta {q_num} encontrada: {value}")

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
            print(f"✅ Pregunta {question_count} creada: {question_text}")
            
            option_count = 0
            print(f"🔍 Buscando opciones para pregunta {q_num}...")
            
            for opt_key, opt_value in request.POST.items():
                prefix = f'question_{q_num}_option_'
                if opt_key.startswith(prefix):
                    opt_index = opt_key[len(prefix):]
                    
                    print(f"  ✅ Encontrada opción: {opt_key} = {opt_value}")
                    
                    if opt_index.isdigit() and opt_value.strip():
                        correct_key = f'question_{q_num}_correct_{opt_index}'
                        is_correct = correct_key in request.POST
                        
                        QuestionOption.objects.create(
                            question=question,
                            text=opt_value.strip(),
                            is_correct=is_correct
                        )
                        option_count += 1
                        print(f"    ✅ Opción guardada: '{opt_value.strip()}' (correcta: {is_correct})")
            
            print(f"  📊 Total de opciones guardadas para pregunta {q_num}: {option_count}")
            
            if option_count == 0:
                default_options = ['Opción A', 'Opción B', 'Opción C', 'Opción D']
                for i, opt_text in enumerate(default_options):
                    QuestionOption.objects.create(
                        question=question,
                        text=opt_text,
                        is_correct=(i == 0)
                    )
                print(f"⚠️ Pregunta {q_num} no tenía opciones, se crearon por defecto.")

        print(f"✅ Total de preguntas guardadas: {question_count}")
        
        if question_count == 0:
            messages.warning(request, f'No se agregaron preguntas al {titulo_pagina.lower()}. Puedes editarlo después.')
        else:
            messages.success(request, f'{titulo_pagina} "{title}" creado con {question_count} preguntas.')

        return redirect('manage_course', course_id=course.id)

    return render(request, 'academi/lecciones/crear_cuestionario.html', {
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
            return render(request, 'academi/lecciones/crear_tarea.html', {
                'module': module,
                'form_data': request.POST
            })

        if not content:
            messages.error(request, 'La descripción de la tarea es obligatoria.')
            return render(request, 'academi/lecciones/crear_tarea.html', {
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

    return render(request, 'academi/lecciones/crear_tarea.html', {'module': module})