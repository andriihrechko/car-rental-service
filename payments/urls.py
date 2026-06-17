from django.urls import path

from payments.views import (
    PaymentCancelView,
    PaymentListView,
    PaymentRetrieveView,
    PaymentSuccessView,
    StripeWebhookView,
)


app_name = "payments"

urlpatterns = [
    path("success/", PaymentSuccessView.as_view(), name="success"),
    path("cancel/", PaymentCancelView.as_view(), name="cancel"),
    path("webhook/", StripeWebhookView.as_view(), name="webhook"),
    path("", PaymentListView.as_view(), name="list"),
    path("<int:pk>/", PaymentRetrieveView.as_view(), name="retrieve"),
]
