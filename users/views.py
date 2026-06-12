from rest_framework import generics

from .serializers import SignUpSerializer, UserMeSerializer


class SignUpView(generics.CreateAPIView):
    """
    Create a new user in the system with email and password.
    First name and last name are optional.
    """
    serializer_class = SignUpSerializer
    authentication_classes = ()
    permission_classes = ()


class UserMeView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update the authenticated user.
    """
    serializer_class = UserMeSerializer

    def get_object(self):
        return self.request.user
