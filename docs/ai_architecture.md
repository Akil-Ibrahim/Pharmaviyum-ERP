# Pharmaviyum CRM — AI Architecture

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

The current RAG pipeline is implemented in `src/pharmaviyum/ai/rag`.

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
- Redis 7;
- Ollama;
- FastAPI API;
- Celery ingestion worker.

Production release deployment is handled through GitHub Actions, GHCR, Ansible, and `deploy/docker-compose.release.yml`.

The repository does **not** use the removed `gateway/`, `infra/`, or `monitoring/` scaffolding as active deployment paths.

## Configuration

Use `.env.example` for local configuration and `.env.prod.example` as the production configuration reference.

The project currently installs runtime dependencies from `requirements.txt`. `pyproject.toml` and `uv.lock` are also maintained and are the planned long-term dependency source of truth; do not introduce a new `requirements-ai.txt` file.

## Local startup

```bash
cp .env.example .env

docker compose up --build
```

Or start the API directly after installing dependencies:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn src.pharmaviyum.main:app --reload --port 8000
```

## Design principles

1. Tenant isolation is enforced before retrieval and generation.
2. LLM output is not trusted as a source of truth; retrieved sources and guardrails remain authoritative.
3. Source citations use stable chunk identifiers.
4. Production deployment has one canonical release path.
5. Documentation describes implemented behavior, not planned infrastructure.
