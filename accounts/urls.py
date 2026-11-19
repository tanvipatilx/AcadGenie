from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView, ProfileView,
    register_html, login_html, logout_html, profile_html,
)

urlpatterns = [
    # JWT / REST API
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='login-refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),

    # HTML / session
    path('html/register/', register_html, name='register_html'),
    path('html/login/', login_html, name='login_html'),
    path('html/logout/', logout_html, name='logout_html'),
    path('html/profile/', profile_html, name='profile_html'),
]