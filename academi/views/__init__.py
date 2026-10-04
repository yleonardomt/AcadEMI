from .auth import (
    home_view, register_view, login_view, logout_view, change_password_view,
    password_reset_request_view, password_reset_confirm_view,
    verify_email_view, profile_view,
    verify_pending_view, resend_verification_email_view, terms_view,
)
from .dashboard import (
    dashboard_view, notifications_view, mark_all_notifications_read_view,
    my_courses_view, my_progress_view,
    my_grades_view, my_certificates_view, my_favorites_view,
    mis_estudiantes_view, mis_resenas_view, certificate_detail_view,
    verify_certificate_view, certificate_send_email_view,
)
from .courses import (
    create_course_view, manage_course_view, edit_course_view,
    delete_course_view, publish_course_view, add_module_view,
    edit_module_view, delete_module_view, reorder_module_view,
    course_stats_view, course_students_view, catalog_view,
    search_courses_view, categories_view, course_detail_view,
    course_learn_view, favorite_toggle_view,
)
from .lessons import (
    add_lesson_view, edit_lesson_view, delete_lesson_view,
    reorder_lesson_view, upload_video_view, upload_document_view,
    lesson_view, mark_lesson_complete, get_module_and_check_permission,
    render_lesson_form, create_lesson_text_view, create_lesson_video_view,
    create_lesson_document_view, create_lesson_quiz_view,
    create_lesson_assignment_view,
    submit_assignment_view, assignment_submissions_view, grade_assignment_view,
)
from .quizzes import quiz_view, quiz_result_view, quiz_tab_switch_alert
from .cart import cart_add_view, cart_remove_view, cart_items_view, cart_view
from .payments import (
    checkout_view, validate_coupon_api, get_active_coupon_api,
    purchase_history_view, invoice_view, invoice_pdf_view,
    teacher_coupons_view, teacher_coupon_edit, teacher_coupon_toggle, teacher_coupon_delete,
)
from .admin_panel import (
    admin_payments_view, admin_courses_view, admin_categories_view,
    admin_reports_view, admin_coupons_view, admin_certificates_view,
    admin_reports_generate_view, admin_users_view, admin_user_create,
    admin_user_edit, admin_user_delete, admin_user_toggle_active,
    admin_user_reset_password, admin_course_moderate, admin_report_resolve,
    admin_category_edit, admin_category_delete, admin_coupon_toggle,
    admin_coupon_edit, admin_certificate_toggle,
)
from .chatbot import chatbot_view, chatbot_send_message
from .engagement import (
    add_comment_view, edit_comment_view, delete_comment_view,
    add_question_view, answer_question_view, teacher_questions_view,
    add_review_view, edit_review_view, delete_review_view,
    report_content_view,
)
