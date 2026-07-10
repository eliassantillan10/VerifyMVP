# Bugfix Plan: Randomized C++ Game Generation and Seconds Feedback

## Overview

Fix the student game generated from teacher selections so answer labels are not
predictable, generated snippets teach C++, and answer feedback reports elapsed
time in seconds instead of raw milliseconds.

## Reported Scenario

- Cover topics: `variables`
- Emphasize topics: `variables`
- Problem type: `solution comparison`

## Acceptance Criteria

- Correct answers vary across generated tasks and are not always `A`.
- Every `correct_solution_id` points to the semantically correct candidate.
- Candidate snippets use C++ function syntax, not Python.
- Feedback displays elapsed answer time in seconds.
- Scoring continues to use millisecond thresholds internally.

## Implementation Tasks

1. Update backend task generation in `backend/apps/core/views.py`.
2. Add backend regression coverage in `backend/apps/core/tests.py`.
3. Update frontend feedback formatting in `frontend/src/App.tsx`.
4. Add frontend coverage in `frontend/src/App.test.tsx`.

## Validation

- `docker compose build backend`
- `docker compose run --rm backend ruff check .`
- `docker compose run --rm backend python manage.py check`
- `docker compose run --rm backend pytest`
- `npm run lint`
- `npm run typecheck`
- `npm test -- --run`
- `npm run build`
