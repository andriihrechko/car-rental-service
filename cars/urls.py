from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cars.views import CarViewSet


app_name = "cars"

router = DefaultRouter()
router.register("cars", CarViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
