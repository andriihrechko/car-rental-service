from django.db import models

from cars.models import Car
from users.models import User


class RentalStatus(models.TextChoices):
    BOOKED = "BOOKED", "Booked"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    OVERDUE = "OVERDUE", "Overdue"


class Rental(models.Model):
    car = models.ForeignKey(Car, on_delete=models.PROTECT, related_name="rentals")
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="rentals")
    start_date = models.DateField()
    end_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=RentalStatus.choices,
        default=RentalStatus.BOOKED,
    )
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Rental"
        verbose_name_plural = "Rentals"

    def __str__(self) -> str:
        return f"Rental #{self.pk} — {self.user} / {self.car} [{self.status}]"
