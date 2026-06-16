import stripe

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.models import Payment
from payments.serializers import PaymentSerializer, PaymentCreateSerializer
from payments.services import create_rental_payment


class PaymentsListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()


class PaymentCreateView(generics.CreateAPIView):
    serializer_class = PaymentCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rental = serializer.validated_data['rental']
        success_url = request.build_absolute_uri(
            reverse("payments:payment-success")
        )
        success_url = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.build_absolute_uri(
            reverse("payments:payment-cancel")
        )

        try:
            payment = create_rental_payment(
                rental,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_409_CONFLICT,
            )
        output_serializer = PaymentSerializer(payment)

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class PaymentSuccessView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(
            {
                "detail": (
                    "Payment success redirect received. "
                    "The payment status is confirmed by webhook."
                )
            }
        )


class PaymentCancelView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(
            {
                "detail": (
                    "Payment was cancelled or paused. "
                    "You can use the checkout session while it is active."
                )
            }
        )


class StripeWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            session_id = session["id"]

            try:
                payment = Payment.objects.get(session_id=session_id)
            except Payment.DoesNotExist:
                return HttpResponse(status=404)

            if payment.status != Payment.Status.PAID:
                payment.status = Payment.Status.PAID
                payment.save(update_fields=["status"])

        return HttpResponse(status=200)

