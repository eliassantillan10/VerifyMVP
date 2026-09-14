# Implementation Plan: Remove Current Case Breaker Problem Content

## Overview

Remove the current bundled Case Breaker catalog from source while preserving the Case Breaker storage system and application flow. Future problems can be added through the existing Django `Problem` model and database table.

## Scope

In scope:

- The deleted raw catalog file: `backend/problems.json`.
- The compressed 280-problem seed content in `backend/apps/core/migrations/0002_seed_problem_catalog.py`.
- Tests and narrow documentation statements that assume the bundled catalog exists.

Out of scope:

- Removing `Problem`, its table, or `0001_problem_catalog.py`.
- Removing Case Breaker challenge, grade, or coach routes.
- Removing the Case Breaker frontend, API client, or LM Studio integration.
- Retiring Case Breaker or returning `410 Gone` responses.
- Creating a replacement catalog or import workflow.

## Architecture Decision

Keep the database-backed `Problem` store empty after a clean install. The app's existing empty-catalog behavior is retained: `POST /api/case-breaker/challenges/` returns `400` with `{"error": "No Case Breaker problems are available."}` until new records are added.

## Migration Decision Gate

Before changing `0002_seed_problem_catalog.py`, determine whether it has ever been applied or shared outside this untracked local worktree.

- **Unshipped path:** delete `0002_seed_problem_catalog.py`; retain `0001_problem_catalog.py` and `migrations/__init__.py`. Fresh databases create an empty `core_problem` table.
- **Shared-history path:** retain the `0002` filename and dependencies but replace its body with a no-op migration. Remove the compressed payload, seed helpers, and `RunPython` operation. Do not drop the table or delete existing database rows.

The current worktree indicates the migrations are untracked, which supports but does not prove the unshipped path.

## Tasks

### Task 1: Confirm the migration path

**Description:** Determine whether the bundled seed migration is local-only or part of any shared migration history.

**Acceptance criteria:**

- [ ] The unshipped or shared-history path is recorded before changing migration files.
- [ ] The selected path preserves the empty `Problem` store for fresh databases.

**Verification:**

- [ ] Inspect migration history for every relevant environment.

**Dependencies:** None.

**Files likely touched:** `backend/apps/core/migrations/0002_seed_problem_catalog.py`.

### Task 2: Remove the bundled catalog content

**Description:** Keep `backend/problems.json` deleted and remove the 280-problem payload from the seed migration using the selected path.

**Acceptance criteria:**

- [ ] No raw JSON or compressed seed content for the current catalog remains in source.
- [ ] `Problem` and `0001_problem_catalog.py` remain intact.
- [ ] No table is dropped and no existing database rows are deleted by this task.

**Verification:**

- [ ] `rg -n "COMPRESSED_PROBLEMS|case-breaker-2026-07|The Case Breaker seed catalog must contain 280|backend/problems.json" backend frontend README.md specs` returns no active catalog content.

**Dependencies:** Task 1.

**Files likely touched:** `backend/problems.json`, `backend/apps/core/migrations/0002_seed_problem_catalog.py`.

### Task 3: Update backend tests for an empty store

**Description:** Remove seed-count assumptions while retaining coverage for the storage-backed Case Breaker flow.

**Acceptance criteria:**

- [ ] No test expects 280 pre-seeded records.
- [ ] A clean migrated test database has zero `Problem` records.
- [ ] Challenge empty-store behavior is covered.
- [ ] Coach tests create a `Problem` fixture explicitly rather than relying on seeded data.

**Verification:**

- [ ] `cd backend && python manage.py migrate --noinput`
- [ ] `cd backend && pytest`

**Dependencies:** Task 2.

**Files likely touched:** `backend/apps/core/tests.py`.

### Task 4: Update documentation narrowly

**Description:** Remove claims that the application ships the old 280-problem catalog, while retaining documentation that Case Breaker uses a database-backed store.

**Acceptance criteria:**

- [ ] Documentation states that the bundled catalog is removed.
- [ ] Documentation does not describe Case Breaker as retired.
- [ ] Documentation does not imply the `Problem` store was removed.

**Verification:**

- [ ] Review `README.md` and `specs/case-breaker.md` for the above statements.

**Dependencies:** Task 2.

**Files likely touched:** `README.md`, `specs/case-breaker.md`.

### Checkpoint: Complete

- [ ] The source no longer contains the current problem catalog.
- [ ] A fresh database retains an empty `Problem` table.
- [ ] Case Breaker model, routes, coach, API client, and UI remain present.
- [ ] Backend and frontend validation passes.

## Validation Commands

```bash
rg -n "COMPRESSED_PROBLEMS|case-breaker-2026-07|The Case Breaker seed catalog must contain 280|backend/problems.json" backend frontend README.md specs
cd backend && ruff check .
cd backend && python manage.py check
cd backend && python manage.py migrate --noinput
cd backend && pytest
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test -- --run
cd frontend && npm run build
```

## Risks and Open Questions

| Risk | Mitigation |
| --- | --- |
| `0002` has been applied in a shared environment. | Preserve its filename and replace its seed body with a no-op instead of deleting it. |
| Tests implicitly rely on seed records. | Create explicit `Problem` fixtures for challenge and coach tests. |
| An empty store makes the normal challenge UI show an error. | Retain and test the existing `400` empty-store response until new problems are added. |

- Has `0002_seed_problem_catalog.py` been applied or shared outside this worktree?
- When you add new problems, should they be added through a new migration, an import command, or an admin/API workflow? That is intentionally a later task.
