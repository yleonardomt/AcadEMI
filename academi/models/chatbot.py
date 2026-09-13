from django.db import models
from django.utils import timezone

from .users import User

# ============================================
# MÓDULO 10: ASISTENTE VIRTUAL - CHATBOT (RF-77 al RF-82)
# ============================================

class ChatSession(models.Model):  # RF-77
    """Sesión de chat del usuario con el asistente virtual"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Chat de {self.user.username} - {self.started_at}"

    def end_session(self):
        self.is_active = False
        self.ended_at = timezone.now()
        self.save()


class ChatMessage(models.Model):  # RF-78, RF-79, RF-80, RF-81, RF-82
    """Mensaje intercambiado en el chat"""

    SENDER_TYPES = (
        ('user', 'Usuario'),
        ('bot', 'Asistente Virtual'),
    )

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_TYPES)
    message = models.TextField()
    response_time = models.FloatField(blank=True, null=True)  # Tiempo de respuesta en segundos
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_sender_display()} - {self.message[:50]}"


class ChatIntent(models.Model):  # RF-78
    """Intenciones reconocidas por el chatbot"""

    INTENT_TYPES = (
        ('greeting', 'Saludo'),
        ('course', 'Información de cursos'),
        ('purchase', 'Información de compras'),
        ('academic', 'Información académica'),
        ('help', 'Ayuda de plataforma'),
        ('other', 'Otro'),
    )

    name = models.CharField(max_length=50, unique=True)
    intent_type = models.CharField(max_length=20, choices=INTENT_TYPES)
    keywords = models.TextField(help_text="Palabras clave separadas por comas")
    response_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ChatKnowledgeBase(models.Model):  # RF-82
    """Base de conocimiento del chatbot"""

    CATEGORIES = (
        ('general', 'General'),
        ('courses', 'Cursos'),
        ('payments', 'Pagos'),
        ('academic', 'Académico'),
        ('support', 'Soporte'),
        ('technical', 'Técnico'),
    )

    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORIES, default='general')
    keywords = models.TextField(help_text="Palabras clave separadas por comas")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kb_entries')

    def __str__(self):
        return f"{self.category} - {self.question[:50]}"


class ChatFeedback(models.Model):  # RF-82
    """Feedback del usuario sobre las respuestas del chatbot"""

    RATING_CHOICES = (
        (1, 'Muy mala'),
        (2, 'Mala'),
        (3, 'Regular'),
        (4, 'Buena'),
        (5, 'Excelente'),
    )

    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.rating} - {self.message.message[:30]}"


class ChatAnalytics(models.Model):  # RF-79, RF-80, RF-81
    """Analíticas del chatbot"""

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='analytics')
    total_messages = models.IntegerField(default=0)
    user_messages = models.IntegerField(default=0)
    bot_messages = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analytics - {self.session.user.username} - {self.created_at}"
