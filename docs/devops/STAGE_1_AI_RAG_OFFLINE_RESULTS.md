# Stage 1 — Offline Synthetic AI/RAG Results

## Run metadata

- Date: 2026-10-15
- Tested revision: `65dd334f`
- Pipeline: `LangGraphRAG` from `src/pharmaviyum/ai/mortarium_rag/graph.py`
- Run type: in-process synthetic benchmark; **not** a live LLM or production load test
- Workload: 100 pharmacy-scoped queries, concurrency 20, two synthetic pharmacy tenants, plus one separate guardrail-blocking case
- Dependencies: deterministic test doubles for the LLM, embeddings and vector retriever; in-memory LangGraph checkpointer
- Data: synthetic fixture evidence only; no patient data or external provider requests
- Raw benchmark output: not persisted; results below were captured from the one-off run

## Results

| Measurement | Result |
|---|---:|
| Workload queries | 100 |
| Concurrency | 20 |
| Successful answers with retrieved sources | 100/100 |
| Answers with valid citations to returned sources | 100/100 |
| Responses scoped to the requesting pharmacy | 100/100 |
| Cross-tenant hits observed by the synthetic retriever | 0 |
| Separate synthetic guardrail-block case | Passed |
| Query errors | 0 |
| Retrieval calls | 800 |
| Embedding calls | 800 |
| Synthetic LLM calls | 400 |
| Total elapsed time, including the separate block case | 0.4288 s |
| Calculated throughput (`100 / total elapsed`) | 233.20 queries/s |

### End-to-end latency

Latency is measured around each `LangGraphRAG.run()` call for the 100 regular
workload queries. It does not include provider or database network latency
because all three external components are deterministic in-process test doubles.

| Statistic | Latency |
|---|---:|
| Minimum | 45.780 ms |
| Mean | 74.952 ms |
| p50 | 72.711 ms |
| p90 | 93.451 ms |
| p95 | 99.384 ms |
| p99 | 111.275 ms |
| Maximum | 111.902 ms |

### Instrumentation observed during the run

The in-process Prometheus registry recorded:

| Metric | Observations |
|---|---:|
| `ai_requests_total{status="success"}` | 101 |
| `ai_rag_retrieval_total{query_type="hybrid_multi_query",status="success"}` | 100 |
| `ai_rag_retrieval_duration_seconds_count{query_type="hybrid_multi_query"}` | 100 |
| `ai_stage_duration_seconds_count{stage="query_transform"}` | 101 |
| `ai_stage_duration_seconds_count{stage="retrieval"}` | 100 |
| `ai_stage_duration_seconds_count{stage="document_grading"}` | 100 |
| `ai_stage_duration_seconds_count{stage="context_compression"}` | 100 |
| `ai_stage_duration_seconds_count{stage="generation"}` | 100 |
| `ai_stage_duration_seconds_count{stage="guardrails"}` | 101 |
| `ai_stage_duration_seconds_count{stage="rag_pipeline"}` | 101 |

The 101 AI-request and pipeline-stage observations include the separately
blocked query. Retrieval, grading, compression and generation were not invoked
for that blocked case.

## Interpretation and limitations

This run exercises the real LangGraph orchestration and Prometheus instrumentation,
but substitutes deterministic test doubles for the LLM, embedding provider and
vector store. The retriever uses in-memory fixture matching rather than
PostgreSQL/pgvector. The guardrail is also a deterministic test double.

Therefore:

- Latency and throughput measure pipeline orchestration with test doubles, not
  model inference, embedding generation, pgvector, network overhead or production
  capacity.
- Citation and tenant-scope results validate the fixture test path; they are not
  a relevance/recall evaluation over a representative knowledge base.
- The counters demonstrate metric wiring, not production telemetry or service
  uptime.
- No external-provider token usage, provider rate limits or monetary cost were
  measured.
- No raw benchmark artifact or reusable benchmark script was saved for this
  one-off run.

Do not present the reported `233.20 queries/s` or `99.384 ms p95` as the
performance of a deployed AI service. A live benchmark requires a configured
provider (or running local inference), synthetic API credentials, an accessible
database/vector store with tenant-scoped fixtures, and a reproducible run
artifact.

## Metrics to collect in a live evaluation

### Retrieval and answer quality

- Retrieval: `Recall@k`, `Precision@k`, `MRR`, and `nDCG@k` on a fixed,
  human-reviewed question/document set.
- Generation: faithfulness/groundedness, answer relevance, completeness and
  citation precision/recall.
- Report evaluation set size, baseline, model/prompt version and dataset/index
  revision with every score.

### Safety and tenant isolation

- Correct block rate for unsafe or out-of-scope requests; false-positive and
  false-negative rates.
- Unsupported-claim rate and invalid/fabricated-citation rate.
- Cross-tenant retrieval/answer leakage: target zero, backed by adversarial
  negative tests and audit logs.

### Performance and reliability

- End-to-end and per-stage p50/p95/p99 latency: query transformation, embedding,
  retrieval, reranking/grading, compression, generation and guardrails.
- Requests/s at stated concurrency, queue wait time, timeouts, retries, provider
  errors/rate limits and partial-retrieval failures.
- Database connection-pool saturation, pgvector query latency, CPU/memory and
  cache-hit rate under the same load profile.

### Cost and ingestion

- Input/output tokens and estimated provider cost per query and per successful
  answer.
- Embedding, ingestion and index-refresh throughput; ingestion failures and
  index freshness.
- Document/chunk counts, tenant count and data-size distribution.

Metrics are defined in
[`src/pharmaviyum/observability/metrics.py`](../../src/pharmaviyum/observability/metrics.py).
Only report a metric as measured when the run actually collected it; distinguish
unavailable values from zero.

## Suggested CV wording

> Benchmarked the Mortarium LangGraph RAG orchestration with 100 synthetic
> queries at concurrency 20; validated source citations and pharmacy tenant
> scoping in 100/100 fixture responses, with zero cross-tenant fixture hits.
> Offline test-double p95 was 99 ms; this excludes real LLM, embeddings and
> pgvector latency. Separately passed 34 focused Mortarium RAG tests.

Keep the **offline/test-double** qualifier next to the latency and throughput
figures. Do not claim the benchmark demonstrates production LLM performance.

## Suggested interview explanation

> I tested the actual RAG graph orchestration with synthetic fixtures and
> deterministic test doubles. All 100 responses included valid fixture
> citations, tenant scoping held across two synthetic pharmacies, and a
> guardrail-block case passed. The 99 ms p95 is only an offline orchestration
> measurement, not live model or pgvector performance. For a production-relevant
> evaluation, I would use a fixed golden set and real provider/vector-store
> traffic, then report retrieval quality, groundedness, per-stage p95, error
> rate, tenant-isolation results and cost per successful answer.
