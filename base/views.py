from django.views.generic.base import TemplateView
from exchange.models import Request


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
            }
        )
        return ctx
