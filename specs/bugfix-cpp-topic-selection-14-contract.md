# Bugfix Plan: 14-Topic C++ Selection Contract

## Plan Review Findings

This plan was revised after review so it matches the actual product change
instead of the older six-topic / fallback-default behavior.

- The original planning assumptions were stale for this task. They implied
  fallback defaults and a smaller topic list, but the current requirement is a
  14-topic contract shared by both `Topics to cover` and `Topics to emphasize`.
- The revised plan treats the frontend and backend topic lists as one contract
  even though the values live in separate files. That contract needs explicit
  regression coverage so the two surfaces do not drift.
- The plan now makes the required selection rules explicit:
  - `Topics to cover` is mandatory.
  - `Types of problem` is mandatory.
  - `Topics to emphasize` is optional.
  - Emphasis selections must always be a subset of cover selections.
- The boolean-expression topic now uses the common C++ operators `&&`, `||`,
  and `!`. The earlier plan did not lock that wording down.
- `backend/apps/core/game_generation.py` is a large generator module. The plan
  separates "review the generator structure" from "accept the topic-selection
  contract" so a future implementation agent does not accidentally mix a large
  refactor into a narrow feature change.
- Manual browser verification is required for the multi-select interaction.
  Unit tests are necessary, but they do not fully cover the disabled-option UX.

## Overview

Replace the current CS1 topic controls with a 14-topic C++ curriculum contract
and make generation depend on explicit teacher selections instead of implicit
defaults.

The plan is intentionally narrow:

- Update the UI options for both topic selectors.
- Enforce required selections before generation starts.
- Keep emphasis optional, but only allow emphasis topics that are also covered.
- Update backend parsing/validation so invalid or incomplete requests fail
  clearly.
- Expand backend generation so the selected topics can be exercised in task
  content without silently falling back to old defaults.

## Product Rules

- The topic list must contain exactly these 14 concepts in the user-facing UI:
  - Variables, primitive data types, and operations
  - iostream input/output
  - if, else if, else, and switch statements
  - Compound boolean expressions with `&&`, `||`, `!`, and order of precedence
  - while and do-while loops
  - string methods and manipulation
  - for and for-each loops, including range-based and traditional for loops
  - arrays and vectors
  - functions and function prototypes
  - pass-by-reference vs pass-by-value parameters
  - fstream file input/output
  - structs
  - classes and object-oriented programming, including encapsulation and
    information hiding
  - pointers
- Both `Topics to cover` and `Topics to emphasize` must use the same 14-topic
  set.
- `Topics to cover` starts empty when the app loads.
- `Topics to emphasize` starts empty when the app loads.
- `Types of problem` starts empty when the app loads.
- The Generate action must remain disabled until at least one cover topic and
  at least one problem type are selected.
- Emphasis selections must be pruned if their corresponding cover topic is
  removed.
- The backend should reject incomplete or invalid requests rather than silently
  inventing defaults.

## Public Contract

Expected POST body keys remain:

- `cover_topics`
- `emphasize_topics`
- `problem_types`

Expected response shape remains unchanged:

- `settings`
- `game`

No new response metadata should be added for this bugfix.

## Relevant Files

- `frontend/src/api.ts`
  - Shared topic and problem-type option definitions.
  - TypeScript topic/problem unions.
- `frontend/src/App.tsx`
  - Multi-select UI, required-selection gating, and emphasis constraints.
- `frontend/src/App.test.tsx`
  - Frontend regression tests for empty defaults, gated generation, and all 14
    topic selections.
- `frontend/src/App.css`
  - Minor copy/help-text styling for the new selection rules.
- `backend/apps/core/views.py`
  - HTTP boundary validation and request parsing.
- `backend/apps/core/game_generation.py`
  - Generator settings, topic profiles, and C++ content rendering.
- `backend/apps/core/tests.py`
  - Endpoint regression tests and generator regression tests.

## Implementation Plan

### Phase 1: Lock Down the Contract

Add or update tests before changing the remaining implementation details.

Acceptance criteria:

- Frontend tests assert the 14 topic options exist and the page starts with no
  selections.
- Frontend tests assert Generate stays disabled until cover topics and problem
  types are selected.
- Frontend tests assert emphasis options are unavailable unless their topic is
  covered.
- Backend tests assert the shared 14-topic contract and the mandatory-selection
  validation.
- Backend tests assert emphasis outside the cover set is rejected.
- Backend tests assert the boolean-expression topic wording uses `&&`, `||`,
  and `!`.

Verification:

- `cd frontend && npm test -- --run`
- `cd backend && docker compose run --rm backend pytest`

Dependencies:

- None

### Phase 2: Update the Frontend Contract

Replace the old six-topic UI values with the 14-topic shared contract. Keep the
UI readable by pairing stable internal IDs with human-readable labels.

Acceptance criteria:

- The cover and emphasis selects render the same 14 options.
- The initial state contains no selected topics or problem types.
- Required selections are enforced before generation.
- Removing a cover topic removes any dependent emphasis selection.
- The summary text clearly shows `None selected` for empty controls.

Files likely touched:

- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/App.css`
- `frontend/src/App.test.tsx`

### Phase 3: Update Backend Validation and Generation

Update the backend so it matches the same contract and does not silently fill
in missing required selections.

Acceptance criteria:

- Empty cover topics are rejected.
- Empty problem types are rejected.
- Emphasis topics outside the cover set are rejected.
- Valid selections are normalized and passed into generation without hidden
  defaults.
- The 14 selected topics can appear in prompts, specifications, explanations,
  and candidate code through curated profiles or safe fallback handling.

Files likely touched:

- `backend/apps/core/views.py`
- `backend/apps/core/game_generation.py`
- `backend/apps/core/tests.py`

### Phase 4: Review Generator Structure Separately

The generator module is already large. Keep the topic-selection change narrow
and treat any structural cleanup as a separate follow-up unless it is needed to
make the behavior correct.

Acceptance criteria:

- The large generator module is explicitly reviewed before merge.
- Any leftover dead code or stale generator branches are identified.
- A follow-up split is proposed if the module grows harder to reason about.

### Phase 5: Manual Browser Check

Do one browser pass after the automated tests are green.

Checklist:

- Open the app and confirm all three selects start empty.
- Select cover topics and confirm Generate becomes available only after a
  problem type is also selected.
- Select an emphasis topic, then remove its matching cover topic, and confirm
  the emphasis is removed or disabled.
- Confirm the long topic labels render cleanly without overflow or obvious
  layout damage.
- Generate a game and confirm the response still renders the student flow.

## Validation Commands

Frontend:

```bash
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test -- --run
cd frontend && npm run build
```

Backend:

```bash
cd backend && docker compose run --rm backend pytest
cd backend && docker compose run --rm backend ruff check .
cd backend && docker compose run --rm backend python manage.py check
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Frontend and backend topic lists drift | High | Keep the shared 14-topic contract explicit in tests and code review. |
| Emphasis selections become invalid after cover-topic edits | Medium | Prune emphasis selections immediately when cover topics change. |
| The generator module becomes harder to review | Medium | Keep structural cleanup separate and make the topic-selection change narrow. |
| Long labels overflow or wrap awkwardly | Low | Verify in the browser and adjust copy/styling only if needed. |

## Open Questions

- Should the backend generator continue to support arbitrary unknown topic IDs
  through sanitization, or should future versions reject unsupported topics?
- If the generator module is split later, should topic profiles move into a
  separate data file or a dedicated profile module?

