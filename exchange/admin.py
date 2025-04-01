from django.contrib import admin
from exchange.models import Conversation, Message, Request


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    
    def has_change_permission(self, request, obj = ...):
        return False

# Register your models here.
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["request", "participant1", "participant2"]
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "sender", "content", "timestamp"]
    def has_change_permission(self, request, obj = ...):
        return False


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ["user", "type", "amount_with_currency", "status"]
    list_filter = ["type", "status"]