from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers

from cars.views import CarViewSet
from payments.views import PaymentViewSet
from rentals.views import RentalViewSet


router = routers.DefaultRouter()
router.register("cars", CarViewSet)
router.register("rentals", RentalViewSet)
router.register("payments", PaymentViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/service/users/", include("users.urls", namespace="users")),
    path("api/service/", include(router.urls)),
    path(
        "api/service/payments/", include("payments.urls", namespace="payments")
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger",
    ),
]

if settings.DEBUG:
    urlpatterns += debug_toolbar_urls()
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
