import json

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.core.case_breaker import issue_challenge
from apps.core.coach import ask_coach
from apps.core.game_generation import build_game_response, normalize_settings_payload
from apps.core.lm_studio import LMStudioUnavailable, grade_test_case
from apps.core.models import Problem


def health(_request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "status": "ok",
            "service": "VerifyMVP API",
            "database": "postgresql",
        }
    )


def _parse_payload(request: HttpRequest) -> dict:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}

    return payload if isinstance(payload, dict) else {}


@csrf_exempt
@require_POST
def generate_game(_request: HttpRequest) -> JsonResponse:
    try:
        settings = normalize_settings_payload(_parse_payload(_request))
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)

    return JsonResponse(build_game_response(settings))


@csrf_exempt
@require_POST
def case_breaker_challenge(request: HttpRequest) -> JsonResponse:
    try:
        challenge = issue_challenge()
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse(
        {
            "challenge": challenge,
            "coachEnabled": settings.CASE_BREAKER_COACH_ENABLED,
            "gradingEnabled": settings.CASE_BREAKER_GRADING_ENABLED,
        }
    )


@csrf_exempt
@require_POST
def case_breaker_grade(request: HttpRequest) -> JsonResponse:
    if not settings.CASE_BREAKER_GRADING_ENABLED:
        return JsonResponse(
            {"error": "Case Breaker grading is not enabled."}, status=503
        )
    payload = _parse_payload(request)
    challenge_id = payload.get("challengeId")
    test_case = payload.get("testCase")
    if (
        not isinstance(challenge_id, str)
        or not isinstance(test_case, str)
        or not test_case.strip()
        or len(test_case) > settings.CASE_BREAKER_GRADING_MAX_INPUT_CHARS
    ):
        return JsonResponse({"error": "Invalid grading request."}, status=400)
    try:
        problem = Problem.objects.get(slug=challenge_id)
    except Problem.DoesNotExist:
        return JsonResponse({"error": "Case Breaker problem not found."}, status=404)
    try:
        grade = grade_test_case(problem, test_case.strip())
    except LMStudioUnavailable:
        return JsonResponse(
            {
                "error": (
                    "The required local LM Studio grader is unavailable. "
                    "Check that its server and configured model are running, "
                    "then retry."
                )
            },
            status=503,
        )
    return JsonResponse({"grade": {"challengeId": problem.slug, **grade}})


@csrf_exempt
@require_POST
def case_breaker_coach(request: HttpRequest) -> JsonResponse:
    if not settings.CASE_BREAKER_COACH_ENABLED:
        return JsonResponse({"error": "Case Breaker coach is not enabled."}, status=503)
    payload = _parse_payload(request)
    challenge_id = payload.get("challengeId")
    mode = payload.get("mode")
    learner_text = payload.get("learnerText", "")
    if (
        not isinstance(challenge_id, str)
        or not isinstance(mode, str)
        or mode not in {"HINT", "EXPLAIN", "REVIEW"}
        or not isinstance(learner_text, str)
        or len(learner_text) > settings.CASE_BREAKER_COACH_MAX_INPUT_CHARS
        or (mode == "REVIEW" and not learner_text.strip())
    ):
        return JsonResponse({"error": "Invalid coach request."}, status=400)
    try:
        problem = Problem.objects.get(slug=challenge_id)
    except Problem.DoesNotExist:
        return JsonResponse({"error": "Case Breaker problem not found."}, status=404)
    try:
        reply = ask_coach(problem, mode, learner_text.strip())
    except LMStudioUnavailable:
        return JsonResponse({"error": "Case Breaker coach is unavailable."}, status=503)
    return JsonResponse(
        {"coach": {"challengeId": problem.slug, "mode": mode, "message": reply}}
    )
