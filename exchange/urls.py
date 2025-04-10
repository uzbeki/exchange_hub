from django.urls import path, include
from exchange import views

urlpatterns = [
    path("create_offer/", views.CreateRequestView.as_view(), name="create_offer"),
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
]
