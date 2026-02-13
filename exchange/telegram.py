import json
import logging
import secrets
from datetime import timedelta
from urllib.error import HTTPError
from urllib import request

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _bot_token() -> str:
    return getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""


def bot_configured() -> bool:
    return bool(_bot_token())


def bot_start_url(token: str) -> str:
    bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "") or ""
    if not bot_username:
        return ""
    return f"https://t.me/{bot_username}?start={token}"


def bot_chat_url() -> str:
    bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "") or ""
    if not bot_username:
        return ""
    return f"https://t.me/{bot_username}"


def create_telegram_link_token(user):
    from exchange.models import TelegramLinkToken

    token = secrets.token_urlsafe(24)
    return TelegramLinkToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(hours=12),
    )


def send_telegram_message(chat_id: str, text: str) -> bool:
    token = _bot_token()
    if not token or not chat_id:
        return False

    payload = json.dumps(
        {
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")

    req = request.Request(
        url=f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=8) as resp:
            status = getattr(resp, "status", 200)
            return 200 <= status < 300
    except HTTPError as exc:
        logger.warning("Telegram send failed with HTTP %s", exc.code)
        return False
    except Exception:
        logger.warning("Telegram send failed")
        return False


def verify_webhook_secret(http_request) -> bool:
    expected_secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "") or ""
    if not expected_secret:
        return True
    incoming = http_request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return incoming == expected_secret
