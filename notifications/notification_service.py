from notifications.telegram import TelegramClient


class NotificationService:
    telegram = TelegramClient()

    @classmethod
    def send(cls, message: str) -> None:
        cls.telegram.send_message(message)
