from django.urls import path

from .views import generate_game, health

urlpatterns = [
    path("health/", health, name="health"),
    path("games/generate/", generate_game, name="generate-game"),
]
