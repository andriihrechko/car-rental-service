from django.db import models


class Rental(models.Model):
    class Status(models.TextChoices):
        BOOKED = "BOOKED", "Booked"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        OVERDUE = "OVERDUE", "Overdue"

    start_date = models.DateField()
    end_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=Status.choices, default=Status.BOOKED, max_length=10)