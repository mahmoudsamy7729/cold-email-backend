from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("profile-overview/", views.ProfileView.as_view(), name="profile"),
    path("token/refresh/", views.RefreshTokenView.as_view(), name="refresh-token"),
]
