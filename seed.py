#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para llenar la base de datos con datos de prueba
Ejecutar: python3 manage.py shell < seed.py
"""

import os
import sys
import random
import datetime
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

# Importar modelos - CORREGIDO: 'academi' en lugar de 'academics'
from academi.models import (
    Category, Course, Module, Lesson, Enrollment,
    LessonProgress, Comment, Question, Answer, Review,
    Favorite, Notification, ActivityLog, SystemSetting, Certificate,
    Evaluation, QuestionEvaluation, QuestionOption, EvaluationResult,
    UserAnswer, Coupon, Cart, CartItem,
)
from academi.utils import issue_certificate

print("=" * 70)
print("🎯 LLENANDO BASE DE DATOS CON DATOS DE PRUEBA")
print("=" * 70)

# ============================================
# 1. LIMPIAR DATOS EXISTENTES (OPCIONAL)
# ============================================
print("\n🧹 Limpiando datos existentes...")

# Descomenta las líneas que quieras limpiar
# LessonProgress.objects.all().delete()
# Enrollment.objects.all().delete()
# Favorite.objects.all().delete()
# Review.objects.all().delete()
# Answer.objects.all().delete()
# Question.objects.all().delete()
# Comment.objects.all().delete()
# Lesson.objects.all().delete()
# Module.objects.all().delete()
# Course.objects.all().delete()
# Category.objects.all().delete()
# User.objects.exclude(is_superuser=True).delete()
# print("✅ Datos limpiados")

# ============================================
# 2. CREAR USUARIOS
# ============================================
print("\n📝 Creando usuarios...")

# Crear administradores
admin_data = [
    {'username': 'admin', 'email': 'admin@academi.com', 'password': 'admin',
     'role': 'admin', 'full_name': 'Administrador Principal', 'email_verified': True, 'is_active': True,
     'is_staff': True, 'is_superuser': True},
    {'username': 'admin2', 'email': 'admin2@academi.com', 'password': 'admin123',
     'role': 'admin', 'full_name': 'Administrador Soporte', 'email_verified': True, 'is_active': True,
     'is_staff': True, 'is_superuser': True},
]

admins = []
for data in admin_data:
    password = data.pop('password')
    user, created = User.objects.get_or_create(
        username=data['username'],
        defaults=data
    )
    if created:
        user.set_password(password)
        user.save()
    admins.append(user)
    print(f"  ✅ Admin: {user.username}")

# Crear docentes
teacher_data = [
    {'username': 'docente', 'email': 'docente@academi.com', 'password': 'docente',
     'role': 'teacher', 'teacher_full_name': 'Prof. Docente Demo', 'teacher_email': 'docente@academi.com',
     'specialty': 'Demostración general', 'experience_years': '5', 'institution': 'AcadEMI',
     'teacher_bio': 'Cuenta de docente para pruebas: tiene cursos propios, cupones y preguntas respondidas.',
     'email_verified': True, 'is_active': True},

    {'username': 'teacher1', 'email': 'teacher1@academi.com', 'password': 'teacher123',
     'role': 'teacher', 'teacher_full_name': 'Dra. María González', 'teacher_email': 'maria@academi.com',
     'specialty': 'Matemáticas y Física', 'experience_years': '12', 'institution': 'UMSA',
     'teacher_bio': 'Doctora en Matemáticas con 12 años de experiencia', 'email_verified': True, 'is_active': True},
     
    {'username': 'teacher2', 'email': 'teacher2@academi.com', 'password': 'teacher123',
     'role': 'teacher', 'teacher_full_name': 'Ing. Carlos Rodríguez', 'teacher_email': 'carlos@academi.com',
     'specialty': 'Programación y Desarrollo', 'experience_years': '10', 'institution': 'UCB',
     'teacher_bio': 'Ingeniero en Sistemas, especialista en Python y Django', 'email_verified': True, 'is_active': True},
     
    {'username': 'teacher3', 'email': 'teacher3@academi.com', 'password': 'teacher123',
     'role': 'teacher', 'teacher_full_name': 'Lic. Ana Fernández', 'teacher_email': 'ana@academi.com',
     'specialty': 'Diseño UX/UI', 'experience_years': '8', 'institution': 'Escuela de Diseño',
     'teacher_bio': 'Diseñadora UX/UI con experiencia en empresas tecnológicas', 'email_verified': True, 'is_active': True},
     
    {'username': 'teacher4', 'email': 'teacher4@academi.com', 'password': 'teacher123',
     'role': 'teacher', 'teacher_full_name': 'Dr. Pablo Mendoza', 'teacher_email': 'pablo@academi.com',
     'specialty': 'Data Science e IA', 'experience_years': '7', 'institution': 'UPB',
     'teacher_bio': 'Doctor en Ciencias de la Computación, especialista en IA', 'email_verified': True, 'is_active': True},
     
    {'username': 'teacher5', 'email': 'teacher5@academi.com', 'password': 'teacher123',
     'role': 'teacher', 'teacher_full_name': 'Lic. Roberto Quiroga', 'teacher_email': 'roberto@academi.com',
     'specialty': 'Inglés y Traducción', 'experience_years': '15', 'institution': 'Instituto Cultural',
     'teacher_bio': 'Especialista en inglés técnico y traducción', 'email_verified': True, 'is_active': True},
]

teachers = []
for data in teacher_data:
    password = data.pop('password')
    user, created = User.objects.get_or_create(
        username=data['username'],
        defaults=data
    )
    if created:
        user.set_password(password)
        user.save()
    teachers.append(user)
    print(f"  ✅ Docente: {user.username}")

# Crear estudiante de prueba principal (credenciales simples para demo)
students = []
demo_student_data = {
    'username': 'estudiante',
    'email': 'estudiante@academi.com',
    'password': 'estudiante',
    'role': 'student',
    'full_name': 'Estudiante Demo',
    'birth_date': datetime.date(1999, 5, 14),
    'city': 'La Paz',
    'education_level': 'Universitario',
    'university': 'UMSA',
    'career': 'Ingeniería de Sistemas',
    'semester': '6° Semestre',
    'interests': 'Programación, IA',
    'email_verified': True,
    'is_active': True,
}
password = demo_student_data.pop('password')
demo_student, created = User.objects.get_or_create(
    username=demo_student_data['username'],
    defaults=demo_student_data
)
if created:
    demo_student.set_password(password)
    demo_student.save()
students.append(demo_student)
print(f"  ✅ Estudiante demo: {demo_student.username}")

# Crear estudiantes numerados (20 más, para tener volumen de datos)
for i in range(1, 21):
    student_username = f'estudiante{i:02d}'
    student_data = {
        'username': student_username,
        'email': f'{student_username}@academi.com',
        'password': 'student123',
        'role': 'student',
        'full_name': f'Estudiante {i}',
        'birth_date': datetime.date(1998, random.randint(1, 12), random.randint(1, 28)),
        'city': random.choice(['La Paz', 'Cochabamba', 'Santa Cruz', 'El Alto', 'Sucre']),
        'education_level': random.choice(['Universitario', 'Técnico Superior']),
        'university': random.choice(['UMSA', 'UCB', 'UPB', 'USFX', 'UMSS']),
        'career': random.choice(['Ingeniería de Sistemas', 'Administración', 'Psicología', 'Medicina']),
        'semester': f"{random.randint(1, 9)}° Semestre",
        'interests': random.choice(['Programación, IA', 'Marketing, Negocios', 'Diseño, Creatividad']),
        'email_verified': True,
        'is_active': True,
    }
    password = student_data.pop('password')
    user, created = User.objects.get_or_create(
        username=student_data['username'],
        defaults=student_data
    )
    if created:
        user.set_password(password)
        user.save()
    students.append(user)
    print(f"  ✅ Estudiante: {user.username}")

print(f"✅ Total usuarios: {User.objects.count()}")

# ============================================
# 3. CREAR CATEGORÍAS
# ============================================
print("\n📂 Creando categorías...")

categories_data = [
    {'name': 'Programación y Desarrollo', 'description': 'Cursos de programación y desarrollo de software'},
    {'name': 'Data Science e IA', 'description': 'Ciencia de datos, machine learning e inteligencia artificial'},
    {'name': 'Diseño y Creatividad', 'description': 'Diseño gráfico, UX/UI, fotografía y creatividad'},
    {'name': 'Negocios y Finanzas', 'description': 'Administración, marketing, finanzas y emprendimiento'},
    {'name': 'Matemáticas y Ciencias', 'description': 'Cálculo, estadística, física y ciencias exactas'},
    {'name': 'Idiomas y Comunicación', 'description': 'Inglés, español y comunicación efectiva'},
    {'name': 'Salud y Bienestar', 'description': 'Psicología, nutrición y bienestar'},
    {'name': 'Marketing Digital', 'description': 'Marketing online, SEO y redes sociales'},
    {'name': 'Tecnología y Hardware', 'description': 'Redes, ciberseguridad y sistemas'},
]

categories = []
for cat_data in categories_data:
    category, created = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={'description': cat_data['description']}
    )
    categories.append(category)
print(f"  ✅ {len(categories)} categorías creadas")

# ============================================
# 4. CREAR CURSOS (MUCHOS CURSOS)
# ============================================
print("\n📚 Creando 20+ cursos...")

# Lista de cursos con diferentes temáticas
courses_data = []

# Programación
for i in range(5):
    courses_data.append({
        'title': random.choice([
            f'Python Mastery {i+1}',
            f'JavaScript Avanzado {i+1}',
            f'Django Framework {i+1}',
            f'React JS {i+1}',
            f'Desarrollo Web Full Stack {i+1}'
        ]),
        'description': f'Curso completo de programación. Aprende desde fundamentos hasta proyectos profesionales.',
        'category': categories[0],
        'teacher': random.choice(teachers),
        'level': random.choice(['beginner', 'intermediate', 'advanced']),
        'price': Decimal(random.choice(['0.00', '29.99', '49.99', '69.99', '89.99'])),
        'status': random.choice(['published', 'published', 'published', 'draft']),
        'is_free': random.choice([True, False]) if i < 2 else False,
        'is_featured': random.choice([True, False]),
        'published_at': timezone.now() - datetime.timedelta(days=random.randint(1, 60)),
        'approved_at': timezone.now() - datetime.timedelta(days=random.randint(1, 30)),
        'approved_by': admins[0],
    })

# Data Science
for i in range(4):
    courses_data.append({
        'title': random.choice([
            f'Data Science con Python {i+1}',
            f'Machine Learning {i+1}',
            f'SQL y Bases de Datos {i+1}',
            f'Power BI {i+1}'
        ]),
        'description': f'Curso de data science y análisis de datos. Aprende a extraer, procesar y visualizar datos.',
        'category': categories[1],
        'teacher': random.choice(teachers),
        'level': random.choice(['intermediate', 'advanced']),
        'price': Decimal(random.choice(['49.99', '69.99', '89.99', '99.99'])),
        'status': 'published',
        'is_free': False,
        'is_featured': random.choice([True, False]),
        'published_at': timezone.now() - datetime.timedelta(days=random.randint(1, 40)),
        'approved_at': timezone.now() - datetime.timedelta(days=random.randint(1, 20)),
        'approved_by': admins[0],
    })

# Diseño
for i in range(4):
    courses_data.append({
        'title': random.choice([
            f'UX/UI Design {i+1}',
            f'Adobe Photoshop {i+1}',
            f'Diseño Gráfico {i+1}',
            f'Fotografía Digital {i+1}'
        ]),
        'description': f'Curso de diseño y creatividad. Aprende herramientas y técnicas profesionales.',
        'category': categories[2],
        'teacher': random.choice(teachers),
        'level': random.choice(['beginner', 'intermediate']),
        'price': Decimal(random.choice(['0.00', '29.99', '44.99', '59.99'])),
        'status': random.choice(['published', 'published', 'draft']),
        'is_free': random.choice([True, False]) if i < 1 else False,
        'is_featured': random.choice([True, False]),
        'published_at': timezone.now() - datetime.timedelta(days=random.randint(1, 30)),
        'approved_at': timezone.now() - datetime.timedelta(days=random.randint(1, 15)),
        'approved_by': admins[0],
    })

# Negocios
for i in range(3):
    courses_data.append({
        'title': random.choice([
            f'Marketing Digital {i+1}',
            f'Finanzas Personales {i+1}',
            f'Liderazgo y Gestión {i+1}'
        ]),
        'description': f'Curso de negocios y liderazgo. Desarrolla habilidades para el mundo empresarial.',
        'category': categories[3],
        'teacher': random.choice(teachers),
        'level': random.choice(['beginner', 'intermediate']),
        'price': Decimal(random.choice(['29.99', '39.99', '49.99', '59.99'])),
        'status': 'published',
        'is_free': False,
        'is_featured': random.choice([True, False]),
        'published_at': timezone.now() - datetime.timedelta(days=random.randint(1, 25)),
        'approved_at': timezone.now() - datetime.timedelta(days=random.randint(1, 10)),
        'approved_by': admins[0],
    })

# Matemáticas
for i in range(3):
    courses_data.append({
        'title': random.choice([
            f'Cálculo Diferencial {i+1}',
            f'Estadística Aplicada {i+1}',
            f'Álgebra Lineal {i+1}'
        ]),
        'description': f'Curso de matemáticas aplicadas. Conceptos teóricos y aplicaciones prácticas.',
        'category': categories[4],
        'teacher': random.choice(teachers),
        'level': random.choice(['beginner', 'intermediate']),
        'price': Decimal(random.choice(['29.99', '39.99', '49.99'])),
        'status': 'published',
        'is_free': False,
        'is_featured': random.choice([True, False]),
        'published_at': timezone.now() - datetime.timedelta(days=random.randint(1, 20)),
        'approved_at': timezone.now() - datetime.timedelta(days=random.randint(1, 8)),
        'approved_by': admins[0],
    })

# Idiomas
for i in range(3):
    courses_data.append({
        'title': random.choice([
            f'Inglés Técnico {i+1}',
            f'Inglés Conversacional {i+1}',
            f'Español para Extranjeros {i+1}'
        ]),
        'description': f'Curso de idiomas para comunicación efectiva en entornos profesionales.',
        'category': categories[5],
        'teacher': random.choice(teachers),
        'level': random.choice(['beginner', 'intermediate']),
        'price': Decimal(random.choice(['0.00', '29.99', '39.99', '44.99'])),
        'status': random.choice(['published', 'published', 'draft']),
        'is_free': random.choice([True, False]) if i < 1 else False,
        'is_featured': random.choice([True, False]),
        'published_at': timezone.now() - datetime.timedelta(days=random.randint(1, 15)),
        'approved_at': timezone.now() - datetime.timedelta(days=random.randint(1, 7)),
        'approved_by': admins[0],
    })

# Salud
for i in range(2):
    courses_data.append({
        'title': random.choice([
            f'Psicología Clínica {i+1}',
            f'Nutrición y Salud {i+1}'
        ]),
        'description': f'Curso de salud y bienestar. Conocimientos para mejorar la calidad de vida.',
        'category': categories[6],
        'teacher': random.choice(teachers),
        'level': 'beginner',
        'price': Decimal(random.choice(['24.99', '34.99', '44.99'])),
        'status': 'published',
        'is_free': False,
        'is_featured': random.choice([True, False]),
        'published_at': timezone.now() - datetime.timedelta(days=random.randint(1, 10)),
        'approved_at': timezone.now() - datetime.timedelta(days=random.randint(1, 5)),
        'approved_by': admins[0],
    })

# Marketing
for i in range(3):
    courses_data.append({
        'title': random.choice([
            f'SEO Avanzado {i+1}',
            f'Social Media Marketing {i+1}',
            f'Content Marketing {i+1}'
        ]),
        'description': f'Curso de marketing digital. Estrategias para posicionamiento y ventas online.',
        'category': categories[7],
        'teacher': random.choice(teachers),
        'level': random.choice(['intermediate', 'advanced']),
        'price': Decimal(random.choice(['39.99', '49.99', '59.99', '69.99'])),
        'status': 'published',
        'is_free': False,
        'is_featured': random.choice([True, False]),
        'published_at': timezone.now() - datetime.timedelta(days=random.randint(1, 30)),
        'approved_at': timezone.now() - datetime.timedelta(days=random.randint(1, 15)),
        'approved_by': admins[0],
    })

# Tecnología
for i in range(2):
    courses_data.append({
        'title': random.choice([
            f'Ciberseguridad {i+1}',
            f'Redes de Computadoras {i+1}'
        ]),
        'description': f'Curso de tecnología y seguridad informática. Protege sistemas y redes.',
        'category': categories[8],
        'teacher': random.choice(teachers),
        'level': random.choice(['beginner', 'intermediate']),
        'price': Decimal(random.choice(['44.99', '54.99', '74.99'])),
        'status': random.choice(['published', 'published', 'draft']),
        'is_free': False,
        'is_featured': random.choice([True, False]),
        'published_at': timezone.now() - datetime.timedelta(days=random.randint(1, 20)),
        'approved_at': timezone.now() - datetime.timedelta(days=random.randint(1, 10)),
        'approved_by': admins[0],
    })

# El primer docente ('docente'/'docente') es la cuenta de prueba principal:
# le forzamos la autoría de un par de cursos (uno gratis, uno de pago) en
# categorías distintas, publicados y destacados, para que siempre tenga
# contenido propio listo para gestionar (cupones, preguntas, estudiantes).
docente_user = teachers[0]
courses_data[0]['teacher'] = docente_user
courses_data[0]['status'] = 'published'
courses_data[0]['is_featured'] = True
courses_data[0]['is_free'] = False
courses_data[0]['price'] = Decimal('49.99')

courses_data[5]['teacher'] = docente_user
courses_data[5]['status'] = 'published'
courses_data[5]['is_featured'] = True
courses_data[5]['is_free'] = True
courses_data[5]['price'] = Decimal('0.00')

# Guardar cursos
courses = []
for course_data in courses_data:
    course, created = Course.objects.get_or_create(
        title=course_data['title'],
        defaults=course_data
    )
    courses.append(course)
    if created:
        print(f"  ✅ Curso creado: {course.title}")
    else:
        print(f"  ⏭️ Curso ya existe: {course.title}")

print(f"✅ Total cursos: {len(courses)}")

# ============================================
# 5. CREAR MÓDULOS Y LECCIONES
# ============================================
print("\n📖 Creando módulos y lecciones...")

def create_evaluation_for_lesson(lesson, num_questions=5):
    """RF-44 al RF-46: toda lección de tipo quiz/examen necesita una
    Evaluation con preguntas y opciones reales, o el estudiante nunca
    podrá rendirla (ver academi/decorators/quiz_decorators.py)."""
    evaluation = Evaluation.objects.create(
        lesson=lesson,
        title=f'{lesson.get_lesson_type_display()}: {lesson.title}',
        description=lesson.description,
        evaluation_type=lesson.lesson_type,
        time_limit_minutes=60 if lesson.lesson_type == 'exam' else 30,
        passing_score=70,
        max_attempts=1 if lesson.lesson_type == 'exam' else 3,
        is_active=True,
    )
    for q in range(1, num_questions + 1):
        question = QuestionEvaluation.objects.create(
            evaluation=evaluation,
            question_type='single',
            text=f'Pregunta {q} sobre {lesson.title}',
            points=1,
            order=q,
        )
        correct_index = random.randint(0, 3)
        for i, letter in enumerate('ABCD'):
            QuestionOption.objects.create(
                question=question,
                text=f'Opción {letter}',
                is_correct=(i == correct_index),
            )
    return evaluation


def create_lessons_for_course(course, num_modules=2, lessons_per_module=3):
    """Crea módulos y lecciones para un curso"""
    for i in range(num_modules):
        module = Module.objects.create(
            course=course,
            title=f'Módulo {i+1}: {course.title[:30]}',
            description=f'Contenido del módulo {i+1} del curso {course.title}',
            order=i+1
        )

        for j in range(lessons_per_module):
            lesson_type = random.choice(['video', 'video', 'video', 'quiz', 'exam', 'assignment'])
            lesson = Lesson.objects.create(
                module=module,
                title=f'Lección {j+1}: {random.choice(["Introducción", "Conceptos Básicos", "Ejercicios Prácticos", "Aplicaciones", "Evaluación", "Proyecto"])}',
                description=f'Descripción de la lección {j+1} del módulo {i+1}',
                lesson_type=lesson_type,
                order=j+1,
                is_published=True,
                duration_minutes=random.randint(10, 45),
                is_free=course.is_free
            )
            if lesson_type in ('quiz', 'exam'):
                create_evaluation_for_lesson(lesson)

for course in courses:
    num_modules = random.randint(2, 4)
    lessons_per_module = random.randint(3, 5)
    create_lessons_for_course(course, num_modules, lessons_per_module)
    print(f"  ✅ Creados {num_modules} módulos con {lessons_per_module} lecciones para: {course.title[:30]}")

print(f"✅ Total módulos: {Module.objects.count()}")
print(f"✅ Total lecciones: {Lesson.objects.count()}")

# ============================================
# 5.5 DATOS DE LA CUENTA DEMO (estudiante <-> docente)
# ============================================
# Todo lo que necesitás para probar la plataforma de punta a punta con
# las credenciales simples (admin/admin, docente/docente,
# estudiante/estudiante) sin tener que navegar generando datos a mano:
# un curso completado con certificado, uno en progreso, una pregunta ya
# respondida por el docente, cupones activos e inactivos, un favorito y
# un curso en el carrito.
print("\n🎬 Creando escenario de demostración (estudiante <-> docente)...")

docente_courses = list(Course.objects.filter(teacher=docente_user).order_by('id'))
course_completed = docente_courses[0] if len(docente_courses) > 0 else None
course_in_progress = docente_courses[1] if len(docente_courses) > 1 else None
other_courses = [c for c in courses if c not in docente_courses]

if course_completed:
    enrollment_a, _ = Enrollment.objects.get_or_create(
        student=demo_student,
        course=course_completed,
        defaults={
            'status': 'completed',
            'progress_percentage': 100,
            'payment_amount': course_completed.price,
            'payment_status': 'paid',
            'payment_method': 'stripe',
            'payment_date': timezone.now() - datetime.timedelta(days=20),
            'completed_date': timezone.now() - datetime.timedelta(days=2),
        }
    )
    for lesson in Lesson.objects.filter(module__course=course_completed):
        LessonProgress.objects.get_or_create(
            enrollment=enrollment_a, lesson=lesson,
            defaults={'completed': True, 'completed_at': timezone.now() - datetime.timedelta(days=3)}
        )
    certificate, _ = issue_certificate(enrollment_a)
    print(f"  🎓 Certificado demo: {demo_student.username} -> {course_completed.title}")

    Review.objects.get_or_create(
        student=demo_student, course=course_completed,
        defaults={'rating': 5, 'comment': 'Excelente curso, el docente responde rápido a las preguntas.'}
    )

    # RF-37/RF-38: pregunta del estudiante ya respondida por el docente,
    # para que "hablar con el docente" se vea funcionando desde el inicio.
    demo_lesson = Lesson.objects.filter(module__course=course_completed).order_by('module__order', 'order').first()
    if demo_lesson:
        question, q_created = Question.objects.get_or_create(
            lesson=demo_lesson, student=demo_student,
            defaults={'content': '¿Este contenido sirve para principiantes o necesito experiencia previa?', 'is_answered': True}
        )
        if q_created:
            Answer.objects.create(
                question=question, teacher=docente_user,
                content='¡Hola! Sí, está pensado para principiantes, cada lección parte desde cero.'
            )

    # RF-60: cupones del docente sobre su propio curso — uno activo por
    # tiempo/cupo limitado ("primeros 10"), y uno vencido/inactivo, para
    # ver ambos estados en "Mis cupones".
    Coupon.objects.get_or_create(
        code='BIENVENIDA10', course=course_completed,
        defaults={
            'discount_type': 'percentage', 'discount_value': Decimal('20.00'),
            'max_uses': 10, 'used_count': 3, 'is_active': True,
            'expires_at': timezone.now() + datetime.timedelta(days=30),
            'created_by': docente_user,
        }
    )
    Coupon.objects.get_or_create(
        code='PROMOVENCIDA', course=course_completed,
        defaults={
            'discount_type': 'fixed', 'discount_value': Decimal('10.00'),
            'max_uses': 5, 'used_count': 5, 'is_active': False,
            'expires_at': timezone.now() - datetime.timedelta(days=5),
            'created_by': docente_user,
        }
    )

    # RF-50/51: intento de evaluación ya rendido, para que "Mis
    # calificaciones" tenga contenido real desde el primer login.
    demo_evaluation = Evaluation.objects.filter(lesson__module__course=course_completed).first()
    if demo_evaluation:
        questions = list(demo_evaluation.questions.all())
        total_points = sum(q.points for q in questions) or len(questions)
        result, r_created = EvaluationResult.objects.get_or_create(
            enrollment=enrollment_a, evaluation=demo_evaluation, attempt_number=1,
            defaults={
                'score': max(1, round(total_points * 0.8)),
                'total_points': total_points,
                'passed': True,
                'completed_at': timezone.now() - datetime.timedelta(days=2),
                'time_spent': 480,
            }
        )
        if r_created:
            for q in questions:
                correct_option = q.options.filter(is_correct=True).first()
                UserAnswer.objects.create(
                    evaluation_result=result, question=q,
                    selected_option=correct_option,
                    is_correct=bool(correct_option),
                    points_obtained=q.points if correct_option else 0,
                )
            print(f"  📝 Evaluación demo respondida: {demo_student.username} -> {demo_evaluation.title}")

if course_in_progress:
    Enrollment.objects.get_or_create(
        student=demo_student,
        course=course_in_progress,
        defaults={
            'status': 'in_progress',
            'progress_percentage': 45,
            'payment_amount': course_in_progress.price,
            'payment_status': 'paid',
            'payment_method': 'paypal',
            'payment_date': timezone.now() - datetime.timedelta(days=5),
        }
    )
    print(f"  📖 Curso en progreso demo: {demo_student.username} -> {course_in_progress.title}")

if len(other_courses) >= 2:
    Favorite.objects.get_or_create(student=demo_student, course=other_courses[0])
    cart, _ = Cart.objects.get_or_create(student=demo_student)
    CartItem.objects.get_or_create(cart=cart, course=other_courses[1])
    print(f"  🛒 Favorito y carrito demo listos para {demo_student.username}")

# ============================================
# 6. CREAR INSCRIPCIONES
# ============================================
print("\n📋 Creando inscripciones...")

for student in students[:15]:
    # Cada estudiante se inscribe en 2-5 cursos
    num_courses = random.randint(2, 5)
    selected_courses = random.sample(courses, min(num_courses, len(courses)))
    
    for course in selected_courses:
        status = random.choice(['enrolled', 'in_progress', 'completed'])
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course=course,
            defaults={
                'status': status,
                'progress_percentage': 100 if status == 'completed' else random.randint(0, 90),
                'payment_amount': course.price,
                'payment_status': 'paid',
                'payment_method': random.choice(['stripe', 'paypal']),
                'payment_date': timezone.now() - datetime.timedelta(days=random.randint(1, 30)),
                'completed_date': timezone.now() if status == 'completed' else None,
            }
        )
        if created:
            print(f"  ✅ Inscripción: {student.username} -> {course.title[:20]}")

        if enrollment.status == 'completed':
            # RF-10, RF-34: el progreso registrado debe respaldar el estado 'completed'.
            lessons = Lesson.objects.filter(module__course=course)
            for lesson in lessons:
                LessonProgress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=lesson,
                    defaults={'completed': True, 'completed_at': timezone.now()}
                )
            # RF-64: todo curso completado debe emitir su certificado.
            certificate, cert_created = issue_certificate(enrollment)
            if cert_created:
                print(f"  🎓 Certificado emitido: {student.username} -> {course.title[:20]}")

print(f"✅ Total inscripciones: {Enrollment.objects.count()}")

# ============================================
# 7. CREAR RESEÑAS
# ============================================
print("\n⭐ Creando reseñas...")

for enrollment in Enrollment.objects.all():
    if random.choice([True, False]) and enrollment.status == 'completed':
        Review.objects.get_or_create(
            student=enrollment.student,
            course=enrollment.course,
            defaults={
                'rating': random.randint(3, 5),
                'comment': random.choice([
                    'Excelente curso, muy recomendado',
                    'Buen contenido, aprendí mucho',
                    'El profesor explica muy bien',
                    'El material es muy completo',
                    'Me encantó el curso',
                    'Muy práctico y útil'
                ])
            }
        )

print(f"✅ Total reseñas: {Review.objects.count()}")

# ============================================
# 8. CREAR NOTIFICACIONES
# ============================================
print("\n🔔 Creando notificaciones...")

for user in User.objects.all()[:10]:
    for i in range(random.randint(1, 3)):
        Notification.objects.create(
            user=user,
            type=random.choice(['course', 'evaluation', 'purchase', 'certificate', 'system']),
            title=random.choice(['Nuevo curso disponible', 'Evaluación lista', 'Compra exitosa', 'Certificado generado']),
            message=f'Mensaje de prueba para {user.username} - Notificación {i+1}',
            is_read=random.choice([True, False])
        )

print(f"✅ Total notificaciones: {Notification.objects.count()}")

# ============================================
# 9. CREAR ACTIVIDADES
# ============================================
print("\n📝 Creando actividades...")

for user in User.objects.all()[:10]:
    for i in range(random.randint(1, 3)):
        ActivityLog.objects.create(
            user=user,
            action_type=random.choice(['login', 'course_create', 'enrollment', 'payment', 'profile_update']),
            description=f'Actividad de prueba {i+1} para {user.username}',
            ip_address=f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

print(f"✅ Total actividades: {ActivityLog.objects.count()}")

# ============================================
# 10. CREAR FAVORITOS
# ============================================
print("\n⭐ Creando favoritos...")

for student in students[:10]:
    # Cada estudiante tiene 2-4 favoritos
    num_favorites = random.randint(2, 4)
    selected_courses = random.sample(courses, min(num_favorites, len(courses)))
    
    for course in selected_courses:
        Favorite.objects.get_or_create(
            student=student,
            course=course
        )

print(f"✅ Total favoritos: {Favorite.objects.count()}")

# ============================================
# RESUMEN FINAL
# ============================================
print("\n" + "=" * 70)
print("📊 RESUMEN FINAL DE DATOS CREADOS")
print("=" * 70)
print(f"✅ Usuarios: {User.objects.count()}")
print(f"   - Administradores: {User.objects.filter(role='admin').count()}")
print(f"   - Docentes: {User.objects.filter(role='teacher').count()}")
print(f"   - Estudiantes: {User.objects.filter(role='student').count()}")
print(f"✅ Categorías: {Category.objects.count()}")
print(f"✅ Cursos: {Course.objects.count()}")
print(f"   - Publicados: {Course.objects.filter(status='published').count()}")
print(f"   - Borradores: {Course.objects.filter(status='draft').count()}")
print(f"   - Gratuitos: {Course.objects.filter(is_free=True).count()}")
print(f"✅ Módulos: {Module.objects.count()}")
print(f"✅ Lecciones: {Lesson.objects.count()}")
print(f"✅ Evaluaciones: {Evaluation.objects.count()}")
print(f"✅ Inscripciones: {Enrollment.objects.count()}")
print(f"✅ Certificados: {Certificate.objects.count()}")
print(f"✅ Reseñas: {Review.objects.count()}")
print(f"✅ Favoritos: {Favorite.objects.count()}")
print(f"✅ Notificaciones: {Notification.objects.count()}")
print(f"✅ Actividades: {ActivityLog.objects.count()}")
print(f"✅ Cupones: {Coupon.objects.count()}")
print(f"✅ Preguntas al docente: {Question.objects.count()} ({Answer.objects.count()} respondidas)")
print(f"✅ Intentos de evaluación: {EvaluationResult.objects.count()}")
print("=" * 70)
print("🎉 ¡BASE DE DATOS LLENADA EXITOSAMENTE!")
print("=" * 70)

print("\n🔑 CREDENCIALES DE PRUEBA")
print("-" * 70)
print("  Administrador  ->  usuario: admin       contraseña: admin")
print("  Docente        ->  usuario: docente     contraseña: docente")
print("  Estudiante     ->  usuario: estudiante  contraseña: estudiante")
print("-" * 70)
print("  Otros usuarios de ejemplo (misma contraseña dentro de cada grupo):")
print("    Admins:      admin2                        / admin123")
print("    Docentes:    teacher1 .. teacher5           / teacher123")
print("    Estudiantes: estudiante01 .. estudiante20   / student123")
print("=" * 70)

# Mostrar algunos ejemplos
print("\n📚 Ejemplos de cursos creados:")
for course in Course.objects.filter(status='published').order_by('-id')[:5]:
    print(f"  • {course.title} - {course.get_level_display()} - ${course.price} - {course.total_lessons} lecciones")