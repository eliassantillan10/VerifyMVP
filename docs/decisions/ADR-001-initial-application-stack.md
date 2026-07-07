# ADR-001: Initial Application Stack

## Status

Accepted

## Date

2026-07-07

## Context

VerifyMVP needs an initial web application foundation that supports a
relational data model, a Python backend, a React frontend, local development
with containers, and repeatable CI checks.

## Decision

Use PostgreSQL for the primary database, Django for the backend, React with
Vite and TypeScript for the frontend, Docker Compose for local development, and
GitHub Actions for build and test automation.

## Alternatives Considered

### SQLite

- Pros: Simple local setup and no external service required.
- Cons: Does not match the intended production database behavior.
- Rejected because the project explicitly needs PostgreSQL from the start.

### Flask or FastAPI

- Pros: Smaller backend surface for APIs.
- Cons: Django provides a batteries-included foundation for models,
  migrations, auth, admin, and future product workflows.
- Rejected in favor of the requested Django backend.

### Next.js

- Pros: Full-stack React framework with routing and server rendering.
- Cons: Adds backend overlap when Django is already the API owner.
- Rejected to keep the frontend focused on React client development.

## Consequences

- Backend and frontend can evolve independently with a clear API boundary.
- PostgreSQL is available in local Docker and CI, reducing database drift.
- CI can run backend, frontend, and Docker build checks independently.
- Future API changes need matching frontend contract validation and tests.
