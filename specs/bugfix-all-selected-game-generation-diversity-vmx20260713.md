# Bugfix Plan: All-Selected Game Generation Diversity

## Plan Review Findings

This plan was revised after `plan-reviewer` identified several gaps:

- The original regression test criteria could pass against the current
  generator because it already tends to sample unique topics and all problem
  types in the all-selected case. The tests now target repeated task shape,
  specification signatures, and normalized correct-solution signatures.
- The public task schema does not expose structured `topic` or `problem_type`
  fields. The revised plan keeps any blueprint metadata private to
  `game_generation.py` and uses internal helpers or text-derived signatures for
  assertions.
- "Near-identical" is now defined through explicit diversity signatures instead
  of left to implementation judgment.
- Retry behavior now has deterministic limits and fallback requirements.
- Frontend payload coverage is conditional because the current production path
  already serializes selected arrays; no frontend production changes are in
  scope unless a payload regression is found.

## Overview

When a teacher selects every available topic to cover, every topic to
emphasize, and every problem type, generated tasks should not collapse into
near-identical specifications and solution shapes. Keep the existing API shape
and five-task game contract, but make the backend generation plan explicitly
favor diversity across topics, problem mechanics, specs, and solution bodies.

## Reported Scenario

- Cover topics: all available CS1 topics.
- Emphasize topics: all available CS1 topics.
- Problem types: all available problem types.
- Observed behavior: each task has similar specifications and nearly identical
  candidate solutions.

## Change Description

Strengthen `backend/apps/core/game_generation.py` so generation first builds a
diverse set of task blueprints, then renders tasks from those blueprints.

The generator should:

- Prefer five distinct cover topics when the selected topic pool has at least
  five options.
- Ensure all selected problem types appear when the selected problem-type pool
  is smaller than or equal to the task count.
- Avoid duplicate rendered specifications within one game.
- Avoid repeated correct-solution bodies after normalizing function names and
  comments.
- Expand prompt/spec/explanation template pools enough that repeated problem
  types still produce visibly different tasks.
- Preserve the current request and response contract for
  `POST /api/games/generate/`.

Do not add an external LLM, network call, or dependency for this bugfix.

## Current Repo Constraints

- Preserve the existing `POST /api/games/generate/` request and response shape.
- Do not add `topic`, `problem_type`, `variant`, task-blueprint data, or other
  generation metadata to API responses.
- Keep unknown topics and unknown problem types permissive: sanitize unknown
  topics and route unknown problem types through the existing fallback behavior.
- Use only local deterministic generation with the request-local `random.Random`
  flow already in `game_generation.py`; no network, LLM, or dependency changes.
- Keep the existing five-task game contract and scoring values unchanged.

## Diversity Definitions

Use concrete signatures so tests and implementation agree on what "different"
means:

- `topic_signature`: for private generator tests, derive from the internal
  blueprint topic. For public-payload assertions, derive from known CS1 topic
  names appearing in prompt/specification/code text without adding response
  fields.
- `problem_type_signature`: for private generator tests, derive from the
  internal blueprint problem type. For public-payload assertions, derive from
  prompt mechanics such as solution comparison, listed constraints, or
  debugging language.
- `spec_signature`: normalize `task["specifications"]` by lowercasing,
  collapsing whitespace, and replacing generated function names with a stable
  placeholder.
- `correct_solution_signature`: find the candidate whose ID matches
  `correct_solution_id`, remove the function declaration and generated comment,
  collapse whitespace, and compare the remaining C++ body text.

These signatures should be strict for the all-selected scenario and flexible for
small pools where repetition is unavoidable.

## Relevant Files

- `backend/apps/core/game_generation.py`
  - Primary implementation target.
  - Add blueprint planning, richer templates, and duplicate-signature avoidance.
- `backend/apps/core/tests.py`
  - Add generator regression coverage for the all-selected case.
  - Add helpers that compare semantic code bodies rather than raw function names.
- `backend/apps/core/views.py`
  - No expected production change beyond preserving delegation to the generator.
- `frontend/src/App.tsx`
  - No production change expected.
  - Inspect only if tests show selected values are not retained.
- `frontend/src/api.ts`
  - Keep payload keys unchanged: `cover_topics`, `emphasize_topics`,
    `problem_types`.
- `frontend/src/App.test.tsx`
  - Optional: add a payload test for selecting all available options if no
    existing coverage proves that behavior.

## Implementation Tasks

### Task 1: Add Backend Diversity Regression Coverage

**Description:** Add or tighten tests for the all-selected scenario using
`build_game_response(..., variant="all-selected-a")`. The tests must fail on the
reported repetitive task shape, not merely restate behavior the current
generator already satisfies. Run the new test against the current code first and
record whether it fails before implementation proceeds.

**Acceptance criteria:**
- [ ] `build_game_response` returns exactly five tasks.
- [ ] Five distinct cover-topic signatures are present when all six CS1 topics
  are selected.
- [ ] All selected supported problem-type mechanics appear at least once.
- [ ] Normalized `spec_signature` values are unique.
- [ ] Normalized `correct_solution_signature` values are unique under the
  diversity definition above.
- [ ] Every `correct_solution_id` references one candidate ID in that task.
- [ ] Unknown-topic and unknown-problem-type fallback tests still pass.

**Verification:**
- [ ] `cd backend && pytest apps/core/tests.py`

**Dependencies:** None

**Files likely touched:**
- `backend/apps/core/tests.py`

**Estimated scope:** Small

### Task 2: Introduce Internal Blueprint Planning

**Description:** Add a private planning helper that creates five task blueprints
before rendering. A blueprint may include topic, emphasis, problem type,
template variant, body variant, and retry attempt metadata, but none of this
metadata should be added to the API response.

**Acceptance criteria:**
- [ ] Topic selection prefers unique cover topics when enough topics exist.
- [ ] Problem-type selection covers every selected supported problem type when
  possible.
- [ ] Planning is deterministic for fixed settings plus fixed variant.
- [ ] Pools smaller than five still produce five renderable blueprints.
- [ ] Unknown problem types keep the existing fallback behavior.

**Verification:**
- [ ] `cd backend && pytest apps/core/tests.py`

**Dependencies:** Task 1

**Files likely touched:**
- `backend/apps/core/game_generation.py`

**Estimated scope:** Medium

### Task 3: Render From Blueprints With Explicit Diversity Guards

**Description:** Render tasks from blueprints and track per-game diversity
signatures for specifications and correct solutions.

**Acceptance criteria:**
- [ ] Duplicate spec signatures are avoided when an unused
  template/requirement/context combination exists.
- [ ] Duplicate correct-solution signatures are avoided when an unused body
  variant exists.
- [ ] Retry logic has a fixed maximum attempt count per task, such as 8.
- [ ] Retry fallback is deterministic for fixed settings plus fixed variant and
  chooses the least-used available signature instead of failing generation.
- [ ] Existing deterministic variant tests still pass.
- [ ] Existing public response contract tests still pass.
- [ ] Existing unknown-topic sanitization behavior remains intact.

**Verification:**
- [ ] `cd backend && pytest apps/core/tests.py`
- [ ] `cd backend && ruff check .`
- [ ] `cd backend && python manage.py check`

**Dependencies:** Task 2

**Files likely touched:**
- `backend/apps/core/game_generation.py`
- `backend/apps/core/tests.py`

**Estimated scope:** Medium

### Task 4: Add Conditional Frontend Payload Coverage

**Description:** First inspect existing frontend tests and serialization code.
Add a focused frontend test only if current coverage does not prove that
selecting every UI option sends every selected value to the backend. Do not make
production frontend changes as part of this backend diversity bugfix unless a
payload bug is reproduced.

**Acceptance criteria:**
- [ ] Existing coverage is documented as sufficient, or one focused test is
  added.
- [ ] If added, the test selects every cover topic option.
- [ ] If added, the test selects every emphasis topic option.
- [ ] If added, the test selects every problem type option.
- [ ] If added, the mocked `fetch` body includes all selected arrays under the
  existing payload keys.
- [ ] No production frontend files are changed unless a serialization bug is
  found.

**Verification:**
- [ ] `cd frontend && npm test -- --run`
- [ ] `cd frontend && npm run typecheck`

**Dependencies:** None. This can run in parallel with backend work.

**Files likely touched:**
- `frontend/src/App.test.tsx`

**Estimated scope:** Small

### Task 5: Validate the Full Change

**Description:** Run the repo-standard backend and frontend checks after the
bugfix is implemented.

**Acceptance criteria:**
- [ ] Backend checks pass.
- [ ] Frontend checks pass.
- [ ] Manual all-selected generation produces five visibly different tasks.

**Verification:**
- [ ] `cd backend && ruff check .`
- [ ] `cd backend && python manage.py check`
- [ ] `cd backend && pytest`
- [ ] `cd frontend && npm run lint`
- [ ] `cd frontend && npm run typecheck`
- [ ] `cd frontend && npm test -- --run`
- [ ] `cd frontend && npm run build`

**Dependencies:** Tasks 1-4

**Files likely touched:** None unless checks expose regressions.

**Estimated scope:** Small

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Diversity assertions become flaky | High | Use fixed variants in automated tests and strict assertions only for the all-selected scenario. |
| Unique function names mask repeated logic | Medium | Normalize code by stripping function names and comments before comparing bodies. |
| Candidate shuffling breaks correctness | High | Assert every `correct_solution_id` still points to the semantically correct candidate set. |
| Scope drifts into UI redesign | Medium | Keep multi-select UI unless the implementation task explicitly includes checkbox conversion. |
| Private blueprint metadata leaks into the API | High | Add blueprint data only inside `game_generation.py`; public response contract tests must stay unchanged. |
| Retry logic makes generation non-deterministic | High | Use the existing request-local RNG, a fixed max attempt count, and deterministic fallback selection. |

## Open Questions

- Should the UI be converted from multi-select controls to literal checkbox
  groups? Default answer for this plan: no, unless the user explicitly expands
  the scope.
- Are backend generator tests sufficient for this iteration, or should a manual
  E2E checklist be added under `specs/e2e/` after implementation?
