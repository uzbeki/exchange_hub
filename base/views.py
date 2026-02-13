from django.views.generic.base import TemplateView
from exchange.models import LuggageListing, Message, Request


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "send_requests": Request.objects.filter(
                    type="send", status="active"
                ).order_by("-created_at"),
                "receive_requests": Request.objects.filter(
                    type="receive", status="active"
                ).order_by("-created_at"),
                "recent_luggage_listings": LuggageListing.objects.filter(
                    is_active=True
                )
                .select_related("seller")
                .order_by("-created_at")[:3],
                "unread_messages": (
                    Message.get_unread_message_count_by_user(self.request.user)
                    if self.request.user.is_authenticated
                    else 0
                ),
            }
        )
        return ctx


class FAQView(TemplateView):
    template_name = "faq.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "unread_messages": (
                    Message.get_unread_message_count_by_user(self.request.user)
                    if self.request.user.is_authenticated
                    else 0
                ),
            }
        )
        return ctx
