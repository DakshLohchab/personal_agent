# Life Sandbox

Life Sandbox is a full-stack life-decision simulation application. It combines a deterministic Python/FastAPI backend with a Next.js frontend for exploring financial and life decisions through simulations, comparisons, sensitivity analysis, breakpoints, timelines, and AI-assisted interpretation.

The deterministic simulator is the numerical source of truth. The LLM can interpret a decision, make explicit assumptions, select allowlisted tools, and explain returned results, but it cannot create or override simulation numbers.

## Project structure

```text
personal_agent/
├── apps/web/                 # Next.js frontend
├── packages/                 # Shared domain models and ports
├── services/
│   ├── api/                  # FastAPI application and routes
│   ├── application/          # Application services, AI orchestration and prompts
│   ├── agents/               # Agent/NAT orchestration
│   ├── llm/                  # LLM provider adapters
│   ├── observability/        # Cost and observability utilities
│   └── ...
├── migrations/               # Alembic database migrations
├── tests/                    # Backend tests
├── docs/                     # Architecture and phase documentation
├── config/                   # Workflow/configuration files
├── Dockerfile                # Backend container
└── docker-compose.db.yml     # Local PostgreSQL + pgvector
```

## Architecture

- Phase 1: deterministic simulation core.
- Phase 2: FastAPI boundary and application services around the validated core.
- Phase 3A: PostgreSQL persistence foundation and research workflows.
- Phase 3B/3C: research and memory foundations.
- Phase 4: provider-neutral structured LLM interpretation.
- Phase 5: agent orchestration.
- Phase 6: Next.js web frontend.
- Phase 7/8: memory controls, audit, evaluation, and observability foundations.

The repository contains the backend, frontend, database migrations, tests, documentation, and deployment configuration.

## Requirements

Backend:
- Python 3.13
- `uv`
- PostgreSQL with pgvector for database-backed functionality

Frontend:
- Node.js and npm
- Next.js 15
- React 19

Optional:
- Docker and Docker Compose
- An LLM provider API key for AI interpretation

## Quick start

### 1. Clone

```bash
git clone https://github.com/DakshLohchab/personal_agent.git
cd personal_agent
```

### 2. Install backend dependencies

```bash
uv sync
```

### 3. Configure the backend

Copy the example environment file:

```bash
cp .env.example .env
```

Set the required local/database configuration in `.env`. The root `.env` is ignored by Git.

Environment variables already exported in the shell take precedence over values loaded from `.env`.

### 4. Start PostgreSQL locally

The repository includes a pgvector PostgreSQL development service:

```bash
docker compose -f docker-compose.db.yml up -d
```

The development database is exposed on port `55432`.

Then run the migrations:

```bash
uv run alembic upgrade head
```

### 5. Start the backend

From the repository root:

```bash
uv run uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at:

- Health: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json

### 6. Start the frontend

Open a second terminal:

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

Open:

http://localhost:3000

By default, the Next.js frontend forwards same-origin `/api` requests to:

```text
http://127.0.0.1:8000
```

Set `INTERNAL_API_URL` in `apps/web/.env.local` if the backend is hosted somewhere else.

## Running without the database

The deterministic simulator and API startup do not require an external LLM provider. Database-backed functionality requires PostgreSQL.

For a basic backend check:

```bash
uv run uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

Then open the Swagger UI and use the deterministic simulation endpoints.

## API

The backend exposes:

```text
GET  /health
POST /api/v1/simulations
POST /api/v1/sensitivity
POST /api/v1/breakpoints
POST /api/v1/ai/interpret
```

The API validates input, converts it into domain objects, executes deterministic simulation logic, and serializes Decimal values as JSON strings.

## AI / LLM configuration

AI interpretation is optional. The deterministic simulator does not require an LLM API key.

### Nebius

For the intended hackathon configuration, set the provider to Nebius and provide a Token Factory API key:

```dotenv
LLM_PROVIDER=nebius
NEBIUS_API_KEY=your_key_here
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEBIUS_MODEL=nvidia/Nemotron-3_5-Lightning
NEBIUS_TIMEOUT_SECONDS=60
NEBIUS_MAX_RETRIES=2
```

The provider adapter is isolated under `services/llm`, while application services depend on provider contracts under `packages/ports/llm.py`.

### Token Harbor development provider

For local development/testing, the repository also supports Token Harbor:

```dotenv
LLM_PROVIDER=token_harbor
TOKENHARBOR_API_KEY=your_key_here
```

The development defaults use:

```text
https://tokenharbor.ai/v1
deepseek-v4.1-flash:free
```

Treat free provider routes as development/test services and review the provider's current terms and privacy conditions before sending sensitive information.

Provider credentials are backend-only. Never expose them through `NEXT_PUBLIC_*` variables or frontend source code.

## Deterministic tool execution

The AI layer uses an allowlisted deterministic tool registry for numerical operations. Tool results are authoritative.

The application validates structured LLM output before using it, and deterministic simulation state cannot be replaced by arbitrary model-generated numbers.

For incomplete user input, the application can return the missing information required before a fair simulation can be performed.

## Frontend

The frontend is located in `apps/web` and uses the Next.js App Router.

Main frontend responsibilities include:
- Decision input and simulation workflows
- Scenario comparison
- Future-path visualization
- Timeline presentation
- Specialist/AI result presentation
- API orchestration and typed frontend models

Frontend checks:

```bash
cd apps/web

npm run typecheck
npm run lint
npm test
npm run build
```

For direct browser-to-API deployments, `NEXT_PUBLIC_API_BASE_URL` can be configured and the backend CORS allowlist must include the frontend origin.

For Vercel deployments using the same-origin proxy, configure `INTERNAL_API_URL` to the deployed FastAPI origin.

## Backend checks

From the repository root:

```bash
uv run pytest -q
uv run ruff check .
uv run pyright
```

## Docker

Build and run the backend:

```bash
docker build -t life-sandbox-api .
docker run --rm -p 8000:8000 life-sandbox-api
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

For local PostgreSQL:

```bash
docker compose -f docker-compose.db.yml up -d
```

Stop it with:

```bash
docker compose -f docker-compose.db.yml down
```

## Database migrations

Check the current migration:

```bash
uv run alembic current
```

Apply migrations:

```bash
uv run alembic upgrade head
```

The application and Alembic use the same root `.env` configuration.

## Configuration

Backend configuration is documented in `.env.example`.

Important backend settings include:

```text
APP_ENV
API_HOST
API_PORT
PORT
CORS_ORIGINS
LOG_LEVEL
DATABASE_URL
LLM_PROVIDER
NEBIUS_API_KEY
NEBIUS_BASE_URL
NEBIUS_MODEL
TOKENHARBOR_API_KEY
```

Frontend configuration is documented in `apps/web/.env.example`:

```text
INTERNAL_API_URL
NEXT_PUBLIC_API_BASE_URL
```

Never commit real API keys, database credentials, or other secrets.

## Documentation

Architecture and implementation documentation is available under `docs/`, including:

- `docs/phase1.md` — deterministic simulation contracts, examples, and modeling limits
- `docs/phase3a-database.md` — database foundation
- `docs/phase3b-r2.md` — research workflow foundation
- `docs/phase3c-research-memory.md` — research and memory foundation
- `docs/phase5-agent-orchestration.md` — agent orchestration
- `docs/phase7-audit.md` — audit and memory controls
- `docs/phase7-personal-memory.md` — personal memory foundation
- `docs/phase8-audit.md` — audit architecture
- `docs/phase8-evaluation-observability.md` — evaluation and observability

## Security and data handling

- Keep provider credentials on the backend.
- Do not put secrets in `NEXT_PUBLIC_*` variables.
- Keep the root `.env` and frontend `.env.local` out of Git.
- Review third-party provider terms and privacy policies before sending sensitive information.
- The LLM is not the numerical source of truth; deterministic simulator output is authoritative.

## License

See the repository for the current project licensing and distribution terms.
