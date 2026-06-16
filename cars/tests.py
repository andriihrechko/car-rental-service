from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cars.models import Car


User = get_user_model()

CAR_LIST_URL = reverse("car-list")


def car_detail_url(car_id):
    return reverse("car-detail", args=[car_id])


def create_car(**kwargs):
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


class UnauthenticatedCarApiTests(APITestCase):
    """Tests for unauthenticated requests."""

    def test_auth_required(self):
        res = self.client.get(CAR_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCarApiTests(APITestCase):
    """Tests for authenticated regular users."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

    def test_list_cars(self):
        create_car()
        create_car(brand="Honda", model="Civic")
        res = self.client.get(CAR_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_retrieve_car(self):
        car = create_car()
        url = car_detail_url(car.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["brand"], car.brand)

    def test_create_car_forbidden(self):
        payload = {
            "brand": "Toyota",
            "model": "Camry",
            "year": 2022,
            "fuel_type": "GAS",
            "daily_rate": "50.00",
            "inventory": 5,
        }
        res = self.client.post(CAR_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_brand(self):
        create_car(brand="Toyota")
        create_car(brand="Honda")
        res = self.client.get(CAR_LIST_URL, {"brand": "Toyota"})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["brand"], "Toyota")

    def test_filter_by_fuel_type(self):
        create_car(fuel_type="GAS")
        create_car(fuel_type="ELECTRIC")
        res = self.client.get(CAR_LIST_URL, {"fuel_type": "GAS"})
        self.assertEqual(len(res.data), 1)

    def test_filter_by_min_year(self):
        create_car(year=2020)
        create_car(year=2022)
        res = self.client.get(CAR_LIST_URL, {"min_year": 2021})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["year"], 2022)

    def test_filter_by_max_year(self):
        create_car(year=2020)
        create_car(year=2022)
        res = self.client.get(CAR_LIST_URL, {"max_year": 2021})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["year"], 2020)

    def test_filter_available_cars(self):
        create_car(inventory=5)
        create_car(inventory=0)
        res = self.client.get(CAR_LIST_URL, {"is_available": True})
        self.assertEqual(len(res.data), 1)


class StaffCarApiTests(APITestCase):
    """Tests for staff users."""

    def setUp(self):
        self.staff = User.objects.create_user(
            email="staff@test.com",
            password="testpass123",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.staff)

    def test_create_car(self):
        payload = {
            "brand": "Toyota",
            "model": "Camry",
            "year": 2022,
            "fuel_type": "GAS",
            "daily_rate": "50.00",
            "inventory": 5,
        }
        res = self.client.post(CAR_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Car.objects.count(), 1)

    def test_update_car(self):
        car = create_car()
        url = car_detail_url(car.id)
        res = self.client.patch(url, {"brand": "Honda"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        car.refresh_from_db()
        self.assertEqual(car.brand, "Honda")

    def test_delete_car(self):
        car = create_car()
        url = car_detail_url(car.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Car.objects.filter(id=car.id).exists())

    def test_filter_available_with_single_inventory(self):
        Car.objects.create(
            brand="Ford",
            model="Focus",
            year=2020,
            fuel_type="GAS",
            daily_rate="30.00",
            inventory=1,
        )
        res = self.client.get(CAR_LIST_URL, {"is_available": "true"})
        self.assertEqual(len(res.data), 1)
