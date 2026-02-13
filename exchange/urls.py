from django.urls import path, include
from exchange import views

urlpatterns = [
    path("create_offer/", views.CreateOfferView.as_view(), name="create_offer"),
    path("my_offers/", include([
        path("", views.MyRequestsView.as_view(), name="my_offers"),
        path("<uuid:request_id>/", include([
            path("complete/", views.CompleteRequestView.as_view(), name="complete_offer"),
            path("delete/", views.DeleteRequestView.as_view(), name="delete_offer"),
            path("update/", views.UpdateOfferView.as_view(), name="update_offer"),
        ])),
    ])),
    
    path("conversations/", include([
        path("", views.ConversationsListView.as_view(), name="conversations_list"),
        path("<uuid:conversation_id>/", include([
            path("", views.ConversationView.as_view(), name="conversation"),
            path("delete/", views.DeleteConversationView.as_view(), name="delete_conversation"),
        ])),
    ])),
    path('start_conversation/<uuid:request_id>/', views.StartConversationView.as_view(), name='start_conversation'),

    path("luggage/", include([
        path("", views.LuggageMarketplaceView.as_view(), name="luggage_marketplace"),
        path("create/", views.LuggageListingCreateView.as_view(), name="luggage_create"),
        path("my/", views.MyLuggageListingsView.as_view(), name="luggage_my_listings"),
        path("notifications/", views.LuggageNotificationsView.as_view(), name="luggage_notifications"),
        path("subscriptions/<int:subscription_id>/update/", views.UpdateLuggageNotificationView.as_view(), name="luggage_notification_update"),
        path("<uuid:listing_id>/edit/", views.LuggageListingUpdateView.as_view(), name="luggage_update"),
        path("<uuid:listing_id>/delete/", views.DeleteLuggageListingView.as_view(), name="luggage_delete"),
        path("<uuid:listing_id>/active/", views.ToggleLuggageListingActiveView.as_view(), name="luggage_toggle_active"),
        path("<uuid:listing_id>/", views.LuggageListingDetailView.as_view(), name="luggage_listing_detail"),
        path("<uuid:listing_id>/reserve/", views.CreateLuggageReservationView.as_view(), name="luggage_reserve"),
        path("<uuid:listing_id>/telegram-notify/", views.ToggleLuggageTelegramSubscriptionView.as_view(), name="luggage_telegram_notify_toggle"),
        path("reservations/<uuid:reservation_id>/status/", views.UpdateLuggageReservationStatusView.as_view(), name="luggage_reservation_status"),
    ])),
    path("telegram/webhook/", views.TelegramWebhookView.as_view(), name="telegram_webhook"),
]
