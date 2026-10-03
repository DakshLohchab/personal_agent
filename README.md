# Life Sandbox

Life Sandbox is a deterministic life-decision simulation project.

## Architecture

- Phase 1: deterministic simulation core.
- Phase 2: FastAPI boundary and application services around the validated core.
- Phase 3A: PostgreSQL persistence foundation; later research workflows are not implemented.
- Phase 4 (planned): Nebius and Nemotron integration.

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

The API layer validates input, converts to Phase 1 domain objects, calls the simulator, and serializes deterministic Decimal values as JSON strings.

See [docs/phase1.md](docs/phase1.md) for the Phase 1 contracts, examples, and modeling limits.