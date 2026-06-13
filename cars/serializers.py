from rest_framework import serializers
from cars.models import Car


class CarSerializer(serializers.ModelSerializer):
    """Serializer for Car model."""

    class Meta:
        model = Car
        fields = "__all__"
