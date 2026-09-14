# ADR-002: Local AI-Assisted Case Breaker Grading

## Status

Accepted

## Context

Case Breaker previously displayed reviewed C++ problems without automatically
assessing learner test cases. Learners need feedback for multiple valid inputs
that can expose the same flaw, without running untrusted C++ in the service.

## Decision

When grading is enabled, the Django backend sends the reviewed database problem
and submitted test case to a locally running LM Studio server. LM Studio is the
sole grading authority: there is no deterministic backend fallback. The exact
loaded model identifier is required through `LM_STUDIO_GRADING_MODEL`, and the
model returns `EXPOSES_FLAW`, `DOES_NOT_EXPOSE_FLAW`, or `UNCLEAR` with concise
feedback.

The backend uses LM Studio's OpenAI-compatible structured-output endpoint. It
looks up the problem by ID and provides the hidden flaw/example only to the
local model; clients cannot supply or receive those values. C++ is never
compiled or executed. Model weights are manually downloaded and remain outside
source control.

## Consequences

- The system can give local feedback for diverse valid test cases without a
  remote model provider or a C++ execution sandbox.
- Grading is an assessment rather than proof; `UNCLEAR` avoids forced false
  negatives or positives.
- Local LM Studio availability, structured-output support, and the configured
  model ID are runtime prerequisites whenever grading is enabled. Unavailable
  or invalid model responses return `503`, never a guessed grade.
- The existing AI coach remains independently optional.
