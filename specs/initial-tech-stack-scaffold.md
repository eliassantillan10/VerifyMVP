# Feature: Initial Tech Stack Scaffold

## Feature Description

Create the baseline VerifyMVP web application stack with PostgreSQL, a Django
backend, a React frontend, Docker-based local runtime, GitHub Actions build and
test automation, and project documentation.

## User Story

As a developer working on VerifyMVP,
I want a working full-stack scaffold,
So that MVP features can be built against a consistent backend, frontend,
database, and CI foundation.

## Problem Statement

The repository started with only a license and a placeholder README. It needed
application structure, runtime configuration, tests, and documentation before
feature development could start.

## Solution Statement

Use a monorepo layout with `backend/` for Django, `frontend/` for Vite React,
PostgreSQL as the database, Docker Compose for local development, and GitHub
Actions for automated verification.

## Relevant Files

- `backend/` contains Django settings, health API endpoint, backend tests, and
  backend container build configuration.
- `frontend/` contains React application code, API client contract validation,
  frontend tests, and frontend container build configuration.
- `docker-compose.yml` defines the local PostgreSQL, backend, and frontend
  services.
- `.github/workflows/ci.yml` defines backend, frontend, and Docker build gates.
- `README.md`, `AGENTS.md`, and `docs/decisions/` provide onboarding and
  architecture context.

## Implementation Plan

### Phase 1: Foundation

- Add Django project structure and environment-driven settings.
- Add the first public API contract at `GET /api/health/`.
- Add backend tests for the health contract.

### Phase 2: Core Implementation

- Add Vite React TypeScript app.
- Add frontend API client validation for the health contract.
- Add a compact status UI and frontend component test.

### Phase 3: Integration

- Add PostgreSQL-backed Docker Compose runtime.
- Add backend and frontend Dockerfiles.
- Add GitHub Actions checks for backend, frontend, and Docker builds.
- Add README, AGENTS, and ADR documentation.

## Step by Step Tasks

### 1. Create Backend Baseline

- Create Django config and core app.
- Configure PostgreSQL through `DATABASE_URL`.
- Add `GET /api/health/` and a test for its response body.

### 2. Create Frontend Baseline

- Create Vite React TypeScript app.
- Add an API client for `/api/health/`.
- Add UI and tests that verify the backend contract renders.

### 3. Add Runtime and Automation

- Add Docker Compose with PostgreSQL, backend, and frontend services.
- Add backend and frontend Dockerfiles.
- Add GitHub Actions for lint, type checking, tests, migrations, builds, and
  Docker image builds.

### 4. Add Documentation

- Replace the placeholder README with project structure, commands, and setup.
- Add `AGENTS.md` with context for root, backend, frontend, docs, CI, and Docker.
- Add an ADR for the initial stack decision.

### 5. Validate

- Run available local checks.
- Note environment-blocked checks clearly.

## Testing Strategy

### Unit and Integration Tests

- Backend: Django test client verifies `GET /api/health/`.
- Frontend: Vitest and Testing Library verify the React app renders the validated
  health response.

### Edge Cases

- Frontend API client rejects unexpected health response shapes.
- Frontend UI displays an offline state when the backend request fails.

## Acceptance Criteria

- PostgreSQL is configured as the application database.
- Django backend exists with a tested health API.
- React frontend exists and consumes the backend health contract.
- Docker Compose can build and run the app stack in Docker-enabled environments.
- GitHub Actions defines backend, frontend, and Docker build checks.
- README and AGENTS.md describe project structure, commands, and agent context.

## Validation Commands

Run these commands to validate the scaffold:

```bash
python3 -m compileall backend
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test -- --run
cd frontend && npm run build
```

In an environment with Python packaging and Docker available, also run:

```bash
cd backend && pip install -r requirements.txt
cd backend && ruff check .
cd backend && python manage.py check
cd backend && python manage.py migrate --noinput
cd backend && pytest
docker compose up --build
```

## Notes

- The local multi-agent `plan-agent` spawn failed before an agent could be
  created, so this spec records the plan followed by the main agent.
- Local backend dependency verification was limited because the available
  `python3` executable did not include `pip`.
- Local Docker verification was limited because Docker was not installed in this
  WSL distro.
