from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from .forms import RegisterForm, LoginForm, UserProfileForm
from django.utils import timezone

User = get_user_model()

# ============================================
# HOME
# ============================================
def home_view(request):
    return render(request, 'academi/index.html')


# ============================================
# REGISTER
# ============================================
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Registro exitoso! Bienvenido a Academia Bolivia.')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    
    return render(request, 'academi/register.html', {'form': form})


# ============================================
# LOGIN
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
                    messages.success(request, f'¡Bienvenido de vuelta, {user.username}!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
    else:
        form = LoginForm()
    
    return render(request, 'academi/login.html', {'form': form})


# ============================================
# LOGOUT
# ============================================
def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


# ============================================
# DASHBOARD
# ============================================
@login_required
def dashboard_view(request):
    context = {
        'user': request.user,
        'is_student': request.user.role == 'student',
        'is_teacher': request.user.role == 'teacher',
        'is_admin': request.user.role == 'admin',
        'now': timezone.now(),
    }
    return render(request, 'academi/dashboard.html', context)


# ============================================
# PERFIL
# ============================================
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Perfil actualizado correctamente!')
            return redirect('profile')
        else:
            messages.error(request, 'Error al actualizar el perfil. Revisa los campos.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'academi/perfil.html', {'form': form})


# ============================================
# CAMBIAR CONTRASEÑA
# ============================================
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '¡Contraseña cambiada correctamente!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Error al cambiar la contraseña. Revisa los campos.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'academi/cambiar_contraseña.html', {'form': form})


# ============================================
# ADMIN - CRUD USUARIOS
# ============================================
@login_required
def admin_users_view(request):
    # Verificar que sea admin
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard')
    
    # Búsqueda
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query) | 
            Q(first_name__icontains=query)
        ).order_by('-date_joined')
    else:
        users = User.objects.all().order_by('-date_joined')
    
    # Estadísticas
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_admins = User.objects.filter(role='admin').count()
    total_active = User.objects.filter(is_active=True).count()
    total_inactive = User.objects.filter(is_active=False).count()
    
    context = {
        'users': users,
        'query': query,
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_admins': total_admins,
        'total_active': total_active,
        'total_inactive': total_inactive,
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
        
        # Validaciones
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return redirect('admin_users')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado.')
            return redirect('admin_users')
        
        if len(password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return redirect('admin_users')
        
        # Crear usuario
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
    
    # No permitir eliminar a sí mismo
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
    
    # No permitir desactivar a sí mismo
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