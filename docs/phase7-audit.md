# Phase 7 Audit

## Existing memory functionality

- `MemoryModel` and the `memories` table already exist.
- Memory records currently contain `memory_type`, free-form `content`, optional
  `structured_data`, optional provenance type/reference, confidence, status,
  retention policy, expiration, and timestamps.
- `MemoryService` delegates basic create/get/list/update/delete operations to the
  user-scoped repository.
- `/api/v1/memories` currently exposes create, list, embedding search, update,
  and delete operations.
- The generic repository applies authenticated user scoping to every operation.
- There is no candidate approval workflow, typed policy validation, expiration
  filtering, supersession behavior, or dedicated decision-context retrieval.

## Existing vector functionality

- PostgreSQL `pgvector` is enabled by the Phase 3A migration.
- `EmbeddingModel` stores embeddings for exactly one memory, document chunk, or
  evidence record.
- `SqlAlchemyEmbeddingRepository` performs user-scoped cosine-distance search and
  excludes only memories with `status = 'archived'`.
- The repository/port layer already provides an embedding abstraction; no
  second vector database is needed.

## Existing user/profile functionality

- `ProfileModel` is the ownership root for user-owned records.
- `AuthPrincipal` is supplied through the API dependency layer.
- `SqlAlchemyUnitOfWork` binds `app.user_id` to each transaction, and repository
  methods require that transaction plus matching user IDs.
- Cross-user access is therefore rejected by repository ownership checks and
  PostgreSQL row-level-security context where configured.
- The default authentication dependency is still an integration stub and tests
  provide fake principals.

## Existing agent-context functionality

- Phase 5 defines typed `AgentContext` and `AgentRequest` contracts.
- `DecisionOrchestrator` creates one context and sends it to all specialists,
  then runs deterministic simulations and synthesis.
- Current context contains the interpretation, model, run ID, user ID, and
  prompt version; it does not contain retrieved memory.
- Specialists receive context but do not directly access repositories.
- AI routes currently call the orchestrator without an authenticated user ID,
  so memory injection must be added without changing deterministic simulation
  ownership or result authority.

## Phase 6 frontend/context functionality

- The Next.js page provides decision input, optional context, interpretation,
  deterministic comparison, scenario graph, specialist panels, and timeline.
- `apps/web/lib/api.ts` centralizes API calls and `apps/web/lib/types.ts`
  contains typed decision/agent response contracts.
- There is no memory list, approval/edit/delete control, provenance display, or
  decision-memory context surface.

## Gaps against Phase 7

1. Replace free-form memory type/status/provenance handling with constrained
   application policy while preserving the existing table.
2. Add `last_confirmed_at` and a migration; retain existing structured fields.
3. Make candidate creation explicit and approval the only promotion path.
4. Implement expiration/lifecycle-aware structured retrieval with deterministic
   precedence and current-input override behavior.
5. Ensure semantic retrieval filters ownership, approved/active lifecycle, and
   expiration before returning context.
6. Add typed decision-memory context with provenance and user-readable reasons.
7. Inject controlled memory context into Phase 5 orchestration and expose it in
   AI responses without allowing agents to mutate memory.
8. Add approve/propose/relevant-memory API operations and consistent validation.
9. Add the Phase 6 personal-memory UI and frontend API/types/tests.
10. Add backend, integration, and frontend tests for lifecycle, ownership,
    provenance, retrieval, precedence, and end-to-end control.
11. Add safe memory-operation observability and Phase 7 documentation.

## Exact files to modify

- `services/persistence/models.py`
- `services/persistence/repositories/memory_repository.py`
- `services/persistence/repositories/embedding_repository.py`
- `services/memory/service.py`
- `services/api/routers/memories.py`
- `services/api/routers/ai.py`
- `services/agents/orchestrator.py`
- `packages/schemas/agents.py`
- `packages/ports/repositories.py`
- `apps/web/app/page.tsx`
- `apps/web/lib/api.ts`
- `apps/web/lib/types.ts`
- `migrations/versions/` (new Phase 7 migration)

Tests will be added under the existing backend and frontend test directories.

## Exact new files

- `docs/phase7-audit.md` (this audit)
- `docs/phase7-personal-memory.md`
- one Phase 7 Alembic migration under `migrations/versions/`
- focused memory service/API/orchestration tests and frontend memory tests

## Migration requirements

- Extend `memories` with `last_confirmed_at`.
- Add only indexes/constraints required by the lifecycle policy.
- Do not create another memory table or vector system.
- Preserve the existing migration chain and `pgvector` embedding table.

## Explicitly deferred functionality

- Autonomous unrestricted memory formation.
- Long-term conversation transcript storage.
- Browser-side embeddings or frontend semantic search.
- Automatic storage of files, prompts, agent reasoning, secrets, or sensitive
  source material as memory.
- New authentication, cloud infrastructure, Redis, QStash, or Phase 8/9 work.
