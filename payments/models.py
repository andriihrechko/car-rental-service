from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        EXPIRED = 'expired', 'Expired'

    class Type(models.TextChoices):
        RENTAL = 'rental', 'Rental'
        CANCELLATION_FEE = 'cancellation_fee', 'Cancellation_fee'
        OVERDUE_FEE = 'overdue_fee', 'Overdue_fee'

    status = models.CharField(
        choices=Status.choices,
        default=Status.PENDING,
        max_length=20,
    )
    type = models.CharField(
        choices=Type.choices,
        default=Type.RENTAL,
        max_length=20,
    )
    rental = models.ForeignKey(
        "rentals.Rental",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    session_url = models.URLField(blank=True, null=True)
    session_id = models.CharField(blank=True, null=True, max_length=255)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.type} payment #{self.pk} ({self.status})"
