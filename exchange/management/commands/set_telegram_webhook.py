import json
from urllib import error, parse, request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Configure Telegram bot webhook URL."

    def _telegram_post(self, token: str, method: str, data: dict | None = None) -> dict:
        payload = parse.urlencode(data or {}).encode("utf-8")
        req = request.Request(
            url=f"https://api.telegram.org/bot{token}/{method}",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise CommandError(
                f"Telegram API HTTP error while calling {method}: {exc.code} {exc.reason}. {body}"
            ) from exc
        except error.URLError as exc:
            raise CommandError(f"Telegram API network error while calling {method}: {exc}") from exc

        if not result.get("ok"):
            raise CommandError(f"Telegram API error from {method}: {result}")

        return result

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

        self._telegram_post(token=token, method="setWebhook", data=data)
        info = self._telegram_post(token=token, method="getWebhookInfo")
        configured_url = (info.get("result") or {}).get("url", "")
        if configured_url != webhook_url:
            raise CommandError(
                f"Webhook mismatch after setWebhook. Expected '{webhook_url}', got '{configured_url}'."
            )

        self.stdout.write(self.style.SUCCESS(f"Webhook set to: {webhook_url}"))
