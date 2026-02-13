import json
from urllib import parse, request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Configure Telegram bot webhook URL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            required=True,
            help="Public base URL of your app, e.g. https://exchangehub.bekhruz.com",
        )

    def handle(self, *args, **options):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
        secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "") or ""

        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN is missing in environment/settings.")

        base_url = options["base_url"].rstrip("/")
        webhook_url = f"{base_url}/exchange/telegram/webhook/"

        data = {
            "url": webhook_url,
            "drop_pending_updates": True,
        }
        if secret:
            data["secret_token"] = secret

        payload = parse.urlencode(data).encode("utf-8")
        req = request.Request(
            url=f"https://api.telegram.org/bot{token}/setWebhook",
            data=payload,
            method="POST",
        )

        with request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))

        if not result.get("ok"):
            raise CommandError(f"Telegram API error: {result}")

        self.stdout.write(self.style.SUCCESS(f"Webhook set to: {webhook_url}"))
