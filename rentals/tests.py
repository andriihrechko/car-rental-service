from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cars.models import Car
from rentals.models import Rental

User = get_user_model()


def sample_car(**kwargs):
    defaults = {
        "brand": "Toyota",
        "model": "Camry",
        "year": 2022,
        "fuel_type": "GAS",
        "daily_rate": "50.00",
        "inventory": 5,
    }
    defaults.update(kwargs)
    return Car.objects.create(**defaults)


def sample_user(**kwargs):
    defaults = {"email": "user@test.com", "password": "pass1234"}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


class RentalAPITests(APITestCase):
    def setUp(self):
        self.user = sample_user()
        self.client.force_authenticate(self.user)
        self.car = sample_car()
        self.today = date.today()

    def _create_rental(self, **kwargs):
        defaults = {
            "car": self.car.pk,
            "start_date": self.today,
            "end_date": self.today + timedelta(days=3),
        }
        defaults.update(kwargs)
        url = reverse("rental-list")
        return self.client.post(url, defaults)

    def test_create_rental_success(self):
        res = self._create_rental()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rental.objects.count(), 1)
        self.car.refresh_from_db()
        self.assertEqual(self.car.inventory, 4)

    def test_create_rental_invalid_dates(self):
        res = self._create_rental(
            start_date=self.today + timedelta(days=5),
            end_date=self.today,
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rental_no_inventory(self):
        self.car.inventory = 0
        self.car.save()
        res = self._create_rental()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_rental(self):
        self._create_rental()
        rental = Rental.objects.first()
        url = reverse("rental-return-rental", args=[rental.pk])
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        rental.refresh_from_db()
        self.assertEqual(rental.status, Rental.Status.COMPLETED)
        self.car.refresh_from_db()
        self.assertEqual(self.car.inventory, 5)

    def test_cancel_rental(self):
        self._create_rental()
        rental = Rental.objects.first()
        url = reverse("rental-cancel-rental", args=[rental.pk])
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        rental.refresh_from_db()
        self.assertEqual(rental.status, Rental.Status.CANCELLED)

    def test_list_rentals_only_own(self):
        self._create_rental()
        other = sample_user(email="other@test.com")
        self.client.force_authenticate(other)
        res = self.client.get(reverse("rental-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)
