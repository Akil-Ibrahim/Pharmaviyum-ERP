# Pharmaviyum ERP/CRM — Engineering Benchmark & Quality Requirements

## Status and purpose

This document defines the measurement contract for assessing Pharmaviyum ERP/CRM and Mortarium AI. It is a test specification and target operating model, **not evidence that the listed tests have run or that targets have been achieved**.

The benchmark is intended for repeatable runs in GitHub Codespaces/local development and, for infrastructure-dependent scenarios, an isolated staging environment. Use synthetic pharmacy tenants, synthetic products and synthetic patient records only.

The canonical business sizing scenario is:

| Dimension | Planning input |
|---|---:|
| Pharmacies | 100 |
| Daily visitors | 200 per pharmacy |
| Total daily visitors | 20,000 |
| Employees | 5 per pharmacy / 500 total |
| POS terminals | 3 per pharmacy / 300 total |

Visitors are not equivalent to authenticated users, concurrent sessions, API requests or AI requests. Actual AI request volume and peak concurrency are not yet specified. Do not infer them from visitor counts. Establish them from pilot telemetry and representative workload observations.

## 1. Measurement and evidence rules

Every report must include:

- repository commit SHA and branch;
- date, environment and runtime/dependency versions;
- test command and configuration;
- workload profile, concurrency, duration and warm-up;
- dataset version, size and synthetic-data provenance;
- raw output/artifact location;
- metric definition, unit and aggregation;
- measured result and comparison target;
- status and limitations.

Use these evidence labels consistently:

| Label | Meaning |
|---|---|
| MEASURED | Collected by an executed test in the stated environment |
| HISTORICAL | Previously measured; retain its original date, revision and limitations |
| ESTIMATED | Modelled or calculated; not an observed result |
| NOT TESTED | Test has not been executed |
| UNAVAILABLE | Required instrumentation, data or dependency was unavailable |
| NOT APPLICABLE | Metric does not apply to the tested component |

Never report unavailable as zero. Never combine results from different environments or datasets without identifying the difference. Do not describe a Codespaces result as production capacity.

## 2. Backend and API performance

Measure by route class and workload, excluding health/readiness noise where appropriate:

- request rate / throughput (requests per second);
- latency p50, p90, p95 and p99;
- HTTP 4xx and 5xx rates, with client errors separated from server failures;
- timeout and cancellation rates;
- concurrent in-flight requests;
- event-loop lag for async workloads;
- CPU, memory, network and process restarts;
- saturation and queue/wait time.

Report both successful-request latency and overall error rate. Do not hide failed or timed-out requests from the denominator.

## 3. PostgreSQL, pgvector and Redis

### PostgreSQL / SQLAlchemy / Neon

- query latency p50/p95/p99 by query class;
- slow-query count/rate and query-plan regressions;
- pool size, checked-out connections, wait time and pool timeout rate;
- transaction success/failure rate, deadlocks and lock wait;
- database CPU, memory, I/O and connection saturation;
- pgvector retrieval latency, rows scanned/returned and index/query-plan behavior.

### Redis-compatible service

- command latency p50/p95/p99;
- operation rate and command errors/timeouts;
- cache hit ratio, defined as hits / (hits + misses), where both counters exist;
- memory use, evictions and rejected connections;
- active connections and pool wait;
- Celery broker queue depth, oldest-message age, task duration, retries and failures.

A cache hit ratio is meaningful only for a defined cache workload; do not apply it to arbitrary Redis commands.

## 4. RAG evaluation

Use a version-pinned Ragas integration for supported answer/context metrics, alongside deterministic retrieval metrics and project-specific evaluators. Metric availability and APIs vary by Ragas version; verify the installed version and use its supported API rather than assuming every metric below is a built-in Ragas metric.

### Retrieval metrics

Evaluate against human-labelled relevant chunk IDs:

- Recall@K: relevant retrieved items / all relevant items;
- Precision@K: relevant retrieved items / retrieved items in top K;
- Hit Rate@K: fraction of queries with at least one relevant result in top K;
- MRR: mean reciprocal rank of the first relevant result;
- nDCG@K: discounted gain normalized by ideal ranking;
- MAP@K where multiple relevant items per query make it useful.

Report K values, labelled-query count, unlabelled-query handling and corpus/index revision. The existing evaluator in `src/pharmaviyum/ai/mortarium_rag/quality_metrics.py` is the repository implementation to inspect and reuse where appropriate.

### Ragas / answer and context metrics

Evaluate supported metrics as appropriate:

- Faithfulness;
- Answer Relevancy;
- Context Precision;
- Context Recall;
- Context Entity Recall;
- Noise Sensitivity;
- Answer Correctness;
- Semantic Similarity.

Record the Ragas version, metric implementation, judge model/version, prompts, dataset schema and evaluator configuration. LLM-as-judge scores are evaluation signals, not clinical ground truth; calibrate them against expert-reviewed examples.

### Citation metrics

Add deterministic project-specific checks:

- Citation Validity: cited source IDs exist in the retrieved evidence;
- Citation Precision: cited evidence supports the claim it is attached to;
- Citation Recall: supported factual claims requiring evidence have an adequate citation;
- Citation Correctness: expert/annotator assessment that the cited source actually supports the associated claim.

A citation that merely points to an existing chunk is valid but is not necessarily correct.

## 5. Pharmacy-specific clinical and medication evaluation

These are custom domain metrics, not assumed native Ragas metrics. Use pharmacist-reviewed golden answers and structured expected entities. Score exact and clinically equivalent matches separately.

- Medication Entity Accuracy;
- Active Ingredient Accuracy;
- Strength / Concentration Accuracy;
- Dosage Accuracy;
- Dosage Form Accuracy;
- Route of Administration Accuracy;
- Frequency / Duration Accuracy where in scope;
- Negation Preservation;
- Contraindication Recall;
- Drug Interaction Accuracy;
- Clinical Hallucination Rate;
- Unsupported Clinical Claim Rate;
- Source Attribution Accuracy;
- Escalation / referral correctness for out-of-scope or unsafe questions.

Preserve critical distinctions: medicine name, active ingredient, strength, dose, formulation, route, frequency, duration, population and negation. A correct drug name with an incorrect strength or dosage is not a correct medication answer.

For each metric document the unit of analysis (entity, field, claim, answer or case), denominator, matching rules, adjudication procedure and confidence interval where sample size permits. Clinical thresholds must be approved by qualified pharmacy/clinical reviewers; do not invent universal pass percentages.

## 6. Agent, LangGraph, Agent Harness and MCP

Measure deterministic task suites and trace-backed executions:

- Task Completion Rate;
- Agent / workflow routing accuracy;
- Tool Selection Accuracy;
- Tool Execution Success Rate;
- Tool Argument Accuracy;
- Agent Step Accuracy;
- Replanning Rate;
- Loop / repeated-step Rate;
- Escalation Accuracy;
- retry and timeout rates;
- end-to-end and per-step latency;
- token usage and cost per successful task, where provider data is available.

A successful tool call is not proof of a successful business outcome. Verify final state and authorization independently. Include negative tests for unauthorized tools and invalid arguments.

## 7. Security, privacy and tenant isolation

Run synthetic, adversarial tests for:

- cross-tenant retrieval and response leakage;
- unauthorized read/write and RBAC bypass;
- unauthorized MCP tool invocation;
- prompt injection in user input and retrieved documents;
- PII and sensitive clinical-data leakage into responses, logs, traces and metric labels;
- insecure direct object references and tenant-context substitution;
- secrets in logs, artifacts or test output.

Release-blocking invariants:

- zero confirmed cross-tenant data leakage;
- zero unauthorized protected tool execution;
- zero secrets or sensitive patient data in exported telemetry;
- all critical authorization tests pass.

These are hard gates, not scores that can be averaged against performance or answer-quality metrics. Any confirmed violation blocks release pending remediation and retest.

## 8. OpenTelemetry and operational observability

Measure instrumentation coverage and usefulness, not just whether an SDK dependency exists:

- trace coverage for defined critical request/workflow paths;
- parent/child span and W3C trace-context propagation;
- span error status and exception visibility;
- metrics coverage for required service and workflow indicators;
- log/trace correlation using trace and span identifiers;
- exporter/collector delivery failures and dropped telemetry;
- alert evaluation and notification delivery;
- detection and recovery timings (MTTD / MTTR) during controlled incident exercises.

Trace critical paths across FastAPI, SQLAlchemy/PostgreSQL, Redis, Celery, LangGraph, RAG, MCP and outbound model calls where technically supported. Do not claim full coverage based on automatic FastAPI instrumentation alone.

Telemetry safety requirements:

- never export patient names, patient IDs, prescription contents, raw prompts, completions, retrieved clinical text, credentials or tokens;
- avoid tenant/user/session IDs as Prometheus labels;
- use bounded-cardinality attributes and route templates;
- apply access control, retention and regional data-residency rules to telemetry backends;
- keep audit records for business actions distinct from diagnostic traces.

## 9. Frontend and end-to-end workflows

Use existing Vitest and Playwright suites where available. Measure:

- unit/component and E2E pass/fail counts;
- critical workflow coverage;
- page/navigation and API integration failures;
- browser console errors;
- frontend build success and bundle size;
- user-visible latency for defined workflows.

Critical pharmacy workflows should include authentication/authorization, product search, POS order flow, inventory operations and the relevant pharmacist/manager journeys. Do not claim POS checkout coverage if the tested API path does not perform actual checkout, payment, batch allocation and inventory decrement.

## 10. Load, stress and capacity scenarios

Use the existing k6 entry point and documented route contracts. Run only against local or isolated staging infrastructure with synthetic data. Read-only load tests are the default. Write scenarios require explicit opt-in, disposable staging data and verified cleanup.

Suggested concurrency steps (25, 50, 100, 250, 500, 1,000) are stress-test profiles, not forecasts of real concurrent users or AI requests. Select realistic arrival rates and user journeys after observing pilot traffic.

Separate workloads:

1. interactive ERP/API reads;
2. transactional writes and POS operations;
3. search and inventory;
4. RAG/AI requests with separately controlled provider cost and concurrency;
5. background ingestion and Celery jobs.

Report sustainable throughput, latency percentiles, error/timeout rate, queue growth, database/cache saturation, CPU/memory, recovery after load and cost where available. Do not let expensive AI traffic obscure core ERP latency.

The 100-pharmacy planning inputs above are business sizing assumptions. Capacity conclusions require measured workload mix, peak-hour distribution, request rates, transaction mix, AI demand and infrastructure limits.

## 11. Quality gates and release policy

Maintain independent gates; do not collapse the system into one average score:

1. Backend/API reliability and performance;
2. database/cache reliability;
3. retrieval quality;
4. answer quality and citation correctness;
5. pharmacy/clinical safety;
6. agent and MCP correctness;
7. security and tenant isolation;
8. observability coverage;
9. frontend/E2E critical workflows;
10. scalability and recovery.

Release policy:

- critical security, tenant-isolation, privacy and clinical-safety failures block release;
- RAG/agent regressions are compared with a versioned baseline and reviewed against risk-specific thresholds;
- performance thresholds are set from representative staging baselines and business SLOs, not guessed from Codespaces;
- all evaluation runs identify dataset, code, prompt, model, embedding and index versions;
- any metric that was not measured is reported as NOT TESTED or UNAVAILABLE, never PASS.

## 12. Tooling and environment boundaries

| Tool | Intended use |
|---|---|
| pytest | Unit, integration, security and deterministic evaluation tests |
| Ragas | Supported RAG answer/context evaluation metrics |
| Project retrieval evaluator | Recall@K, Precision@K, MRR, nDCG and retrieval latency |
| Locust / k6 | Controlled load and stress testing; prefer the repository's existing k6 workflow |
| Playwright / Vitest | Browser E2E and frontend tests |
| OpenTelemetry | Distributed traces, metrics and correlated telemetry |
| Prometheus / Grafana | Metrics storage/query and dashboards |
| Tempo / Jaeger | Trace storage and inspection, depending on the configured stack |
| Loki | Centralized logs, if deployed |
| LangSmith / Arize Phoenix | Optional specialized LLM trace/evaluation UI; not mandatory if equivalent capabilities already exist |

### GitHub Codespaces can validate

- repository structure, configuration and dependency declarations;
- tests that do not require unavailable external services;
- deterministic RAG/agent/MCP evaluation using fixtures and mocks;
- synthetic-data tenant-isolation and security tests;
- local instrumentation and trace propagation;
- local API/database/cache tests if the required Compose services are available;
- limited local benchmarks with the environment and resource limits recorded.

### Codespaces cannot prove by itself

- production capacity for 100 pharmacies;
- FastAPI Cloud or managed Neon/Redis production performance;
- real external LLM provider latency, quotas or cost unless explicitly configured and cost-controlled;
- production availability, alert delivery, recovery objectives or regional data residency;
- clinical correctness without expert-reviewed data and adjudication.

Run infrastructure and capacity validation in isolated staging with production-like limits and representative synthetic data. Do not use production patient data for benchmark fixtures.

## 13. Required benchmark report

For each metric include:

| Field | Required content |
|---|---|
| Metric | Name and definition |
| Status | MEASURED / HISTORICAL / ESTIMATED / NOT TESTED / UNAVAILABLE / NOT APPLICABLE |
| Result | Value and unit, or explicit reason unavailable |
| Target | Approved threshold or “not yet defined” |
| Environment | Codespaces / local Compose / staging / production |
| Revision | Commit SHA |
| Workload | Duration, concurrency, rate and scenario |
| Dataset | Version and sample count |
| Evidence | Command, test name and artifact/log reference |
| Limitations | Mocks, missing dependencies, sample-size constraints |
| Follow-up | Owner/action/priority |

The report must end with a prioritized remediation backlog and an explicit statement of what is and is not proven. No production-readiness claim may be based solely on a static code audit or a Codespaces run.
