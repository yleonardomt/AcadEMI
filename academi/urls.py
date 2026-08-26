from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home_view, name='home'),
    
    # Autenticación
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    # Dashboard y Perfil
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # Admin - CRUD Usuarios (USAR panel/ EN VEZ DE admin/)
    path('panel/usuarios/', views.admin_users_view, name='admin_users'),
    path('panel/usuarios/crear/', views.admin_user_create, name='admin_user_create'),
    path('panel/usuarios/editar/<int:user_id>/', views.admin_user_edit, name='admin_user_edit'),
    path('panel/usuarios/eliminar/<int:user_id>/', views.admin_user_delete, name='admin_user_delete'),
    path('panel/usuarios/activar/<int:user_id>/', views.admin_user_toggle_active, name='admin_user_toggle'),
    path('panel/usuarios/reset-password/<int:user_id>/', views.admin_user_reset_password, name='admin_user_reset_password'),
]