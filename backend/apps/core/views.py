import json
import random
import re
from dataclasses import dataclass

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
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


def _cpp_identifier(value: str) -> str:
    identifier = re.sub(r"[^0-9a-zA-Z_]+", "_", value.strip().lower()).strip("_")
    if not identifier:
        return "topic"
    if identifier[0].isdigit():
        return f"topic_{identifier}"
    return identifier


def _build_task(
    topic: str,
    emphasize: str,
    problem_type: str,
    index: int,
    rng: random.Random,
    correct_label_offset: int,
) -> dict:
    topic_identifier = _cpp_identifier(topic)
    labels = ["A", "B", "C"]
    spec = (
        f"A function named `check_{topic_identifier}_{index}` should verify a {topic} "
        f"requirement while emphasizing {emphasize}."
    )
    candidates = [
        {
            "is_correct": True,
            "code": (
                f"bool check_{topic_identifier}_{index}() {{\n"
                f"    return true; // handles the core {topic} idea\n"
                "}"
            ),
        },
        {
            "is_correct": False,
            "code": (
                f"bool check_{topic_identifier}_{index}() {{\n"
                f"    return false; // misses the {emphasize} requirement\n"
                "}"
            ),
        },
        {
            "is_correct": False,
            "code": (
                f"bool check_{topic_identifier}_{index}() {{\n"
                f"    return {len(topic)} > 3; // unrelated shortcut\n"
                "}"
            ),
        },
    ]
    distractors = [candidate for candidate in candidates if not candidate["is_correct"]]
    rng.shuffle(distractors)

    correct_position = (index + correct_label_offset) % len(labels)
    ordered_candidates = list(distractors)
    ordered_candidates.insert(correct_position, candidates[0])

    candidate_solutions = []
    correct_solution_id = labels[correct_position]
    for label, candidate in zip(labels, ordered_candidates, strict=True):
        candidate_solutions.append(
            {
                "id": label,
                "label": f"Solution {label}",
                "code": candidate["code"],
            }
        )

    return {
        "id": f"task-{index + 1}",
        "prompt": f"Does the best solution satisfy the {problem_type}?",
        "specifications": spec,
        "candidate_solutions": candidate_solutions,
        "correct_solution_id": correct_solution_id,
        "explanation": (
            f"Solution {correct_solution_id} matches the {topic} specification "
            "and respects the "
            f"emphasis on {emphasize}."
        ),
    }


@csrf_exempt
@require_POST
def generate_game(_request: HttpRequest) -> JsonResponse:
    settings = _parse_settings(_request)
    rng = random.Random("|".join(settings.cover_topics + settings.emphasize_topics))

    tasks: list[dict] = []
    correct_label_offset = rng.randrange(3)
    for index in range(5):
        topic = settings.cover_topics[index % len(settings.cover_topics)]
        emphasize = settings.emphasize_topics[index % len(settings.emphasize_topics)]
        problem_type = settings.problem_types[index % len(settings.problem_types)]
        tasks.append(
            _build_task(
                topic,
                emphasize,
                problem_type,
                index,
                rng,
                correct_label_offset,
            )
        )

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
