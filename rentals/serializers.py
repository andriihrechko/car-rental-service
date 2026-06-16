from datetime import date

from rest_framework import serializers

from rentals.models import Rental


class RentalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = [
            "id",
            "car",
            "user",
            "start_date",
            "end_date",
            "actual_return_date",
            "status",
            "price_per_day",
        ]
        read_only_fields = [
            "user",
            "actual_return_date",
            "status",
            "price_per_day",
        ]

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError(
                {"end_date": "end_date must be >= start_date."}
            )
        return attrs

    def create(self, validated_data):
        car = validated_data["car"]
        start_date = validated_data["start_date"]
        end_date = validated_data["end_date"]

        active_rentals_count = Rental.objects.filter(
            car=car,
            status__in=[Rental.Status.BOOKED, Rental.Status.OVERDUE],
            start_date__lte=end_date,
            end_date__gte=start_date,
        ).count()

        if active_rentals_count >= car.inventory:
            raise serializers.ValidationError(
                {
                    "car": "No available inventory"
                    " for this car on the selected dates."
                }
            )

        validated_data["price_per_day"] = car.daily_rate
        validated_data["user"] = self.context["request"].user

        return super().create(validated_data)


class RentalReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = ["actual_return_date"]

    def validate(self, attrs):
        rental = self.instance
        if rental.status != Rental.Status.BOOKED:
            raise serializers.ValidationError(
                "Only BOOKED rentals can be returned."
            )
        return attrs

    def update(self, instance, validated_data):
        today = date.today()
        instance.actual_return_date = today
        instance.status = (
            Rental.Status.OVERDUE
            if today > instance.end_date
            else Rental.Status.COMPLETED
        )
        instance.save()
        return instance


class RentalCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = []

    def validate(self, attrs):
        rental = self.instance
        if rental.status != Rental.Status.BOOKED:
            raise serializers.ValidationError(
                "Only BOOKED rentals can be cancelled."
            )
        return attrs

    def update(self, instance, validated_data):
        instance.status = Rental.Status.CANCELLED
        instance.save()
        return instance
