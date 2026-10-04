# Life Sandbox

Life Sandbox is a deterministic life-decision simulation project.

## Architecture

- Phase 1: deterministic simulation core.
- Phase 2: FastAPI boundary and application services around the validated core.
- Phase 3A: PostgreSQL persistence foundation and research workflows.
- Phase 4: provider-neutral structured LLM interpretation with Nebius Token Factory and
  NVIDIA Nemotron 3.5 Lightning.

Phases 3 and 4 are planned and are not implemented in this repository.

## Install

```sh
uv sync
```

## Local environment

Copy `.env.example` to `.env`, then replace the example `DATABASE_URL` with your real local or Neon connection string. The root `.env` file is local-only and ignored by Git. After that, commands load `DATABASE_URL` automatically:

```sh
uv run alembic current
uv run alembic upgrade head
uv run pytest
```

The application and Alembic use the same root `.env` loading behavior. Environment variables already set in the shell take precedence over values in `.env`.

## Run tests

```sh
uv run pytest -q
```

## Run lint

```sh
uv run ruff check .
```

## Run type checking

```sh
uv run pyright
```

## Run the API server

```sh
uv run uvicorn services.api.main:app --reload --host "${API_HOST:-0.0.0.0}" --port "${PORT:-${API_PORT:-8000}}"
```

Set configuration in the environment; `PORT` takes precedence over `API_PORT`.
See [.env.example](.env.example) for the supported variables.

## Phase 4 AI configuration

Create a Nebius account, generate a Token Factory API key, and put it in the local `.env`
file as `NEBIUS_API_KEY`. The key is only required when the AI endpoint is used; application
startup and deterministic simulator endpoints do not require it. The defaults are:

```dotenv
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEBIUS_MODEL=nvidia/Nemotron-3_5-Lightning
NEBIUS_TIMEOUT_SECONDS=60
NEBIUS_MAX_RETRIES=2
```

`NEBIUS_MODEL` can be changed to another Nebius model without changing application code.
The provider adapter is isolated under `services/llm`; application services depend only on
the contracts in `packages/ports/llm.py`. `POST /api/v1/ai/interpret` validates a structured
decision interpretation, executes only the allowlisted deterministic tools, and asks the
model to explain their results. Tests use a fake provider and do not need cloud credentials.

The simulator remains the mathematical source of truth. LLM output may interpret decisions,
propose explicit assumptions, select tools, and explain results, but it cannot create or
override numerical simulation state.

## Run with Docker

```sh
docker build -t life-sandbox-api .
docker run --rm -p 8000:8000 life-sandbox-api
```

Check the service with `curl http://127.0.0.1:8000/health`.

## Swagger and OpenAPI

- Swagger: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Health: http://127.0.0.1:8000/health

The server reads `APP_ENV`, `API_HOST`, `API_PORT`, `PORT`, `CORS_ORIGINS`, and `LOG_LEVEL`.

## API overview

The backend exposes:

- GET /health
- POST /api/v1/simulations
- POST /api/v1/sensitivity
- POST /api/v1/breakpoints
- POST /api/v1/ai/interpret

The API layer validates input, converts to Phase 1 domain objects, calls the simulator, and serializes deterministic Decimal values as JSON strings.

See [docs/phase1.md](docs/phase1.md) for the Phase 1 contracts, examples, and modeling limits.