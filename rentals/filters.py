from django_filters import rest_framework as filters

from rentals.models import Rental


class RentalFilter(filters.FilterSet):
    class Meta:
        model = Rental
        fields = ["status", "user"]
