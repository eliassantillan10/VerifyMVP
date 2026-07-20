# ruff: noqa: E501
"""Safe Case Breaker challenge generation and grading.

The local Llama service can author wording, but it never supplies executable
logic or decides whether a player's test breaks the code.  Those decisions are
made by the small, allowlisted evaluators in this module.
"""

from __future__ import annotations

import json
import os
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.core import signing

from apps.core.game_generation import TOPIC_LABELS

TOKEN_SALT = "case-breaker.challenge"
TOKEN_MAX_AGE_SECONDS = 60 * 30
MAX_TEST_CASE_FIELDS = 8
MAX_ABS_VALUE = 1_000_000


@dataclass(frozen=True)
class InputField:
    name: str
    label: str
    description: str


@dataclass(frozen=True)
class ChallengeTemplate:
    id: str
    topic: str
    specification: str
    code: str
    fields: tuple[InputField, ...]
    expected: Callable[[dict[str, int]], bool]
    buggy: Callable[[dict[str, int]], bool]
    hints: tuple[str, ...]
    explanation: str


def _range_expected(values: dict[str, int]) -> bool:
    return values["low"] <= values["value"] <= values["high"]


def _range_buggy(values: dict[str, int]) -> bool:
    return values["value"] >= values["low"] or values["value"] <= values["high"]


def _exclusive_expected(values: dict[str, int]) -> bool:
    return values["value"] > values["low"] and values["value"] < values["high"]


def _exclusive_buggy(values: dict[str, int]) -> bool:
    return values["value"] >= values["low"] and values["value"] <= values["high"]


RANGE_FIELDS = (
    InputField("value", "Value", "The value to check."),
    InputField("low", "Lower bound", "The lowest allowed value."),
    InputField("high", "Upper bound", "The highest allowed value."),
)

TEMPLATES: dict[str, tuple[ChallengeTemplate, ...]] = {
    "if": (
        ChallengeTemplate(
            id="if-inclusive-range",
            topic="if",
            specification="Return true only when value is inside the inclusive range [low, high].",
            code=(
                "bool isAllowed(int value, int low, int high) {\n"
                "    if (value >= low || value <= high) {\n"
                "        return true;\n"
                "    }\n"
                "    return false;\n"
                "}"
            ),
            fields=RANGE_FIELDS,
            expected=_range_expected,
            buggy=_range_buggy,
            hints=(
                "Try a value that is outside one of the two bounds.",
                "Ask whether satisfying just one comparison should be enough.",
            ),
            explanation="The condition uses ||, so any value that passes either bound is accepted. The specification requires both bounds to hold.",
        ),
    ),
    "else-if": (
        ChallengeTemplate(
            id="else-if-exclusive-range",
            topic="else-if",
            specification="Return true only when value is strictly between low and high.",
            code=(
                "bool isMiddle(int value, int low, int high) {\n"
                "    if (value <= low) return false;\n"
                "    else if (value <= high) return true;\n"
                "    return false;\n"
                "}"
            ),
            fields=RANGE_FIELDS,
            expected=_exclusive_expected,
            buggy=lambda values: values["value"] > values["low"] and values["value"] <= values["high"],
            hints=("Check the exact boundary values.", "The second branch includes one endpoint that the specification excludes."),
            explanation="The upper boundary is accepted because the second condition uses <=. A strict range must reject both endpoints.",
        ),
    ),
}


def _alias_template(topic: str) -> ChallengeTemplate:
    """Give every selectable topic a valid logical-error challenge at launch.

    The displayed wording names the selected taught topic while a later content
    pass can replace aliases with richer topic-specific evaluator families.
    """
    base = TEMPLATES["if"][0]
    label = TOPIC_LABELS[topic]
    return ChallengeTemplate(
        id=f"{topic}-range-guard",
        topic=topic,
        specification=(
            f"In this {label} exercise, return true only when value is inside "
            "the inclusive range [low, high]."
        ),
        code=base.code.replace("isAllowed", f"check_{topic.replace('-', '_')}_range"),
        fields=base.fields,
        expected=base.expected,
        buggy=base.buggy,
        hints=base.hints,
        explanation=(
            f"This {label} implementation accepts a value when either boundary "
            "passes. The specification requires both boundaries to pass."
        ),
    )


def select_template(
    topics: list[str], learner_profile: object | None = None
) -> ChallengeTemplate:
    supported = [topic for topic in topics if topic in TOPIC_LABELS]
    if not supported:
        raise ValueError("Select at least one supported topic to cover.")
    topic = secrets.SystemRandom().choices(
        supported, weights=[_topic_weight(topic, learner_profile) for topic in supported]
    )[0]
    return secrets.choice(TEMPLATES.get(topic, (_alias_template(topic),)))


def _token_payload(template: ChallengeTemplate) -> dict[str, str]:
    return {"challenge_id": template.id, "topic": template.topic, "nonce": secrets.token_urlsafe(8)}


def issue_challenge(learner_profile: object | None = None) -> dict[str, Any]:
    template = select_template(list(TOPIC_LABELS), learner_profile)
    authored = _author_copy(template)
    token = signing.dumps(_token_payload(template), salt=TOKEN_SALT, compress=True)
    return {
        "challenge_token": token,
        "topic": template.topic,
        "topic_label": TOPIC_LABELS[template.topic],
        "specification": authored.get("specification", template.specification),
        "prompt": authored.get("prompt", "Find one concrete input that proves this code violates the specification."),
        "code": template.code,
        "input_schema": [field.__dict__ for field in template.fields],
    }


def grade_challenge(token: object, test_case: object) -> dict[str, Any]:
    if not isinstance(token, str):
        raise ValueError("A challenge token is required.")
    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE_SECONDS)
    except signing.BadSignature as error:
        raise ValueError("This challenge has expired. Generate a new one.") from error
    if not isinstance(payload, dict):
        raise ValueError("This challenge token is invalid.")

    template = _template_for(str(payload.get("challenge_id", "")), str(payload.get("topic", "")))
    values = _validate_test_case(test_case, template.fields)
    is_breaking = template.expected(values) != template.buggy(values)
    if is_breaking:
        return {
            "is_breaking": True,
            "expected_output": template.expected(values),
            "actual_output": template.buggy(values),
            "explanation": template.explanation,
        }
    return {
        "is_breaking": False,
        "hint": template.hints[0],
        "feedback": "That input behaves the same in the specification and the buggy code. Try another case.",
    }


def _template_for(challenge_id: str, topic: str) -> ChallengeTemplate:
    for template in TEMPLATES.get(topic, ()):  # dedicated templates first
        if template.id == challenge_id:
            return template
    if topic in TOPIC_LABELS and challenge_id == f"{topic}-range-guard":
        return _alias_template(topic)
    raise ValueError("This challenge token is invalid.")


def _topic_weight(topic: str, learner_profile: object | None) -> int:
    if not isinstance(learner_profile, dict):
        return 1
    stats = learner_profile.get(topic)
    if not isinstance(stats, dict):
        return 2
    attempts, passes = stats.get("attempts"), stats.get("passes")
    if (
        isinstance(attempts, bool)
        or isinstance(passes, bool)
        or not isinstance(attempts, int)
        or not isinstance(passes, int)
    ):
        return 1
    return max(1, min(5, attempts - passes + 1))


def _validate_test_case(test_case: object, fields: tuple[InputField, ...]) -> dict[str, int]:
    if not isinstance(test_case, dict) or len(test_case) > MAX_TEST_CASE_FIELDS:
        raise ValueError("Enter values for every test-case field.")
    values: dict[str, int] = {}
    for field in fields:
        value = test_case.get(field.name)
        if isinstance(value, bool) or not isinstance(value, int) or abs(value) > MAX_ABS_VALUE:
            raise ValueError(f"{field.label} must be an integer between -{MAX_ABS_VALUE} and {MAX_ABS_VALUE}.")
        values[field.name] = value
    return values


def _author_copy(template: ChallengeTemplate) -> dict[str, str]:
    """Ask the local model for optional copy, with a safe deterministic fallback."""
    if os.getenv("CASE_BREAKER_LLM_ENABLED", "false").lower() != "true":
        return {}
    body = {
        "model": os.getenv("CASE_BREAKER_LLM_MODEL", "llama3.2:3b-instruct-q4_K_M"),
        "stream": False,
        "format": {"type": "object", "properties": {"prompt": {"type": "string"}, "specification": {"type": "string"}}, "required": ["prompt", "specification"]},
        "options": {"temperature": 0.4, "num_predict": 120},
        "prompt": (
            "Write concise, student-friendly copy for a C++ Case Breaker challenge. "
            "Do not reveal a hint, test case, expected output, or explanation. "
            f"Topic: {TOPIC_LABELS[template.topic]}. Specification: {template.specification}"
        ),
    }
    endpoint = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/") + "/api/generate"
    request = Request(endpoint, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=5) as response:  # nosec B310: endpoint is configured by deployment
            payload = json.loads(response.read().decode())
        authored = json.loads(payload.get("response", "{}"))
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(authored, dict):
        return {}
    return {
        key: value.strip()
        for key in ("prompt", "specification")
        if isinstance((value := authored.get(key)), str) and 0 < len(value.strip()) <= 500
    }
