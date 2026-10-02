# Implementation Plan: Local AI-Assisted Case Breaker Grading

## Overview

Restore Case Breaker test-case grading through a locally running LM Studio
server. The default configured grader is `meta-llama/Llama-3.2-3B-Instruct`.
The backend sends the reviewed database problem and a learner's submitted input
to the local model; it never executes C++ and never exposes the problem's
stored flaw or example directly to the browser.

## Approved Decisions

- The response verdicts are `EXPOSES_FLAW`, `DOES_NOT_EXPOSE_FLAW`, and
  `UNCLEAR`; `UNCLEAR` is a valid non-punitive result when the model cannot
  assess the input reliably.
- Grading is controlled independently from the existing AI coach by
  `CASE_BREAKER_GRADING_ENABLED`, which defaults to `false`.
- The grader receives the server-side `Problem.flaw` and `Problem.example`
  fields as hidden evaluation context. The browser never receives them.
- The backend uses LM Studio's OpenAI-compatible chat endpoint with structured
  JSON output for grading. The existing native LM Studio coach integration
  remains independent.
- Model weights are not bundled, committed, or downloaded by application
  startup. A developer must accept the model licence, download a compatible
  local model, and configure the exact runtime model identifier.

## API Contract

### Request

`POST /api/case-breaker/grade/`

```json
{
  "challengeId": "string-password-exclamation-check",
  "testCase": "!dasasdadsasd"
}
```

### Success response

```json
{
  "grade": {
    "challengeId": "string-password-exclamation-check",
    "verdict": "EXPOSES_FLAW",
    "message": "This input is likely to expose the condition's handling of an exclamation mark at index zero."
  }
}
```

### Error behavior

- `400`: malformed payload, blank input, or input over the configured limit.
- `404`: no stored problem matches `challengeId`.
- `503`: grading disabled, LM Studio unavailable, model unavailable, timeout,
  or malformed model output.

The endpoint ignores all client-supplied problem description, code, flaw, and
example fields.

## Dependency Graph

```text
Grading feature flag + LM Studio configuration
                    |
Structured local grader client
                    |
Backend grade endpoint and contract
                    |
Frontend submit/result workflow
                    |
Tests, documentation, and ADR
```

## Tasks

### Task 1: Record the revised Case Breaker contract

**Description:** Update the Case Breaker specification and create an ADR that
replaces the retired automatic-grading contract with local AI-assisted grading.

**Acceptance criteria:**

- [ ] The docs state that grading is model-assisted, local, and does not
  execute C++.
- [ ] The three approved verdicts and error semantics are documented.
- [ ] The docs state that server-side flaw/example context is not returned to
  the browser.

**Verification:** Review `specs/case-breaker.md` and the new ADR against this
document.

**Dependencies:** None.

**Files likely touched:** `specs/case-breaker.md`,
`docs/decisions/ADR-*.md`.

### Task 2: Add grading-specific local-model configuration

**Description:** Add independent grading settings and Compose environment
pass-through without changing the existing coach feature's behavior.

**Acceptance criteria:**

- [ ] `CASE_BREAKER_GRADING_ENABLED` defaults to `false`.
- [ ] The configured default model is `meta-llama/Llama-3.2-3B-Instruct`.
- [ ] The startup configuration continues to limit LM Studio URLs to the
  intended local hosts.
- [ ] Input, output, and timeout limits are explicit and independently named
  where grading needs different bounds.

**Verification:** `cd backend && python manage.py check` with grading disabled
and enabled configurations.

**Dependencies:** Task 1.

**Files likely touched:** `backend/config/settings.py`, `.env.example`,
`docker-compose.yml`.

### Task 3: Implement structured local grading

**Description:** Add a small LM Studio grading client that asks the local model
to assess whether the submitted input exposes the stored flaw, returning only a
strictly validated verdict and learner-safe explanation.

**Acceptance criteria:**

- [ ] The request uses LM Studio's OpenAI-compatible structured-output path.
- [ ] The prompt treats database content and learner input as untrusted data,
  forbids instruction-following from that content, and does not permit tool
  use or code execution.
- [ ] Only the approved verdicts and a bounded plain-text message are accepted.
- [ ] Invalid JSON, invalid schema values, timeouts, and network/model failures
  become a single unavailable-grader error.

**Verification:** Mocked backend tests cover a valid response, malformed JSON,
invalid verdict, timeout, and unavailable model.

**Dependencies:** Task 2.

**Files likely touched:** `backend/apps/core/lm_studio.py`,
`backend/apps/core/grading.py`, `backend/apps/core/tests.py`.

### Task 4: Restore the backend grade endpoint

**Description:** Replace the retired endpoint with the approved contract and
server-side problem lookup.

**Acceptance criteria:**

- [ ] The endpoint validates only `challengeId` and `testCase`.
- [ ] It fetches the `Problem` by slug and never uses client-provided code,
  flaw, or example content.
- [ ] It returns the specified `400`, `404`, `503`, and `200` responses.
- [ ] The existing coach endpoint and its feature flag continue to work
  unchanged.

**Verification:** `cd backend && pytest`.

**Dependencies:** Task 3.

**Files likely touched:** `backend/apps/core/views.py`,
`backend/apps/core/urls.py`, `backend/apps/core/tests.py`.

### Checkpoint: Backend grading

- [ ] The endpoint returns a validated grade when the local client succeeds.
- [ ] Disabled or unavailable local inference does not break opening a case or
  using the coach.
- [ ] Backend validation passes.

### Task 5: Connect test-case submission to grading

**Description:** Replace the browser-only draft submission with an accessible
grading interaction when grading is enabled.

**Acceptance criteria:**

- [ ] The frontend sends only `challengeId` and `testCase` to the backend.
- [ ] It presents pending, verdict, `UNCLEAR`, and retryable error states.
- [ ] Copy describes outcomes as AI-assisted/likely, never as proof.
- [ ] Editing the input or opening another challenge clears the prior result.
- [ ] The browser still does not contact LM Studio directly.

**Verification:** `cd frontend && npm test -- --run`.

**Dependencies:** Task 4.

**Files likely touched:** `frontend/src/api.ts`, `frontend/src/App.tsx`,
`frontend/src/App.css`, `frontend/src/App.test.tsx`.

### Task 6: Document local setup and validate the full slice

**Description:** Document the gated manual model setup, exact runtime-model-ID
check, local-only security posture, and all changed behavior.

**Acceptance criteria:**

- [ ] README explains how to accept the Llama licence, download/load the model
  in LM Studio, identify its installed runtime ID, and start the local server.
- [ ] README documents Docker Desktop/Linux host connectivity and optional API
  token setup.
- [ ] Documentation no longer claims that automatic grading is retired.
- [ ] `.env.example` does not imply LM Studio is required for the base app.

**Verification:** Follow the documented setup with LM Studio running, submit a
known flaw-exposing case, and confirm the frontend displays a result.

**Dependencies:** Tasks 1-5.

**Files likely touched:** `README.md`, `.env.example`, `docker-compose.yml`,
`specs/case-breaker.md`, `docs/decisions/ADR-*.md`.

## Complete Validation

```bash
cd backend && ruff check .
cd backend && python manage.py check
cd backend && pytest
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test -- --run
cd frontend && npm run build
```

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| The configured model ID does not match LM Studio's installed ID. | Verify it with the local model-list endpoint before enabling grading. |
| A small local model misclassifies edge cases. | Provide `UNCLEAR`, deterministic settings, concise evidence, and no claim of proof. |
| Prompt injection in learner input or catalog content. | Treat all inserted content as data, constrain output schema, and do not enable tools. |
| LM Studio is stopped, slow, or unreachable from Compose. | Use bounded timeouts, return `503`, and document host networking. |
| Local model weights are accidentally committed or deployed. | Keep weights outside the repository and prohibit runtime download during application startup. |

## Sources

- LM Studio local REST quickstart: <https://lmstudio.ai/docs/developer/rest/quickstart>
- LM Studio structured output: <https://lmstudio.ai/docs/developer/openai-compat/structured-output>
- Llama 3.2 3B Instruct model card and licence: <https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct>
