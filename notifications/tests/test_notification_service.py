from unittest.mock import patch

from django.test import SimpleTestCase

from notifications.notification_service import NotificationService


class NotificationServiceTests(SimpleTestCase):

    @patch(
        "notifications.notification_service.TelegramClient.send_message"
    )
    def test_send_calls_telegram_client(
        self,
        mock_send_message,
    ):
        NotificationService.send("test message")

        mock_send_message.assert_called_once_with(
            "test message",
        )