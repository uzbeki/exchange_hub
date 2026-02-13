from django.contrib import admin
from exchange.models import (
    Conversation,
    Message,
    Request,
    LuggageListing,
    LuggageReservation,
    LuggageTelegramSubscription,
    TelegramLinkToken,
)


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


@admin.register(LuggageReservation)
class LuggageReservationAdmin(admin.ModelAdmin):
    list_display = ["listing", "buyer", "kg_requested", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["buyer__username", "listing__title", "contact_handle"]


@admin.register(LuggageListing)
class LuggageListingAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "seller",
        "total_kg",
        "price_per_kg",
        "available_until",
        "is_active",
    ]
    list_filter = ["is_active", "available_until"]
    search_fields = ["title", "seller__username", "pickup_location_tokyo"]


@admin.register(LuggageTelegramSubscription)
class LuggageTelegramSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "listing", "is_active", "updated_at"]
    list_filter = ["is_active", "notify_on_sold_out", "notify_on_new_reservation"]
    search_fields = ["user__username", "listing__title"]


@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "token", "expires_at", "used_at"]
    list_filter = ["created_at", "expires_at", "used_at"]
    search_fields = ["user__username", "token"]