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
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('reset-password/<str:uidb64>/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email_view, name='verify_email'),
    
    # Dashboard y Perfil
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('notifications/', views.notifications_view, name='notifications'),
    
    # ============================================
    # GESTIÓN DE CURSOS
    # ============================================
    path('my-courses/', views.my_courses_view, name='my_courses'),
    path('create-course/', views.create_course_view, name='create_course'),
    path('course/edit/<int:course_id>/', views.edit_course_view, name='edit_course'),
    path('course/delete/<int:course_id>/', views.delete_course_view, name='delete_course'),
    path('course/publish/<int:course_id>/', views.publish_course_view, name='publish_course'),
    path('manage-course/<int:course_id>/', views.manage_course_view, name='manage_course'),
    
    # Módulos
    path('course/<int:course_id>/add-module/', views.add_module_view, name='add_module'),
    path('module/edit/<int:module_id>/', views.edit_module_view, name='edit_module'),
    path('module/delete/<int:module_id>/', views.delete_module_view, name='delete_module'),
    path('module/reorder/<int:module_id>/<str:direction>/', views.reorder_module_view, name='reorder_module'),
    
    # Lecciones
    path('module/<int:module_id>/add-lesson/', views.add_lesson_view, name='add_lesson'),
    path('lesson/edit/<int:lesson_id>/', views.edit_lesson_view, name='edit_lesson'),
    path('lesson/delete/<int:lesson_id>/', views.delete_lesson_view, name='delete_lesson'),
    path('lesson/reorder/<int:lesson_id>/<str:direction>/', views.reorder_lesson_view, name='reorder_lesson'),
    path('lesson/<int:lesson_id>/upload-video/', views.upload_video_view, name='upload_video'),
    path('lesson/<int:lesson_id>/upload-document/', views.upload_document_view, name='upload_document'),
    
    # Estadísticas y estudiantes
    path('course/<int:course_id>/stats/', views.course_stats_view, name='course_stats'),
    path('course/<int:course_id>/students/', views.course_students_view, name='course_students'),
    
    # Para estudiante
    path('my-progress/', views.my_progress_view, name='my_progress'),
    path('my-grades/', views.my_grades_view, name='my_grades'),
    path('my-certificates/', views.my_certificates_view, name='my_certificates'),
    path('my-favorites/', views.my_favorites_view, name='my_favorites'),
    path('purchase-history/', views.purchase_history_view, name='purchase_history'),
    
    # ============================================
    # CARRITO DE COMPRAS (AGREGAR ESTO)
    # ============================================
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:course_id>/', views.cart_add_view, name='cart_add'),
    path('cart/remove/<int:course_id>/', views.cart_remove_view, name='cart_remove'),
    path('cart/items/', views.cart_items_view, name='cart_items'),
    path('checkout/', views.checkout_view, name='checkout'),
    
    # ============================================
    # CATÁLOGO
    # ============================================
    path('catalog/', views.catalog_view, name='catalog'),
    path('search/', views.search_courses_view, name='search_courses'),
    path('categories/', views.categories_view, name='categories'),
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    
    # Chatbot
    path('chatbot/', views.chatbot_view, name='chatbot'),
    
    # Admin
    path('panel/usuarios/', views.admin_users_view, name='admin_users'),
    path('panel/usuarios/crear/', views.admin_user_create, name='admin_user_create'),
    path('panel/usuarios/editar/<int:user_id>/', views.admin_user_edit, name='admin_user_edit'),
    path('panel/usuarios/eliminar/<int:user_id>/', views.admin_user_delete, name='admin_user_delete'),
    path('panel/usuarios/activar/<int:user_id>/', views.admin_user_toggle_active, name='admin_user_toggle'),
    path('panel/usuarios/reset-password/<int:user_id>/', views.admin_user_reset_password, name='admin_user_reset_password'),
    
    path('admin/courses/', views.admin_courses_view, name='admin_courses'),
    path('admin/categories/', views.admin_categories_view, name='admin_categories'),
    path('admin/reports/', views.admin_reports_view, name='admin_reports'),
    path('admin/coupons/', views.admin_coupons_view, name='admin_coupons'),
    path('admin/payments/', views.admin_payments_view, name='admin_payments'),
    path('admin/certificates/', views.admin_certificates_view, name='admin_certificates'),
    path('admin/reports-generate/', views.admin_reports_generate_view, name='admin_reports_generate'),
    
    # ============================================
    # CREAR LECCIONES POR TIPO
    # ============================================
    path('module/<int:module_id>/lesson/create/text/', views.create_lesson_text_view, name='create_lesson_text'),
    path('module/<int:module_id>/lesson/create/video/', views.create_lesson_video_view, name='create_lesson_video'),
    path('module/<int:module_id>/lesson/create/document/', views.create_lesson_document_view, name='create_lesson_document'),
    path('module/<int:module_id>/lesson/create/quiz/', views.create_lesson_quiz_view, name='create_lesson_quiz'),
    path('module/<int:module_id>/lesson/create/assignment/', views.create_lesson_assignment_view, name='create_lesson_assignment'),
    # En la sección de URLs
path('course/learn/<int:course_id>/', views.course_learn_view, name='course_learn'),
path('lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
path('lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
path('quiz/<int:lesson_id>/', views.quiz_view, name='quiz_view'),
path('quiz/result/<int:result_id>/', views.quiz_result_view, name='quiz_result'),
# urls.py
path('quiz/alert/tab-switch/', views.quiz_tab_switch_alert, name='quiz_tab_switch_alert'),
path('mis-estudiantes/', views.mis_estudiantes_view, name='mis_estudiantes'),
path('mis-resenas/', views.mis_resenas_view, name='mis_resenas'),


]