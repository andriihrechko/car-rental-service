import stripe
from django.conf import settings
from django.http import HttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.tasks import send_payment_notification
from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Payment.objects.select_related("rental")
    serializer_class = PaymentSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(rental__user=self.request.user)


class PaymentSuccessView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"detail": "Stripe session_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            Payment.objects.filter(session_id=session_id).update(
                status=Payment.Status.PAID
            )

        return Response(
            {
                "detail": (
                    "Payment success redirect received. "
                    "The payment status is confirmed by Stripe."
                ),
                "payment_status": session.payment_status,
            }
        )


class PaymentCancelView(APIView):
    authentication_classes = []
    permission_classes = []

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
    permission_classes = [AllowAny]

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
            payment = Payment.objects.get(session_id=session["id"])
            payment.status = Payment.Status.PAID
            payment.save()

            send_payment_notification.delay(payment.id)

        return HttpResponse(status=200)
