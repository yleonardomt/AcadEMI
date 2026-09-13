from django.db import migrations

OLD_KEYWORDS = 'curso, cursos, catalogo, disponible, ver cursos'
NEW_KEYWORDS = 'que cursos hay, cursos disponibles, ver catalogo, catalogo de cursos, que cursos tienen'


def narrow_keywords(apps, schema_editor):
    """La palabra suelta "curso"/"cursos" aparecía en casi cualquier
    pregunta relacionada a cursos (precio, inscripción, etc.), así que
    esta entrada genérica ganaba por encima de respuestas más
    específicas que sí coincidían con la pregunta real del usuario."""
    ChatKnowledgeBase = apps.get_model('academi', 'ChatKnowledgeBase')
    ChatKnowledgeBase.objects.filter(keywords=OLD_KEYWORDS).update(keywords=NEW_KEYWORDS)


def widen_keywords(apps, schema_editor):
    ChatKnowledgeBase = apps.get_model('academi', 'ChatKnowledgeBase')
    ChatKnowledgeBase.objects.filter(keywords=NEW_KEYWORDS).update(keywords=OLD_KEYWORDS)


class Migration(migrations.Migration):

    dependencies = [
        ('academi', '0004_expand_chatbot_knowledge_base'),
    ]

    operations = [
        migrations.RunPython(narrow_keywords, widen_keywords),
    ]
