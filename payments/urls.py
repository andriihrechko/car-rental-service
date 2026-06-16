from django.urls import path

from payments.views import (
    PaymentCancelView,
    PaymentSuccessView,
    StripeWebhookView,
)


app_name = "payments"

urlpatterns = [
    path("success/", PaymentSuccessView.as_view(), name="success"),
    path("cancel/", PaymentCancelView.as_view(), name="cancel"),
    path("webhook/", StripeWebhookView.as_view(), name="webhook"),
]
