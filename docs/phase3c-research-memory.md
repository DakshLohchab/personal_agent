# Phase 3C: research and memory

## Provider interfaces

`ResearchProvider` returns normalized `ResearchResult` values. `TavilyResearchProvider`
contains all Tavily HTTP details; the research service only depends on the port. The
`EmbeddingProvider` port supports single and batch embedding, while `VectorStore`
defines upsert, exact similarity search, and deletion.

## Research flow

`ResearchService` calls a provider, creates a user-owned research query, bounds snippets
to 2,000 characters, hashes the stored snippet, and persists source metadata. It never
turns a snippet into a claim. Provider failures are exposed as safe application errors.

## Evidence model

Evidence links a user-owned claim and bounded evidence text to a research source. The
source URL and evidence hash are retained as provenance. An externally derived
assumption must reference evidence; user-provided assumptions may omit it.

## Memory types

Structured memories support `goal`, `constraint`, `preference`, `decision`, `correction`,
`workflow`, and `fact`. Each memory has explicit provenance, confidence, status,
retention metadata, and optional expiry. Files and document chunks are never
automatically converted into memories.

## Embedding storage and vector search

Embeddings are stored in PostgreSQL with `model_name`, dimensions, and a pgvector value.
The initial retrieval implementation uses exact cosine distance. Queries filter by
authenticated `user_id`, model name, owner, and active status; archived memories are
excluded. Raw vectors are not returned by the memory API.

## Ownership

Research queries own sources transitively. Evidence, assumptions, memories, files,
documents, chunks, and embeddings carry direct user ownership or validate a user-owned
parent before insertion. PostgreSQL RLS and repository transaction checks provide
defense in depth.

## Testing strategy

Unit tests use fake research and embedding providers. Persistence tests use local
PostgreSQL with pgvector and verify provenance, exact search, archived exclusion,
cross-user isolation, and file-document-chunk relationships. Live Tavily and R2
services are not required in CI.
