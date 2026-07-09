import json
import random
from dataclasses import dataclass

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST


def health(_request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "status": "ok",
            "service": "VerifyMVP API",
            "database": "postgresql",
        }
    )


@dataclass(frozen=True)
class GameSettings:
    cover_topics: list[str]
    emphasize_topics: list[str]
    problem_types: list[str]


CS1_DEFAULT_TOPICS = [
    "variables",
    "conditionals",
    "loops",
    "functions",
    "arrays",
    "strings",
]


def _normalize_items(values: object, fallback: list[str]) -> list[str]:
    if not isinstance(values, list):
        return fallback

    items = [str(item).strip() for item in values if str(item).strip()]
    return items or fallback


def _parse_settings(request: HttpRequest) -> GameSettings:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    return GameSettings(
        cover_topics=_normalize_items(payload.get("cover_topics"), CS1_DEFAULT_TOPICS),
        emphasize_topics=_normalize_items(
            payload.get("emphasize_topics"), ["conditionals"]
        ),
        problem_types=_normalize_items(
            payload.get("problem_types"),
            ["solution comparison", "specification checking"],
        ),
    )


def _build_task(topic: str, emphasize: str, problem_type: str, index: int) -> dict:
    spec = (
        f"A function named `check_{topic}_{index}` should verify a {topic} "
        f"requirement while emphasizing {emphasize}."
    )
    candidate_solutions = [
        {
            "id": "A",
            "label": "Solution A",
            "code": (
                f"def check_{topic}_{index}():\n"
                f"    return True  # handles the core {topic} idea"
            ),
        },
        {
            "id": "B",
            "label": "Solution B",
            "code": (
                f"def check_{topic}_{index}():\n"
                f"    return False  # misses the {emphasize} requirement"
            ),
        },
        {
            "id": "C",
            "label": "Solution C",
            "code": (
                f"def check_{topic}_{index}():\n"
                f"    return len('{topic}') > 3  # unrelated shortcut"
            ),
        },
    ]

    return {
        "id": f"task-{index + 1}",
        "prompt": f"Does the best solution satisfy the {problem_type}?",
        "specifications": spec,
        "candidate_solutions": candidate_solutions,
        "correct_solution_id": "A",
        "explanation": (
            f"Solution A matches the {topic} specification and respects the "
            f"emphasis on {emphasize}."
        ),
    }


@require_POST
def generate_game(_request: HttpRequest) -> JsonResponse:
    settings = _parse_settings(_request)
    rng = random.Random("|".join(settings.cover_topics + settings.emphasize_topics))

    tasks: list[dict] = []
    for index in range(5):
        topic = settings.cover_topics[index % len(settings.cover_topics)]
        emphasize = settings.emphasize_topics[index % len(settings.emphasize_topics)]
        problem_type = settings.problem_types[index % len(settings.problem_types)]
        tasks.append(_build_task(topic, emphasize, problem_type, index))

    rng.shuffle(tasks)

    return JsonResponse(
        {
            "settings": {
                "cover_topics": settings.cover_topics,
                "emphasize_topics": settings.emphasize_topics,
                "problem_types": settings.problem_types,
            },
            "game": {
                "title": "CS1 Solution Spotlight",
                "tasks": tasks,
                "scoring": {
                    "correctness_points": 100,
                    "time_bonus_points": 25,
                    "fast_answer_threshold_ms": 8000,
                },
            },
        }
    )
