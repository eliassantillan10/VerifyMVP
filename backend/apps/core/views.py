import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.core.game_generation import build_game_response, normalize_settings_payload


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
