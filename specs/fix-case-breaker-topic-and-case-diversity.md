# Implementation Plan: Database-backed Case Breaker Catalog

## Decision

Use the reviewed 280-problem catalog as database seed data. Case Breaker is a
display-only C++ review experience: it selects a problem, shows its topic,
description, and code, and does not execute or automatically grade C++.

## Implementation

- Create the `Problem` model with deterministic catalog IDs and source order.
- Seed all 14 topics and 280 problems in a self-contained Django data
  migration so clean CI and Docker databases need no source JSON file.
- Return a display-only challenge from `POST /api/case-breaker/challenges/`.
- Return `410 Gone` from the retired grade endpoint.
- Remove test-input, hint, feedback, and progress UI from the frontend.
- Remove both JSON catalog files after the migration captures the content.

## Verification

```bash
cd backend && ruff check . && python manage.py check && pytest
cd frontend && npm run lint && npm run typecheck && npm test -- --run && npm run build
docker compose build
```
