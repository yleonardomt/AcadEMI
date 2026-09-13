from django.contrib import admin

from ..models import Evaluation, QuestionEvaluation, EvaluationResult


# ============================================
# ADMIN - EVALUACIONES
# ============================================
@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'evaluation_type', 'is_active', 'created_at')
    list_filter = ('evaluation_type', 'is_active')


@admin.register(QuestionEvaluation)
class QuestionEvaluationAdmin(admin.ModelAdmin):
    list_display = ('text', 'evaluation', 'question_type', 'points', 'order')
    list_filter = ('question_type',)


@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'evaluation', 'score', 'passed', 'completed_at')
    list_filter = ('passed',)
