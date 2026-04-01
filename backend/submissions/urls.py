from django.urls import path
from . import views

urlpatterns = [
    path('<int:challenge_id>/submit/', views.submit_flag),
    path('my/', views.my_submissions),
]
