# Phase 8 evaluation and observability

## Architecture

The application uses a provider-neutral local boundary under
`services/observability`. Correlation context is carried with Python context variables;
events contain a name, status, monotonic duration, safe structured attributes, and a
correlation ID. The local in-memory sink is intended for tests and local inspection.
No vendor SDK or cloud telemetry service is required.

## Trace model

An API request receives or creates `x-correlation-id`. A decision run has a stable
`run_id`, and agent metadata references that run. Tool events include a generated
invocation ID, deterministic status, and duration. LLM responses include provider,
model, usage, duration, structured-output intent, tool-call count, and retry metadata.
Prompts, raw user context, full model output, and chain-of-thought are not telemetry.

## Metrics

- API request duration and status.
- LLM duration, provider/model, optional input/output/total tokens, structured output
  success, tool-call count, and retry count.
- Deterministic tool duration, success/failure, invocation ID, and deterministic flag.
- Agent duration, status, model, prompt version, and correlation ID.
- Offline evaluation pass rate, case count, and failure count.

Durations use monotonic timers. Monetary values are `Decimal` calculations.

## Cost measurement

`PricingCatalog` maps `(provider, model)` to versioned input/output prices per million
tokens. Unknown pricing or missing usage produces a null estimate; it is never presented
as an invoice. Costs can be aggregated from the LLM metadata at agent and decision-run
boundaries.

## Error taxonomy

The stable categories are `VALIDATION_ERROR`, `AUTH_ERROR`, `RATE_LIMIT`, `TIMEOUT`,
`PROVIDER_ERROR`, `TOOL_ERROR`, `RESEARCH_ERROR`, `DATABASE_ERROR`, `MEMORY_ERROR`,
`STRUCTURED_OUTPUT_ERROR`, and `INTERNAL_ERROR`. Existing public API error contracts
remain unchanged.

## Evaluation methodology

The offline suite reuses `tests/fixtures/golden_cases.py` and executes each deterministic
case twice with the same seed. It checks exact monthly ending cash, summary metrics, and
reproducibility. Contract and memory-policy tests use local fakes and require no cloud
credentials. Evaluation results are deterministic and objective; no subjective LLM
quality score is invented.

Run the evaluation suite with:

```sh
uv run pytest -q tests/evaluation
```

Run the full backend checks with:

```sh
uv run pytest -q
uv run ruff check .
uv run pyright
```

## Budget guardrails and limitations

The request schemas cap deterministic Monte Carlo samples and research results. The
orchestrator also supports configurable `MAX_AGENT_EXECUTIONS` (default `8`) and
`MAX_TOOL_CALLS` (default `100`) limits. Exceeded budgets raise an explicit
orchestration failure; provider-specific free-tier assumptions are not encoded.

## Privacy

Telemetry contains identifiers, statuses, durations, hashes, provider/model metadata,
and token counts only. It does not store passwords, credentials, private documents,
full sensitive memory text, unrestricted prompts, or unrestricted transcripts. Existing
user-scoped persistence and memory policy remain authoritative.

## Local inspection and known limitations

Events are available through the injectable `InMemoryObservability` sink for tests and
local debugging. There is no production dashboard, exporter, persistent analytics
store, or live-provider evaluation. Agent-run persistence remains the existing
user-scoped boundary and is not expanded until a caller requires durable telemetry.
