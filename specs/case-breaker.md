# Spec: Case Breaker

## Objective

Replace multiple-choice comparison with one counterexample challenge. Llama 3.2
3B Instruct runs locally through Ollama to author student-facing wording;
allowlisted backend evaluators remain the grading authority.

## Contract

- `POST /api/case-breaker/challenges/` accepts an optional learner-progress profile
  and returns code, specification, typed inputs, and an expiring opaque token; it
  never includes an oracle, hint, or explanation. No topic selection is required:
  challenges adapt from progress recorded while playing.
- `POST /api/case-breaker/grade/` accepts the token and integer inputs. A failed
  attempt returns a hint; a breaking test returns expected/actual and explanation.

## Local model

Ollama serves `llama3.2:3b-instruct-q4_K_M`. Its JSON output is constrained to
copy, validated, and falls back safely. It never executes code or grades answers.
