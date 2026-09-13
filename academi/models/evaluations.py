from django.db import models

from .courses import Lesson
from .learning import Enrollment

# ============================================
# MÓDULO 6: EVALUACIONES (RF-44 al RF-53)
# ============================================

class Evaluation(models.Model):  # RF-44, RF-46
    EVALUATION_TYPES = (
        ('quiz', 'Cuestionario'),
        ('exam', 'Examen'),
        ('assignment', 'Tarea'),
        ('practical', 'Práctico'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='evaluations')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    evaluation_type = models.CharField(max_length=20, choices=EVALUATION_TYPES, default='quiz')
    time_limit_minutes = models.IntegerField(default=30)  # RF-46
    passing_score = models.IntegerField(default=70)  # RF-46
    max_attempts = models.IntegerField(default=1)  # RF-46
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class QuestionEvaluation(models.Model):  # RF-45
    QUESTION_TYPES = (
        ('multiple', 'Opción múltiple'),
        ('single', 'Opción única'),
        ('true_false', 'Verdadero/Falso'),
        ('open', 'Respuesta abierta'),
    )

    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single')
    text = models.TextField()
    points = models.IntegerField(default=1)  # RF-46
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evaluation.title} - {self.text[:50]}"


class QuestionOption(models.Model):  # RF-45
    question = models.ForeignKey(QuestionEvaluation, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class EvaluationResult(models.Model):  # RF-50, RF-51, RF-52
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='evaluation_results')
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)  # RF-47
    completed_at = models.DateTimeField(blank=True, null=True)
    time_spent = models.IntegerField(default=0)  # RF-48
    attempt_number = models.IntegerField(default=1)
    ip_address = models.GenericIPAddressField(blank=True, null=True)  # RF-53
    user_agent = models.TextField(blank=True, null=True)  # RF-53

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.evaluation.title}"


class UserAnswer(models.Model):  # RF-49
    evaluation_result = models.ForeignKey(EvaluationResult, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(QuestionEvaluation, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, blank=True, null=True)
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_obtained = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.evaluation_result} - {self.question.text[:30]}"


class EvaluationIncident(models.Model):  # RF-53
    INCIDENT_TYPES = (
        ('copy_paste', 'Copiar y pegar'),
        ('tab_switch', 'Cambio de pestaña'),
        ('timeout', 'Tiempo agotado'),
        ('other', 'Otro'),
    )

    evaluation_result = models.ForeignKey(EvaluationResult, on_delete=models.CASCADE, related_name='incidents')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evaluation_result} - {self.incident_type}"
