# Feature: Fix Game Generation 403 CSRF Failure

## Feature Description
Fix the browser flow where a teacher clicks "Generate game" and receives `Game generation failed with status 403`. The fix should preserve the current `/api/games/generate/` JSON contract, keep Django's global CSRF middleware enabled, and make the endpoint's CSRF behavior explicit.

## User Story
As a CS1 teacher
I want the game generator to work from the React app
So that I can create a deterministic practice game without hitting an unexpected CSRF rejection.

## Problem Statement
The frontend sends a JSON `POST` to `/api/games/generate/` without a CSRF token. Django's `CsrfViewMiddleware` is globally enabled, but the existing backend test uses the default test client, which does not enforce CSRF checks. As a result, tests pass while the real browser request can fail with HTTP 403.

`CSRF_TRUSTED_ORIGINS` is not a replacement for a CSRF token or endpoint exemption. It only controls which request origins Django will trust during CSRF origin/referer validation. A tokenless unsafe request can still fail even when the origin is trusted.

## Solution Statement
Use one explicit CSRF policy: exempt only `POST /api/games/generate/` from CSRF because it is currently unauthenticated, deterministic, and non-persistent. Keep `CsrfViewMiddleware` enabled globally and keep `@require_POST` on the endpoint. Add regression tests that use Django's CSRF-enforcing client so the bug is covered by tests that match browser behavior.

Input validation improvements are out of scope for this bugfix unless a test reveals they are required to preserve the existing contract. Do not add broader payload validation or behavior changes as part of this fix.

## Relevant Files
Use these files to implement the bugfix:

- `backend/apps/core/views.py`
  - Add `@csrf_exempt` to `generate_game`.
  - Place `@csrf_exempt` above `@require_POST` so the final callable is CSRF-exempt while still method-gated.
  - Preserve `@require_POST` and the existing response contract.
- `backend/apps/core/tests.py`
  - Add CSRF-enforced regression coverage for `POST /api/games/generate/`.
  - Preserve the existing contract assertions for settings, title, tasks, and scoring.
- `frontend/src/api.ts`
  - No production change is expected if the endpoint exemption is used.
  - Keep the relative `/api/games/generate/` request path.
- `frontend/src/App.test.tsx` or a new `frontend/src/api.test.ts`
  - Assert the frontend sends the relative endpoint, `POST` method, and expected JSON payload.
  - Preserve the existing non-OK error behavior.
- `backend/config/settings.py`
  - Verify `CsrfViewMiddleware` remains enabled.
  - Do not solve this by removing global CSRF protection.

### New Files
Create a new frontend API test file only if that keeps request-construction assertions clearer than adding them to `App.test.tsx`:

- `frontend/src/api.test.ts`

Do not create `.claude` files for this bugfix. Manual verification belongs in this spec, and automated coverage should live in repo-native backend/frontend test files.

## Implementation Plan
### Phase 1: Confirm Current Behavior
Add a backend regression test with `Client(enforce_csrf_checks=True)` that posts valid JSON to `reverse("generate-game")` without a CSRF cookie or token. Confirm this test fails with HTTP 403 before the endpoint is exempted.

### Phase 2: Apply the Narrow Fix
Decorate `generate_game` with `@csrf_exempt` above `@require_POST`, so the final callable Django routes to is exempt while still rejecting non-POST methods. Keep `CsrfViewMiddleware` in `backend/config/settings.py`. Do not add CSRF token bootstrap code, credentials handling, new auth behavior, or unrelated input validation.

### Phase 3: Tighten Regression Coverage
Update backend and frontend tests so they lock down the intended behavior:

- Backend CSRF-enforced no-token `POST` succeeds after exemption.
- Backend response contract remains unchanged.
- Frontend uses the relative endpoint, `POST`, `application/json`, and the selected settings payload.
- Frontend still throws/renders `Game generation failed with status <status>` for non-OK responses.

### Phase 4: Verify Browser Flow
Run automated validation, then manually verify the React flow through the Vite proxy. Confirm the browser sends `POST /api/games/generate/`, receives 200, and renders the generated game instead of the 403 error.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add the Backend Failing Regression Test First
- In `backend/apps/core/tests.py`, import Django's `Client`.
- Add a test that creates `Client(enforce_csrf_checks=True)`.
- Post valid JSON to `reverse("generate-game")` without a CSRF token.
- Before the fix, assert this reproduces the bug as a 403 during local development.
- Keep or reuse the existing assertions for:
  - `settings.cover_topics`
  - `settings.emphasize_topics`
  - `settings.problem_types`
  - `game.title`
  - `game.tasks`
  - `game.scoring`

### 2. Exempt Only the Game Generation Endpoint
- In `backend/apps/core/views.py`, import `csrf_exempt` from `django.views.decorators.csrf`.
- Add `@csrf_exempt` to `generate_game` above `@require_POST`.
- Keep `@require_POST` in place so non-POST methods remain rejected.
- Do not remove `django.middleware.csrf.CsrfViewMiddleware` from settings.
- Do not change the request schema or response schema.

### 3. Update Backend Assertions After the Fix
- Change the new CSRF-enforced no-token test to expect HTTP 200 after `@csrf_exempt`.
- Assert the JSON contract matches the existing behavior.
- Add or preserve a non-POST assertion if existing coverage does not already prove `@require_POST` is still effective.

### 4. Tighten Frontend Request Coverage
- In `frontend/src/App.test.tsx` or `frontend/src/api.test.ts`, assert `fetch` is called with:
  - `/api/games/generate/` when `VITE_API_BASE_URL` is empty
  - `method: "POST"`
  - `Content-Type: "application/json"`
  - a JSON body containing `cover_topics`, `emphasize_topics`, and `problem_types`
- Keep the existing error behavior assertion for a non-OK response, including `Game generation failed with status <status>`.
- Do not add CSRF token headers or `credentials: "include"` for this chosen exemption-based fix.
- If creating `frontend/src/api.test.ts`, account for `frontend/src/api.ts` computing `apiBaseUrl` at module load:
  - To test `VITE_API_BASE_URL`, set or stub the env value before importing `generateGame`, or call `vi.resetModules()` before a dynamic import.
  - To test the default relative path, avoid env mutation and assert the current `fetch` URL is `/api/games/generate/`.

### 5. Verify CSRF Settings Scope
- Inspect `backend/config/settings.py`.
- Confirm `CsrfViewMiddleware` remains globally enabled.
- Leave `CSRF_TRUSTED_ORIGINS` unchanged unless manual reproduction proves a separate origin-validation issue.
- Document in code review notes that trusted origins only address origin validation and do not replace token handling or exemption.

### 6. Run Validation Commands
- Run every command in the `Validation Commands` section.
- After automated checks pass, perform the manual browser verification in the same section.

## Testing Strategy
### Unit Tests
- Backend: use `Client(enforce_csrf_checks=True)` to prove tokenless `POST /api/games/generate/` succeeds only after the endpoint-level exemption.
- Backend: preserve response contract assertions for deterministic game generation.
- Frontend: assert request construction uses the relative API endpoint, `POST`, and the expected JSON payload.
- Frontend: when testing `VITE_API_BASE_URL` in a new `api.test.ts`, set/stub env before importing `generateGame` or use `vi.resetModules()` before dynamic import because `apiBaseUrl` is computed at module load. The default relative path can be tested without env mutation by asserting the current `fetch` URL.
- Frontend: preserve non-OK error behavior.

### Edge Cases
- Non-POST request to `/api/games/generate/` is still rejected by `@require_POST`.
- CSRF middleware remains active for the rest of the Django app.
- Frontend keeps working when `VITE_API_BASE_URL` is empty and requests are proxied through Vite.
- Frontend API tests avoid stale module-level env state when covering `VITE_API_BASE_URL`.
- Backend 403/500 responses still produce controlled frontend error text.

## Acceptance Criteria
- `generate_game` is decorated with `@csrf_exempt` above `@require_POST`, making the final callable CSRF-exempt while still protected by method gating.
- `CsrfViewMiddleware` remains enabled globally.
- Backend tests use `Client(enforce_csrf_checks=True)` and cover a no-token JSON `POST` to `/api/games/generate/`.
- The CSRF-enforced no-token backend test would fail with 403 before the exemption and passes with 200 after it.
- Existing backend contract assertions for settings, title, tasks, and scoring are preserved.
- Frontend tests assert the relative endpoint, method, content type, payload, and existing non-OK error behavior.
- No `.claude` files are added.
- No unrelated input validation or schema behavior changes are included.
- The manual browser flow returns 200 and renders the generated game without showing `Game generation failed with status 403`.

## Validation Commands
Execute every command to validate the bugfix with zero regressions:

```bash
(cd backend && ruff check .)
(cd backend && python manage.py check)
(cd backend && pytest)
(cd frontend && npm run lint)
(cd frontend && npm run typecheck)
(cd frontend && npm test -- --run)
(cd frontend && npm run build)
```

Manual verification:

```text
1. Start the app with docker compose up --build, or run Django on :8000 and Vite on :5173.
2. Open http://localhost:5173.
3. Select at least one topic to cover, one topic to emphasize, and one problem type.
4. Click "Generate game".
5. In the Network tab, confirm POST /api/games/generate/ returns 200.
6. Confirm the generated game title and task UI render.
7. Confirm the page does not show "Game generation failed with status 403".
```

## Notes
- This bugfix intentionally chooses endpoint-level `@csrf_exempt` because the current endpoint is unauthenticated, deterministic, and non-persistent.
- Revisit this policy if the endpoint becomes authenticated, mutates server state, stores generated games, or depends on user/session data.
- `CSRF_TRUSTED_ORIGINS` only controls allowed origins during CSRF checks. It does not satisfy CSRF token validation and does not replace an explicit exemption.
