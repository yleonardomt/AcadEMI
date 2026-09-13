from django.db import migrations


KNOWLEDGE_BASE = [
    {
        'category': 'general',
        'question': '¿Qué es AcadEMI?',
        'answer': 'AcadEMI es una plataforma educativa online donde puedes aprender con cursos de programación, diseño, marketing, negocios y más, dictados por docentes expertos.',
        'keywords': 'que es, acerca de, sobre acadEMI, plataforma',
    },
    {
        'category': 'courses',
        'question': '¿Qué cursos hay disponibles?',
        'answer': 'Tenemos cursos de programación, diseño, negocios, ciencia de datos, idiomas y más. Puedes verlos todos en el catálogo, organizado por categorías.',
        'keywords': 'curso, cursos, catalogo, disponible, ver cursos',
    },
    {
        'category': 'courses',
        'question': '¿Cómo busco un curso específico?',
        'answer': 'Usa la barra de búsqueda en el menú "Buscar" para encontrar cursos por nombre, o navega por categoría desde el catálogo.',
        'keywords': 'buscar, encontrar curso, busqueda',
    },
    {
        'category': 'courses',
        'question': '¿Cómo agrego un curso a favoritos?',
        'answer': 'Desde el catálogo o la página del curso, presiona el ícono de corazón para guardarlo en tu lista de favoritos.',
        'keywords': 'favorito, favoritos, guardar curso, corazon',
    },
    {
        'category': 'payments',
        'question': '¿Cómo compro un curso?',
        'answer': 'Agrega el curso al carrito desde el catálogo o su página de detalle, luego ve al carrito y completa el pago con el método que prefieras.',
        'keywords': 'comprar, compra, adquirir curso',
    },
    {
        'category': 'payments',
        'question': '¿Qué métodos de pago aceptan?',
        'answer': 'Aceptamos tarjeta, transferencia bancaria, pago QR y pago móvil. Puedes elegir el método al finalizar tu compra en el carrito.',
        'keywords': 'pago, metodo de pago, tarjeta, qr, transferencia',
    },
    {
        'category': 'payments',
        'question': '¿Tengo cupones de descuento?',
        'answer': 'Si tienes un código de cupón, puedes ingresarlo en el carrito antes de pagar para aplicar el descuento correspondiente.',
        'keywords': 'cupon, descuento, codigo promocional',
    },
    {
        'category': 'payments',
        'question': '¿Dónde veo mi historial de compras?',
        'answer': 'En tu perfil, entra a "Historial" para ver todas tus compras y descargar tus comprobantes de pago.',
        'keywords': 'historial, comprobante, factura, mis compras',
    },
    {
        'category': 'academic',
        'question': '¿Cómo veo mi progreso?',
        'answer': 'En el menú de tu cuenta, entra a "Mi progreso" para ver tu avance y las lecciones completadas en cada curso.',
        'keywords': 'progreso, avance, lecciones completadas',
    },
    {
        'category': 'academic',
        'question': '¿Cómo veo mis calificaciones?',
        'answer': 'Ve a "Calificaciones" en tu cuenta para consultar los resultados de todas tus evaluaciones y cuestionarios.',
        'keywords': 'calificacion, nota, evaluacion, resultado',
    },
    {
        'category': 'academic',
        'question': '¿Cómo obtengo mi certificado?',
        'answer': 'Al completar el 100% de un curso, tu certificado se genera automáticamente y lo encontrarás en "Mis certificados", donde también puedes descargarlo o enviarlo por correo.',
        'keywords': 'certificado, diploma, finalizar curso',
    },
    {
        'category': 'support',
        'question': '¿Cómo funciona la plataforma?',
        'answer': 'Explora el catálogo, agrega los cursos que te interesen al carrito, complétalos a tu ritmo y obtén tu certificado al finalizar. ¿Hay algo puntual en lo que te pueda ayudar?',
        'keywords': 'como funciona, ayuda, funcionamiento',
    },
    {
        'category': 'support',
        'question': '¿Cómo cambio mi contraseña?',
        'answer': 'En tu perfil, ve a "Cambiar contraseña" e ingresa tu contraseña actual junto con la nueva.',
        'keywords': 'contraseña, password, cambiar clave',
    },
    {
        'category': 'general',
        'question': 'Hola',
        'answer': '¡Hola! Soy el asistente virtual de AcadEMI. Puedo ayudarte con información sobre cursos, compras, tu progreso académico o el uso de la plataforma.',
        'keywords': 'hola, buenas, hey, saludos',
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
        ('academi', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_knowledge_base, remove_knowledge_base),
    ]
