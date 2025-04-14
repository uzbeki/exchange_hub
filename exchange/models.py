from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from uuid import uuid4
from django.contrib.humanize.templatetags.humanize import intcomma


# Create your models here.
class Request(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    TYPE_CHOICES = [
        ("send", _("Send to Uzbekistan")),
        ("receive", _("Receive from Uzbekistan")),
    ]
    CURRENCY_CHOICES = [
        ("JPY", _("Japanese Yen")),
        ("UZS", _("Uzbekistan Sum")),
        ("USD", _("US Dollar")),
    ]
    STATUS_CHOICES = [
        ("active", _("Active")),
        ("completed", _("Completed")),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    deadline = models.DateTimeField()
    urgent = models.BooleanField(default=False)
    conditions = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    hide_contacts = models.BooleanField(
        default=False, help_text=_("Hide contacts from other users")
    )
    @property
    def amount_with_currency(self):
        return f"{intcomma(self.amount)} {self.get_currency_display()}"

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount_with_currency}"

    def potential_savings_amount(self):
        # for now, it is an approximate amount based on the amount
        # this should be replaced with a real calculation based on the exchange rate
        return int(self.amount * Decimal(0.03))  # 3% savings



class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    request = models.ForeignKey(
        "Request", on_delete=models.CASCADE, related_name="conversations"
    )
    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_p1",
    )
    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_p2",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["request", "participant1", "participant2"]

    def __str__(self):
        return f"Conversation between {self.participant1} and {self.participant2} about {self.request}"

    @classmethod
    def get_user_conversations(cls, user):
        return (
            cls.objects.filter(
                models.Q(participant1=user) | models.Q(participant2=user)
            )
            .distinct()
            .annotate(
                last_message=models.Max("messages__content"),
                last_message_timestamp=models.Max("messages__timestamp"),
                unread_count=models.Count(
                    models.Case(
                        models.When(
                            models.Q(messages__is_read=False)
                            & ~models.Q(messages__sender=user),
                            then=models.Value(1),
                        ),
                        output_field=models.IntegerField(),
                    )
                ),
            )
        )


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return self.content
