from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from cars.models import Car
from rentals.models import Rental


User = get_user_model()


class RentalAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass1234",
        )
        self.client.force_authenticate(user=self.user)

        self.car = Car.objects.create(
            brand="Toyota",
            model="Camry",
            year=2022,
            fuel_type="GAS",
            daily_rate="50.00",
            inventory=5,
        )

        self.today = date.today()
        self.rental_data = {
            "car": self.car.pk,
            "start_date": self.today,
            "end_date": self.today + timedelta(days=3),
        }

    def test_create_rental_success(self):
        res = self.client.post(
            reverse("rentals:rental-list"), self.rental_data
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rental.objects.count(), 1)

    def test_create_rental_invalid_dates(self):
        data = {
            "car": self.car.pk,
            "start_date": self.today + timedelta(days=5),
            "end_date": self.today,
        }
        res = self.client.post(reverse("rentals:rental-list"), data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rental_no_inventory(self):
        self.car.inventory = 0
        self.car.save()

        res = self.client.post(
            reverse("rentals:rental-list"), self.rental_data
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_rentals_only_own(self):
        self.client.post(reverse("rentals:rental-list"), self.rental_data)

        other_user = User.objects.create_user(
            email="other@test.com", password="pass1234"
        )
        other_client = APIClient()
        other_client.force_authenticate(user=other_user)

        res = other_client.get(reverse("rentals:rental-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)
