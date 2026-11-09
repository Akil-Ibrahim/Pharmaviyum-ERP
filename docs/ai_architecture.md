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

Both the LangGraph pharmacist agent and RAG graph use opaque, versioned
HMAC-SHA-256 checkpoint thread identifiers derived from the authenticated
pharmacy, user, and conversation scope. The Redis dialogue-memory namespace
uses the same application secret to pseudonymize API-scoped session IDs. Keep
the application `SECRET_KEY` stable across deployments to preserve continuity;
rotating it changes derived identifiers.

Pseudonymizing keys does not encrypt checkpoint or Redis payloads. Checkpoint
state, conversation turns, summaries, and retrieved clinical context may still
contain sensitive data. Apply database/Redis access controls, encryption,
retention, backup protection, and deletion policies independently. New
application code does not read legacy plaintext Redis keys; their configured
seven-day TTL allows them to expire. An explicit memory-clear operation removes
the exact legacy keys for that authenticated session.

### Ingestion

Document ingestion is implemented under `src/pharmaviyum/ai/rag/ingestion` and is integrated with the project's Celery worker in the development Docker Compose stack.

Do not document a separate Kubernetes ingestion deployment; the repository no longer maintains a Kubernetes manifest tree.

## RAG and pharmacy AI evaluation

Retrieval ranking metrics and the offline synthetic benchmark are documented in [`devops/STAGE_1_AI_RAG_OFFLINE_RESULTS.md`](./devops/STAGE_1_AI_RAG_OFFLINE_RESULTS.md). The reusable retrieval evaluator currently covers Recall@K, Precision@K, MRR and nDCG using labelled relevant chunk IDs. The expanded evaluation contract is maintained in [`devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md`](./devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md).

Ragas may be used for answer/context metrics supported by the pinned installed version. Pharmacy-specific checks—including medication entity, ingredient, strength, dosage, dosage-form and route accuracy; negation preservation; contraindication and interaction accuracy; citation correctness; and clinical hallucination rate—require project-specific evaluators and pharmacist-reviewed ground truth. Do not present these custom measures as built-in Ragas metrics or treat an LLM judge as clinical ground truth.

Evaluation results must identify dataset, model, prompt, embedding and index versions, sample size and execution environment. Security and tenant-isolation failures are independent release blockers and must not be averaged into a composite quality score.

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

The JSON-RPC server permits public protocol initialization only. Tool, resource,
and prompt discovery/execution require a trusted authenticated tenant context.
Write tools are denied unless a trusted one-time approval verifier is configured;
a role flag or model-supplied argument is not sufficient approval. The active
MCP tool set is read-only until that approval workflow is implemented and
verified.

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

The repository also contains Prometheus/Grafana configuration under `docker/`. OpenTelemetry instrumentation boundaries, trace-context propagation, data-protection rules and observability acceptance criteria are documented in [`observability/opentelemetry.md`](./observability/opentelemetry.md).

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
