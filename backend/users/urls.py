from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.register),
    path('login/', views.login),
    path('logout/', views.logout_view),
    path('profile/', views.profile),
    path('users/', views.user_list),
    path('users/<str:username>/', views.user_detail),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-otp/', views.verify_otp),
]
