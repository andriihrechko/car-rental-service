from django.db import models


class FuelType(models.TextChoices):
    GAS = "GAS", "Gas"
    DIESEL = "DIESEL", "Diesel"
    HYBRID = "HYBRID", "Hybrid"
    ELECTRIC = "ELECTRIC", "Electric"


class Car(models.Model):
    """Car model representing a vehicle available for rental."""

    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    fuel_type = models.CharField(max_length=10, choices=FuelType.choices)
    daily_rate = models.DecimalField(max_digits=8, decimal_places=2)
    inventory = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["brand", "model", "year", "fuel_type"],
                name="unique_car",
            )
        ]

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"
