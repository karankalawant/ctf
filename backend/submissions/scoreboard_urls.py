from django.urls import path
from .scoreboard_views import user_scoreboard, team_scoreboard, score_over_time

urlpatterns = [
    path('users/', user_scoreboard),
    path('teams/', team_scoreboard),
    path('timeline/', score_over_time),
]
