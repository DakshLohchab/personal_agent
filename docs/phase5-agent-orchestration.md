# Phase 5 agent orchestration

Phase 5 uses `nvidia-nat==1.8.0`, the stable NeMo Agent Toolkit release selected
for Python 3.13. The project registers
`services.agents.nat_components` through NAT's `nat.components` entry-point
group. The configuration uses NAT's `functions` and `workflow` sections with
`_type` values resolved by those registrations.

The NAT adapter keeps workflow ownership in `DecisionOrchestrator`;
deterministic tools remain the numerical source of truth and the existing
Nebius `LLMProvider` remains the application model-configuration boundary.

The graph is:

`DecisionInterpretation -> parallel Finance/Time/Research/Risk/Opportunity ->
deterministic tools -> FutureYou -> Synthesis`

Only `simulate_scenario`, `run_sensitivity`, and `find_breakpoint` are exposed
through NAT-registered wrappers backed by the validated
`DeterministicToolRegistry`. Agent execution metadata is
stored in `agent_runs` by the user-scoped repository. `LocalJobQueue` provides
the synchronous development boundary; `QStashJobQueue` is an explicit adapter
boundary and is not required for simulator runs.

The API entry point is `POST /api/v1/ai/run`. It accepts either a Phase 4
`interpretation` or a decision request that is interpreted first. The current
implementation intentionally does not expose hidden reasoning, raw prompts, or
credentials.
