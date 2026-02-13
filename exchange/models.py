from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
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

    @classmethod
    def get_unread_message_count_by_user(cls, user):
        return cls.objects.filter(
            conversation__in=Conversation.objects.filter(
                models.Q(participant1=user) | models.Q(participant2=user)
            ),
            is_read=False,
        ).exclude(sender=user).count()


class LuggageListing(models.Model):
    PRICE_CURRENCY_CHOICES = [
        ("JPY", _("Japanese Yen")),
        ("UZS", _("Uzbekistan Sum")),
        ("USD", _("US Dollar")),
    ]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="luggage_listings",
    )
    title = models.CharField(max_length=120)
    total_kg = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    price_currency = models.CharField(max_length=3, choices=PRICE_CURRENCY_CHOICES, default="JPY")
    available_until = models.DateField()
    arrival_datetime = models.DateTimeField(blank=True, null=True)
    departure_city = models.CharField(max_length=120, default="Tashkent")
    arrival_city = models.CharField(max_length=120, default="Tokyo")
    pickup_location_tokyo = models.CharField(max_length=255)
    delivery_options = models.TextField(blank=True)
    allowed_items = models.TextField()
    prohibited_items = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.seller.username}"

    def clean(self):
        if self.total_kg <= 0:
            raise ValidationError({"total_kg": _("Storage must be greater than 0 kg.")})
        if self.price_per_kg <= 0:
            raise ValidationError({"price_per_kg": _("Price per kg must be greater than 0.")})

    @property
    def committed_kg(self):
        result = self.reservations.filter(
            status__in=[LuggageReservation.STATUS_PENDING, LuggageReservation.STATUS_RESERVED]
        ).aggregate(total=Sum("kg_requested"))
        return result["total"] or Decimal("0")

    @property
    def reserved_kg(self):
        result = self.reservations.filter(
            status=LuggageReservation.STATUS_RESERVED
        ).aggregate(total=Sum("kg_requested"))
        return result["total"] or Decimal("0")

    @property
    def remaining_kg(self):
        return max(Decimal("0"), self.total_kg - self.committed_kg)

    @property
    def is_expired(self):
        return self.available_until < timezone.localdate()

    @property
    def is_sellable(self):
        return self.is_active and not self.is_expired and self.remaining_kg > 0


class LuggageReservation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RESERVED = "reserved"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending")),
        (STATUS_RESERVED, _("Reserved")),
        (STATUS_CANCELLED, _("Cancelled")),
    ]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    listing = models.ForeignKey(
        LuggageListing,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="luggage_reservations",
    )
    kg_requested = models.DecimalField(max_digits=6, decimal_places=2)
    contact_handle = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.buyer.username} - {self.kg_requested} kg ({self.status})"

    def clean(self):
        if self.kg_requested <= 0:
            raise ValidationError({"kg_requested": _("Reserved kg must be greater than 0.")})

        if not self.listing_id:
            return

        if self.listing.seller_id == self.buyer_id:
            raise ValidationError(_("You cannot reserve your own listing."))

        if self.listing.is_expired or not self.listing.is_active:
            raise ValidationError(_("This listing is no longer available."))

        taken_kg = (
            self.listing.reservations.filter(
                status__in=[self.STATUS_PENDING, self.STATUS_RESERVED]
            )
            .exclude(pk=self.pk)
            .aggregate(total=Sum("kg_requested"))["total"]
            or Decimal("0")
        )
        remaining_for_new = self.listing.total_kg - taken_kg
        if self.kg_requested > remaining_for_new:
            raise ValidationError(
                {
                    "kg_requested": _(
                        "Only %(remaining)s kg is left for reservation."
                    )
                    % {"remaining": remaining_for_new}
                }
            )


class LuggageTelegramSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="luggage_telegram_subscriptions",
    )
    listing = models.ForeignKey(
        LuggageListing,
        on_delete=models.CASCADE,
        related_name="telegram_subscriptions",
    )
    notify_on_new_reservation = models.BooleanField(default=True)
    notify_on_status_change = models.BooleanField(default=True)
    notify_on_sold_out = models.BooleanField(default=True)
    notify_on_reopened = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "listing"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} subscribed to {self.listing}"


class TelegramLinkToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_link_tokens",
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_valid(self):
        return self.used_at is None and timezone.now() <= self.expires_at
