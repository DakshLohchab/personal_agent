# Phase 7: Personal Memory

## Architecture

```text
Current decision input ──┐
                         ├─> MemoryService ──> approved, valid memories
Saved candidate ─> user approval ────────────┘          │
                                                        v
                                            Phase 5 AgentContext
                                                        │
                              deterministic simulator remains authoritative
```

## Model and lifecycle

Memories are user-owned structured records in the existing `memories` table.
Supported types are `preference`, `stable_constraint`, `goal`, `commitment`,
`past_decision`, `correction`, and `workflow_pattern`. A proposed memory starts
as `candidate`; explicit approval changes it to `active`. Existing facts may be
`superseded`, `expired`, or `deleted` (forgotten). `last_confirmed_at` records
the latest explicit approval.

The service rejects credentials and secret-like content. It does not store
conversation transcripts, uploaded files, or agent reasoning automatically.

## Provenance and retrieval

Each memory preserves a provenance type/reference and confidence. Relevant
context is retrieved only for the authenticated user, active records, and
non-expired records. Structured token overlap is deterministic; an existing
pgvector embedding search may supplement it. Semantic search is still
ownership/status/expiration filtered. Equal-ranked records use confirmation,
update time, and identifier ordering.

The decision context exposes a user-readable provenance label and retrieval
reason. Current decision keys are excluded from conflicting saved structured
values, so temporary assumptions in the current request take precedence and
do not mutate permanent memory.

## Agent integration

The supervisor receives a typed `DecisionMemory` list in `AgentContext`. Agents
can read this explicit context but have no repository access and cannot mutate
memory. Writes must use the memory API/service. Simulation outputs continue to
come from deterministic tools and are not replaced by memory or agent output.

## User controls and API

- `GET /api/v1/memories` lists owned records.
- `POST /api/v1/memories` proposes a candidate.
- `POST /api/v1/memories/{id}/approve` activates a candidate.
- `PATCH /api/v1/memories/{id}` edits owned content/structured data.
- `DELETE /api/v1/memories/{id}` forgets the record through a soft delete.
- `POST /api/v1/memories/relevant` retrieves decision-specific context.
- Existing semantic `/search` remains available for internal embedding use.

The frontend renders provenance, status, confirmation date, approval, and
forget controls. It does not calculate relevance, expiry, ownership, or
simulation values.

## Security and observability

All persistence calls require the authenticated user and transaction-bound
ownership context. Vector retrieval applies the same ownership and lifecycle
filters. Memory logs contain operation metadata and counts, never full content,
financial values, private documents, or secrets.

## Testing and limitations

Tests use repository fakes/mocks and cover lifecycle, policy validation,
provenance, expiration, precedence, vector filtering, ownership, orchestration
context, and frontend controls. Candidate proposal is intentionally explicit;
there is no automatic memory extraction or background promotion. Editing UI is
limited to the backend patch surface and can be expanded in a later phase.
