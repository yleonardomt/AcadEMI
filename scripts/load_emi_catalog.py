#!/usr/bin/env python3
"""Carga idempotente del catálogo de ingeniería orientado a la EMI La Paz.

Uso: .venv/bin/python scripts/load_emi_catalog.py [--archive-legacy] [--no-images]
No elimina cursos, matrículas, pagos ni respuestas existentes.
"""

import argparse
import html
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django  # noqa: E402

django.setup()

import requests  # noqa: E402
from django.conf import settings  # noqa: E402
from django.db import transaction  # noqa: E402
from django.core.files import File  # noqa: E402
from django.core.files.storage import default_storage  # noqa: E402
from django.utils import timezone  # noqa: E402
from academi.models import (  # noqa: E402
    Category, Course, Evaluation, Lesson, Module, QuestionEvaluation,
    QuestionOption, User,
)


# La oferta de carreras de la Unidad Académica La Paz se verificó en:
# https://emi.edu.bo/index.php/universidad/unidades-academicas/lapaz
# AcadEMI es una plataforma independiente: estos cursos no se anuncian como
# asignaturas oficiales ni se atribuyen a docentes de la EMI.
COURSES = [
    dict(title='Cálculo diferencial para ingeniería', area='Ciencias básicas', level='beginner', price=0,
         topic='derivadas, tasas de cambio y optimización', example='Determina la velocidad instantánea de un móvil con s(t)=3t²+2t en t=4 s.',
         answer='26 m/s', video='https://www.youtube.com/watch?v=7K1sB05pE0A', image='mathematics calculus blackboard',
         questions=[('La derivada de x² es', '2x', ['x', 'x²', '2']), ('Si s(t)=3t², la velocidad en t=2 es', '12', ['6', '9', '24']), ('Una derivada positiva indica que la función', 'crece localmente', ['decrece localmente', 'es constante', 'no es continua'])]),
    dict(title='Python aplicado a problemas de ingeniería', area='Ingeniería de Sistemas', level='beginner', price=0,
         topic='variables, estructuras de control y cálculo reproducible', example='Programa una función que calcule el promedio de 20 mediciones y alerte si supera 50.',
         answer='El promedio es suma de mediciones / 20; compara el resultado con 50.', video='https://www.youtube.com/watch?v=nykOeWgQcHM', image='computer programming code screen',
         questions=[('¿Qué estructura almacena una secuencia mutable en Python?', 'list', ['tuple', 'str', 'int']), ('¿Cuál es el promedio de 4, 6 y 8?', '6', ['5', '7', '18']), ('¿Qué instrucción repite una operación sobre una lista?', 'for', ['if', 'return', 'import'])]),
    dict(title='Álgebra lineal y matrices', area='Ciencias básicas', level='beginner', price=0,
         topic='vectores, matrices y sistemas lineales', example='Resuelve el sistema x+y=5; x−y=1 y comprueba ambos resultados.',
         answer='x=3, y=2.', video='https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/', image='File:Mathematics lecture at the Helsinki University of Technology.jpg',
         questions=[('¿Cuál es la solución de x+y=5; x−y=1?', 'x=3, y=2', ['x=2, y=3', 'x=4, y=1', 'x=5, y=0']), ('La matriz identidad 2×2 tiene diagonal', '1, 1', ['0, 0', '2, 2', '1, 0']), ('Un vector en R³ tiene', '3 componentes', ['2 componentes', '4 componentes', '1 componente'])]),
    dict(title='Mecánica de estructuras y cargas', area='Ingeniería Civil', level='intermediate', price=69,
         topic='equilibrio estático, diagramas de cuerpo libre y cargas', example='Calcula las reacciones verticales de una viga simplemente apoyada de 6 m con carga puntual de 12 kN en el centro.',
         answer='6 kN en cada apoyo.', video='https://edtech.engineering.utoronto.ca/project-catalog/mechanics/beams/', image='File:Construction of Pampanga Delta Bridge & Approaches 06.jpg',
         questions=[('Una viga simplemente apoyada con carga centrada P reparte en cada apoyo', 'P/2', ['P', '2P', '0']), ('La unidad SI de fuerza es', 'newton', ['pascal', 'metro', 'vatio']), ('En equilibrio estático, la suma de fuerzas es', 'cero', ['uno', 'máxima', 'negativa siempre'])]),
    dict(title='Bases de datos y SQL para proyectos', area='Ingeniería de Sistemas', level='intermediate', price=59,
         topic='modelado relacional, consultas y calidad de datos', example='Diseña tablas Sensor(id, zona) y Lectura(id, sensor_id, valor) y consulta el promedio por zona.',
         answer='JOIN por sensor_id, GROUP BY zona y AVG(valor).', video='https://www.youtube.com/watch?v=WXk7yDqsKxs', image='File:Datacenter Server Racks (22370909788).jpg',
         questions=[('¿Qué cláusula agrupa filas para calcular AVG?', 'GROUP BY', ['ORDER BY', 'LIMIT', 'INSERT']), ('Una clave foránea referencia', 'una clave de otra tabla', ['solo texto libre', 'un índice de archivo', 'una vista']), ('¿Qué función SQL calcula el promedio?', 'AVG', ['SUM', 'COUNT', 'MAX'])]),
    dict(title='Procesos y mejora continua', area='Ingeniería Industrial', level='intermediate', price=59,
         topic='diagramas de proceso, capacidad y mejora continua', example='Una línea produce 240 piezas en 8 h. Calcula su tasa horaria y plantea un indicador de defectos.',
         answer='30 piezas/h; tasa de defectos = piezas defectuosas / total × 100.', video='', image='File:Industrial production line operating in a large modern factory.jpg',
         questions=[('240 piezas en 8 horas equivalen a', '30 piezas/h', ['20 piezas/h', '40 piezas/h', '80 piezas/h']), ('Un cuello de botella es', 'la etapa con menor capacidad', ['la etapa más cara', 'el último proceso', 'el almacén']), ('El ciclo PHVA termina con', 'Actuar', ['Planear', 'Hacer', 'Verificar'])]),
    dict(title='Circuitos eléctricos fundamentales', area='Ingeniería en Sistemas Electrónicos', level='beginner', price=49,
         topic='ley de Ohm, potencia y circuitos serie-paralelo', example='Para una resistencia de 10 Ω conectada a 20 V, calcula corriente y potencia.',
         answer='I=2 A; P=40 W.', video='https://www.youtube.com/watch?v=gWZi71JkPAA', image='electronics circuit board engineering',
         questions=[('Con V=20 V y R=10 Ω, la corriente es', '2 A', ['0,5 A', '10 A', '200 A']), ('La potencia eléctrica se calcula con', 'P=VI', ['P=V/I', 'P=R/V', 'P=I/V']), ('En serie, la corriente por dos resistencias es', 'la misma', ['siempre cero', 'doble en la segunda', 'independiente'])]),
    dict(title='Control y sensores para mecatrónica', area='Ingeniería Mecatrónica', level='intermediate', price=79,
         topic='sensores, actuadores y control en lazo cerrado', example='Diseña un control de temperatura: define sensor, consigna, actuador y regla para encender un ventilador.',
         answer='Sensor de temperatura; consigna 30 °C; ventilador se activa al superar la consigna y se desactiva al bajar con histéresis.', video='https://www.youtube.com/watch?v=KJnAy6hzetw', image='robot industrial automation factory',
         questions=[('La realimentación usa', 'la salida medida', ['solo el reloj', 'un valor aleatorio', 'la potencia nominal']), ('¿Qué convierte una orden eléctrica en movimiento?', 'actuador', ['sensor', 'resistencia', 'transductor pasivo']), ('Una consigna es', 'el valor deseado', ['el error medido', 'el ruido', 'la frecuencia de muestreo'])]),
    dict(title='Señales y telecomunicaciones', area='Ingeniería en Telecomunicaciones', level='intermediate', price=69,
         topic='señales periódicas, muestreo y transmisión', example='Una señal de 1 kHz se muestrea a 3 kHz. Explica si cumple Nyquist y calcula el período de muestreo.',
         answer='Sí, 3 kHz > 2 kHz; período ≈0,333 ms.', video='https://www.youtube.com/watch?v=KJnAy6hzetw', image='telecommunications antenna tower technology',
         questions=[('La frecuencia mínima de muestreo para 1 kHz es', 'más de 2 kHz', ['menos de 1 kHz', '1 kHz exacto', '500 Hz']), ('El período de una señal de 1 kHz es', '1 ms', ['1 s', '10 ms', '0,1 s']), ('El ruido en un canal puede', 'degradar la señal', ['crear ancho de banda', 'eliminar atenuación', 'garantizar exactitud'])]),
    dict(title='Hidrología y gestión del agua', area='Ingeniería Ambiental', level='intermediate', price=59,
         topic='balance hídrico, escorrentía y calidad de agua', example='En una cuenca entran 100 mm de lluvia; 35 mm infiltran y 20 mm evapotranspiran. Estima la escorrentía.',
         answer='45 mm, si se desprecia la variación de almacenamiento.', video='https://www.youtube.com/watch?v=XHeoQ0F6hYc', image='File:River landscape scenics aerial photography.jpg',
         questions=[('Lluvia 100 mm, infiltración 35 mm y evapotranspiración 20 mm: escorrentía', '45 mm', ['35 mm', '55 mm', '80 mm']), ('El caudal se expresa habitualmente en', 'm³/s', ['m²/s', 'kg/m', 'Pa']), ('La turbidez es un indicador de', 'partículas suspendidas', ['solo temperatura', 'salinidad exacta', 'presión'])]),
    dict(title='Cartografía digital y SIG', area='Ingeniería Geográfica', level='beginner', price=49,
         topic='coordenadas, capas espaciales y análisis territorial', example='Crea un mapa de zonas de riesgo combinando una capa de pendientes y otra de cursos de agua; indica la proyección usada.',
         answer='Definir SRC, superponer capas y justificar umbrales de pendiente y distancia a cauces.', video='', image='geographic map satellite earth',
         questions=[('En un SIG, una capa vectorial puede representar', 'puntos, líneas y polígonos', ['solo píxeles', 'únicamente tablas', 'solamente sonido']), ('El SRC define', 'cómo se expresan las coordenadas', ['la resolución de pantalla', 'el color del mapa', 'el peso del archivo']), ('Una escala 1:50 000 significa que 1 cm representa', '500 m', ['50 m', '5 km', '50 km'])]),
    dict(title='Fundamentos de ingeniería petrolera', area='Ingeniería Petrolera', level='beginner', price=69,
         topic='porosidad, permeabilidad y balance de fluidos', example='Una muestra de roca tiene 25 cm³ de poros en 100 cm³ de volumen total. Calcula la porosidad.',
         answer='25 %.', video='https://www.youtube.com/watch?v=XHeoQ0F6hYc', image='File:Oil platform P-51 (Brazil).jpg',
         questions=[('25 cm³ de poros en 100 cm³ de roca dan porosidad de', '25 %', ['4 %', '40 %', '75 %']), ('La permeabilidad describe', 'facilidad de flujo en la roca', ['volumen total', 'densidad del crudo', 'temperatura']), ('La presión suele medirse en', 'Pa', ['kg', 'm³', 'W'])]),
    dict(title='Matemática financiera aplicada', area='Ingeniería Financiera', level='beginner', price=49,
         topic='interés compuesto, valor presente y evaluación de proyectos', example='Invierte Bs 1.000 al 10 % anual compuesto durante dos años. Calcula el valor futuro.',
         answer='Bs 1.210.', video='', image='File:Calculator-385506 1280.jpg',
         questions=[('Bs 1000 al 10 % compuesto por 2 años valen', 'Bs 1210', ['Bs 1100', 'Bs 1200', 'Bs 1002']), ('El valor presente descuenta', 'flujos futuros', ['solo costos históricos', 'el número de clientes', 'la inflación a cero']), ('Un VAN positivo, bajo supuestos correctos, indica', 'valor añadido', ['pérdida segura', 'tasa cero', 'ausencia de riesgo'])]),
    dict(title='Análisis de mercados y costos', area='Ingeniería Comercial', level='beginner', price=49,
         topic='segmentación, costos y punto de equilibrio', example='Con costo fijo Bs 1.000, precio Bs 20 y costo variable Bs 10 por unidad, calcula el punto de equilibrio.',
         answer='100 unidades.', video='', image='File:Business breakfast meeting. (54641476579).jpg',
         questions=[('CF=1000, P=20 y CV=10: equilibrio en unidades', '100', ['50', '200', '1000']), ('El margen de contribución unitario es', 'precio menos costo variable', ['precio más costo fijo', 'ingreso total', 'costo fijo / precio']), ('Segmentar mercado consiste en', 'agrupar clientes con características comunes', ['fijar un precio único', 'eliminar competencia', 'aumentar inventario'])]),
]


def download_image(query, slug):
    """Usa miniaturas Wikimedia con licencia explícita y guarda atribución."""
    target = Path(settings.MEDIA_ROOT) / 'courses' / f'emi-{slug}.jpg'
    if target.exists() and target.stat().st_size > 5000:
        return f'courses/{target.name}', None
    api = 'https://commons.wikimedia.org/w/api.php'
    params = {'action': 'query', 'prop': 'imageinfo',
              'iiprop': 'url|size|extmetadata', 'iiurlwidth': 1100, 'format': 'json'}
    if query.startswith('File:'):
        params['titles'] = query
    else:
        params.update({'generator': 'search', 'gsrsearch': query + ' filetype:bitmap',
                       'gsrnamespace': 6, 'gsrlimit': 12})
    headers = {'User-Agent': 'AcadEMI-Catalog/1.0 (educational catalog; info@academi.bo)'}
    data = requests.get(api, params=params, headers=headers, timeout=20).json()
    pages = sorted(data.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
    for page in pages:
        if not page['title'].lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            continue
        info = page.get('imageinfo', [{}])[0]
        meta = info.get('extmetadata', {})
        license_name = html.unescape(re.sub('<[^>]+>', '', meta.get('LicenseShortName', {}).get('value', '')))
        if not (license_name.startswith('CC BY') or license_name in {'CC0', 'Public domain'}):
            continue
        if info.get('width', 0) < 700 or info.get('height', 0) < 400 or info.get('width', 0) < info.get('height', 0) * 1.15:
            continue
        url = info.get('thumburl')
        if not url:
            continue
        try:
            response = requests.get(url, headers=headers, timeout=25)
            response.raise_for_status()
            if not response.headers.get('content-type', '').startswith('image/') or len(response.content) < 5000:
                continue
            from PIL import Image
            from io import BytesIO
            image = Image.open(BytesIO(response.content)).convert('RGB')
            image.thumbnail((1100, 750))
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target, 'JPEG', quality=84, optimize=True)
            author = ' '.join(html.unescape(re.sub('<[^>]+>', '', meta.get('Artist', {}).get('value', 'Autor no indicado'))).split())
            source = info.get('descriptionurl', '')
            return f'courses/{target.name}', f'{target.name} | {page["title"]} | {author} | {license_name} | {source}'
        except (requests.RequestException, OSError):
            continue
    return None, None


def upsert_lesson(module, order, title, kind, content='', video='', is_free=False, duration=15):
    lesson, _ = Lesson.objects.update_or_create(module=module, title=title, defaults={
        'order': order, 'lesson_type': kind, 'content': content, 'description': content[:180],
        'video_url': video or None, 'is_free': is_free, 'is_published': True,
        'duration_minutes': duration,
    })
    return lesson


def run(archive_legacy=False, no_images=False, only_if_empty=False):
    existing_titles = set()
    if only_if_empty:
        existing_titles = set(Course.objects.filter(
            title__in=[item['title'] for item in COURSES],
        ).values_list('title', flat=True))
        if len(existing_titles) == len(COURSES):
            print('El catálogo inicial ya está completo; no se modifica.')
            return
    teacher, _ = User.objects.get_or_create(username='equipo_academi', defaults={
        'email': 'equipo@academi.local', 'first_name': 'Equipo', 'last_name': 'AcadEMI',
        'role': 'teacher', 'is_active': True, 'email_verified': True,
        'teacher_full_name': 'Equipo AcadEMI', 'specialty': 'Material académico de ingeniería',
        'institution': 'AcadEMI',
    })
    if not teacher.has_usable_password():
        pass
    else:
        teacher.set_unusable_password()
        teacher.save(update_fields=['password'])
    archive_titles = {item['title'] for item in COURSES}
    if archive_legacy:
        changed = Course.objects.filter(status='published').exclude(title__in=archive_titles).update(status='archived', is_featured=False)
        print(f'Cursos anteriores archivados: {changed}')
    attribution = []
    for index, item in enumerate(COURSES):
        if item['title'] in existing_titles:
            continue
        area, _ = Category.objects.get_or_create(name=item['area'], defaults={
            'description': f'Cursos aplicados a {item["area"].lower()} para estudiantes de ingeniería.'})
        slug = re.sub(r'[^a-z0-9]+', '-', item['title'].lower().translate(str.maketrans('áéíóúñ', 'aeioun'))).strip('-')
        image_path = None
        bundled_image = ROOT / 'media' / 'courses' / f'emi-{slug}.jpg'
        if bundled_image.is_file():
            image_path = f'courses/{bundled_image.name}'
            if settings.STORAGES['default']['BACKEND'] != 'django.core.files.storage.FileSystemStorage':
                if not default_storage.exists(image_path):
                    with bundled_image.open('rb') as source:
                        default_storage.save(image_path, File(source))
        elif not no_images:
            try:
                image_path, credit = download_image(item['image'], slug)
                if credit:
                    attribution.append(credit)
            except (requests.RequestException, ValueError) as exc:
                print(f'Imagen pendiente para {item["title"]}: {exc}')
        with transaction.atomic():
            defaults = {'description': (
                f'Aprende {item["topic"]} con casos de ingeniería, ejercicios resueltos y una evaluación final. '
                'Incluye un proyecto práctico con criterios de entrega y retroalimentación en la plataforma.'),
                'category': area, 'teacher': teacher, 'level': item['level'], 'price': item['price'],
                'is_free': item['price'] == 0, 'is_featured': index < 6, 'status': 'published',
                'published_at': timezone.now(), 'approved_at': timezone.now(), 'approved_by': User.objects.filter(is_superuser=True).first(),
            }
            if image_path:
                defaults['image'] = image_path
            course, _ = Course.objects.update_or_create(title=item['title'], teacher=teacher, defaults=defaults)
            intro, _ = Module.objects.update_or_create(course=course, title='Fundamentos', defaults={
                'order': 1, 'description': f'Conceptos básicos de {item["topic"]}.'})
            applied, _ = Module.objects.update_or_create(course=course, title='Aplicación y evaluación', defaults={
                'order': 2, 'description': 'Resuelve un caso aplicado y comprueba lo aprendido.'})
            upsert_lesson(intro, 1, 'Guía de aprendizaje', 'text',
                f'Objetivo: comprender {item["topic"]}.\n\nAntes de comenzar, identifica las unidades de cada variable y anota los supuestos de tu modelo. '
                'Después de cada ejercicio, verifica el resultado sustituyéndolo en el planteamiento original.\n\n'
                f'Caso de referencia: {item["example"]}\nResultado esperado: {item["answer"]}', is_free=True, duration=20)
            if item['video']:
                upsert_lesson(intro, 2, 'Video complementario: fundamentos', 'video',
                    'Material audiovisual de fuente abierta. Revisa la fuente original enlazada y toma notas de los conceptos aplicables al caso del curso.',
                    video=item['video'], is_free=True, duration=40)
            upsert_lesson(intro, 3, 'Ejercicio resuelto paso a paso', 'text',
                f'Enunciado: {item["example"]}\n\nProcedimiento: 1) Identifica datos y unidades. 2) Selecciona la ecuación o método pertinente. '
                f'3) Sustituye y calcula. 4) Verifica magnitud y unidades.\n\nComprobación: {item["answer"]}', duration=25)
            upsert_lesson(applied, 1, 'Práctica aplicada', 'assignment',
                f'Problema: {item["example"]}\n\nEntrega un PDF de 1 a 3 páginas con: datos, procedimiento, resultado y una breve interpretación. '
                'Incluye una comprobación independiente y cita cualquier recurso externo.\n\n'
                f'Referencia para autoevaluación: {item["answer"]}\n\nRúbrica: planteamiento 25 %, procedimiento 35 %, resultado 25 %, explicación 15 %.', duration=60)
            exam = upsert_lesson(applied, 2, 'Examen de aplicación', 'exam',
                'Responde las preguntas de aplicación. Puedes revisar las lecciones antes de iniciar.', duration=25)
            evaluation, _ = Evaluation.objects.update_or_create(lesson=exam, defaults={
                'title': f'Examen: {item["title"]}', 'evaluation_type': 'exam', 'time_limit_minutes': 25,
                'passing_score': 66, 'max_attempts': 3, 'is_active': True,
            })
            for number, (prompt, correct, incorrect) in enumerate(item['questions'], 1):
                question, _ = QuestionEvaluation.objects.update_or_create(evaluation=evaluation, order=number,
                    defaults={'text': prompt, 'question_type': 'single', 'points': 1})
                # Si alguien ya respondió, no borramos opciones; solo corregimos las existentes.
                for value in [correct, *incorrect]:
                    QuestionOption.objects.update_or_create(question=question, text=value,
                        defaults={'is_correct': value == correct})
        print(f'✓ {course.title} ({course.get_price_display()})')
    if attribution:
        credits = ROOT / 'docs' / 'FUENTES_CATALOGO.md'
        credits.parent.mkdir(exist_ok=True)
        existing = credits.read_text() if credits.exists() else '# Fuentes de imágenes del catálogo\n\nImágenes de Wikimedia Commons. Consultar la licencia de cada archivo antes de redistribuir.\n\n'
        known = {line.split(' | ')[0] for line in existing.splitlines()}
        with credits.open('a') as f:
            for credit in attribution:
                if credit.split(' | ')[0] not in known:
                    f.write(credit + '\n')
    print(f'Catálogo actualizado: {len(COURSES)} cursos, {Course.objects.filter(status="published").count()} publicados.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-legacy', action='store_true', help='Archiva cursos publicados anteriores, sin borrar datos históricos')
    parser.add_argument('--no-images', action='store_true', help='Omite descarga de imágenes')
    parser.add_argument('--only-if-empty', action='store_true', help='Solo crea el catálogo si aún no hay cursos')
    arguments = parser.parse_args()
    run(arguments.archive_legacy, arguments.no_images, arguments.only_if_empty)
