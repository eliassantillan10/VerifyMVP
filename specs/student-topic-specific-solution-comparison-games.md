# Spec: Student-Created, Topic-Specific Solution-Comparison Games

## Objective

Students create their own CS1 practice games by selecting only the concepts
they have learned. The UI replaces teacher authoring with a compact vertical
topic checklist. Every generated task is a multiple-choice solution-comparison
question: select the best implementation for the stated requirements.

The existing backend emphasis capability remains for a later UI, but it is not
displayed or sent by this student flow. Problem-type choice is removed; solution
comparison is the sole game mechanic.

## Decisions and Assumptions

- Each topic below has a stable atomic ID and a dedicated `TopicProfile`.
  Profile requirements, correct answer, distractors, prompt, and explanation
  must assess only its selected topic. They must not test a sibling concept from
  an old combined category.
- A profile may use prerequisite C++ syntax necessary to express a solution,
  but that syntax cannot be the evaluated concept.
- `pointers` remains selectable.
- `POST /api/games/generate/` requires `cover_topics` and may accept optional
  `emphasize_topics` for the deferred backend feature. The student client sends
  only `cover_topics`.
- `problem_types` is removed from the supported request/response settings
  contract. Legacy input containing it is ignored for compatibility; the server
  always creates solution-comparison tasks and does not echo the field.
- `emphasize_topics` defaults to `[]`, must be a subset of `cover_topics`, and
  remains in the backend settings and response for a future selector.
- Alternative task builders may remain private temporarily, but no public
  request or blueprint path may select them.

## Atomic Topic Contract

The following ordered 24-item catalog replaces the combined catalog in both
the frontend and backend. IDs are request values.

| ID | Checkbox label | Topic-specific boundary |
| --- | --- | --- |
| `variables` | Variables | Declaring, storing, or updating a value. |
| `primitive-data-types` | Primitive data types | Selecting a primitive type for a representation or range. |
| `operations` | Operations | Arithmetic or comparison operation behavior. |
| `iostream` | iostream input/output | Reading from or writing to a stream. |
| `if` | if statements | A single conditional branch. |
| `else-if` | else if statements | Ordered multi-branch conditional selection. |
| `else` | else statements | Fallback behavior when a condition is false. |
| `switch` | switch statements | Discrete case selection and default behavior. |
| `compound-boolean-expressions` | Compound boolean expressions | Combining conditions with `&&`, `||`, or `!`. |
| `order-of-precedence` | Order of precedence | Parenthesizing/evaluating an expression by precedence. |
| `while-loops` | while loops | Pre-condition repetition. |
| `do-while-loops` | do-while loops | Post-condition repetition with at least one execution. |
| `strings` | string methods and manipulation | String operations only. |
| `for-loops` | for loops | Counter-controlled traditional `for` iteration. |
| `for-each-loops` | for-each loops | Range-based iteration. |
| `arrays` | arrays | Fixed-size indexed collection behavior. |
| `vectors` | vectors | Dynamic `std::vector` behavior. |
| `functions` | functions and function prototypes | Declaration, prototype, parameter, return, or call contract. |
| `pass-by-reference` | pass-by-reference | Mutation or aliasing through a reference parameter. |
| `pass-by-value` | pass-by-value | Copy semantics and no mutation of the caller value. |
| `fstream` | fstream file input/output | File stream read, write, or open behavior. |
| `structs` | structs | Struct organization and member access. |
| `classes` | classes | Encapsulation, member access, or object behavior. |
| `pointers` | pointers | Address, dereference, or pointer-safety behavior. |

## Public API Contract

`POST /api/games/generate/`

```json
{
  "cover_topics": ["arrays", "vectors"],
  "emphasize_topics": []
}
```

`cover_topics` is required, must be a list, is de-duplicated while preserving
order, and must contain at least one supported atomic ID. `emphasize_topics` is
optional and must contain supported values that are also in `cover_topics`.
The student client omits it until the future emphasis selector exists.

The response echoes only supported settings:

```json
{
  "settings": {
    "cover_topics": ["arrays", "vectors"],
    "emphasize_topics": []
  },
  "game": {
    "title": "CS1 Solution Spotlight",
    "tasks": [
      {
        "id": "task-1",
        "prompt": "Choose the best implementation...",
        "specifications": "...",
        "candidate_solutions": ["..."],
        "correct_solution_id": "A",
        "explanation": "..."
      }
    ]
  }
}
```

`problem_types` is ignored if sent by a legacy client, absent from responses,
and not represented in frontend API types. The generator supplies the fixed
internal value `solution comparison` for every task blueprint; validation no
longer requires or validates a problem-type list.

## UI and Accessibility

- Replace all teacher-authoring and teacher/student-play copy with student
  self-service copy. The configuration panel heading is **Create your practice
  game**.
- Render one `fieldset` with legend **Topics to cover**. Each topic is a native
  checkbox with a unique `id` and associated label; use one compact vertical
  row per topic, no groups and no multi-selects.
- Checked state is visibly distinct without color alone. Keyboard focus remains
  visible, and mouse, touch, keyboard, and label activation all toggle topics.
- Generation is disabled until at least one topic is selected. Selections stay
  intact after generation errors and while a generated or finished game is
  displayed.
- Remove visible emphasis and problem-style controls and their summaries. Do
  not retain a redundant summary unless it has a specific student benefit.

## Files and Style

- `frontend/src/api.ts`: replace the catalog/types; remove public
  problem-type fields; send only student-supported fields.
- `frontend/src/App.tsx`: checkbox state, student copy, and topic-only readiness.
- `frontend/src/App.css`: compact vertical checkbox rows, checked/focus states,
  and responsive layout.
- `frontend/src/App.test.tsx`: catalog, UI, API-payload, and game-flow tests.
- `backend/apps/core/game_generation.py`: atomic catalog; one profile per topic;
  optional emphasis; fixed solution-comparison blueprints; response changes.
- `backend/apps/core/tests.py`: API contract, profile-isolation, validation, and
  solution-comparison-only tests.

Use immutable catalog data. Keep HTTP names in snake_case and React state in
camelCase.

```tsx
<label htmlFor={`topic-${topic.id}`} className="topic-option">
  <input
    id={`topic-${topic.id}`}
    type="checkbox"
    checked={settings.coverTopics.includes(topic.id)}
    onChange={() => toggleTopic(topic.id)}
  />
  <span>{topic.label}</span>
</label>
```

## Testing Strategy

Frontend tests must prove the exact ordered 24-item catalog; absence of teacher,
emphasis, and problem-type controls; checkbox behavior and button readiness;
the cover-topics-only student request; and candidate selection, feedback, and
scoring.

Backend tests must prove a cover-topics-only request succeeds with empty
emphasis and no returned `problem_types`; legacy `problem_types` cannot alter
the mechanic; invalid topic/emphasis inputs are handled intentionally; all 24
topics have profiles and isolation coverage; and every task has three candidates
using solution-comparison (not debugging or specification-checking) mechanics.

## Commands

```bash
cd backend && ruff check .
cd backend && python manage.py check
cd backend && pytest
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test -- --run
cd frontend && npm run build
```

## Boundaries

- Always: validate at the Django boundary; preserve the health endpoint; keep
  the UI responsive and accessible; run all listed checks.
- Ask first: add dependencies, alter schema or CI, remove emphasis support, or
  add topics beyond this catalog.
- Never: expose a topic without a dedicated profile, reintroduce student
  problem-type choice, or add teacher-role behavior.

## Success Criteria

- Students select one or more of the exact 24 atomic topics from a compact
  vertical checkbox list to create a game.
- No student-facing teacher-authoring, emphasis, or problem-type controls remain.
- Each selectable topic produces questions specific to that topic alone.
- The student client sends no `problem_types`; the server never returns it and
  always builds solution-comparison multiple-choice tasks.
- Backend emphasis capability remains available for the later selector.
- Every command above succeeds.

## Implementation Tasks

1. Replace the topic catalog and implement/test 24 dedicated backend profiles.
2. Fix the generator to solution comparison and revise settings normalization,
   response, and validation without removing emphasis.
3. Implement the accessible student checkbox UI and student-facing copy.
4. Update all contract and game-flow tests; run the complete validation suite.
