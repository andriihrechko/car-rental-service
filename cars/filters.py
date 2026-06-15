from django_filters import rest_framework as filters

from cars.models import Car


class CarFilter(filters.FilterSet):
    min_year = filters.NumberFilter(field_name="year", lookup_expr="gte")
    max_year = filters.NumberFilter(field_name="year", lookup_expr="lte")
    is_available = filters.BooleanFilter(
        method="filter_available", label="Available"
    )

    def filter_available(self, queryset, _name, value):
        if value:
            return queryset.filter(inventory__gt=0)
        return queryset.filter(inventory=0)

    class Meta:
        model = Car
        fields = ["brand", "fuel_type", "min_year", "max_year", "is_available"]
