from django.contrib import admin

from ..models import ChatSession, ChatMessage, ChatIntent, ChatKnowledgeBase


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
