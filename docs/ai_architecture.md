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


### Agent and memory prompt boundaries

Agent policy is sent in a dedicated `SystemMessage`. Authenticated request
metadata, historical Redis memory, retrieved RAG evidence, and tool results
remain untrusted content in human/tool messages; they must never be interpolated
into the system-policy message. The agent inserts a separately marked
`untrusted_reference_context` message before the latest user request.
Intent routing and memory summarization also use separate system and data
messages. User-controlled delimiters are escaped before structured context is
assembled.

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

The graph requires an explicit PostgreSQL-backed checkpointer. **Both LangGraph checkpoint namespaces are now patient-scoped and pseudonymized:** `PharmacistAgent._thread_id()` derives `agent:v2:<HMAC-SHA256 digest>`, while `LangGraphRAG._thread_id()` derives `rag:v2:<HMAC-SHA256 digest>`. Both digests bind pharmacy, authenticated user, patient (including an explicit no-patient scope) and session. At the API boundary, synchronous and streaming endpoints derive `mortarium-session:v3:<HMAC-SHA256 digest>` only after tenant authorization and patient-to-pharmacy validation. This implementation was merged into `main` by [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287). See the [Mortarium RAG audit](./rag_architecture_audit.md), [ADR-0003](./adr/ADR-0003-patient-scoped-ai-state.md), and [patient-session isolation contract](./ai/patient-session-isolation.md).

Agent Harness Redis dialogue-memory namespaces use HMAC-SHA-256 keys derived from the API-scoped session ID and therefore inherit the patient boundary. This pseudonymizes Redis key names only; it does not encrypt conversation payloads. Redis transport security, access control, encryption at rest, and retention controls remain mandatory infrastructure responsibilities.

The namespace change intentionally does not resume records written under former key formats. Existing Redis memory and PostgreSQL checkpoint records are not rewritten at application startup. Memory has a bounded seven-day TTL, but TTL is not a complete PHI retention/deletion policy. Checkpoint payloads can contain questions and retrieved clinical context; retention, deletion, backup expiry and restore behavior remain separate PHI lifecycle responsibilities.

**Release gate:** the isolation code is merged into `main`, but the staged end-to-end Patient A → Patient B → no-patient session-switch test, using one client session across streaming and non-streaming paths with real Redis and PostgreSQL checkpoint persistence, and production activation are not evidenced here. Do not automatically delete legacy checkpoints or rotate `SECRET_KEY` without an approved migration/retention/rollback plan.

### Ingestion

Document ingestion used by the API is implemented under `src/pharmaviyum/ai/mortarium_rag/ingestion` and dispatched through the project's Celery worker. The API authorizes the pharmacy tenant before dispatch; the worker stamps canonical tenant/source metadata before chunking and vector persistence. A separate `IngestionOrchestrator` class is constructed by AI dependency initialization, but no API caller was found in this audit; its direct ingestion method does not explicitly stamp the same tenant metadata before the fail-closed vector-store upsert. Treat the Celery task path as canonical until the unused orchestrator is reconciled or retired.

Do not document a separate Kubernetes ingestion deployment; the repository no longer maintains a Kubernetes manifest tree.

## RAG and pharmacy AI evaluation

Retrieval ranking metrics and the offline synthetic benchmark are documented in [`devops/STAGE_1_AI_RAG_OFFLINE_RESULTS.md`](./devops/STAGE_1_AI_RAG_OFFLINE_RESULTS.md). The reusable retrieval evaluator currently covers Recall@K, Precision@K, MRR and nDCG using labelled relevant chunk IDs. The expanded evaluation contract is maintained in [`devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md`](./devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md).

Ragas 0.4.3 is declared in the `eval` dependency group in `pyproject.toml`, resolved in `uv.lock`, and loaded lazily by `src/pharmaviyum/ai/evaluation/ragas_adapter.py`; it is not a production runtime dependency. The CI RAG-evaluation job installs this group with `uv sync --frozen --group eval`, verifies the Ragas collections API import, and runs adapter/unit and golden-dataset tests. The adapter tests stub Ragas metric classes, so this is API/contract coverage rather than a measured run against a real judge model. Pharmacy-specific checks—including medication name/strength/form, negation, patient-context isolation, citation support and clinical hallucination—are implemented as project evaluators in `src/pharmaviyum/ai/evaluation/clinical_metrics.py`; they require labeled synthetic/de-identified data and, for claim support, an independent judge. These custom measures are not native Ragas metrics.

Evaluation results must identify dataset, model, prompt, embedding and index versions, sample size and execution environment. Security and tenant-isolation failures are independent release blockers and must not be averaged into a composite quality score. The evaluator supports separate Russian/English retrieval scores, but current application, RAG and ingestion defaults omit Russian; RU support and quality are therefore not established. See the current [Mortarium audit](./rag_architecture_audit.md).

## Runtime caveats

- `PgVectorStore` performs vector search plus PostgreSQL full-text search and reciprocal-rank fusion. A `RerankerPort` is optional, but no concrete reranker is injected by the current `AIComponents` runtime; `RAG_RERANK_TOP_N` is not an effective runtime control.
- `RAG_ENABLE_CONTEXTUAL_COMPRESSION` is declared but is not passed to `LangGraphRAG`; the compression node is always part of the compiled graph. `RAG_RRF_K`, `RAG_DEFAULT_LANGUAGES`, `RAG_MAX_CHUNK_TOKENS` and `RAG_CHUNK_OVERLAP` also need configuration-wiring review. The current Celery ingestion task uses per-job values with hard-coded defaults for chunk size/overlap.
- The model router uses query-length, keyword and context heuristics. It is not a validated clinical-risk classifier. The API's current confidence and safety-score fields are fixed warning-dependent presentation heuristics, not calibrated clinical probabilities.

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

Important RAG metrics include retrieval totals and retrieval latency. Metric labels are deliberately kept low-cardinality; do not add `session_id`, user IDs, pharmacy IDs, or similar identifiers to Prometheus labels. RAG node spans record bounded counts and outcomes, not prompts or clinical payloads. The existence of instrumentation does not prove an OTLP exporter, collector, alerting and retention policy are active in every deployment.

The repository also contains Prometheus/Grafana configuration under `docker/`. OpenTelemetry instrumentation boundaries, trace-context propagation, data-protection rules and observability acceptance criteria are documented in [`observability/opentelemetry.md`](./observability/opentelemetry.md).

## Data and infrastructure

The default development Docker Compose stack currently provides:

- PostgreSQL 18 with pgvector 0.8.7;
- Redis 8.8.4;
- Ollama;
- FastAPI API;
- Celery ingestion worker;
- local observability services where configured.

These are disposable development/CI targets only. Hosted Production uses Neon PostgreSQL 18 and a separately managed Redis endpoint; Demo must use isolated PostgreSQL 18 and its own managed Redis endpoint. Redis 8.8.4 is the compatibility target, not a claim about a provider-managed server version until verified. The legacy `docker-compose.prod.yml` file still contains PostgreSQL 16/Redis 7 images and is not an approved deployment path; do not use it for Production or Demo. Pharmacy Edge is a separately governed profile and is not the hosted Production/Demo data plane. See [the canonical Production/Demo baseline](deployment/PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.md).

FastAPI Cloud is the hosted application deployment target. GitHub Actions provides CI and a manually triggered deployment workflow; database, cache, and other required services must be provisioned and configured separately.

The repository does not use a separate Kubernetes AI deployment; Mortarium remains an application-level AI layer.

## LLM deployment profiles

Mortarium uses different LLM profiles depending on the deployment target:

| Deployment profile | LLM provider | Model profile | Status / boundary |
|---|---|---|---|
| FastAPI Cloud demo | QwenCloud API | `qwen3.8-flash` | Demo-only provider profile; free quota and provider-console Free quota only controls apply. |
| Ansible / on-premises production target | Local Ollama runtime | `Qwen3.5 9B Q4_K_M` | Target profile; hardware validation and production rollout are not yet complete. |

These are intentionally separate deployment profiles. The QwenCloud demo key, quota assumptions and cloud API configuration must not be copied into production Ansible inventories. The on-premises production target runs local inference through Ollama and is capacity-bound by the selected host's CPU/GPU, RAM, disk and concurrency limits. The primary production AI runtime is intended for Central; Edge-local inference is optional and must be explicitly approved per hardware profile. POS and other deterministic pharmacy transactions must never depend on Mortarium availability.

See [QwenCloud demo operations](./ai/QWENCLOUD_DEMO.md) for the demo profile and [Pharmacy Edge Ansible rollout](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) for the on-premises production target. Neither profile description is evidence of a completed live deployment.

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
