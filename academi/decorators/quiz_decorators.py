# academi/decorators/quiz_decorators.py
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from ..models import Evaluation, Enrollment, EvaluationResult, Lesson
from ..utils import QuizSecurityManager, AntiCheatingMonitor


# ============================================
# QUIZ REQUIRED - Verificar que el cuestionario existe y está disponible
# ============================================
def quiz_required(view_func):
    @wraps(view_func)
    def wrapper(request, lesson_id, *args, **kwargs):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        evaluation = Evaluation.objects.filter(lesson=lesson).first()
        
        if not evaluation:
            messages.error(request, 'Este cuestionario no está disponible.')
            return redirect('course_learn', course_id=lesson.module.course.id)
        
        enrollment = Enrollment.objects.filter(
            student=request.user,
            course=lesson.module.course
        ).first()
        
        if not enrollment:
            messages.error(request, 'No estás inscrito en este curso.')
            return redirect('catalog')
        
        security = QuizSecurityManager(request.user, evaluation)
        if not security.check_attempt_limit():
            messages.error(request, 'Has alcanzado el límite de intentos para este cuestionario.')
            return redirect('course_learn', course_id=lesson.module.course.id)
        
        request.quiz_evaluation = evaluation
        request.quiz_enrollment = enrollment
        request.quiz_security = security
        
        return view_func(request, lesson_id, *args, **kwargs)
    return wrapper


# ============================================
# PREVENT CHEATING - Prevenir trampas durante el cuestionario
# ============================================
def prevent_cheating(view_func):
    @wraps(view_func)
    def wrapper(request, lesson_id, *args, **kwargs):
        if request.method == 'POST':
            # Verificar que la sesión está activa
            if not request.session.get('quiz_active', False):
                return JsonResponse({
                    'error': 'Sesión de cuestionario expirada',
                    'code': 'SESSION_EXPIRED'
                }, status=403)
            
            # Verificar tiempo límite
            start_time = request.session.get('quiz_start_time')
            if start_time:
                try:
                    start_time = timezone.datetime.fromisoformat(start_time)
                    limit = request.quiz_evaluation.time_limit_minutes
                    elapsed = (timezone.now() - start_time).total_seconds()
                    if elapsed > limit * 60:
                        return JsonResponse({
                            'error': 'Tiempo límite excedido',
                            'code': 'TIME_EXCEEDED'
                        }, status=403)
                except:
                    pass  # Si falla, continuar
            
            # Verificar trampas
            try:
                monitor = AntiCheatingMonitor(None)
                
                if monitor.check_tab_switch(request):
                    return JsonResponse({
                        'error': 'Cambio de pestaña detectado',
                        'code': 'TAB_SWITCH'
                    }, status=403)
                
                if monitor.check_copy_paste(request):
                    return JsonResponse({
                        'error': 'Copiar/pegar no permitido',
                        'code': 'COPY_PASTE'
                    }, status=403)
            except:
                pass  # Si falla, continuar
        
        return view_func(request, lesson_id, *args, **kwargs)
    return wrapper


# ============================================
# VALIDATE QUIZ TOKEN - Validar token de seguridad
# ============================================
def validate_quiz_token(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = request.GET.get('token') or request.POST.get('token')
        
        if not token:
            messages.error(request, 'Token de seguridad requerido.')
            return redirect('catalog')
        
        security = getattr(request, 'quiz_security', None)
        if not security:
            messages.error(request, 'Sesión de cuestionario inválida.')
            return redirect('catalog')
        
        if not security.verify_token(token):
            messages.error(request, 'Token de seguridad inválido.')
            return redirect('catalog')
        
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================
# RATE LIMIT - Limitar intentos de envío
# ============================================
def rate_limit_quiz(max_attempts=5, period=60):
    """
    Decorador para limitar intentos de envío de cuestionarios.
    max_attempts: Número máximo de intentos permitidos en el periodo
    period: Período de tiempo en segundos
    """
    from django.core.cache import cache
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                # Usar IP + usuario para identificar
                key = f'quiz_rate_{request.user.id}_{request.META.get("REMOTE_ADDR")}'
                
                try:
                    attempts = cache.get(key, 0)
                    
                    if attempts >= max_attempts:
                        return JsonResponse({
                            'error': f'Demasiados intentos. Espera {period} segundos.',
                            'code': 'RATE_LIMIT_EXCEEDED'
                        }, status=429)
                    
                    # Incrementar contador
                    cache.set(key, attempts + 1, period)
                except:
                    pass  # Si falla, continuar
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator