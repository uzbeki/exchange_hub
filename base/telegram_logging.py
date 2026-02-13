import logging
import threading

from django.conf import settings

from exchange.telegram import send_telegram_message


_state = threading.local()


class TelegramAdminHandler(logging.Handler):
    def emit(self, record):
        if getattr(_state, "sending", False):
            return

        admin_chat_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", "") or ""
        if not admin_chat_id:
            return

        try:
            _state.sending = True
            message = self.format(record)
            text = f"🚨 Exchange Hub Error\n\n{message[:3500]}"
            send_telegram_message(admin_chat_id, text)
        except Exception:
            pass
        finally:
            _state.sending = False
