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

The backend API runs at `http://localhost:8000`. Case Breaker reads reviewed
problems from PostgreSQL. The initial health contract is `GET /api/health/`.

### LM Studio grading (required when enabled)

LM Studio is the only authority for Case Breaker test-case grades. When
`CASE_BREAKER_GRADING_ENABLED=true`, load a model and start LM Studio's local
server before learners submit test cases. The browser never contacts LM Studio
directly and the service never executes C++.

Load a model that supports structured JSON output, start its local server, and
configure its exact identifier as shown by LM Studio (downloaded quantizations
often use a different ID):

```dotenv
CASE_BREAKER_GRADING_ENABLED=true
LM_STUDIO_GRADING_MODEL=qwen/qwen3-4b-2507
LM_STUDIO_GRADING_TIMEOUT_SECONDS=90
```

Grading is an assessment, not proof, and the model may return `UNCLEAR` only
when the submitted input or reviewed context cannot be assessed reliably.
Local models can take longer than ordinary web requests to
process a prompt, so grading has its own 90-second timeout by default. To
enable the separate coach, also set
`CASE_BREAKER_COACH_ENABLED=true` and `LM_STUDIO_MODEL`.

For host tools, verify the server with:

```bash
curl --fail --silent --show-error http://127.0.0.1:1234/v1/models
```

Docker Desktop's backend container must use
`LM_STUDIO_BASE_URL=http://host.docker.internal:1234`, which is the Compose
default. `127.0.0.1` inside that container refers to the container itself. To
verify container reachability after `docker compose up --build`, run:

```bash
docker compose exec -T backend python -c "from urllib.request import urlopen; print(urlopen('http://host.docker.internal:1234/v1/models', timeout=5).read().decode())"
```

If the host probe works but the container probe fails, check Docker Desktop
networking, LM Studio's bind address, and local firewall rules. If either probe
does not list the configured model ID, correct the loaded model or
`LM_STUDIO_GRADING_MODEL`. If LM Studio uses token authentication, set
`LM_STUDIO_API_TOKEN`; do not expose the server, model weights, or token.

The grading model must also return strict JSON-schema output. Before enabling
grading for learners, submit a small grading request in the app and confirm the
response contains a nonempty JSON object with `verdict` and `message`. A model
that returns an empty or malformed completion is reachable but incompatible
with this grading contract; the app reports that condition separately from a
stopped server or timeout.

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
