import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    phone = models.CharField(max_length=16, unique=True, blank=True, null=True)
    phone_verified = models.BooleanField(default=False)

    def contact_info(self):
        return dict(
            phone=self.phone if self.phone_verified else None,
            email=self.email if self.email else None,
            username=self.username if self.username else None,
            social_accounts=self.social_accounts.all() if hasattr(self, "social_accounts") else [],
        )