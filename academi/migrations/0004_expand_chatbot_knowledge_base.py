from django.db import migrations


KNOWLEDGE_BASE = [
    {
        'category': 'payments',
        'question': '¿Cuánto cuesta un curso?',
        'answer': 'Cada curso muestra su precio en su página de detalle y en el catálogo. Los precios varían según el curso, y varios son completamente gratuitos.',
        'keywords': 'cuanto cuesta, precio, cuanto vale, costo del curso',
    },
    {
        'category': 'courses',
        'question': '¿Cómo me inscribo en un curso?',
        'answer': 'Una vez que compras un curso (o si es gratuito, lo agregas), aparece automáticamente en "Mis cursos". Desde ahí entra a "Continuar" para empezar a ver sus lecciones.',
        'keywords': 'inscribir, inscribirme, como empiezo un curso, iniciar curso, empezar curso',
    },
    {
        'category': 'academic',
        'question': '¿Puedo hablar con el docente?',
        'answer': 'Sí: entra a cualquier lección del curso y usa la sección "Preguntas y respuestas" al final de la lección para escribirle tu duda directamente al docente; él o ella podrá responderte ahí mismo.',
        'keywords': 'hablar con el docente, preguntar al profesor, contactar profesor, dudas al docente, pregunta al docente, hablar con el profesor',
    },
    {
        'category': 'courses',
        'question': '¿Puedo dejar una reseña de un curso?',
        'answer': 'Sí, en la página de detalle de cualquier curso que hayas adquirido encontrarás la sección de Reseñas, donde puedes calificarlo del 1 al 5 y dejar tu opinión.',
        'keywords': 'resena, opinion del curso, valorar curso, calificar curso, dejar reseña',
    },
    {
        'category': 'courses',
        'question': '¿Puedo comentar en las lecciones?',
        'answer': 'Sí, al final de cada lección hay una sección de Comentarios donde puedes publicar, editar o eliminar tus comentarios sobre el contenido.',
        'keywords': 'comentar, comentario en la leccion, dejar un comentario',
    },
    {
        'category': 'general',
        'question': '¿Quién eres?',
        'answer': 'Soy el asistente virtual de AcadEMI. Estoy aquí para ayudarte con dudas sobre cursos, compras, tu progreso académico y certificados.',
        'keywords': 'quien eres, quien te creo, eres un robot, eres humano',
    },
    {
        'category': 'general',
        'question': 'Despedida',
        'answer': 'Con gusto. Si tienes otra duda sobre AcadEMI, aquí estoy.',
        'keywords': 'gracias, adios, chau, hasta luego, nos vemos',
    },
]


def seed_knowledge_base(apps, schema_editor):
    ChatKnowledgeBase = apps.get_model('academi', 'ChatKnowledgeBase')
    for entry in KNOWLEDGE_BASE:
        ChatKnowledgeBase.objects.get_or_create(
            question=entry['question'],
            defaults={
                'answer': entry['answer'],
                'category': entry['category'],
                'keywords': entry['keywords'],
            },
        )


def remove_knowledge_base(apps, schema_editor):
    ChatKnowledgeBase = apps.get_model('academi', 'ChatKnowledgeBase')
    questions = [entry['question'] for entry in KNOWLEDGE_BASE]
    ChatKnowledgeBase.objects.filter(question__in=questions).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('academi', '0003_assignmentsubmission'),
    ]

    operations = [
        migrations.RunPython(seed_knowledge_base, remove_knowledge_base),
    ]
