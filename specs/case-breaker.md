# Spec: Case Breaker

## Objective

Case Breaker presents randomly selected C++ debugging problems from the
application database. Learners review the problem description and code; the
application does not execute C++. When enabled, a host-run LM Studio model is
the sole authority for feedback on a submitted test case.

## Contract

- `POST /api/case-breaker/challenges/` accepts an empty JSON object and returns
  a stable problem ID, topic, description, and C++ code.
- `POST /api/case-breaker/grade/` accepts a `challengeId` and a `testCase` when
  grading is enabled. It uses the required LM Studio model and returns
  `EXPOSES_FLAW`, `DOES_NOT_EXPOSE_FLAW`, or `UNCLEAR` plus model feedback.
- `POST /api/case-breaker/coach/` is an optional backend-mediated LM Studio
  coach for hints, explanations, and learner-reasoning feedback.

## Grading and Safety

- The backend seeds and selects one database problem per request. It does not
  retain browser history or use learner progress for selection.
- C++ is shown to learners but is never compiled or executed by the service.
- The backend, not the browser, retrieves the reviewed problem and sends its
  hidden flaw/example fields to the local grader. Those fields are not returned
  in grading feedback.
- Local grading is an assessment, not proof. If its required LM Studio server,
  configured model, or structured response is unavailable, grading returns
  `503` rather than inventing a fallback verdict.

## Catalog Maintenance

The previously bundled 280-problem catalog has been removed. Future catalog
changes should add records through a new reviewed data migration, import path,
or admin/API workflow with stable IDs and backend tests covering the intended
database records.
