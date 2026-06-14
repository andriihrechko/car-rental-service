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

        if car.inventory < 1:
            raise serializers.ValidationError(
                {"car": "No inventory available for this car."}
            )

        overlapping = Rental.objects.filter(
            car=car,
            status__in=[Rental.Status.BOOKED, Rental.Status.OVERDUE],
            start_date__lte=validated_data["end_date"],
            end_date__gte=validated_data["start_date"],
        ).exists()
        if overlapping:
            raise serializers.ValidationError(
                {"car": "This car already has an overlapping rental."}
            )

        validated_data["price_per_day"] = car.daily_rate
        validated_data["user"] = self.context["request"].user

        car.inventory -= 1
        car.save(update_fields=["inventory"])

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
        instance.car.inventory += 1
        instance.car.save(update_fields=["inventory"])
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
        instance.car.inventory += 1
        instance.car.save(update_fields=["inventory"])
        instance.save()
        return instance
