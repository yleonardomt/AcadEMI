#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para llenar la base de datos con datos de prueba
Ejecutar: python3 manage.py shell < seed_data.py
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
    Favorite, Notification, ActivityLog, SystemSetting
)

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
    {'username': 'admin', 'email': 'admin@academi.com', 'password': 'admin123', 
     'role': 'admin', 'full_name': 'Administrador Principal', 'email_verified': True, 'is_active': True},
    {'username': 'admin2', 'email': 'admin2@academi.com', 'password': 'admin123', 
     'role': 'admin', 'full_name': 'Administrador Soporte', 'email_verified': True, 'is_active': True},
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

# Crear estudiantes (20)
students = []
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
            Lesson.objects.create(
                module=module,
                title=f'Lección {j+1}: {random.choice(["Introducción", "Conceptos Básicos", "Ejercicios Prácticos", "Aplicaciones", "Evaluación", "Proyecto"])}',
                description=f'Descripción de la lección {j+1} del módulo {i+1}',
                lesson_type=lesson_type,
                order=j+1,
                is_published=True,
                duration_minutes=random.randint(10, 45),
                is_free=course.is_free
            )

for course in courses:
    num_modules = random.randint(2, 4)
    lessons_per_module = random.randint(3, 5)
    create_lessons_for_course(course, num_modules, lessons_per_module)
    print(f"  ✅ Creados {num_modules} módulos con {lessons_per_module} lecciones para: {course.title[:30]}")

print(f"✅ Total módulos: {Module.objects.count()}")
print(f"✅ Total lecciones: {Lesson.objects.count()}")

# ============================================
# 6. CREAR INSCRIPCIONES
# ============================================
print("\n📋 Creando inscripciones...")

for student in students[:15]:
    # Cada estudiante se inscribe en 2-5 cursos
    num_courses = random.randint(2, 5)
    selected_courses = random.sample(courses, min(num_courses, len(courses)))
    
    for course in selected_courses:
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course=course,
            defaults={
                'status': random.choice(['enrolled', 'in_progress', 'completed']),
                'progress_percentage': random.randint(0, 100),
                'payment_amount': course.price,
                'payment_status': 'paid',
                'payment_method': random.choice(['stripe', 'paypal']),
                'payment_date': timezone.now() - datetime.timedelta(days=random.randint(1, 30)),
            }
        )
        if created:
            print(f"  ✅ Inscripción: {student.username} -> {course.title[:20]}")

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
print(f"✅ Inscripciones: {Enrollment.objects.count()}")
print(f"✅ Reseñas: {Review.objects.count()}")
print(f"✅ Favoritos: {Favorite.objects.count()}")
print(f"✅ Notificaciones: {Notification.objects.count()}")
print(f"✅ Actividades: {ActivityLog.objects.count()}")
print("=" * 70)
print("🎉 ¡BASE DE DATOS LLENADA EXITOSAMENTE!")
print("=" * 70)

# Mostrar algunos ejemplos
print("\n📚 Ejemplos de cursos creados:")
for course in Course.objects.filter(status='published').order_by('-id')[:5]:
    print(f"  • {course.title} - {course.get_level_display()} - ${course.price} - {course.total_lessons} lecciones")