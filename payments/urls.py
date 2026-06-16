from django.urls import path

from payments.views import (
    PaymentCancelView,
    PaymentCreateView,
    PaymentDetailView,
    PaymentsListView,
    PaymentSuccessView,
    StripeWebhookView,
)


app_name = "payments"

urlpatterns = [
    path("", PaymentsListView.as_view(), name="payment-list"),
    path("create/", PaymentCreateView.as_view(), name="payment-create"),
    path("success/", PaymentSuccessView.as_view(), name="payment-success"),
    path("cancel/", PaymentCancelView.as_view(), name="payment-cancel"),
    path("webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("<int:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
]
