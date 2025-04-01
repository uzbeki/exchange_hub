from django.views.generic.base import TemplateView
from exchange.models import Request


class IndexView(TemplateView):
    template_name = "index.html"
    extra_context = {
        "send_requests": Request.objects.filter(type="send", status="active").order_by(
            "-created_at"
        ),
        "receive_requests": Request.objects.filter(
            type="receive", status="active"
        ).order_by("-created_at"),
    }
