# VerifyMVP

VerifyMVP is a web application scaffold for validating MVP ideas with a
Django API, React frontend, PostgreSQL database, Docker-based local runtime,
and GitHub Actions quality gates.

## Project Structure

```text
.
├── backend/                 # Django project and API apps
│   ├── apps/core/           # Shared API endpoints, starting with health
│   └── config/              # Django settings, URLs, ASGI/WSGI entrypoints
├── frontend/                # Vite, React, TypeScript frontend
│   └── src/                 # UI, API client, tests, and styles
├── specs/                   # Planning specs for implementation work
├── docs/decisions/          # Architecture decision records
├── .github/workflows/       # CI workflows
├── docker-compose.yml       # Local app stack: Postgres, backend, frontend
├── .env.example             # Local environment template
└── AGENTS.md                # Repository context for AI coding agents
```

## Quick Start

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Start the full stack:

   ```bash
   docker compose up --build
   ```

3. Open the frontend at `http://localhost:5173`.

The backend API runs at `http://localhost:8000`, and the initial health
contract is `GET /api/health/`.

## Commands

| Command | Description |
| --- | --- |
| `docker compose up --build` | Build and run PostgreSQL, Django, and React |
| `docker compose down` | Stop the local stack |
| `cd backend && python manage.py migrate` | Run Django migrations |
| `cd backend && python manage.py check` | Validate Django configuration |
| `cd backend && pytest` | Run backend tests |
| `cd backend && ruff check .` | Lint backend Python code |
| `cd frontend && npm run dev` | Start the Vite dev server |
| `cd frontend && npm run lint` | Lint frontend code |
| `cd frontend && npm run typecheck` | Type-check frontend TypeScript |
| `cd frontend && npm test -- --run` | Run frontend tests once |
| `cd frontend && npm run build` | Build the frontend |

## Local Development

The Docker Compose stack is the default development path because it provides
PostgreSQL and uses the same `DATABASE_URL` shape as CI.

For local frontend-only work, run the Django backend on port `8000`, then run:

```bash
cd frontend
npm install
npm run dev
```

For local backend-only work, export the values from `.env.example` or use your
own PostgreSQL database, then run:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## API Contract

`GET /api/health/`

```json
{
  "status": "ok",
  "service": "VerifyMVP API",
  "database": "postgresql"
}
```

The React app validates this response before rendering it, so backend contract
changes should be made intentionally and with matching frontend test updates.

## CI

GitHub Actions runs on pull requests and pushes to `main`:

- Backend: install Python dependencies, lint with Ruff, run Django checks,
  apply migrations against PostgreSQL, and run pytest.
- Frontend: install npm dependencies, lint, type-check, test, and build.
- Docker: build backend and frontend container images after tests pass.

## Architecture Notes

The initial stack decision is recorded in
[`docs/decisions/ADR-001-initial-application-stack.md`](docs/decisions/ADR-001-initial-application-stack.md).
