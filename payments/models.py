from django.db import models

from rentals.models import Rental


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PAID = "PAID", "Paid"
    EXPIRED = "EXPIRED", "Expired"


class PaymentType(models.TextChoices):
    RENTAL = "RENTAL", "Rental"
    CANCELLATION_FEE = "CANCELLATION_FEE", "Cancellation Fee"
    OVERDUE_FEE = "OVERDUE_FEE", "Overdue Fee"


class Payment(models.Model):
    status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    type = models.CharField(max_length=20, choices=PaymentType.choices)
    rental = models.ForeignKey(Rental, on_delete=models.PROTECT, related_name="payments")
    session_url = models.URLField(max_length=500)
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self) -> str:
        return f"Payment #{self.pk} — {self.type} / {self.status} / ${self.money_to_pay}"
