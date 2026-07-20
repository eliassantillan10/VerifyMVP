from django.urls import path

from .views import case_breaker_challenge, case_breaker_grade, generate_game, health

urlpatterns = [
    path("health/", health, name="health"),
    path("games/generate/", generate_game, name="generate-game"),
    path(
        "case-breaker/challenges/",
        case_breaker_challenge,
        name="case-breaker-challenge",
    ),
    path("case-breaker/grade/", case_breaker_grade, name="case-breaker-grade"),
]
