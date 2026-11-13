# Senior Python Engineer | AI / LLM — Interview Q&A

This is the practical interview companion to [`README.md`](./README.md). The goal is not to memorize definitions, but to explain **why the system is designed this way, what can fail, and how you would improve it in production**.

The answers below are deliberately phrased as interview answers that can be expanded into a deeper technical discussion.

## 1. Give me a high-level overview of the project.

**Answer:**

Pharmaviyum CRM is a modular pharmacy CRM with a FastAPI backend, PostgreSQL/pgvector, Redis, Celery workers, a React frontend, and an AI layer built around LangGraph/LangChain and a configured LLM provider.

The important architectural point is that the LLM is not the application. Authentication, tenant isolation, persistence, retrieval, tool authorization, validation, observability, and error handling remain deterministic application responsibilities.

**Where to point in the repo:**

- `src/pharmaviyum/`
- `src/pharmaviyum/ai/`
- `docs/ai_architecture.md`

---

## 2. Why FastAPI?

**Answer:**

FastAPI fits this system because it provides strong request/response validation through Pydantic, dependency injection, OpenAPI generation, and an async-first execution model that works well for database, network, and streaming workloads.

I would not choose FastAPI merely because it is fast. The more important benefit is that it gives clear boundaries around validation, dependencies, and API contracts.

**Senior follow-up:**

I would still keep business logic out of route handlers and avoid using async code where the underlying operation is CPU-bound.

---

## 3. Why use async Python?

**Answer:**

Async is valuable when the workload spends significant time waiting for I/O: PostgreSQL, Redis, HTTP APIs, model providers, or streaming responses.

It allows one process to make progress on other requests while an operation is waiting. It does not make CPU-heavy code automatically faster.

For CPU-heavy work I would move the workload to workers or another appropriate execution model.

---

## 4. What is the `src/` layout and why does it matter?

**Answer:**

The application package lives under `src/pharmaviyum`. A `src` layout helps prevent accidental imports from the repository root and makes packaging behavior closer to an installed package.

It also means tooling needs to understand the package boundary correctly. In this repository mypy uses:

```bash
mypy --explicit-package-bases src
```

That avoids the same source file being interpreted through ambiguous module paths.

---

## 5. Why PostgreSQL instead of a separate database for everything?

**Answer:**

PostgreSQL is the system of record for transactional data, and pgvector adds vector retrieval capabilities without introducing another primary persistence system.

That gives us a useful balance: relational constraints and transactions remain authoritative, while vectors support semantic retrieval.

I would introduce another datastore only when the workload demonstrates a concrete need that PostgreSQL cannot satisfy economically or operationally.

---

## 6. What is the difference between relational data and vector data here?

**Answer:**

Relational data represents authoritative application state: users, products, orders, tenant relationships, and other business entities.

Vector data represents a retrieval index over content. A vector similarity result should not become an authorization mechanism or the authoritative business record.

A good rule is:

> **Vector search finds relevant information; the application and database decide what the user is allowed to access.**

---

## 7. Explain the RAG pipeline.

**Answer:**

The current pipeline is:

```text
transform_query
    -> retrieve
    -> grade_documents
    -> compress
    -> generate
    -> guardrails
```

Each stage has a separate responsibility:

- `transform_query` improves the retrieval query/context;
- `retrieve` finds candidate content within the allowed tenant context;
- `grade_documents` evaluates relevance;
- `compress` reduces unnecessary context;
- `generate` produces the model response;
- `guardrails` validates or constrains the final behavior.

This is easier to reason about and observe than one large function containing the entire RAG workflow.

The graph is implemented under `src/pharmaviyum/ai/rag` and documented in `docs/ai_architecture.md`.

---

## 8. Why is tenant isolation not an LLM responsibility?

**Answer:**

Because an LLM is probabilistic and should not be trusted to enforce authorization.

If a user changes the wording of a query, that must never allow access to another pharmacy's documents. Tenant filtering must happen in deterministic application/data-access logic before content reaches the model.

The LLM can reason over data that it has been authorized to receive; it should not decide whether the user is authorized to receive that data.

---

## 9. How do you defend against prompt injection in RAG?

**Answer:**

I treat retrieved documents as untrusted input.

A retrieved document may contain text such as "ignore previous instructions". That text is content, not an application instruction.

Defense in depth includes:

1. strict authorization before retrieval;
2. clear separation of system instructions and retrieved content;
3. controlled tool permissions;
4. output validation and guardrails;
5. source/citation tracking;
6. adversarial evaluation cases;
7. logging and monitoring of suspicious behavior.

The key principle is that security cannot depend on a single prompt sentence.

---

## 10. How would you improve RAG quality if users say answers are poor?

**Answer:**

I would not immediately change the LLM.

First I would determine which stage is failing:

```text
query -> retrieval -> relevance -> context -> generation
```

I would measure:

- retrieval recall/relevance;
- document grading quality;
- duplicate or noisy context;
- chunk size and overlap;
- metadata filtering;
- embedding/model compatibility;
- context length;
- groundedness and citation correctness.

Only after identifying the bottleneck would I change embeddings, chunking, reranking, prompts, or the model.

---

## 11. Why contextual compression?

**Answer:**

Retrieving ten large documents does not mean all ten documents belong in the final prompt.

Compression reduces irrelevant context, which can improve both model quality and latency/cost. The important engineering question is to verify that compression does not remove evidence required for a correct answer.

So I would evaluate compression as a retrieval-quality trade-off rather than assuming that fewer tokens automatically means better results.

---

## 12. Why LangGraph instead of one LLM call?

**Answer:**

The workflow has state and multiple explicit stages: query transformation, retrieval, grading, compression, generation, and guardrails.

A graph makes those transitions explicit and allows conditional paths, checkpointing, observability, and controlled failure handling.

It is useful when the AI system behaves like a workflow rather than a single prompt/response operation.

---

## 13. What is the Agent Harness responsible for?

**Answer:**

The Agent Harness provides application-level orchestration around LLM calls. In the current architecture it covers model routing, dialogue memory, guardrails, caching, tool access, and observability.

That keeps cross-cutting concerns outside individual prompts and helps maintain a consistent runtime policy.

See `docs/ai_architecture.md` and `src/pharmaviyum/ai`.

---

## 14. How would you handle LLM timeouts and retries?

**Answer:**

I would define explicit timeouts and bounded retries around external model calls.

Retries need to be selective because retrying a non-idempotent tool or an already expensive model request can amplify load and cost.

I would also use:

- exponential backoff where appropriate;
- maximum retry counts;
- cancellation/deadline propagation;
- circuit-breaking or provider fallback when justified;
- metrics for retry rate and failure reason.

A retry is a reliability mechanism, not a substitute for diagnosing the underlying failure.

---

## 15. How would you prevent an LLM from abusing tools?

**Answer:**

Tools should be narrow capabilities with explicit schemas and authorization checks.

The execution boundary should look like:

```text
LLM intent
 -> application authorization
 -> argument validation
 -> controlled tool execution
 -> structured result
```

The model does not receive arbitrary infrastructure access. Sensitive operations should require deterministic application authorization.

The repository's MCP implementation is under `src/pharmaviyum/ai/mcp` and integrates authorization with application roles and pharmacy membership.

---

## 16. What is MCP doing here?

**Answer:**

The project contains an MCP JSON-RPC implementation for tools and resources. It provides a standardized application-level interface for exposing controlled capabilities to the AI layer.

The important design decision is that MCP is an internal application component, not an unrestricted gateway into infrastructure.

---

## 17. Why Celery?

**Answer:**

Document ingestion and similar long-running tasks should not occupy latency-sensitive HTTP workers.

Celery gives us a queue-backed worker model where API requests can enqueue work and workers can process it independently.

For production I would pay particular attention to idempotency, retry semantics, task timeouts, queue backpressure, and duplicate execution.

The repository integrates document ingestion with the Celery worker in the development Docker Compose stack.

---

## 18. What does idempotency mean for background jobs?

**Answer:**

A retried task should not corrupt state or create unintended duplicates.

For example, if document ingestion is executed twice, the system should have a deterministic way to recognize the same source/version or otherwise make the operation safe to repeat.

The exact mechanism depends on the domain, but typical tools include unique constraints, idempotency keys, deterministic identifiers, and transactional state transitions.

---

## 19. How would you design database transactions?

**Answer:**

I define the transaction around a business consistency boundary rather than around arbitrary function calls.

Within the transaction I would:

1. validate the operation;
2. load the required state;
3. apply changes;
4. enforce invariants with database constraints where possible;
5. commit once the unit of work is valid.

I avoid unnecessarily long transactions because they increase lock contention and reduce throughput.

---

## 20. SQLAlchemy ORM or raw SQL?

**Answer:**

I would use the appropriate abstraction for the query.

ORM models are useful for domain-oriented CRUD and maintainability. Explicit SQL can be appropriate for complex analytical queries, specialized PostgreSQL features, or performance-critical operations where generated SQL is not sufficient.

The important point is to measure query behavior and keep the database access layer understandable.

---

## 21. How would you debug a slow endpoint?

**Answer:**

I would first measure rather than guess.

I would break the latency into:

```text
HTTP
 -> application logic
 -> database
 -> Redis
 -> retrieval
 -> model/tool calls
```

Then inspect traces, database query plans, connection-pool behavior, cache hit rate, queue time, and external model latency.

For PostgreSQL I would use query plans and indexes based on actual access patterns, not add indexes blindly.

---

## 22. What is your approach to caching?

**Answer:**

I cache data when it is expensive to compute and safe to reuse.

I first define:

- cache key;
- ownership/tenant scope;
- TTL;
- invalidation strategy;
- consistency expectations;
- maximum size;
- behavior when Redis is unavailable.

A cache should improve performance without becoming an accidental source of truth.

For AI workloads, I would also be careful not to cache responses across tenant or authorization boundaries.

---

## 23. What should be observable in an AI system?

**Answer:**

At minimum I want to know:

- request latency;
- retrieval latency;
- model latency;
- errors by category;
- retry rate;
- token/cost signals where available;
- tool failures;
- queue latency;
- retrieval quality metrics;
- citation/grounding failures.

I would avoid putting user IDs, session IDs, or tenant IDs into Prometheus labels because they create high cardinality.

The repository explicitly documents low-cardinality RAG metrics.

---

## 24. Why are high-cardinality Prometheus labels dangerous?

**Answer:**

Each unique label combination creates a separate time series. User/session/tenant identifiers can therefore cause uncontrolled series growth, increased memory usage, and degraded monitoring performance.

For correlation, I would use logs and traces rather than turning every identifier into a metric dimension.

---

## 25. How do you test an LLM application?

**Answer:**

I use multiple layers.

### Deterministic tests

Unit tests for parsing, validation, transformations, authorization, and business logic.

### Integration tests

Database, Redis, API, migration, queue, and tool integration.

### RAG evaluation

Representative datasets with measurable retrieval relevance, groundedness, citation correctness, refusal behavior, latency, and regression cases.

### End-to-end tests

User-facing workflows through the frontend and API.

LLM quality should be evaluated as an engineering system, not only through a handful of manually selected prompts.

---

## 26. What would you do if tests pass but production is still unreliable?

**Answer:**

Passing tests does not prove production reliability.

I would inspect missing failure modes:

- dependency failures;
- timeouts;
- concurrency;
- retries;
- queue saturation;
- database connection exhaustion;
- cache outages;
- provider failures;
- malformed external data;
- observability gaps.

Then I would add a regression test for the specific failure and improve the runtime behavior.

---

## 27. How do you approach dependency upgrades?

**Answer:**

Incrementally.

I update a coherent dependency group, review compatibility, run formatting/type/tests/security checks, inspect the lockfile, and verify CI before moving to another group.

I do not blindly upgrade everything with a global `pip install -U` because that makes failures difficult to attribute and can introduce incompatible transitive changes.

Lockfiles should be generated by the package manager rather than manually edited.

---

## 28. What is your CI philosophy?

**Answer:**

CI should be a required engineering gate, not a final ceremony before release.

For this project the Python quality chain includes:

```bash
ruff check .
black --check .
isort --check-only .
mypy --explicit-package-bases src
pytest
```

Security scanning and deployment checks are separate quality gates.

Small commits are valuable because when CI fails, the cause is easier to identify and revert.

---

## 29. How would you explain a CI failure caused by mypy and `src/` layout?

**Answer:**

I would explain that the problem was not necessarily a type error in application logic. The type checker can interpret the same source file through different module paths when package roots are ambiguous.

Using `--explicit-package-bases` tells mypy how to interpret the `src` package boundary and removes that ambiguity.

This is a good example of why senior engineering includes understanding tooling semantics, not just fixing the line that happens to fail.

---

## 30. What is the most important security principle in this AI architecture?

**Answer:**

The model must never become the authorization layer.

Authorization, tenant isolation, tool permissions, and access to sensitive data are deterministic application responsibilities.

The model can assist with reasoning and language generation, but it should operate inside boundaries enforced by the application.

---

# Rapid-fire questions

Use these for a final interview drill.

| Question | Core point to mention |
|---|---|
| Why async? | I/O concurrency, not CPU acceleration |
| Why PostgreSQL? | Transactions, constraints, mature ecosystem |
| Why pgvector? | Semantic retrieval close to authoritative data |
| Why Redis? | Cache/state, not source of truth |
| Why Celery? | Isolate long-running/background work |
| Why LangGraph? | Explicit stateful multi-step orchestration |
| What is RAG? | Retrieval + grounded generation |
| Biggest RAG risk? | Bad retrieval, injection, leakage, hallucination |
| Biggest AI security rule? | LLM does not authorize access |
| What is MCP? | Structured tool/resource protocol |
| How to reduce latency? | Measure first; optimize retrieval, DB, model, queues |
| How to reduce LLM cost? | Control context, retries, model routing, caching where safe |
| How to handle retries? | Bounded, observable, idempotent where required |
| Why mypy? | Catch classes of defects before runtime |
| Why CI? | Repeatable quality gate |
| Why small commits? | Easier review, attribution, rollback |
| How to evaluate RAG? | Retrieval relevance + groundedness + citations + regression set |
| What is high cardinality? | Too many unique metric series |
| ORM or SQL? | Use the appropriate abstraction and measure |
| What makes code Senior-level? | Correctness, boundaries, operability, trade-offs, maintainability |

# Final answer pattern for the interview

When asked **"Why did you design it this way?"**, use this structure:

```text
1. Requirement / constraint
2. Failure mode we need to avoid
3. Design choice
4. Trade-off
5. How we validate it
6. What I would change at larger scale
```

Example:

> "We keep tenant authorization outside the LLM because authorization must be deterministic. The trade-off is that the application has to carry tenant context through the retrieval path. We validate this with authorization and retrieval tests. At larger scale I would add stronger policy enforcement at the data-access layer and dedicated adversarial evaluation for cross-tenant leakage."

This style demonstrates engineering reasoning rather than framework memorization.
