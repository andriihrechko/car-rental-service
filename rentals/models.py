from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Rental(models.Model):
    class Status(models.TextChoices):
        BOOKED = "BOOKED", "Booked"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        OVERDUE = "OVERDUE", "Overdue"

    car = models.ForeignKey(
        "cars.Car",
        on_delete=models.PROTECT,
        related_name="rentals",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="rentals",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BOOKED,
    )
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"Rental #{self.pk} — {self.car} ({self.status})"
