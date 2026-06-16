from rest_framework.response import Response
from rest_framework.views import APIView


class PaymentSuccessView(APIView):
    def get(self, request, *args, **kwargs):

        return Response(
            {
                "detail": (
                    "Payment success redirect received."
                    "The payment status is confirmed by webhook."
                )
            }
        )


class PaymentCancelView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(
            {
                "detail": (
                    "Payment was cancelled or paused."
                    "You can use the checkout session while it is active."
                )
            }
        )
