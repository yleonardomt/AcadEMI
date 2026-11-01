from django.contrib import admin

from ..models import ChatSession, ChatMessage, ChatIntent, ChatKnowledgeBase, ChatFeedback, ChatAnalytics


# ============================================
# ADMIN - CHATBOT
# ============================================
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'started_at', 'ended_at')
    list_filter = ('is_active',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'message', 'created_at')
    list_filter = ('sender',)


@admin.register(ChatIntent)
class ChatIntentAdmin(admin.ModelAdmin):
    list_display = ('name', 'intent_type', 'is_active')
    list_filter = ('intent_type', 'is_active')


@admin.register(ChatKnowledgeBase)
class ChatKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer', 'keywords')


@admin.register(ChatFeedback)
class ChatFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'message', 'created_at')
    list_filter = ('rating',)
    search_fields = ('message__message', 'user__username')


@admin.register(ChatAnalytics)
class ChatAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('session', 'total_messages', 'avg_response_time', 'resolved')
