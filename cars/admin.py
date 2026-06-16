from django.contrib import admin

from cars.models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        "brand",
        "model",
        "year",
        "daily_rate",
        "fuel_type",
        "inventory",
    )
    list_filter = ("fuel_type", "year")
    search_fields = ("brand", "model")
