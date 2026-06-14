from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MinValueValidator


class FuelType(models.TextChoices):
    GAS = "GAS", "Gas"
    DIESEL = "DIESEL", "Diesel"
    HYBRID = "HYBRID", "Hybrid"
    ELECTRIC = "ELECTRIC", "Electric"


class Car(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    fuel_type = models.CharField(max_length=10, choices=FuelType.choices)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    inventory = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = "cars"
        verbose_name = "Car"
        verbose_name_plural = "Cars"

    def __str__(self) -> str:
        return f"{self.year} {self.brand} {self.model}"
