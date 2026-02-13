import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    phone = models.CharField(max_length=16, unique=True, blank=True, null=True)
    phone_verified = models.BooleanField(default=False)
    telegram_chat_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    telegram_username = models.CharField(max_length=128, blank=True)
    telegram_notifications_enabled = models.BooleanField(default=False)
    telegram_linked_at = models.DateTimeField(blank=True, null=True)

    def link_telegram(self, chat_id: str, username: str = ""):
        self.telegram_chat_id = str(chat_id)
        self.telegram_username = username or ""
        self.telegram_notifications_enabled = True
        self.telegram_linked_at = timezone.now()

    def contact_info(self):
        return dict(
            phone=self.phone if self.phone_verified else None,
            email=self.email if self.email else None,
            username=self.username if self.username else None,
            social_accounts=self.social_accounts.all() if hasattr(self, "social_accounts") else [],
        )