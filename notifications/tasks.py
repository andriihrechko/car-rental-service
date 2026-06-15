from celery import shared_task
from django.utils import timezone

from notifications.notification_service import NotificationService


@shared_task
def notify_overdue_rentals(rental):
    overdue_rentals = rental.objects.filter(
        actual_return_date__isnull=True,
        end_date__lt=timezone.now().date(),
    )

    if not overdue_rentals.exists():
        return

    message = (
        f"🚨 Overdue rentals report\n\n"
        f"Total overdue rentals: {overdue_rentals.count()}\n\n"
    )

    for rental in overdue_rentals:
        message += f"Rental ID: {rental.id}\nUser ID: {rental.user_id}\n\n"

    NotificationService.send(message)


@shared_task
def send_payment_notification(payment, payment_id: int):
    payment = payment.objects.select_related(
        "rental",
        "rental__user",
    ).get(id=payment_id)

    message = (
        "💰 Payment successful\n\n"
        f"Payment ID: {payment.id}\n"
        f"Rental ID: {payment.rental.id}\n"
        f"User ID: {payment.rental.user.id}\n"
        f"Amount: {payment.money_to_pay}"
    )

    NotificationService.send(message=message)
