from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rentals.views import RentalViewSet


app_name = "rentals"

router = DefaultRouter()
router.register("rentals", RentalViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
