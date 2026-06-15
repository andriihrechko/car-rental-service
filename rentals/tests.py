from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from cars.models import Car
from rentals.models import Rental


@pytest.fixture
def car(db):
    return Car.objects.create(
        brand="Toyota",
        model="Camry",
        year=2022,
        fuel_type="GAS",
        daily_rate="50.00",
        inventory=5,
    )


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        email="user@test.com",
        password="pass1234",
    )


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def api_client(user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def rental_data(car):
    today = date.today()
    return {
        "car": car.pk,
        "start_date": today,
        "end_date": today + timedelta(days=3),
    }


def test_create_rental_success(api_client, car, rental_data):
    res = api_client.post(reverse("rental-list"), rental_data)
    assert res.status_code == status.HTTP_201_CREATED
    assert Rental.objects.count() == 1
    car.refresh_from_db()
    assert car.inventory == 4


def test_create_rental_invalid_dates(api_client, car):
    today = date.today()
    data = {
        "car": car.pk,
        "start_date": today + timedelta(days=5),
        "end_date": today,
    }
    res = api_client.post(reverse("rental-list"), data)
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_create_rental_no_inventory(api_client, car, rental_data):
    car.inventory = 0
    car.save()
    res = api_client.post(reverse("rental-list"), rental_data)
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_return_rental(api_client, car, rental_data):
    api_client.post(reverse("rental-list"), rental_data)
    rental = Rental.objects.first()
    res = api_client.post(reverse("rental-return-rental", args=[rental.pk]))
    assert res.status_code == status.HTTP_200_OK
    rental.refresh_from_db()
    assert rental.status == Rental.Status.COMPLETED
    car.refresh_from_db()
    assert car.inventory == 5


def test_cancel_rental(api_client, car, rental_data):
    api_client.post(reverse("rental-list"), rental_data)
    rental = Rental.objects.first()
    res = api_client.post(reverse("rental-cancel-rental", args=[rental.pk]))
    assert res.status_code == status.HTTP_200_OK
    rental.refresh_from_db()
    assert rental.status == Rental.Status.CANCELLED


def test_list_rentals_only_own(api_client, car, rental_data, django_user_model):
    api_client.post(reverse("rental-list"), rental_data)
    other = django_user_model.objects.create_user(
        email="other@test.com", password="pass1234"
    )
    from rest_framework.test import APIClient
    other_client = APIClient()
    other_client.force_authenticate(user=other)
    res = other_client.get(reverse("rental-list"))
    assert res.status_code == status.HTTP_200_OK
    assert len(res.data) == 0