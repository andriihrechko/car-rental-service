from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import SignUpView, UserMeView


app_name = "users"

urlpatterns = [
    path("users/", SignUpView.as_view(), name="signup"),
    path("users/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("users/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/me/", UserMeView.as_view(), name="me"),
]
