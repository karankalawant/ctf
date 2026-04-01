from django.urls import path
from . import views

urlpatterns = [
    path('', views.challenge_list),
    path('categories/', views.category_list),
    path('event/', views.event_detail),
    path('hints/<int:hint_id>/unlock/', views.unlock_hint),
    path('admin/', views.admin_challenge_list),
    path('admin/<int:pk>/', views.admin_challenge_detail),
    path('<int:pk>/', views.challenge_detail),
]
