import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class TelegramClient:
    def send_message(self, text: str) -> None:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
                    "text": text,
                },
                timeout=10,
            )

            response.raise_for_status()

            logger.info("Telegram message sent successfully")

        except requests.RequestException:
            logger.exception("Failed to send telegram message")
            raise
