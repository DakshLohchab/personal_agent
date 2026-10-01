# Life Sandbox

Life Sandbox is a deterministic life-decision simulation project split into two phases.

- Phase 1 = deterministic simulation engine
- Phase 2 = API boundary around the validated engine
- Future phases will connect agents and tools to this API

## Install

```sh
uv sync
```

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
uv run uvicorn services.api.main:app --reload
```

## Swagger and OpenAPI

- Swagger: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Health: http://127.0.0.1:8000/health

## API overview

The backend exposes:

- GET /health
- POST /api/v1/simulations
- POST /api/v1/sensitivity
- POST /api/v1/breakpoints

The API layer validates input, converts to Phase 1 domain objects, calls the simulator, and serializes deterministic Decimal values as JSON strings.

See [docs/phase1.md](docs/phase1.md) for the Phase 1 contracts, examples, and modeling limits.