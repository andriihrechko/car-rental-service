from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter

from cars.models import Car
from cars.serializers import CarSerializer


class CarFilter(filters.FilterSet):
    min_year = filters.NumberFilter(field_name="year", lookup_expr="gte")
    max_year = filters.NumberFilter(field_name="year", lookup_expr="lte")
    is_available = filters.BooleanFilter(method="filter_available", label="Available")

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(inventory__gt=0)
        return queryset.filter(inventory=0)

    class Meta:
        model = Car
        fields = ["brand", "fuel_type", "min_year", "max_year", "is_available"]


class CarViewSet(viewsets.ModelViewSet):
    """ViewSet for managing cars inventory."""

    queryset = Car.objects.all()
    serializer_class = CarSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CarFilter
    search_fields = ["brand", "model"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
