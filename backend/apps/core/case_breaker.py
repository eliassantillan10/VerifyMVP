"""Issue display-only Case Breaker challenges from the reviewed database catalog."""

from __future__ import annotations

from typing import Any

from apps.core.models import Problem


def issue_challenge() -> dict[str, Any]:
    problem = Problem.objects.order_by("?").first()
    if problem is None:
        raise ValueError("No Case Breaker problems are available.")
    return {
        "id": problem.slug,
        "topic": problem.topic,
        "description": problem.description,
        "code": problem.code,
    }
