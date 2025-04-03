from django.urls import path, include
from exchange import views

urlpatterns = [
    path("create_request/", views.CreateRequestView.as_view(), name="create_request"),
    path("my_requests/", include([
        path("", views.MyRequestsView.as_view(), name="my_requests"),
        path("<uuid:request_id>/", include([
            path("complete/", views.CompleteRequestView.as_view(), name="complete_request"),
            path("delete/", views.DeleteRequestView.as_view(), name="delete_request"),
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
