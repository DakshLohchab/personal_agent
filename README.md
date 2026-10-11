# Life Sandbox

Life Sandbox is a decision-support app that compares possible futures using a deterministic simulation engine. AI helps structure a decision, coordinate specialist analysis, and explain results; the simulator remains the source of truth for numerical projections.

## What’s in the repository

- **Backend:** Python 3.13, FastAPI, and a deterministic simulation engine with scenario, sensitivity, and breakpoint analysis.
- **AI and orchestration:** provider-neutral LLM interfaces, Nebius Token Factory and Token Harbor adapters, and NeMo Agent Toolkit orchestration with allowlisted deterministic tools.
- **Persistence and services:** PostgreSQL/SQLAlchemy/Alembic repositories, private Cloudflare R2 object storage, research and evidence services, and user-controlled personal memory with pgvector retrieval.
- **Frontend:** Next.js 15 and React 19 interface for decision input, interpretation, scenario comparison, specialist results, timeline, and memory controls.
- **Evaluation and observability:** deterministic evaluation cases, request correlation, safe operational events, and execution guardrails.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm for the web app
- Docker Compose and PostgreSQL with pgvector only for local database and persistence workflows

## Backend setup

Install the Python dependencies:

```sh
uv sync
```

Copy `.env.example` to `.env` and set only the integrations you plan to use. The root `.env` is ignored by Git, and shell environment variables take precedence. The deterministic simulator and health endpoint do not need database or provider credentials. Database-backed features and Alembic migrations need `DATABASE_URL`; AI routes need a key for the selected LLM provider.

### Start the API

```sh
uv run uvicorn services.api.main:app --reload --host "${API_HOST:-0.0.0.0}" --port "${PORT:-${API_PORT:-8000}}"
```

`PORT` takes precedence over `API_PORT`. The API is available at `http://127.0.0.1:8000` by default:

- Health: `GET /health`
- Interactive Swagger docs: `/docs`
- OpenAPI schema: `/openapi.json`
- Simulation: `POST /api/v1/simulations`
- Sensitivity analysis: `POST /api/v1/sensitivity`
- Breakpoint analysis: `POST /api/v1/breakpoints`
- AI interpretation and agent runs: `/api/v1/ai/interpret`, `/api/v1/ai/run`
- Research, evidence, files, and memories: see the corresponding `/api/v1` routes in Swagger

Simulation values are calculated by the deterministic engine and serialized as JSON strings for exact decimal values. AI explanations do not replace or modify those results.

### Database

For a local PostgreSQL database with pgvector, start the included Compose service and apply migrations:

```sh
docker compose -f docker-compose.db.yml up -d
export DATABASE_URL=postgresql+psycopg://life_sandbox:local_dev_only_change_me@localhost:55432/life_sandbox_dev
uv run alembic upgrade head
```

The Compose database uses a development-only password. For other environments, provide a PostgreSQL `postgresql+psycopg://` URL. See [docs/phase3a-database.md](docs/phase3a-database.md) for schema, migration, repository, and ownership details. To stop and remove the local database and its data:

```sh
docker compose -f docker-compose.db.yml down -v
```

### LLM and integrations

The default provider is Nebius. Configure `NEBIUS_API_KEY` in `.env` to use AI interpretation and agent runs. To use the development Token Harbor adapter instead, set `LLM_PROVIDER=token_harbor` and `TOKENHARBOR_API_KEY`. Provider base URLs, models, timeouts, and retry limits are configurable in `.env.example`. Keep all provider credentials server-side; never expose them through `NEXT_PUBLIC_` variables.

Research uses a fake provider when `TAVILY_API_KEY` is absent and Tavily when it is configured. File upload and download use private R2 storage; see `.env.example` and [docs/phase3b-r2.md](docs/phase3b-r2.md) for setup. Database-backed user routes require an authentication provider integration: `get_current_principal()` is currently a host integration stub, so production authentication is not included here.

## Web app

The Next.js frontend runs separately from FastAPI. In one terminal, start the API. In another:

```sh
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. By default, browser requests use the same-origin `/api` rewrite to FastAPI at `http://127.0.0.1:8000`. Set `INTERNAL_API_URL` when the API is hosted elsewhere. `NEXT_PUBLIC_API_BASE_URL` is optional for intentional direct browser-to-API access; configure backend CORS for that frontend origin. Provider, database, storage, and research credentials belong only in the backend environment. More details are in [apps/web/README.md](apps/web/README.md).

## Docker API image

```sh
docker build -t life-sandbox-api .
docker run --rm -p 8000:8000 life-sandbox-api
```

The image runs the FastAPI service. Supply required environment configuration when using integrations that need a database or credentials.

## Development checks

Backend:

```sh
uv run pytest -q
uv run ruff check .
uv run pyright
```

Frontend (from `apps/web`):

```sh
npm run typecheck
npm run lint
npm test
npm run build
```

PostgreSQL persistence integration tests use `TEST_DATABASE_URL` and skip when it is unset. The evaluation suite can also be run on its own with `uv run pytest -q tests/evaluation`.

## Architecture notes

- The simulator is deterministic and owns all numerical state and results.
- The AI layer can interpret decisions and call only validated, allowlisted simulation tools; it cannot override simulation output.
- Personal memories are user-controlled: candidates require explicit approval, and only valid, approved memories can inform a run.
- Database repositories enforce user scoping, with PostgreSQL row-level security as defense in depth.
- Agent and request telemetry excludes raw prompts, credentials, private documents, and chain-of-thought.

## Further documentation

- [Phase 1 simulation contracts and limits](docs/phase1.md)
- [Database and ownership](docs/phase3a-database.md)
- [Private R2 file storage](docs/phase3b-r2.md)
- [Research and memory foundations](docs/phase3c-research-memory.md)
- [Agent orchestration](docs/phase5-agent-orchestration.md)
- [Personal memory lifecycle](docs/phase7-personal-memory.md)
- [Evaluation and observability](docs/phase8-evaluation-observability.md)
