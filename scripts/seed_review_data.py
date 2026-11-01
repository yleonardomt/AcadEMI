#!/usr/bin/env python3
"""Llena una instalación académica con cuentas y actividad de revisión.

Uso: python scripts/seed_review_data.py --credentials-file backups/credenciales_revision.json
El archivo de claves debe ser local y no estar en Git. La carga es idempotente.
"""

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django  # noqa: E402
django.setup()

from django.db import transaction  # noqa: E402
from django.utils import timezone  # noqa: E402
from academi.models import (  # noqa: E402
    Answer, Certificate, Comment, Coupon, Course, Enrollment, Evaluation,
    EvaluationResult, Favorite, Lesson, LessonProgress, Notification, Payment,
    PaymentItem, Question, QuestionOption, Review, User, UserAnswer,
)


# Recursos abiertos de sus instituciones originales; no alojamos copias de los videos.
VIDEOS = {
    'Cálculo diferencial para ingeniería': ('https://www.youtube.com/watch?v=7K1sB05pE0A', 'MIT OpenCourseWare'),
    'Python aplicado a problemas de ingeniería': ('https://www.youtube.com/watch?v=nykOeWgQcHM', 'MIT OpenCourseWare'),
    'Álgebra lineal y matrices': ('https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/', 'MIT OpenCourseWare'),
    'Mecánica de estructuras y cargas': ('https://edtech.engineering.utoronto.ca/project-catalog/mechanics/beams/', 'University of Toronto'),
    'Bases de datos y SQL para proyectos': ('https://www.youtube.com/watch?v=WXk7yDqsKxs', 'Harvard CS50'),
    'Procesos y mejora continua': ('https://ocw.mit.edu/courses/16-660j-introduction-to-lean-six-sigma-methods-january-iap-2012/resources/lecture-videos/', 'MIT OpenCourseWare'),
    'Circuitos eléctricos fundamentales': ('https://www.youtube.com/watch?v=AfQxyVuLeCs', 'MIT OpenCourseWare'),
    'Control y sensores para mecatrónica': ('https://www.youtube.com/watch?v=Z8oMbOj9IWM', 'MIT OpenCourseWare'),
    'Señales y telecomunicaciones': ('https://www.youtube.com/watch?v=KJnAy6hzetw', 'MIT OpenCourseWare'),
    'Hidrología y gestión del agua': ('https://www.youtube.com/watch?v=XHeoQ0F6hYc', 'MIT OpenCourseWare'),
    'Cartografía digital y SIG': ('https://ocw.mit.edu/courses/introduction-to-r-and-gis-fall-2023/resources/lecture-videos/', 'MIT OpenCourseWare'),
    'Fundamentos de ingeniería petrolera': ('https://www.youtube.com/watch?v=8mfBomrw0rs', 'North Carolina State University'),
    'Matemática financiera aplicada': ('https://www.youtube.com/watch?v=Rm6UdfRs3gw', 'Khan Academy'),
    'Análisis de mercados y costos': ('https://www.youtube.com/watch?v=ShzPtU7IOXs', 'Khan Academy'),
}

BACKGROUND = [
    ('ana_salas', 'Ana', 'Salas', 'Ingeniería de Sistemas'),
    ('carlos_rojas', 'Carlos', 'Rojas', 'Ingeniería Civil'),
    ('lucia_mamani', 'Lucía', 'Mamani', 'Ingeniería Industrial'),
    ('diego_quispe', 'Diego', 'Quispe', 'Ingeniería Mecatrónica'),
    ('valeria_flores', 'Valeria', 'Flores', 'Ingeniería Ambiental'),
    ('marco_vargas', 'Marco', 'Vargas', 'Ingeniería Financiera'),
]


def account(username, password, role, **fields):
    user, created = User.objects.get_or_create(username=username, defaults={
        'email': f'{username}@example.invalid', 'role': role, **fields,
    })
    if not created and user.email != f'{username}@example.invalid':
        raise ValueError(f'El usuario {username} ya existe y no es una cuenta de revisión.')
    for key, value in fields.items():
        setattr(user, key, value)
    user.role = role
    user.email_verified = True
    user.is_active = True
    user.is_staff = role == 'admin'
    user.is_superuser = role == 'admin'
    user.set_password(password)
    user.save()
    return user


def enroll(student, course, fraction, completed=False):
    lessons = list(Lesson.objects.filter(module__course=course, is_published=True).order_by('module__order', 'order'))
    done = len(lessons) if completed else min(len(lessons), max(1, round(len(lessons) * fraction)))
    now = timezone.now()
    enrollment, _ = Enrollment.objects.get_or_create(student=student, course=course, defaults={
        'status': 'completed' if completed else 'in_progress',
        'progress_percentage': 100 if completed else round(done * 100 / len(lessons)),
        'completed_date': now if completed else None,
        'payment_status': 'demo' if not course.is_free else 'paid',
        'payment_method': 'demo' if not course.is_free else 'free',
        'payment_amount': Decimal('0.00'), 'payment_date': now,
    })
    if not course.is_free:
        marker = f'REVIEW-{student.username}-{course.pk}'
        payment = Payment.objects.filter(transaction_id=marker).first()
        if not payment:
            payment = Payment.objects.create(
                student=student, amount=course.price, final_amount=course.price,
                payment_method='demo', status='completed', transaction_id=marker,
                confirmed_at=now, billing_name=student.get_full_name(),
                billing_email=student.email, metadata={'source': 'review_seed'},
            )
        PaymentItem.objects.get_or_create(payment=payment, course=course, defaults={
            'price': course.price, 'final_price': course.price,
        })
        if not enrollment.transaction_id:
            enrollment.transaction_id = marker
            enrollment.save(update_fields=['transaction_id'])
    if enrollment.status in ('pending', 'enrolled'):
        enrollment.status = 'completed' if completed else 'in_progress'
        enrollment.progress_percentage = 100 if completed else round(done * 100 / len(lessons))
        enrollment.completed_date = now if completed else None
        enrollment.save(update_fields=['status', 'progress_percentage', 'completed_date'])
    for lesson in lessons[:done]:
        LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson, defaults={
            'completed': True, 'completed_at': now, 'time_spent': (lesson.duration_minutes or 15) * 60,
        })
    return enrollment


def grade_and_certificate(enrollment):
    evaluation = Evaluation.objects.filter(lesson__module__course=enrollment.course, is_active=True).first()
    if evaluation:
        questions = list(evaluation.questions.all().order_by('order'))
        total = sum(question.points for question in questions)
        result = EvaluationResult.objects.filter(enrollment=enrollment, evaluation=evaluation, attempt_number=1).first()
        if not result:
            result = EvaluationResult.objects.create(
                enrollment=enrollment, evaluation=evaluation, score=total,
                total_points=total, passed=True, completed_at=timezone.now(),
                time_spent=540, attempt_number=1,
            )
        for question in questions:
            correct = QuestionOption.objects.filter(question=question, is_correct=True).first()
            if correct:
                UserAnswer.objects.get_or_create(evaluation_result=result, question=question, defaults={
                    'selected_option': correct, 'is_correct': True,
                    'points_obtained': question.points,
                })
    Certificate.objects.get_or_create(enrollment=enrollment, defaults={
        'certificate_code': f'ACAREV{enrollment.pk:08d}',
    })


def notify(user, kind, title, message):
    Notification.objects.get_or_create(user=user, title=title, defaults={
        'type': kind, 'message': message,
    })


@transaction.atomic
def run(credentials):
    required = {'estudiante', 'docente', 'admin'}
    if set(credentials) != required or not all(credentials.values()):
        raise ValueError('El archivo debe contener estudiante, docente y admin con sus contraseñas.')
    admin = account('admin', credentials['admin'], 'admin', first_name='Administración', last_name='AcadEMI')
    teacher = account('docente', credentials['docente'], 'teacher',
        first_name='Equipo', last_name='AcadEMI', teacher_full_name='Equipo AcadEMI',
        specialty='Formación aplicada en ingeniería', institution='AcadEMI')
    student = account('estudiante', credentials['estudiante'], 'student',
        first_name='Estudiante', last_name='AcadEMI', full_name='Estudiante AcadEMI',
        city='La Paz', university='Escuela Militar de Ingeniería',
        career='Ingeniería de Sistemas', semester='4')
    background = []
    for username, first, last, career in BACKGROUND:
        person, created = User.objects.get_or_create(username=username, defaults={
            'email': f'{username}@example.invalid', 'first_name': first, 'last_name': last,
            'full_name': f'{first} {last}', 'role': 'student', 'email_verified': True,
            'city': 'La Paz', 'university': 'Escuela Militar de Ingeniería', 'career': career,
        })
        if not created and person.email != f'{username}@example.invalid':
            raise ValueError(f'El usuario {username} ya existe y no es de revisión.')
        if created:
            person.set_unusable_password()
            person.save(update_fields=['password'])
        background.append(person)

    courses = list(Course.objects.filter(status='published').order_by('id'))
    if not courses:
        raise RuntimeError('Primero carga el catálogo de cursos.')
    Course.objects.filter(pk__in=[c.pk for c in courses], teacher__username='equipo_academi').update(teacher=teacher)
    for course in courses:
        if course.title not in VIDEOS:
            continue
        url, source = VIDEOS[course.title]
        video = Lesson.objects.filter(module__course=course, lesson_type='video').order_by('pk').first()
        if video:
            if video.video_url != url:
                video.video_url = url
                video.content = f'Recurso audiovisual de {source}. Consulta el material en su sitio original y relaciona los conceptos con el ejercicio del curso.'
                video.save(update_fields=['video_url', 'content'])
        else:
            module = course.modules.order_by('order').first()
            Lesson.objects.create(module=module, title='Video complementario: fundamentos',
                description=f'Clase de {source}', lesson_type='video', video_url=url,
                content=f'Recurso audiovisual de {source}. Aplica los conceptos al caso práctico del curso.',
                order=2, is_free=True, is_published=True, duration_minutes=30)

    main_courses = courses[:4]
    for index, course in enumerate(main_courses):
        enrollment = enroll(student, course, 1 if index == 0 else 0.4 + index * 0.1, completed=index == 0)
        if index == 0:
            grade_and_certificate(enrollment)
        notify(student, 'course', f'Acceso a {course.title}', f'Ya puedes continuar el curso {course.title}.')
    for course in courses[4:7]:
        Favorite.objects.get_or_create(student=student, course=course)

    for index, course in enumerate(courses):
        person = background[index % len(background)]
        completed = index in (1, 4, 7)
        enrollment = enroll(person, course, 1 if completed else 0.6, completed=completed)
        if completed:
            grade_and_certificate(enrollment)
        if index < 10:
            Review.objects.get_or_create(student=person, course=course, defaults={
                'rating': 5 if index % 3 else 4,
                'comment': 'Los ejercicios y el caso práctico ayudan a aplicar los conceptos de ingeniería.',
            })
    for index, course in enumerate(main_courses[:2]):
        Review.objects.get_or_create(student=student, course=course, defaults={
            'rating': 5, 'comment': 'Contenido claro, con una práctica útil para repasar los fundamentos.',
        })
    lesson = Lesson.objects.filter(module__course=main_courses[0], lesson_type='text').first()
    if lesson:
        Comment.objects.get_or_create(student=student, lesson=lesson,
            content='El ejemplo de tasas de cambio me ayudó a comprobar las unidades del resultado.')
        question, _ = Question.objects.get_or_create(student=student, lesson=lesson,
            content='¿Cómo puedo verificar el resultado de la derivada con un valor numérico?',
            defaults={'is_answered': True})
        Answer.objects.get_or_create(question=question, teacher=teacher, defaults={
            'content': 'Sustituye un valor cercano en la función original y compara el cambio promedio con la derivada en ese punto.',
        })
    pending_lesson = Lesson.objects.filter(module__course=courses[4]).first() if len(courses) > 4 else None
    if pending_lesson:
        Question.objects.get_or_create(student=background[4], lesson=pending_lesson,
            content='¿Qué diferencia práctica hay entre una clave primaria y una clave foránea?')
    notify(teacher, 'question', 'Consulta pendiente de un estudiante',
        'Tienes una pregunta nueva en el contenido de tus cursos.')
    notify(student, 'certificate', 'Tu certificado está disponible',
        f'Completaste {main_courses[0].title}. Ya puedes descargar el certificado.')
    Coupon.objects.get_or_create(code='EMI10', defaults={
        'discount_type': 'percentage', 'discount_value': Decimal('10.00'),
        'max_uses': 100, 'is_active': True,
        'expires_at': timezone.now() + timezone.timedelta(days=180), 'created_by': admin,
    })
    print('Cuentas:', User.objects.filter(username__in=['estudiante', 'docente', 'admin']).count())
    print('Cursos:', Course.objects.filter(status='published').count(), 'videos:', Lesson.objects.filter(lesson_type='video', module__course__status='published').count())
    print('Inscripciones:', Enrollment.objects.count(), 'pedidos:', Payment.objects.count(),
          'evaluaciones realizadas:', EvaluationResult.objects.count(), 'certificados:', Certificate.objects.count())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials-file', type=Path, required=True)
    args = parser.parse_args()
    if args.credentials_file.stat().st_mode & 0o077:
        raise SystemExit('El archivo de credenciales debe tener permisos 600 (chmod 600).')
    run(json.loads(args.credentials_file.read_text()))
