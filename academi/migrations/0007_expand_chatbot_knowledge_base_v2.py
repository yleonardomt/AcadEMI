from django.db import migrations


KNOWLEDGE_BASE = [
    {
        'category': 'payments',
        'question': '¿Cómo funciona el carrito de compras?',
        'answer': 'Agrega los cursos que quieras al carrito desde su página de detalle o el catálogo, y cuando estés listo entra a "Carrito" (ícono en la barra superior) para pagar todos juntos. Ahí también puedes aplicar un cupón si tienes uno.',
        'keywords': 'carrito, agregar al carrito, comprar varios cursos, como pago',
    },
    {
        'category': 'support',
        'question': '¿Olvidé mi contraseña, cómo la recupero?',
        'answer': 'En la página de inicio de sesión toca "¿Olvidaste tu contraseña?" e ingresa tu correo; te enviaremos un enlace para crear una nueva. Si ya iniciaste sesión y solo quieres cambiarla, hazlo desde tu Perfil, en "Cambiar contraseña".',
        'keywords': 'olvide mi contraseña, recuperar contraseña, no puedo entrar, reestablecer clave',
    },
    {
        'category': 'academic',
        'question': '¿Cómo me convierto en docente y publico un curso?',
        'answer': 'Al registrarte puedes elegir el rol "Docente". Una vez dentro, desde "Mis cursos" tienes la opción "Crear curso": agregas módulos y lecciones, y al publicarlo queda pendiente de aprobación por un administrador antes de aparecer en el catálogo.',
        'keywords': 'ser docente, ser profesor, crear curso, publicar curso, subir un curso, como enseño',
    },
    {
        'category': 'academic',
        'question': '¿Cómo son los exámenes y qué seguridad tienen?',
        'answer': 'Los exámenes tienen tiempo límite, no permiten copiar/pegar ni clic derecho, y quedan registrados si cambias de pestaña/ventana o intentas algo indebido; tras varios avisos el sistema puede expulsarte del examen. Todo esto es para que lo rindas de forma honesta.',
        'keywords': 'examen, cuestionario, seguridad del examen, tiempo limite examen, me expulsaron del examen, hacer trampa',
    },
    {
        'category': 'general',
        'question': '¿Dónde veo mis notificaciones?',
        'answer': 'Toca la campana en la barra superior o entra a "Notificaciones" desde tu menú: ahí ves avisos de compras, respuestas del docente, certificados y novedades de la plataforma.',
        'keywords': 'notificaciones, avisos, campana, mensajes del sistema',
    },
    {
        'category': 'payments',
        'question': '¿Tengo descuento por ser estudiante de la EMI?',
        'answer': 'Sí: si te registras con tu correo institucional de la EMI (dominio @est.emi.edu.bo), obtienes automáticamente 15% de descuento en tu primera compra, sin necesidad de ningún código. Te avisamos por notificación al registrarte.',
        'keywords': 'descuento emi, estudiante emi, correo emi, descuento estudiante militar, primera compra descuento',
    },
    {
        'category': 'payments',
        'question': '¿Hay promociones o cupones especiales?',
        'answer': 'Sí, de vez en cuando hay promociones por tiempo limitado (como Navidad o Black Friday) que verás como una etiqueta con el descuento y la fecha límite directamente en la tarjeta del curso, en el catálogo.',
        'keywords': 'promocion, cupon navidad, black friday, descuento por tiempo limitado, oferta especial',
    },
    {
        'category': 'general',
        'question': '¿Cómo edito mi perfil?',
        'answer': 'Entra a tu Perfil desde el menú de usuario: ahí puedes actualizar tu foto, tus datos personales y cambiar tu contraseña.',
        'keywords': 'editar perfil, cambiar mis datos, actualizar foto de perfil, mi cuenta',
    },
    {
        'category': 'academic',
        'question': '¿Cómo verifico si un certificado es válido?',
        'answer': 'Cada certificado tiene un código único. En la página "Verificar certificado" (accesible sin iniciar sesión) cualquiera puede ingresar ese código y confirmar que es auténtico y a quién pertenece.',
        'keywords': 'verificar certificado, certificado valido, codigo de certificado, autenticar certificado',
    },
    {
        'category': 'courses',
        'question': '¿Puedo ver algo del curso antes de comprarlo?',
        'answer': 'Sí: los cursos suelen tener un video de presentación y algunas lecciones marcadas como "gratis" que puedes abrir directamente desde la página del curso, sin comprarlo, para darte una idea antes de decidir.',
        'keywords': 'vista previa, leccion gratis, probar el curso, ver antes de comprar, muestra gratis',
    },
    {
        'category': 'support',
        'question': '¿Cómo contacto soporte?',
        'answer': 'Para algo que no pueda resolver este asistente, escribe a soporte@academi.com y el equipo te va a responder.',
        'keywords': 'soporte, contacto, ayuda humana, hablar con alguien, reclamo',
    },
    {
        'category': 'general',
        'question': '¿Dónde están los términos y condiciones?',
        'answer': 'Puedes leerlos en cualquier momento en la página de Términos y condiciones, enlazada también en el registro.',
        'keywords': 'terminos y condiciones, contrato, politicas del sitio, reglas de la plataforma',
    },
    {
        'category': 'support',
        'question': 'No me llegó el correo de verificación',
        'answer': 'Después de registrarte quedas en una página que te pide verificar tu correo; ahí mismo tienes un botón para reenviar el correo de verificación por si el primero no llegó (revisa también tu carpeta de spam).',
        'keywords': 'no me llego el correo, reenviar verificacion, verificar mi cuenta, correo de confirmacion',
    },
    {
        'category': 'academic',
        'question': '¿Qué diferencia hay entre estudiante y docente?',
        'answer': 'Como estudiante compras/inscribes cursos, avanzas lecciones y obtienes certificados. Como docente creas y gestionas tus propios cursos, respondes preguntas de tus estudiantes y ves estadísticas de tus ventas.',
        'keywords': 'diferencia estudiante docente, tipos de cuenta, roles de usuario',
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
        ('academi', '0006_certificate_is_revoked_certificate_revoked_at'),
    ]

    operations = [
        migrations.RunPython(seed_knowledge_base, remove_knowledge_base),
    ]
