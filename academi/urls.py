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
    path('my-certificates/<int:certificate_id>/', views.certificate_detail_view, name='certificate_detail'),
    path('my-certificates/<int:certificate_id>/send-email/', views.certificate_send_email_view, name='certificate_send_email'),
    path('verify-certificate/<str:code>/', views.verify_certificate_view, name='verify_certificate'),
    path('my-favorites/', views.my_favorites_view, name='my_favorites'),
    path('purchase-history/', views.purchase_history_view, name='purchase_history'),
    path('purchase-history/invoice/<int:payment_id>/', views.invoice_view, name='invoice'),
    
    # ============================================
    # CARRITO DE COMPRAS (AGREGAR ESTO)
    # ============================================
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:course_id>/', views.cart_add_view, name='cart_add'),
    path('cart/remove/<int:course_id>/', views.cart_remove_view, name='cart_remove'),
    path('cart/items/', views.cart_items_view, name='cart_items'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('api/validate-coupon/', views.validate_coupon_api, name='validate_coupon_api'),
    path('api/get-active-coupon/', views.get_active_coupon_api, name='get_active_coupon_api'),
    
    # ============================================
    # CATÁLOGO
    # ============================================
    path('catalog/', views.catalog_view, name='catalog'),
    path('search/', views.search_courses_view, name='search_courses'),
    path('categories/', views.categories_view, name='categories'),
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('course/<int:course_id>/favorite/', views.favorite_toggle_view, name='favorite_toggle'),
    
    # Chatbot
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('chatbot/send/', views.chatbot_send_message, name='chatbot_send'),
    
    # Admin
    path('panel/usuarios/', views.admin_users_view, name='admin_users'),
    path('panel/usuarios/crear/', views.admin_user_create, name='admin_user_create'),
    path('panel/usuarios/editar/<int:user_id>/', views.admin_user_edit, name='admin_user_edit'),
    path('panel/usuarios/eliminar/<int:user_id>/', views.admin_user_delete, name='admin_user_delete'),
    path('panel/usuarios/activar/<int:user_id>/', views.admin_user_toggle_active, name='admin_user_toggle'),
    path('panel/usuarios/reset-password/<int:user_id>/', views.admin_user_reset_password, name='admin_user_reset_password'),
    
    # NOTA: estas rutas usan el prefijo 'panel/' (y no 'admin/') porque
    # core/urls.py registra Django admin en 'admin/' antes de estas urls;
    # usar 'admin/' aquí hacía que todas estas vistas fueran inalcanzables
    # (Django las interceptaba y redirigía al login del admin de Django).
    path('panel/courses/', views.admin_courses_view, name='admin_courses'),
    path('panel/courses/<int:course_id>/<str:action>/', views.admin_course_moderate, name='admin_course_moderate'),
    path('panel/categories/', views.admin_categories_view, name='admin_categories'),
    path('panel/categories/<int:category_id>/edit/', views.admin_category_edit, name='admin_category_edit'),
    path('panel/categories/<int:category_id>/delete/', views.admin_category_delete, name='admin_category_delete'),
    path('panel/reports/', views.admin_reports_view, name='admin_reports'),
    path('panel/reports/<int:report_id>/<str:action>/', views.admin_report_resolve, name='admin_report_resolve'),
    path('panel/coupons/', views.admin_coupons_view, name='admin_coupons'),
    path('panel/coupons/<int:coupon_id>/toggle/', views.admin_coupon_toggle, name='admin_coupon_toggle'),
    path('panel/coupons/<int:coupon_id>/editar/', views.admin_coupon_edit, name='admin_coupon_edit'),
    path('panel/payments/', views.admin_payments_view, name='admin_payments'),
    path('panel/certificates/', views.admin_certificates_view, name='admin_certificates'),
    path('panel/reports-generate/', views.admin_reports_generate_view, name='admin_reports_generate'),
    
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
path('mis-cupones/', views.teacher_coupons_view, name='teacher_coupons'),
path('mis-cupones/<int:coupon_id>/editar/', views.teacher_coupon_edit, name='teacher_coupon_edit'),
path('mis-cupones/<int:coupon_id>/activar/', views.teacher_coupon_toggle, name='teacher_coupon_toggle'),
path('mis-cupones/<int:coupon_id>/eliminar/', views.teacher_coupon_delete, name='teacher_coupon_delete'),

# ============================================
# MÓDULO 5: COMENTARIOS, PREGUNTAS, RESEÑAS Y REPORTES
# ============================================
path('lesson/<int:lesson_id>/comments/add/', views.add_comment_view, name='add_comment'),
path('comments/<int:comment_id>/edit/', views.edit_comment_view, name='edit_comment'),
path('comments/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),
path('lesson/<int:lesson_id>/questions/add/', views.add_question_view, name='add_question'),
path('questions/<int:question_id>/answer/', views.answer_question_view, name='answer_question'),
path('course/<int:course_id>/reviews/add/', views.add_review_view, name='add_review'),
path('reviews/<int:review_id>/edit/', views.edit_review_view, name='edit_review'),
path('reviews/<int:review_id>/delete/', views.delete_review_view, name='delete_review'),
path('reports/add/', views.report_content_view, name='report_content'),

# ============================================
# ENTREGA Y CALIFICACIÓN DE TAREAS
# ============================================
path('lesson/<int:lesson_id>/assignment/submit/', views.submit_assignment_view, name='submit_assignment'),
path('lesson/<int:lesson_id>/assignment/submissions/', views.assignment_submissions_view, name='assignment_submissions'),
path('assignment-submissions/<int:submission_id>/grade/', views.grade_assignment_view, name='grade_assignment'),

]