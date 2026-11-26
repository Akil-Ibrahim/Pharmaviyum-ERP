# Mortarium AI / RAG Architecture Audit

**Audit date:** 2026-11-19  
**Audited ref:** `main` at `cec7ba8ad4fa8bc40cc0b3f870a17509ca4e2743`  
**Method:** Static source, configuration, documentation and test-contract review  
**Execution status:** No application tests, live model calls, production queries or deployment changes were executed as part of this documentation audit.

## Executive assessment

Mortarium is an application-level pharmacist assistant built around two LangGraph workflows: the pharmacist agent and a separate LangGraph RAG graph. The runtime also includes an Agent Harness, Redis dialogue memory and prompt cache, PostgreSQL/pgvector retrieval, Celery document ingestion, role-filtered MCP tools, medical guardrails and OpenTelemetry instrumentation.

The architecture has meaningful fail-closed controls: authenticated pharmacy context is established at the API boundary; patient IDs are checked against the selected pharmacy; pgvector retrieval requires a positive pharmacy ID; patient-level chunks require an explicit patient filter; MCP execution requires trusted request context and RBAC; and MCP writes are denied unless a trusted approval verifier is configured.

**The original P0 patient-context isolation finding is remediated in `main` by PR #287 (merge commit `4d761990b31ef3aa78327dda1380689f2d094e8f`).** The synchronous and streaming API now derive a versioned `mortarium-session:v4` HMAC namespace from pharmacy, authenticated user, patient (including explicit no-patient scope) and client session. Agent and RAG checkpoints independently derive opaque, versioned HMAC identifiers that include patient scope. Regression tests cover scope separation, invalid identifiers, tenant separation and secret rotation. The merge record reports the RAG Safety Regression, Unit Tests and Integration Tests checks as passed.

**Production readiness remains unproven.** The staged end-to-end release gate must still alternate Patient A → Patient B → no patient using one client session in both streaming and non-streaming paths, with actual Redis memory and PostgreSQL checkpoint persistence. Legacy plaintext RAG checkpoint records are not automatically migrated or deleted; their retention/deletion plan and rollback behavior require approval before rollout. This static review did not execute tests or inspect production state.

Other material gaps remain: Russian language/OCR/embedding quality needs measured RU/EN benchmarks; the runtime does not inject a dedicated reranker; several declared RAG settings are not wired into the runtime; and the separate `IngestionOrchestrator` is not the API's active ingestion path.

## Runtime map

| Layer | Current implementation | Audit assessment |
|---|---|---|
| API boundary | `src/pharmaviyum/api/v1/ai.py`; authenticated user, pharmacy membership and patient-in-pharmacy checks | Patient-aware HMAC session scope merged; staged integration gate remains open |
| Agent orchestration | `PharmacistAgent` LangGraph graph: router → knowledge retrieval → planner/executor loop → structured reviewer | Implemented; iteration limit is 5 |
| Agent Harness | `AgentHarness`: memory → input guardrail → cache → model router → agent → output guardrail → memory | Implemented |
| RAG orchestration | `LangGraphRAG` compiled `StateGraph` with explicit PostgreSQL checkpointer | Implemented |
| Retrieval | PostgreSQL/pgvector vector search + PostgreSQL full-text search + reciprocal-rank fusion | Implemented; optional reranker is not wired |
| Ingestion | API dispatches tenant-authorized Celery tasks; worker loads, preprocesses, stamps tenant metadata, chunks, embeds and persists | Active API path is implemented |
| Operational tools | Single internal MCP registry/server with role filtering and trusted request-scoped context | Implemented; current pharmacy operations tools are read-only |
| Evaluation | Project retrieval metrics, pharmaceutical-specific evaluators, lazy Ragas 0.4.3 adapter | Offline framework implemented; measured clinical quality is not established |
| Observability | Prometheus metrics and bounded OpenTelemetry spans | Instrumentation exists; end-to-end production coverage is not established |

## Findings and priorities

### P0 — Patient-context isolation: code remediation merged; staged release gate open

PR #287 has merged the following controls into `main`:

- API session namespace `mortarium-session:v4` binds pharmacy, authenticated user, patient (including explicit `None`) and client session using HMAC-SHA-256.
- Both synchronous and streaming endpoints validate tenant/patient scope before deriving the internal session namespace.
- `PharmacistAgent._thread_id()` uses `agent:v2:<digest>` and includes patient scope.
- `LangGraphRAG._thread_id()` uses `rag:v2:<digest>` and includes patient scope.
- Direct checkpoint construction validates identifier shape and fails closed in staging/production if `SECRET_KEY` is missing.
- Regression tests cover patient A/B/no-patient separation, malformed identifiers, tenant isolation and secret rotation.

**Residual release gate:** run staged end-to-end tests against real Redis and PostgreSQL checkpoint persistence, reusing one client session across Patient A → Patient B → no patient in both streaming and non-streaming modes. Verify memory, summaries, checkpoints and cache behavior. No staged execution evidence or production activation is asserted by this static audit. See [ADR-0003](./adr/ADR-0003-patient-scoped-ai-state.md) and [patient-session isolation contract](./ai/patient-session-isolation.md).


### P1 — RAG checkpoint pseudonymization: code remediation merged; legacy retention open

PR #287 replaced the plaintext composite RAG checkpoint identifier with `rag:v2:<HMAC-SHA256 digest>`, scoped to pharmacy, user, patient and session. Production/staging also fail closed when `SECRET_KEY` is absent. This closes the code-level finding on `main`.

**Residual operational work:** legacy plaintext checkpoint rows are not rewritten or deleted automatically. Approve a retention/deletion and backup-expiry plan, confirm the stable secret distribution/rotation process, and test rollback semantics before production rollout. Do not delete checkpoint data as part of this documentation change.

### P1 — Russian is not enabled by the current default language configuration

The evaluation helper supports separate `ru` and `en` retrieval scores, but current defaults do not establish Russian support:

- `RAGSettings.default_languages`: `vi, en, ar, th, id`;
- ingestion loader/task defaults: `vi, en, ar, th, id`;
- core `SUPPORTED_LANGUAGES`: `vi, en, zh, ko, ms, id, th`;
- model-router language-specific branch: `vi, th, id, ar`, not `ru`.

BM25 uses PostgreSQL's `simple` text-search configuration for non-English languages, but this alone does not prove multilingual embedding quality or Russian OCR/ingestion quality. The configured local embedding default is `mxbai-embed-large`; the actual model/corpus combination needs a measured RU/EN benchmark.

**Remediation:** add Russian consistently to supported API, loader, OCR, ingestion and routing configuration only after choosing/validating the embedding and OCR profile; then run a balanced, labelled RU/EN retrieval benchmark and report scores separately.

### P1 — Reranking is an extension point, not an active runtime stage

`PgVectorStore` accepts an optional `RerankerPort`, but `AIComponents.initialize()` constructs it without a reranker. No concrete reranker factory or runtime injection was found in the audited path. `RAG_RERANK_TOP_N` is declared in settings/template but is not consumed by runtime construction. RRF currently uses the `hybrid_search()` default `rrf_k=60`.

**Assessment:** hybrid vector + keyword retrieval and RRF are active; a cross-encoder or other dedicated reranker is not established as active.

### P1 — Several declared RAG settings are not effective runtime controls

| Setting | Source declaration | Runtime finding |
|---|---|---|
| `RAG_TOP_K` | `RAGSettings.top_k` | Passed into `LangGraphRAG`; active |
| `RAG_MAX_CONTEXT_DOCS` | `RAGSettings.max_context_docs` | Passed into `LangGraphRAG`; active |
| `RAG_MAX_REWRITES` | `RAGSettings.max_rewrites` | Passed into `LangGraphRAG`; active |
| `RAG_MAX_QUERY_VARIATIONS` | `RAGSettings.max_query_variations` | Passed into `LangGraphRAG`; active |
| `RAG_ENABLE_MULTI_QUERY` | `RAGSettings.enable_multi_query` | Passed into graph; active |
| `RAG_ENABLE_HYDE` | `RAGSettings.enable_hyde` | Passed into graph; active |
| `RAG_RERANK_TOP_N` | Settings/template | Not consumed; no active reranker is injected |
| `RAG_RRF_K` | Settings class | Not passed to runtime; hybrid search uses its method default |
| `RAG_ENABLE_CONTEXTUAL_COMPRESSION` | Settings/template | Not passed to graph; compression node is always in the graph |
| `RAG_MAX_CHUNK_TOKENS`, `RAG_CHUNK_OVERLAP` | Settings/template | Celery ingestion task reads per-job config with hard-coded defaults, not these settings |
| `RAG_DEFAULT_LANGUAGES` | Settings class | Ingestion paths use their own language defaults; no runtime consumption found |

**Remediation:** remove unused knobs or wire them through the active construction path, then add configuration contract tests that prove changing each supported environment variable changes runtime behavior.

### P1 — Ingestion has two paths with different guarantees

The API routes in `src/pharmaviyum/api/v1/ingestion.py` dispatch Celery tasks. The worker task in `mortarium_rag/ingestion/tasks.py` validates the pharmacy ID and stamps canonical tenant/source metadata before chunking and persistence. This is the active API ingestion path.

A separate `IngestionOrchestrator` is instantiated in AI dependency initialization, but no API caller of its `ingest_file()`/ `ingest_batch()` methods was found. Its `ingest_file()` path validates a pharmacy ID for deduplication but does not explicitly stamp the same canonical tenant metadata before `PgVectorStore.upsert()`; the vector store then fails closed if the chunk metadata lacks required tenant metadata.

**Remediation:** make the Celery worker the single documented ingestion path and either retire the unused orchestrator or align it with the same trusted tenant-stamping, authorization, lifecycle and tests. Do not expose the orchestrator as a second ingestion API until the contracts match.

### P2 — Runtime citation validation checks ID membership, not claim entailment

The RAG graph and Agent Harness reject missing/fabricated citation IDs when retrieved sources exist. This is useful provenance validation, but it does not prove that a source supports the sentence to which it is attached. The offline `citation_correctness()` evaluator can use an injected entailment judge; without one, it reports the metric unavailable.

Do not label runtime citation-ID validation as semantic citation correctness. Keep entailment and clinical-claim support in offline expert-reviewed evaluation.

### P2 — API confidence and safety scores are heuristic placeholders

The AI API currently assigns fixed confidence and safety-score values based on whether warnings are present. These are not calibrated probabilities or independently measured clinical safety scores. Treat them as presentation heuristics only; do not use them for automated clinical decisions, risk ranking or release acceptance.

### P2 — Model routing is heuristic

`ModelRouter` selects fast/main/complex models using query length, English keyword matching, patient/prescription context and a small language list. This is deterministic heuristic routing, not a validated clinical-risk classifier. It must not replace policy-based escalation or pharmacist review. Russian-specific routing is not configured.

### P2 — Retention and feedback controls need operational proof

PostgreSQL graph checkpoints can contain questions and retrieved clinical context. Redis memory has a bounded seven-day TTL, but TTL is not a complete PHI retention/deletion policy. Backup expiry, legal retention, deletion propagation, access audit and restore behavior need explicit operational validation. A first-class pharmacist feedback → adjudicated evaluation dataset → regression workflow was not established by this audit.

## RAG and evaluation implementation

### Active RAG graph

`LangGraphRAG` compiles a state graph with:
1. input guardrail and query transformation;
2. original query retained alongside bounded multi-query candidates and optional HyDE;
3. tenant-filtered vector and keyword retrieval;
4. LLM document grading with bounded rewrite attempts;
5. contextual compression;
6. generation under an input-token preflight budget;
7. output guardrails and post-generation citation-ID validation.

The graph requires an explicit checkpointer, uses a 90-second default graph deadline, bounds retrieval concurrency to 6 and grading concurrency to 4, and has an explicit recursion ceiling. HyDE output is a retrieval aid, not verified evidence.

### Ragas and pharmaceutical evaluators

- Ragas is pinned at `0.4.3` in the `eval` dependency group in `pyproject.toml` and resolved in `uv.lock`; the group is selected for CI/offline evaluation, not production runtime installation.
- `RagasEvaluationAdapter` lazily imports the Ragas 0.4 collections API; evaluator LLM and embeddings are injected.
- CI's RAG evaluation job verifies the collections API import and runs `tests/unit/ai/test_ragas_evaluation.py` plus the golden-dataset validation suite.
- The adapter unit tests stub Ragas metric classes; this is contract coverage, not a measured run against a real judge model.
- Project-specific evaluators cover medication name/strength/form exact matching, labeled negation, source-ID/claim support, clinical hallucination rate, source metadata isolation, and separate RU/EN gold-source recall.
- Citation entailment and clinical hallucination metrics report unavailable if no independent claim-support judge is supplied.

**No new live Ragas run, pharmacist-adjudicated clinical benchmark, or real RU/EN retrieval benchmark was executed in this static audit.** Existing historical benchmark results remain tied to their original revisions and synthetic/test-double limitations; they are not production performance or clinical quality evidence.

## MCP and pharmacy operations

The current documented pharmacy operations MCP tools are read-only. Tool schemas are validated, role discovery is filtered, and tool execution requires a trusted request-scoped user/role/pharmacy context. Generic SQL, shell, filesystem and code-execution inputs are rejected. Write tools must explicitly declare write execution and pharmacist confirmation; the registry denies them until a trusted approval verifier validates and consumes an approval.

ERP remains the source of truth for prices, stock, FEFO, prescription controls, payment state and transactional outcomes. Mortarium must not claim a write or business operation succeeded without authoritative confirmation.

## Observability and privacy

RAG graph nodes and agent execution emit bounded OpenTelemetry spans. The documented policy prohibits prompts, completions, patient identifiers, retrieved clinical text and raw tool arguments in telemetry. Prometheus labels must remain low-cardinality. The presence of SDKs/spans is not proof that an OTLP exporter, collector, alerts, retention and incident response are operational in every deployment.

## Validation evidence and limits

The repository contains unit/security tests for RAG contracts, MCP RBAC/authorization, agent execution budgets, patient metadata isolation, citation checks and Ragas adapter behavior. The CI workflow defines unit, integration, security and RAG-evaluation jobs. This audit did not execute those jobs and does not claim they are green at the audited SHA.

The previous synthetic benchmark dated 2026-10-15 used deterministic test doubles for LLM/embeddings/retrieval for its main concurrency result. Its separate pgvector smoke test used deliberately constructed vectors and a tiny fixture corpus. Retain those results as historical, limited evidence only.

## Prioritized remediation backlog

1. **P0 release gate:** Execute staged Patient A → Patient B → no-patient tests on the same client session across streaming/non-streaming API paths, Redis memory and PostgreSQL checkpoints; record evidence before production activation.
2. **P1 operational:** Approve legacy plaintext RAG checkpoint retention/deletion and backup-expiry policy; validate secret distribution, rotation and rollback.
3. **P1:** Reconcile ingestion to one canonical path with identical tenant stamping and lifecycle guarantees.
4. **P1:** Wire or remove ineffective RAG settings; add tests proving environment overrides affect runtime.
5. **P1:** Decide and validate Russian language/OCR/embedding support; run separate RU and EN retrieval benchmarks.
6. **P1:** Implement and inject a concrete reranker only if a labelled benchmark shows measurable benefit; otherwise remove the misleading rerank setting.
7. **P2:** Separate heuristic API confidence/safety fields from calibrated evaluation outputs.
8. **P2:** Add claim-level citation/clinical-claim evaluation against pharmacist-reviewed gold labels.
9. **P2:** Complete PHI checkpoint/memory retention, deletion, backup and restore operational policy.
10. **P2:** Establish a governed pharmacist-feedback-to-evaluation regression process.

## Release statement

This is a static architecture audit, not a clinical validation, regulatory assessment, production security certification, load test or deployment approval. Patient-aware session/checkpoint namespace code is merged, but staged isolation verification and production activation remain open. Legacy checkpoint retention, measured RU/EN quality and deployment-specific PHI lifecycle controls also remain open. No production configuration, database, model provider or deployment was changed by this documentation audit.
