from django.urls import path

from payments.views import PaymentCancelView, PaymentSuccessView


app_name = "payments"

urlpatterns = [
    path("success/", PaymentSuccessView.as_view(), name="success"),
    path("cancel/", PaymentCancelView.as_view(), name="cancel"),
]
