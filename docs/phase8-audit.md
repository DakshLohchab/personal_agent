# Phase 8 repository audit

## Scope

This audit records the observability, evaluation, and measurement capabilities present
before Phase 8 changes. The repository is a Python 3.13 FastAPI application with a
deterministic simulator, provider-neutral LLM ports, Phase 5 orchestration, PostgreSQL
persistence, and a Next.js frontend.

## Existing observability

- `services/api/logging.py` configures the standard-library logger
  `life_sandbox.api`.
- `services/api/main.py` logs application startup and request method/path/status, but
  does not currently include duration, correlation IDs, route operation names, or
  structured error categories.
- `services/memory/service.py` logs memory creation, approval, and retrieval with safe
  user and operation metadata. Memory content is not logged.
- No metrics registry, timer abstraction, tracing provider, OpenTelemetry/Sentry/Better
  Stack integration, or evaluation-record abstraction exists.

## Existing traces and correlation

There is no request or decision-run trace context. Phase 5 creates a UUID run ID in
`AgentContext`; child metadata references that ID, but the ID is not propagated into
logs, jobs, LLM calls, or tool executions. Background jobs have a separate queue ID.

## Existing agent-run metadata and persistence

`packages/schemas/agents.py` already defines `AgentRunMetadata` with run/parent IDs,
agent identity/version, model, prompt version, status, timestamps, input/output hashes,
error fields, and a tool-call list. `services/agents/specialists.py` populates a subset
of this metadata, and `services/agents/orchestrator.py` returns it.

`AgentRunModel` and migration `20261004_0003_phase5_agent_runs` persist concise,
user-scoped agent metadata plus tool-call and output snapshots. The persistence model
does not yet include duration, token usage, estimated cost, correlation ID, or a
standardized error category. The orchestration path currently does not write metadata
to this repository.

## Existing LLM/provider boundary

`packages/ports/llm.py` provides provider-neutral `LLMRequest`, `LLMResponse`, and
optional `LLMUsage`. Nebius and Token Harbor adapters use the same OpenAI-compatible
shape and extract prompt/completion/total token counts when providers return usage.
Provider calls have no duration, retry, structured-output outcome, tool outcome, or
cost metadata. Provider-specific behavior remains isolated in `services/llm`.

## Existing tools, simulator, memory, and jobs

- `DeterministicToolRegistry` allowlists `simulate_scenario`, `run_sensitivity`, and
  `find_breakpoint`, validates inputs, and returns typed results.
- `services/simulator` is deterministic and is the mathematical source of truth.
  No tool timing or execution records exist.
- `MemoryService.retrieve_relevant_memories` enforces user-scoped repository access,
  active/expiry filtering, and structured/semantic ranking. Retrieval has a log entry
  but no duration or evaluation record.
- `LocalJobQueue` exposes queued/running/completed/failed status but has no submit,
  duration, failure-category, or run correlation telemetry.

## Existing evaluation/test infrastructure

The suite includes deterministic unit/property tests, API integration tests, provider
adapter tests, persistence boundary tests, and Phase 5 orchestrator tests. Golden
deterministic cases are in `tests/fixtures/golden_cases.py`. There is no dedicated
`tests/evaluation` suite, evaluation dataset, metric scorer, or offline workflow
evaluation. Tests do not require live provider credentials.

## Exact missing pieces

1. A provider-neutral observability boundary for correlation IDs, timers, events, and
   metrics.
2. Request, decision, agent, tool, LLM, memory, research, and job duration/status
   measurements.
3. Safe structured error categories and correlation-aware request logs.
4. LLM telemetry enrichment and a deterministic pricing/cost-estimation layer.
5. Traceable tool and agent execution metadata without unrestricted prompts or
   chain-of-thought.
6. Optional persisted run-level measurement fields on the existing agent-run table.
7. A backend-only local inspection surface for recent run telemetry.
8. Configurable execution guardrails.
9. Offline evaluation fixtures, metrics, and representative evaluation tests.
10. Phase 8 documentation and verification instructions.

## Exact files to modify

- `services/api/main.py`, `services/api/logging.py`, and `services/api/errors.py` for
  request correlation, timing, safe structured events, and error categorization.
- `packages/ports/llm.py`, `services/llm/nebius.py`, and
  `services/llm/token_harbor.py` for optional provider-neutral telemetry.
- `services/application/ai_service.py` and `services/application/ai_tools.py` for
  LLM/tool measurement.
- `services/agents/specialists.py`, `services/agents/orchestrator.py`, and
  `services/agents/jobs.py` for trace construction, timing, and guardrails.
- `services/memory/service.py` for retrieval measurement.
- `services/api/dependencies.py` and relevant API routers for configuration and a
  backend-only inspection endpoint.
- `services/persistence/models.py` and the next Alembic revision only if persistence
  is necessary after implementation.
- `tests` files adjacent to each changed boundary for focused regression coverage.

## New files required

- `services/observability/` provider-neutral telemetry, timing, cost, and error
  categorization modules.
- `tests/evaluation/` fixtures and offline evaluation tests.
- `tests/unit/observability/` focused telemetry, pricing, and guardrail tests.
- `docs/phase8-evaluation-observability.md`.

## Migration requirements

The existing `agent_runs` table is the correct persistence boundary. A small additive
migration may add correlation ID, duration, token counts, estimated cost, and pricing
metadata if the implementation persists those measurements. No separate analytics or
tracing database is justified.

## Intentionally deferred

- External telemetry vendors and live exporters.
- A large analytics/dashboard platform.
- Full prompt/result transcript storage.
- Chain-of-thought capture.
- Provider/model replacement, speculative caching, or architecture redesign.
- Phase 9 production hardening, deployment redesign, authentication replacement, and
  new databases.

