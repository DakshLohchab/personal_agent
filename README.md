# Life Sandbox

Life Sandbox is an offline decision-simulation engine. Phase 1 provides typed domain schemas, branchable scenarios, deterministic monthly simulation, seeded uncertainty sampling, sensitivity analysis, and constraint breakpoint search.

## Setup

Install `uv`, then run:

```sh
uv python install 3.13
uv sync --all-groups
```

## Run

```sh
uv run python -m services.simulator
```

## Validate

```sh
uv run pytest tests/unit -q
uv run pytest tests/property -q
uv run ruff check .
uv run pyright
```

See [docs/phase1.md](docs/phase1.md) for the Phase 1 contracts, examples, and modeling limits.