# RAG Architecture Audit

Date: 2026-09-15  
Branch: `dev`

## Target runtime

`Authentication -> TenantContext -> RAG use case -> LangGraph -> Retrieve -> Grade/Rerank -> Compress -> Generate -> Guardrails -> Answer + Sources`

Ingestion remains outside the query graph and is executed as a batch workflow. LangGraph is the orchestration layer, not the vector store or the whole RAG system.

## Audit

| # | Component | Status | Current assessment |
|---|---|---|---|
| 1 | Ingestion | OK | Loader/preprocess/dedup/version/chunk/embed/upsert pipeline exists outside LangGraph. |
| 2 | Document processing | OK | Preprocessing includes normalization, metadata extraction and optional PII redaction. |
| 3 | Chunking | OK | Medical-aware chunking with configurable size/overlap exists. |
| 4 | Metadata | PARTIAL | Metadata is flexible and includes tenant filtering, but a canonical metadata contract for source/version/effective dates/access level is not yet enforced. |
| 5 | Embeddings | OK | Embedding provider/factory is separated from RAG orchestration. |
| 6 | Vector store | OK | PostgreSQL + pgvector with HNSW and metadata/FTS indexes. |
| 7 | Query transformation | OK | Multi-query + HyDE + bounded rewrite loop. |
| 8 | Hybrid retrieval | OK | Vector + keyword retrieval with RRF fusion. |
| 9 | Tenant isolation | HARDENED | `QueryContext.pharmacy_id` is mandatory; LangGraph applies it to retrieval; pgvector now fails closed when the tenant filter is absent. |
| 10 | Reranking | PARTIAL | Optional reranking exists, but it currently uses embedding similarity rather than a dedicated cross-encoder/reranker contract. |
| 11 | Relevance grading | OK | LLM relevance grading treats retrieved documents as untrusted data and fails closed after bounded rewrites. |
| 12 | Context compression | OK | Dedicated contextual compressor runs before generation. |
| 13 | Generation | OK | Generation is grounded on retrieved context and explicitly instructed not to follow embedded instructions. |
| 14 | Citations/provenance | PARTIAL | Sources are returned with the response, but answer text is not yet bound to stable source/citation IDs. |
| 15 | Input guardrails | PARTIAL | Shared guardrails detect PII/prompt-injection patterns, but the query-path contract should make input validation explicit before transformation/retrieval. |
| 16 | Output guardrails | OK | Shared post-processing plus dosage/disclaimer enforcement is present. |
| 17 | Observability | PARTIAL | Latency/tokens/warnings and structured logging exist; end-to-end trace/tenant/user correlation still needs to be made invariant across retrieval, LLM and MCP calls. |
| 18 | Evaluation | PARTIAL | Golden-dataset evaluation and RAG tests exist, but retrieval/security metrics need a dedicated regression suite. |
| 19 | Feedback loop | MISSING | No first-class answer feedback -> evaluation dataset -> retraining/re-ranking improvement loop is enforced. |

## Priority order

### P0 — security invariants

1. Tenant context must originate from authenticated application context, not from an arbitrary client-supplied `pharmacy_id`.
2. Retrieval must fail closed without tenant scope.
3. Ingestion must stamp and validate tenant metadata before persistence.
4. MCP tools must receive authenticated role + tenant context and cannot bypass centralized authorization.

### P1 — retrieval quality

1. Replace optional embedding-based reranking with a typed reranker port.
2. Add canonical metadata schema and effective-date/version semantics.
3. Add stable citation IDs and source provenance to the generated answer contract.

### P2 — production operations

1. Propagate trace/user/tenant IDs through RAG, LLM, vector store and MCP.
2. Add retrieval metrics: Recall@K, Precision@K, MRR/NDCG.
3. Add generation metrics: faithfulness, answer relevance, citation correctness and hallucination rate.
4. Add adversarial tests: cross-tenant retrieval, prompt injection in retrieved documents, unauthorized MCP tool access.
5. Introduce a controlled feedback loop from user/pharmacist feedback into the evaluation dataset.

## Current conclusion

The repository already has a real LangGraph RAG query pipeline and a separate ingestion pipeline. The main remaining architectural work is not adding another framework; it is enforcing security and contracts at every boundary and making retrieval quality/evaluation measurable.
