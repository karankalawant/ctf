from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/challenges/', include('challenges.urls')),
    path('api/teams/', include('teams.urls')),
    path('api/submissions/', include('submissions.urls')),
    path('api/scoreboard/', include('submissions.scoreboard_urls')),
]
