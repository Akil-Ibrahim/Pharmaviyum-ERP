# Mortarium AI / LLM System Design

**Status:** Current implementation plus explicitly labeled design requirements.

## 1. System role
Mortarium is a pharmacist-facing decision-support assistant embedded in Pharmaviyum. It helps staff retrieve information, summarize authorized context and navigate workflows.

It is not a system of record, substitute for a licensed professional, authorization engine, deterministic pricing/inventory/payment/dispensing engine or proof that a medication is appropriate.

Deterministic application code owns permissions, calculations, transactional changes and regulatory constraints. AI output is advisory and evidence-bounded.

## 2. Logical architecture
The request path is: authenticated pharmacist → FastAPI AI API → tenant/patient validation → Agent Harness → bounded Redis memory and prompt cache → model routing → LangGraph pharmacist agent → LangGraph RAG and/or role-filtered MCP registry → grounded response with sources and warnings → pharmacist review.

These are logical application components, not separate deployable services.

## 3. Request lifecycle
1. FastAPI authenticates the user.
2. The API resolves authorized pharmacy context.
3. If a patient is selected, the API verifies that the patient is active and belongs to the pharmacy.
4. Trusted context is built from server-side identity and validated request fields.
5. Agent Harness loads bounded memory, applies input controls and checks eligible cache entries.
6. Model routing selects the configured model for the task.
7. The LangGraph agent decides whether to answer from context, invoke retrieval or request an authorized MCP tool.
8. RAG retrieves tenant-filtered evidence, grades it, rewrites within a bounded budget when needed, compresses evidence and generates a cited response.
9. MCP tools execute only with trusted request-scoped authorization context and role filtering.
10. Output guardrails run before the response is returned.
11. The pharmacist reviews the answer and remains responsible for the professional decision.

Exact request/response schemas are defined in code and generated OpenAPI, not duplicated here.

## 4. Agent Harness
The Harness owns cross-cutting input/output guardrails, bounded dialogue memory, prompt/cache orchestration, model routing, agent execution/streaming, structured response construction and telemetry.

Memory is contextual convenience, not an authoritative patient record. Memory summaries must not override current validated patient data, prescription state or source documents.

Cache identity must include every context dimension that can change correctness or authorization. Never reuse patient-specific answers across patient, tenant, user or permission boundaries.

## 5. LangGraph agent and RAG
The pharmacist agent and RAG are separate LangGraph workflows. RAG uses bounded query transformation, retrieval, document grading, compression, generation and guardrails.

Retrieval rules:
- Hybrid retrieval combines PostgreSQL full-text search and pgvector similarity.
- Filters include authenticated pharmacy context.
- Patient-level documents require an explicit patient filter.
- Original user query remains a retrieval candidate; rewrites supplement it.
- Medication names, strengths, dosage forms and negation must be preserved.
- HyDE output is a retrieval aid, not verified evidence.
- Retrieved documents are untrusted input and never become system policy.
- Stable source IDs survive retrieval, compression and citation.

Do not describe a reranker as active unless a concrete reranker is injected and tested. The audit identifies declared settings that are not all wired into runtime; see [RAG audit](../rag_architecture_audit.md) and [LLM engineering standard](../llm_engineering_standards.md).

## 6. Ingestion
The active API ingestion path dispatches tenant-authorized Celery tasks. Worker processing loads/preprocesses documents, stamps tenant metadata, chunks, embeds and persists them. Do not assume a separate orchestrator path has equivalent metadata and authorization behavior without tests.

Jobs must be idempotent, bounded and safe to retry. Retain source, jurisdiction, language, version and tenant metadata.

## 7. MCP tool boundary
The registry filters tools by role; execution requires trusted request-scoped authorization context.
- The model may propose a tool call; the server decides whether it is authorized.
- Never trust tenant/user/role identifiers supplied inside model-generated arguments.
- Validate arguments against strict schemas.
- Use deterministic domain services for writes.
- Write operations require explicit authorization and a separately verified approval flow; model intent is not approval.
- Return minimum necessary data.
- Record bounded tool outcome metadata without sensitive arguments/results.

The currently documented pharmacist operations tools are read-only. Do not infer write capability from MCP's existence.

## 8. Patient-context isolation
PR #287 merged the patient-scoped session and checkpoint namespace implementation into `main` (merge commit `4d761990b31ef3aa78327dda1380689f2d094e8f`). Its RAG Safety Regression, Unit Tests and Integration Tests checks passed on the merge commit.

This is not evidence of production activation or a completed staging release gate. The required end-to-end test remains: reuse one client session across Patient A → Patient B → no patient in synchronous and streaming modes, including PostgreSQL checkpoint persistence and Redis memory. Until that test is evidenced and the release is explicitly deployed, do not claim patient-context isolation is operationally proven in production.

Required invariant: pharmacy + authenticated user + patient (including explicit none) + client session.

Namespace changes require a compatibility, retention and rollback plan. See [ADR-0003](../adr/ADR-0003-patient-scoped-ai-state.md) and [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287).

## 9. Pharmaceutical evaluation
Ragas is an offline evaluator, not a production request dependency. Pair generic RAG metrics with deterministic pharmacy-specific metrics.

| Dimension | Evaluation |
|---|---|
| Citation correctness | Valid source ID and claim-level entailment |
| Medication entity accuracy | Exact name, strength and dosage form |
| Negation preservation | Correct polarity of positive/negative propositions |
| Clinical hallucination rate | Unsupported clinical claims / all labeled clinical claims |
| Patient-context isolation | No source or state from another tenant/patient |
| Multilingual retrieval | Gold-source recall and answer quality by language, especially English and Russian |
| Abstention | Safe no-answer behavior for missing, stale or conflicting evidence |

Record dataset, corpus/index revision, language, model, prompt, evaluator version, sample count and adjudication. LLM-judge scores are regression signals, not clinical validation. Thresholds require qualified review.

See [Ragas evaluation](./ragas-pharmaceutical-evaluation.md) and [benchmark requirements](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md).

## 10. Observability and privacy
Use bounded spans/metrics for request and graph duration, retrieval counts, rewrite count, warning codes, provider latency/error class, MCP tool name/outcome and ingestion task status.

Do not record prompts, completions, patient identifiers, prescription data, retrieved clinical text, Redis keys/values or raw MCP arguments. Automatic FastAPI, SQLAlchemy and HTTPX instrumentation is opt-in only in development/test after redaction review; Redis command auto-instrumentation remains disabled.

See [OpenTelemetry policy](../observability/opentelemetry.md).

## 11. Reliability and cost controls
- Bound graph recursion, rewrites, retrieval concurrency and execution time.
- Use explicit timeouts and bounded retries with jitter.
- Apply token budgets without dropping warnings or dosage units.
- Cache only when scope and freshness are proven safe.
- Degrade optional AI independently from POS and core ERP.
- Handle provider quota, rate limit and outage as expected failures.
- Avoid hidden model calls in deterministic CRUD paths.

## 12. Threat model checklist
- [ ] Cross-tenant retrieval and tool invocation.
- [ ] Cross-patient memory, cache and checkpoint reuse.
- [ ] Prompt injection in uploaded/retrieved documents.
- [ ] Tool argument tampering and privilege escalation.
- [ ] Unsupported citations and hallucinated claims.
- [ ] Medication strength/formulation substitution.
- [ ] Negation loss during rewriting or compression.
- [ ] PHI leakage through traces, logs, caches or evaluation data.
- [ ] Unbounded graph loops, document size or tool fan-out.
- [ ] Stale corpus, wrong jurisdiction or language mismatch.

## Related material
- [AI architecture](../ai_architecture.md)
- [LangGraph RAG architecture](./langgraph-rag-architecture.md)
- [Mortarium pharmacy operations](./mortarium-pharmacy-operations.md)
- [Ragas pharmaceutical evaluation](./ragas-pharmaceutical-evaluation.md)
- [LLM engineering standards](../llm_engineering_standards.md)
- [RAG architecture audit](../rag_architecture_audit.md)
- [Patient-scoped state ADR](../adr/ADR-0003-patient-scoped-ai-state.md)
