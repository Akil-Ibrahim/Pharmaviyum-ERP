# Pharmaviyum ERP/CRM — AI Architecture

## Purpose

This document describes the AI architecture that is currently implemented in `src/pharmaviyum/ai` and exposed through the FastAPI application.

The AI layer is part of the main backend and is deployed with the application stack.

## Runtime architecture

```text
Client / Frontend
       |
       v
FastAPI API (`src/pharmaviyum`)
       |
       +--> Auth + tenant context
       |
       +--> AI API (`/api/v1/ai/...`)
               |
               +--> Agent Harness
               |      +--> model routing / LLM
               |      +--> dialogue memory
               |      +--> guardrails
               |      +--> cache
               |
               +--> RAG graph
               |      +--> query transformation
               |      +--> tenant-safe retrieval
               |      +--> document grading
               |      +--> contextual compression
               |      +--> generation with source citations
               |
               +--> MCP tool layer
               |
               +--> observability / metrics
               |
               +--> PostgreSQL + pgvector
               +--> Redis
               +--> Ollama / configured LLM provider
```

## RAG

The current RAG implementation is under `src/pharmaviyum/ai/mortarium_rag/`.

### Retrieval guarantees

- Retrieval is scoped by authenticated pharmacy/tenant context.
- Country and language are carried through the query context.
- Retrieved documents are treated as untrusted input before generation.
- Stable source identifiers use the `src-{chunk_uuid}` format.
- `RAGResponse` materializes citations from returned sources when appropriate.
- Retrieval metrics do not include high-cardinality tenant, user, or session identifiers.

### Pipeline

```text
Query
  -> transform_query
  -> retrieve
  -> grade_documents
  -> compress
  -> generate
  -> guardrails
```

The graph requires an explicit checkpointer and derives the checkpoint/thread scope from the authenticated pharmacy and user context.

Both the Mortarium RAG graph and the pharmacist Agent Harness use opaque,
versioned HMAC-SHA-256 checkpoint thread identifiers. The digest is keyed with
the application `SECRET_KEY`; raw pharmacy, user, and conversation identifiers
must not be embedded in checkpoint metadata. Keep `SECRET_KEY` stable across
deployments to preserve checkpoint continuity. Rotating it changes derived
thread identifiers.

Agent Harness Redis dialogue-memory namespaces also use versioned HMAC-SHA-256
keys. Raw API-scoped session IDs are not embedded in Redis key names or
application log fields. The same `SECRET_KEY` stability requirement applies to
memory continuity. This pseudonymizes Redis key names only; it does not encrypt
conversation payloads. Redis transport security, access control, encryption at
rest, and retention controls remain mandatory infrastructure responsibilities.

The `v2` checkpoint identifiers and memory namespaces do not automatically
resume/read records written with the former plaintext `rag:`, `agent:`, or
`agent:memory:` formats. Existing checkpoint and memory records are not
rewritten by application startup. The previous memory tiers have a bounded
seven-day TTL and are allowed to expire naturally; no unsafe legacy-key
fallback is performed. Before any compatibility migration, verify authenticated
tenant ownership and retention requirements. Checkpoint payload retention and
deletion remain separate PHI lifecycle responsibilities.

### Ingestion

Document ingestion is implemented under `src/pharmaviyum/ai/rag/ingestion` and is integrated with the project's Celery worker in the development Docker Compose stack.

Do not document a separate Kubernetes ingestion deployment; the repository no longer maintains a Kubernetes manifest tree.

## Agent Harness and memory

The Agent Harness provides the application-level orchestration around LLM calls.

Current responsibilities include:

- model routing;
- dialogue memory;
- guardrails;
- caching;
- tool access;
- observability.

Dialogue memory supports summary/fact compression and recent-message retention. The harness injects the agent's configured main LLM into memory summarization instead of creating a hidden second LLM client.

Memory is scoped to the authenticated API session and supports TTL/trim/clear operations.

## MCP tools

The project contains an MCP implementation under `src/pharmaviyum/ai/mcp`.

It provides a JSON-RPC 2.0 server and a registry for tools/resources. MCP authorization is integrated with application roles and pharmacy membership.

MCP is an internal application component; it is not a separate top-level deployment service.

## API surface

AI endpoints are implemented under `src/pharmaviyum/api/v1/ai.py`.

The API currently provides query/streaming, ingestion-related operations, and AI health/metrics integration. Exact request and response schemas should be taken from the FastAPI OpenAPI schema rather than copied into this document.

Local API documentation:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Metrics: `http://localhost:8000/metrics`

## Observability

The AI/RAG layer uses application metrics and optional tracing integrations.

Important RAG metrics include retrieval totals and retrieval latency. Metric labels are deliberately kept low-cardinality; do not add `session_id`, user IDs, pharmacy IDs, or similar identifiers to Prometheus labels.

The repository also contains Prometheus/Grafana configuration under `docker/`.

## Data and infrastructure

Development Docker Compose currently provides:

- PostgreSQL 16 with pgvector;
- Redis 7 in the development Compose/CI profile (the managed deployment configuration uses a Redis-compatible Valkey service);
- Ollama;
- FastAPI API;
- Celery ingestion worker.

FastAPI Cloud is the hosted application deployment target. GitHub Actions provides CI and a manually triggered deployment workflow; database, cache, and other required services must be provisioned and configured separately.

The repository does not use a separate Kubernetes AI deployment; Mortarium remains an application-level AI layer.

## LLM deployment profiles

Mortarium uses different LLM profiles depending on the deployment target:

| Deployment | LLM provider | Default model profile |
|---|---|---|
| FastAPI Cloud deployment | Gemini cloud provider | Main: `gemini-3.5-flash`; Fast: `gemini-3.5-flash-lite`; Complex/evaluation: `gemini-2.5-pro`; Embeddings: `gemini-embedding-001` |
| Ansible / on-premises pharmacy deployment | Ollama | Qwen3.5 9B Q4_K_M |

This separation is intentional: FastAPI Cloud is the hosted application deployment target, while Ansible provisions the local Ollama-based Mortarium runtime for on-premises installations. Gemma is not the current default; it can be introduced later as an additional Ollama profile without changing the Mortarium architecture.

## Configuration

Use `.env.example` for local configuration and `.env.prod.example` as the production configuration reference.

The current Python dependency source of truth is `pyproject.toml` for direct dependency declarations and `uv.lock` for resolved versions. CI installs the locked environment with `uv sync --frozen`. Do not introduce a second authoritative dependency list or a separate `requirements-ai.txt` file.

## Local startup

```bash
cp .env.example .env

docker compose up --build
```

Or start the API directly after installing dependencies:

```bash
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn src.pharmaviyum.main:app --reload --port 8000
```

## Design principles

1. Tenant isolation is enforced before retrieval and generation.
2. LLM output is not trusted as a source of truth; retrieved sources and guardrails remain authoritative.
3. Source citations use stable chunk identifiers.
4. Production deployment has one canonical release path.
5. Documentation describes implemented behavior, not planned infrastructure.
