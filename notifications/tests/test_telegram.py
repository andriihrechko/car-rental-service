from unittest.mock import Mock, patch

import requests
from django.conf import settings
from django.test import SimpleTestCase

from notifications.telegram import TelegramClient


class TelegramClientTests(SimpleTestCase):

    @patch("notifications.telegram.requests.post")
    def test_should_send_message(
        self,
        mock_post,
    ):
        response = Mock()
        response.raise_for_status.return_value = None

        mock_post.return_value = response

        TelegramClient().send_message("test")

        mock_post.assert_called_once_with(
            (
                f"https://api.telegram.org/bot"
                f"{settings.TELEGRAM_BOT_TOKEN}"
                "/sendMessage"
            ),
            json={
                "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
                "text": "test",
            },
            timeout=10,
        )

        response.raise_for_status.assert_called_once()

    @patch("notifications.telegram.requests.post")
    def test_should_raise_exception_when_telegram_api_fails(
        self,
        mock_post,
    ):
        response = Mock()
        response.raise_for_status.side_effect = (
            requests.RequestException
        )

        mock_post.return_value = response

        with self.assertRaises(
            requests.RequestException,
        ):
            TelegramClient().send_message("test")