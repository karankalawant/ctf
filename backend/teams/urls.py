from django.urls import path
from . import views

urlpatterns = [
    path('', views.team_list),
    path('create/', views.team_create),
    path('join/', views.team_join),
    path('leave/', views.team_leave),
    path('my/', views.my_team),
    path('<int:pk>/', views.team_detail),
]
