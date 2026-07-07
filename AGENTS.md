# VerifyMVP Agent Context

Use this file as the routing guide for work in this repository. Prefer small,
verified changes and keep backend, frontend, Docker, CI, and documentation
concerns separated unless a task explicitly requires a full-stack slice.

## Repository Root

- Root files own cross-cutting project setup: `docker-compose.yml`,
  `.env.example`, `.gitignore`, `README.md`, `AGENTS.md`, and GitHub Actions.
- Keep secrets out of source control. Use `.env.example` for names and safe
  development defaults only.
- When changing runtime behavior, update README commands and CI if the workflow
  changes.

## `backend/`

- Django is the backend framework. The settings module is `config.settings`.
- PostgreSQL is the intended database. Configure it with `DATABASE_URL`.
- Place reusable API code under `backend/apps/`.
- Keep API responses stable and explicit. The current public contract is
  `GET /api/health/`.
- Validate user input at API boundaries before adding feature endpoints.
- Run `ruff check .`, `python manage.py check`, and `pytest` after backend
  changes.

## `frontend/`

- React, TypeScript, and Vite are the frontend stack.
- Use relative `/api/...` calls for backend endpoints during development; Vite
  proxies them to Django.
- Keep UI components accessible, responsive, and focused on real workflows.
- Put frontend tests next to the code they cover when practical.
- Run `npm run lint`, `npm run typecheck`, `npm test -- --run`, and
  `npm run build` after frontend changes.

## `docs/`

- Store architecture decision records in `docs/decisions/`.
- Add or update an ADR when changing framework, database, deployment, API, or
  other expensive-to-reverse architecture choices.

## `specs/`

- Store implementation plans and handoff specs for non-trivial work.
- Keep specs concrete: relevant files, ordered tasks, acceptance criteria, and
  validation commands.

## `.github/workflows/`

- CI should install dependencies from committed manifests, run lint/type/test
  gates, and build containers.
- Keep CI credentials scoped to test environments. Do not add production
  secrets to workflow files.

## Docker

- `docker-compose.yml` is the default local runtime for the full app.
- Backend and frontend Dockerfiles live with their respective app code.
- If a Docker command changes, keep README quick-start commands in sync.
