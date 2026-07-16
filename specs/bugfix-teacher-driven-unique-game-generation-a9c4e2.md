# Bugfix Plan: Teacher-Driven Unique Game Generation

## Plan Review Findings

This plan was revised before implementation to make it more actionable for this
repository.

- The original plan preserved the right product goal, but left several
  implementation choices open: whether to expose `variant_id`, whether to reject
  unknown settings, and how much repeated-generation difference is enough.
- The plan now chooses the narrowest contract-preserving path: randomness stays
  internal, the response schema remains unchanged, and backend inputs continue
  to fall back or sanitize rather than introducing new 400 behavior.
- The original plan proposed a `.claude/commands/e2e/...` file, but AGENTS.md
  routes implementation plans to `specs/` and tests to repo-native backend and
  frontend test files. This revision keeps E2E validation as a manual checklist
  in this spec instead of adding a new nonstandard file.
- The original test sequencing was ambiguous because endpoint tests cannot pass
  controlled variants through HTTP unless the implementation exposes a hook. The
  revised plan separates pure generator unit tests from endpoint contract tests.
- The problem-type requirement now has concrete mechanics so an implementation
  agent does not only rewrite prompt text while leaving identical tasks.

## Feature Description

Fix `POST /api/games/generate/` so teacher settings materially shape generated
specifications, prompts, candidate solutions, explanations, and overall game
composition, while repeated generations with the same settings can still produce
meaningfully different games.

Preserve the existing student play contract where possible:

- Response top-level keys remain `settings` and `game`.
- `game.title` remains `CS1 Solution Spotlight`.
- `game.tasks` contains five tasks.
- Each task has `id`, `prompt`, `specifications`, `candidate_solutions`,
  `correct_solution_id`, and `explanation`.
- Each task has exactly three candidate solutions with IDs `A`, `B`, and `C`.
- `correct_solution_id` points to exactly one semantically correct candidate.
- Candidate snippets remain C++, not Python.
- `game.scoring` remains unchanged.
- The frontend POST body remains unchanged.
- Existing CSRF exemption and POST-only behavior remain unchanged.

Do not add an external LLM, network call, or third-party dependency for this
bugfix. Use standard-library randomness plus curated local content pools.

## User Story

As a CS1 teacher, I want generated practice games to reflect my selected topics,
emphasized concepts, and problem styles with fresh variation each time, so that
students receive targeted practice that does not feel repetitive or predictable.

## Current Problem

The current implementation in `backend/apps/core/views.py` is deterministic for
the same teacher topics and emphasis topics, omits `problem_types` from the RNG
seed, and uses a small fixed template shape:

- `specifications` is always one generic `check_<topic>_<index>` requirement.
- Candidate solutions are always `return true`, `return false`, and a topic
  length shortcut.
- `problem_type` changes prompt wording but not task mechanics.
- Topic and emphasis values are interpolated but do not select different
  scenarios, signatures, constraints, misconceptions, or distractors.
- Frontend rendering in `frontend/src/App.tsx` displays the backend response
  directly, so uniqueness belongs in backend generation.

## Target Design

Create a small pure backend generation module and keep the Django view focused
on HTTP concerns.

Key decisions:

- Add `backend/apps/core/game_generation.py` for pure generation code.
- Keep request parsing in the Django boundary, but move reusable normalization,
  settings dataclass, content profiles, task builders, fingerprinting, variant
  creation, and payload assembly into `game_generation.py`.
- Build a stable settings fingerprint from normalized `cover_topics`,
  `emphasize_topics`, and `problem_types`.
- Serialize the fingerprint deterministically, for example with
  `json.dumps(..., sort_keys=True)`. Do not use Python's built-in `hash()`,
  because its result is intentionally randomized between processes.
- Generate a per-request random variant internally with a standard-library
  entropy source such as `secrets.token_hex(8)` or `uuid.uuid4().hex`.
- Seed a request-local `random.Random` with the settings fingerprint and
  variant, then pass that RNG through all builder code. Do not use module-level
  `random` state.
- Let tests pass fixed variants directly to the pure generator. Endpoint tests
  should not depend on probabilistic differences.
- Keep randomness internal. Do not add `game.variant_id`, `generation_id`, or
  other response metadata in this bugfix.
- Continue accepting arbitrary API-supplied topic/problem strings. Supported
  frontend values get rich profiles; unknown values are sanitized and routed
  through a generic profile rather than rejected, preserving current permissive
  behavior.

Suggested public interface for the new module:

```python
@dataclass(frozen=True)
class GameSettings:
    cover_topics: list[str]
    emphasize_topics: list[str]
    problem_types: list[str]


def normalize_settings_payload(payload: Mapping[str, object]) -> GameSettings:
    ...


def build_game_response(settings: GameSettings, variant: str | None = None) -> dict:
    ...
```

`variant=None` means the module creates fresh entropy. Tests use explicit
variant strings such as `"variant-a"` and `"variant-b"`.

## Relevant Files

- `backend/apps/core/views.py`
  - Keep `health` and the Django `generate_game` view.
  - Replace inline generation with parsing plus delegation to
    `game_generation.build_game_response`.
  - Preserve `@csrf_exempt` and `@require_POST`.
- `backend/apps/core/game_generation.py`
  - New pure generation module.
  - Contains `GameSettings`, defaults, normalization helpers, topic profiles,
    problem-type builders, settings fingerprinting, variant creation, and game
    payload assembly.
- `backend/apps/core/tests.py`
  - Existing backend endpoint tests live here.
  - Add pure generator tests and endpoint regression tests here unless the file
    becomes hard to scan; if it does, create a focused
    `backend/apps/core/test_game_generation.py`.
- `backend/apps/core/urls.py`
  - Confirm endpoint remains `POST /api/games/generate/`.
- `frontend/src/api.ts`
  - No production change expected because the response schema and POST body
    should remain unchanged.
- `frontend/src/App.tsx`
  - No production change expected.
- `frontend/src/App.test.tsx`
  - Keep existing flow coverage. Update only if backend fixtures need to reflect
    more realistic generated content while preserving the same schema.
- `specs/bugfix-game-generation-randomized-cpp-time.md`
  - Preserve accepted behavior: C++ snippets and varied correct answer labels.
- `specs/bugfix-game-generation-403-csrf-a7f3c9.md`
  - Preserve accepted behavior: explicit CSRF exemption for this unauthenticated
    non-persistent endpoint and POST method gating.

## Implementation Plan

### Phase 1: Lock Down Behavior With Tests

Add focused tests before changing generation internals. Separate deterministic
pure-function tests from HTTP endpoint tests.

Pure generator tests should call `build_game_response(settings, variant=...)`
after the new module exists. It is acceptable for the first test commit to fail
on import while the module is being introduced, but do not leave endpoint tests
depending on uncontrolled randomness.

Endpoint tests should continue to post JSON to `reverse("generate-game")` and
assert the public contract, CSRF policy, and method behavior.

### Phase 2: Extract Generation

Create `backend/apps/core/game_generation.py` and move reusable generation
concerns out of `views.py`. The view should parse JSON, normalize settings, call
the pure generator, and return `JsonResponse`.

Keep the module free of Django request/response objects. This keeps tests fast
and lets implementation agents reason about generator behavior without HTTP
fixtures.

### Phase 3: Add Teacher-Driven Content

Add curated local profiles for the frontend-supported CS1 topics:

- `variables`
- `conditionals`
- `loops`
- `functions`
- `arrays`
- `strings`

Each profile should contain enough variety to build multiple tasks:

- Scenario/context fragments.
- Function names or name stems.
- C++ signatures.
- Requirement fragments.
- Correct implementation patterns.
- Plausible misconception/distractor patterns.
- Explanation fragments tied to the topic and emphasis.

Unknown topics should use a generic profile with sanitized identifiers and
escaped/safe text interpolation. Do not echo raw untrusted strings into code
without passing through the existing `_cpp_identifier` style sanitization.

### Phase 4: Add Problem-Type Mechanics

Implement distinct builders for the three problem types already exposed by the
frontend:

- `solution comparison`: students choose the implementation that satisfies a
  concrete specification. Distractors should be plausible but fail the stated
  requirement.
- `specification checking`: students choose the implementation that matches all
  listed constraints, where distractors violate one named constraint such as a
  boundary case, comparison operator, accumulator initialization, or string/array
  index rule.
- `debugging`: students choose the corrected C++ function from one buggy
  version and one superficially changed but still incorrect version. The prompt
  should mention debugging, and the explanation should name the bug fixed by the
  correct candidate.

Problem type must affect the generated specification, prompt, candidate code,
and explanation. A prompt-only change is not sufficient.

### Phase 5: Assemble Diverse Games

Generate exactly five tasks per game. For each task, sample from settings and
profiles with the request-local RNG rather than only cycling by index.

Within one generated game:

- Prefer different topic/problem-type combinations when the settings allow it.
- Avoid duplicate function names and identical specifications when the profile
  pool allows it.
- Shuffle candidate order after assigning semantic correctness.
- Recompute `correct_solution_id` after shuffling.
- Shuffle task order only after task IDs are assigned, or assign stable task IDs
  after shuffling. IDs must remain unique.
- Keep correct answer labels varied across the five tasks when possible.

Across repeated calls with identical settings:

- Different explicit variants must produce different game signatures in tests.
- At least one task-level visible field must differ between two fixed variants;
  target stronger variation when profiles allow it, such as multiple changed
  specifications or candidate code snippets.

### Phase 6: Wire the Endpoint

Update `backend/apps/core/views.py` so `generate_game` delegates to
`game_generation.py` while preserving:

- Endpoint URL: `/api/games/generate/`.
- `@csrf_exempt`.
- `@require_POST`.
- JSON POST request shape.
- Invalid JSON fallback behavior unless a separate validation task changes it.
- Top-level response keys `settings` and `game`.
- Existing scoring values.
- Existing title.

Do not add frontend-only uniqueness logic. The backend response should already
contain unique generated content.

### Phase 7: Validate and Manually Exercise the Flow

Run all backend and frontend validation commands from AGENTS.md. Then manually
exercise the browser flow with two same-settings generations and one
changed-settings generation.

## Step-by-Step Tasks

Execute these in order.

### 1. Add Pure Generator Test Targets

Files likely touched:

- `backend/apps/core/tests.py`
- `backend/apps/core/game_generation.py` once introduced

Acceptance criteria:

- A helper builds a stable game signature from task prompts, specifications,
  candidate code, correct IDs, and explanations.
- A test with the same `GameSettings` and the same fixed variant gets the same
  signature.
- A test with the same `GameSettings` and two different fixed variants gets
  different signatures.
- A test with different topic/emphasis/problem-type settings gets different
  signatures and includes selected settings in generated visible content.

Verification:

- `cd backend && pytest backend/apps/core/tests.py`

### 2. Preserve Endpoint Contract Tests

Files likely touched:

- `backend/apps/core/tests.py`

Acceptance criteria:

- Endpoint tests continue asserting normalized `settings`, title, five tasks,
  scoring, three candidates, valid `correct_solution_id`, C++ snippets, and no
  Python `def` snippets.
- CSRF-enforced no-token POST still returns 200, preserving the prior CSRF
  bugfix.
- GET still returns 405.
- Tests do not assert that two real HTTP calls always differ, because that would
  be probabilistic.

Verification:

- `cd backend && pytest backend/apps/core/tests.py`

### 3. Extract and Normalize Settings

Files likely touched:

- `backend/apps/core/game_generation.py`
- `backend/apps/core/views.py`
- `backend/apps/core/tests.py`

Acceptance criteria:

- `GameSettings`, `CS1_DEFAULT_TOPICS`, normalization helpers, and
  `_cpp_identifier`-style sanitization live in the pure generation module.
- `views.py` catches `json.JSONDecodeError` as it does today, passes a payload
  mapping to the normalizer, and returns the generated payload.
- Missing or empty arrays still fall back to safe defaults.
- Duplicate setting values are normalized consistently. Prefer deduping while
  preserving order so repeated teacher selections do not cause duplicate-heavy
  output.

Verification:

- `cd backend && ruff check backend/apps/core`
- `cd backend && pytest backend/apps/core/tests.py`

### 4. Implement Fingerprint and Variant RNG

Files likely touched:

- `backend/apps/core/game_generation.py`
- `backend/apps/core/tests.py`

Acceptance criteria:

- The settings fingerprint includes normalized `cover_topics`,
  `emphasize_topics`, and `problem_types`.
- The fingerprint serialization is deterministic across Python processes and
  does not use Python's built-in `hash()`.
- `build_game_response(settings, variant=None)` creates a variant internally
  only when one is not supplied.
- The local `random.Random` seed combines fingerprint and variant.
- No module-level mutable RNG is used.
- Tests prove same variant is deterministic and different variants can differ.

Verification:

- `cd backend && pytest backend/apps/core/tests.py`

### 5. Implement Topic Profiles

Files likely touched:

- `backend/apps/core/game_generation.py`
- `backend/apps/core/tests.py`

Acceptance criteria:

- Profiles exist for `variables`, `conditionals`, `loops`, `functions`,
  `arrays`, and `strings`.
- Generated C++ identifiers are valid and derived through the sanitizer.
- Generated content includes the selected cover and emphasis topics in visible
  specifications, prompts, or explanations.
- Unknown/custom topics use the generic profile and sanitized identifiers
  without changing the endpoint to return 400.

Verification:

- `cd backend && pytest backend/apps/core/tests.py`
- `cd backend && ruff check backend/apps/core`

### 6. Implement Problem-Type Builders

Files likely touched:

- `backend/apps/core/game_generation.py`
- `backend/apps/core/tests.py`

Acceptance criteria:

- `solution comparison`, `specification checking`, and `debugging` each have a
  distinct builder path.
- Each builder returns the existing task schema only.
- Each task has exactly one semantically correct candidate.
- Candidate code and explanations match the selected problem type mechanics.
- Unsupported/custom problem types fall back to a supported builder while still
  preserving the normalized setting value in the response.

Verification:

- `cd backend && pytest backend/apps/core/tests.py`

### 7. Assemble and Shuffle Complete Games

Files likely touched:

- `backend/apps/core/game_generation.py`
- `backend/apps/core/tests.py`

Acceptance criteria:

- Each generated game has five uniquely identified tasks.
- Candidate order is shuffled and `correct_solution_id` remains valid.
- Correct labels vary across tasks when possible.
- Duplicate specifications/function names are avoided when the content pool
  allows it.
- The previous C++ and scoring regressions stay covered.

Verification:

- `cd backend && pytest backend/apps/core/tests.py`

### 8. Keep Frontend Contract Stable

Files likely touched:

- Usually none.
- `frontend/src/App.test.tsx` only if fixture content must be updated while
  keeping the same schema.

Acceptance criteria:

- No frontend code fabricates uniqueness.
- No frontend type changes are required because no response fields are added.
- Existing test still proves selected settings are posted to
  `/api/games/generate/` and returned game content renders.

Verification:

- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm test -- --run`

### 9. Run Full Validation

Run every command listed in the Validation Commands section. Fix only issues
directly caused by this bugfix.

## Testing Strategy

Backend pure generator tests:

- Same settings plus same fixed variant yields identical signatures.
- Same settings plus different fixed variants yields different signatures.
- Changing cover topics changes generated visible content.
- Changing emphasis topics changes generated visible content.
- Changing problem types changes mechanics, candidate code, and explanation.
- Empty/missing settings use defaults.
- Duplicate settings are deduped or otherwise handled without duplicate-heavy
  output.
- Unknown topics are sanitized and generated through the generic profile.
- Candidate shuffling never disconnects `correct_solution_id`.
- Every generated candidate snippet is C++ shaped and does not contain Python
  `def` syntax.

Backend endpoint tests:

- JSON POST success preserves the public contract.
- Invalid JSON keeps the current fallback behavior unless a separate
  validation decision changes it.
- CSRF-enforced tokenless POST succeeds because the endpoint is explicitly
  exempt.
- GET is rejected with 405.

Frontend tests:

- Existing tests continue to verify the selected teacher settings are sent to
  `/api/games/generate/`.
- Existing tests continue to verify returned game content renders and non-OK
  responses show controlled error text.

Manual browser validation:

1. Start the app with `docker compose up --build`, or run Django on `:8000` and
   Vite on `:5173`.
2. Open `http://localhost:5173`.
3. Select one cover topic, one emphasis topic, and one problem type.
4. Generate a game and record visible specifications, prompts, and candidate
   code for the first task.
5. Generate again with the same settings and confirm at least one visible task
   field differs.
6. Change topic, emphasis, or problem type and generate again.
7. Confirm the changed setting appears in visible content and changes the task
   mechanics or code, not only the page summary.
8. Confirm the browser flow does not show a 403 or method error.

## Acceptance Criteria

- Repeated game generation can produce different games for identical teacher
  settings because a per-request random variant is used.
- Tests prove uniqueness with controlled variants, not probability-based HTTP
  assertions.
- Teacher `cover_topics`, `emphasize_topics`, and `problem_types` all influence
  generated visible content.
- `solution comparison`, `specification checking`, and `debugging` produce
  distinct task mechanics.
- Each generated game contains exactly five tasks.
- Each task contains exactly three candidate solutions and one valid correct
  solution.
- Generated code snippets remain C++ and do not regress to Python syntax.
- Existing scoring response values remain unchanged.
- Existing frontend settings POST body remains unchanged.
- Existing CSRF and method behavior remains unchanged.
- No external generation dependency, LLM call, or network dependency is added.
- No response metadata is added in this bugfix.

## Validation Commands

Execute every command after implementation:

```bash
cd backend && ruff check .
```

```bash
cd backend && python manage.py check
```

```bash
cd backend && pytest
```

```bash
cd frontend && npm run lint
```

```bash
cd frontend && npm run typecheck
```

```bash
cd frontend && npm test -- --run
```

```bash
cd frontend && npm run build
```

Manual E2E validation is the checklist in Testing Strategy. Do not add a new
E2E framework or nonstandard command file for this bugfix.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Random tests become flaky | High | Test pure generator behavior with fixed variants; do not assert live HTTP calls always differ. |
| Correct answer ID breaks after shuffling | High | Track semantic correctness before shuffle and recompute `correct_solution_id` afterward. |
| Content pools are too small and repeat within a game | Medium | Avoid duplicates when possible and test single-topic settings specifically. |
| Problem types only change prompt text | Medium | Add tests that compare candidate code and explanation differences across problem types. |
| Unknown topic strings create invalid C++ | Medium | Sanitize identifiers and use generic profile for unsupported values. |
| Frontend contract drifts unnecessarily | Medium | Keep response schema unchanged and avoid frontend production edits unless tests fail. |

## Out of Scope

- Persisting generated games.
- Adding authentication or changing CSRF policy.
- Adding an LLM-backed generator.
- Adding new frontend UI for generation metadata.
- Changing task count or scoring.
- Rejecting unsupported teacher settings with 400 responses.

## Open Questions For Product Review

These are not blockers for the bugfix because the plan chooses conservative
defaults above.

- Should a future API version validate teacher settings against an allowlist and
  return 400 for unsupported values?
- Should future responses expose `generation_id` for observability once games
  are stored or associated with users?
- Should teachers eventually control task count or difficulty?
