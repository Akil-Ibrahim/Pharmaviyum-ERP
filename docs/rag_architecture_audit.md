# RAG Architecture Audit

Date: 2026-09-16  
Branch: `dev`

## Target runtime

`Authentication -> TenantContext -> RAG use case -> LangGraph -> Retrieve -> Grade/Rerank -> Compress -> Generate -> Guardrails -> Answer + Sources`

Ingestion remains outside the query graph and is executed as a batch workflow. LangGraph is the orchestration layer, not the vector store or the whole RAG system.

## Audit

| # | Component | Status | Current assessment |
|---|---|---|---|
| 1 | Ingestion | HARDENED | Ingestion requires an authorized pharmacy tenant, stamps tenant/canonical metadata before chunking, and vector persistence fails closed. |
| 2 | Document processing | OK | Preprocessing includes normalization, metadata extraction and optional PII redaction. |
| 3 | Chunking | OK | Medical-aware chunking with configurable size/overlap exists. |
| 4 | Metadata | CLOSED | `CanonicalMetadata` enforces pharmacy_id, source, version/effective-date fields, access level, country/language and document type semantics. |
| 5 | Embeddings | OK | Embedding provider/factory is separated from RAG orchestration. |
| 6 | Vector store | OK | PostgreSQL + pgvector with HNSW and metadata/FTS indexes; retrieval requires a tenant filter. |
| 7 | Query transformation | OK | Multi-query + HyDE + bounded rewrite loop. |
| 8 | Hybrid retrieval | OK | Vector + keyword retrieval with RRF fusion. |
| 9 | Tenant isolation | CLOSED | API resolves the pharmacy through authenticated membership; LangGraph carries tenant context; pgvector rejects unscoped retrieval and ingestion. |
| 10 | Reranking | CLOSED | Retrieval accepts an explicit `RerankerPort`; the previous embedding-similarity-as-reranker implementation was removed. |
| 11 | Relevance grading | OK | LLM relevance grading treats retrieved documents as untrusted data and fails closed after bounded rewrites. |
| 12 | Context compression | OK | Dedicated contextual compressor runs before generation and preserves stable citation IDs. |
| 13 | Generation | CLOSED | Generation requires factual claims to reference stable `[src-UUID]` citation IDs from supplied evidence. |
| 14 | Citations/provenance | CLOSED | Source citations are deterministic from chunk IDs and preserve source/version metadata through compression and response binding. |
| 15 | Input guardrails | PARTIAL | Shared guardrails run before query transformation; broader observability/contract hardening remains. |
| 16 | Output guardrails | OK | Shared post-processing plus dosage/disclaimer enforcement is present. |
| 17 | Observability | PARTIAL | Latency/tokens/warnings and structured logging exist; end-to-end trace/tenant/user correlation still needs to be made invariant across retrieval, LLM and MCP calls. |
| 18 | Evaluation | PARTIAL | Golden-dataset evaluation and RAG tests exist, but retrieval/security metrics need a dedicated regression suite. |
| 19 | Feedback loop | MISSING | No first-class answer feedback -> evaluation dataset -> retraining/re-ranking improvement loop is enforced. |

## Closed priority items

### P0 — security invariants

1. Tenant identity is proven through authenticated pharmacy membership before ingestion or retrieval.
2. Retrieval fails closed without a positive `pharmacy_id` tenant filter.
3. Ingestion stamps and validates tenant metadata before persistence.
4. MCP tools already enforce authenticated tenant/role context at their registry boundary.

### P1 — retrieval quality

1. Reranking now has a typed infrastructure contract and no longer masquerades embedding similarity as a cross-encoder.
2. Canonical metadata is validated before persistence and carries source/version/effective-date/access semantics.
3. Stable citation IDs survive retrieval, compression and generation prompts and are materialized in `RAGResponse.citations`.

## Remaining P2 work

1. Propagate trace/user/tenant IDs through RAG, LLM, vector store and MCP as an invariant.
2. Add retrieval metrics: Recall@K, Precision@K, MRR/NDCG.
3. Add generation metrics: faithfulness, answer relevance, citation correctness and hallucination rate.
4. Expand adversarial tests: cross-tenant retrieval, prompt injection in retrieved documents, unauthorized MCP tool access.
5. Introduce a controlled feedback loop from user/pharmacist feedback into the evaluation dataset.
