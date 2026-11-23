# Senior Software Engineer — Python Backend & AI Engineering
## Technical Curriculum Architecture
**Document:** 2 — Curriculum Architecture  
**Version:** 1.0 — Recovered Edition  
**Date:** 23 November 2026  
**Status:** Reconstructed from confirmed decisions and available project context; not a verbatim recovery of the prior writing block.

---

## 1. Purpose and relationship to Document 1

This document converts the master standard into a measurable curriculum: domain allocation, competency groups, learning objectives, priorities, levels, practice, and completion criteria.

Document 1 remains authoritative. If a conflict arises, Document 1 takes precedence. This allocation is a proposed planning baseline and must be validated against current job-description evidence; it is not a statistical claim about the frequency of interview questions in the market.

## 2. Question allocation

The program contains exactly 300 Main Questions and 1,200 Follow-ups.

| # | Domain | Main | Follow-ups | Total |
|---:|---|---:|---:|---:|
| 1 | Python Core & Advanced Python | 45 | 180 | 225 |
| 2 | Algorithms & Data Structures | 20 | 80 | 100 |
| 3 | Backend & Database Engineering | 45 | 180 | 225 |
| 4 | Operating Systems & Networking | 20 | 80 | 100 |
| 5 | System Design & Distributed Systems | 40 | 160 | 200 |
| 6 | Quality, Testing & Code Review | 25 | 100 | 125 |
| 7 | Production Engineering & Debugging | 25 | 100 | 125 |
| 8 | AI / LLM / RAG / Agent Engineering | 35 | 140 | 175 |
| 9 | Project Deep Dive — Pharmaviyum | 20 | 80 | 100 |
| 10 | Behavioral, Leadership & Communication | 25 | 100 | 125 |
| **Total** | | **300** | **1,200** | **1,500** |

Each Main Question has four Follow-ups as the planning ratio. A follow-up must add a distinct evaluation dimension and include its own answer.

## 3. Allocation principles

- Allocate more questions to broad, central senior-engineering domains: Python, backend/database, and system design.
- Preserve explicit coverage for algorithms, operating systems, networking, quality, and production engineering.
- Give AI engineering a substantial allocation reflecting the target Backend & AI profile.
- Keep Pharmaviyum deep dive focused: it tests architectural ownership and evidence, not memorization of the entire product.
- Give behavioral and leadership preparation a defined allocation rather than treating it as an afterthought.
- Revisit allocation after market mapping and diagnostic assessment, without changing the total of 1,500 unless explicitly approved.

## 4. Domain 1 — Python Core & Advanced Python
**Allocation:** 45 Main / 180 Follow-ups / 225 total  
**Target:** L3–L4; **Priority:** P0 overall.

### Competency groups
1. Python object model and data model: identity, equality, mutability, hashability, special methods, descriptors, attribute lookup.
2. Core data structures and semantics: list, tuple, dict, set, ordering, hashing, copying, slicing, comprehensions.
3. Functions and call semantics: scope, closures, argument binding, decorators, higher-order functions.
4. Iteration and lazy evaluation: iterators, generators, yield, generator expressions, itertools.
5. Object-oriented Python: classes, inheritance, MRO, composition, polymorphism, abstract base classes, protocols.
6. Memory management and runtime: references, garbage collection, reference counting where applicable, allocation, object lifetime, `__slots__`.
7. Exceptions and resource management: exception hierarchy, chaining, context managers, `with`, cleanup guarantees.
8. Typing and API design: annotations, generics, protocols, structural typing, static checking, runtime limitations.
9. Concurrency and parallelism: threads, processes, GIL semantics by Python version/build, asyncio, synchronization, cancellation.
10. Performance and internals: profiling, algorithmic cost, interpreter behavior, import system, packaging, runtime trade-offs.

### Learning outcomes
The candidate can explain Python semantics precisely; predict behavior in non-trivial examples; choose suitable abstractions; reason about memory and concurrency; profile rather than guess; and communicate version-dependent behavior accurately.

### Practical verification
Explain and review snippets; diagnose mutation/aliasing bugs; design iterator/context-manager APIs; compare threading, multiprocessing, and asyncio for a workload; profile a slow path; and discuss compatibility across relevant Python versions.

## 5. Domain 2 — Algorithms & Data Structures
**Allocation:** 20 Main / 80 Follow-ups / 100 total  
**Target:** L2–L4; **Priority:** P0 for core patterns.

### Competency groups
1. Complexity analysis: Big-O, time/space trade-offs, amortized analysis.
2. Linear structures: arrays/lists, strings, linked lists, stacks, queues, deques.
3. Hash-based structures: hash maps/sets, collision concepts, lookup trade-offs.
4. Trees and heaps: binary trees, BST concepts, traversals, priority queues, tries where relevant.
5. Graphs: representations, BFS, DFS, shortest-path concepts, topological ordering.
6. Algorithmic patterns: two pointers, sliding window, prefix sums, binary search, recursion, backtracking, greedy, dynamic programming.
7. Correctness and testing: invariants, boundary cases, adversarial inputs.
8. Interview execution: clarification, decomposition, explanation, implementation, testing, complexity discussion.

### Learning outcomes
Solve representative problems independently, justify the selected data structure, prove or explain correctness, analyze complexity, and communicate while coding.

### Practical verification
Timed exercises across easy/medium patterns, selected advanced problems, code review, edge-case tests, and verbal explanation without relying on memorized templates.

## 6. Domain 3 — Backend & Database Engineering
**Allocation:** 45 Main / 180 Follow-ups / 225 total  
**Target:** L3–L4; **Priority:** P0.

### Competency groups
1. HTTP and API fundamentals: methods, status codes, headers, caching, content negotiation, idempotency.
2. REST and API design: resource modeling, pagination, filtering, versioning, error contracts, OpenAPI.
3. FastAPI and Python backend architecture: dependency injection, request lifecycle, async endpoints, validation, middleware, lifespan.
4. Data validation and serialization: Pydantic concepts, schema boundaries, input normalization.
5. Authentication and authorization: password storage, sessions, JWT trade-offs, OAuth/OIDC concepts, RBAC/permissions, token lifecycle.
6. SQL and relational modeling: normalization, constraints, joins, aggregates, schema design.
7. PostgreSQL internals and operations: indexes, query plans, transactions, isolation, locks, vacuum concepts, connection pooling, backups.
8. ORM and data access: SQLAlchemy/SQLModel patterns, identity map, unit of work, eager/lazy loading, N+1, transaction boundaries.
9. Caching and consistency: cache-aside, invalidation, TTL, stampede, Redis data structures, consistency boundaries.
10. Backend security and resilience: validation, injection prevention, rate limiting, secrets, timeouts, retries, safe error handling.
11. Async data access and performance: connection lifecycle, pool sizing, blocking calls, query optimization, batching.
12. Migrations and data lifecycle: schema evolution, backward compatibility, migration safety, restore and integrity.

### Learning outcomes
Design maintainable APIs and data models; reason about request and transaction lifecycles; diagnose database bottlenecks; implement secure auth boundaries; and make justified consistency/performance trade-offs.

### Practical verification
Design an API contract, inspect query plans, identify N+1 queries, reason about transaction isolation, review auth flows, plan a zero/low-downtime schema migration, and diagnose connection-pool exhaustion.

## 7. Domain 4 — Operating Systems & Networking
**Allocation:** 20 Main / 80 Follow-ups / 100 total  
**Target:** L2–L4; **Priority:** P0/P1 by competency.

### Competency groups
1. Processes, threads, scheduling, context switching.
2. Virtual memory, address spaces, allocation, memory pressure.
3. Filesystems, file descriptors, permissions, signals.
4. Synchronization primitives and common concurrency hazards.
5. Linux process and service troubleshooting.
6. Networking layers, IP addressing, routing, ports, sockets.
7. TCP lifecycle, reliability, congestion concepts, connection states.
8. DNS, TLS, certificates, HTTP/1.1, HTTP/2, HTTP/3 concepts.
9. Proxies, load balancers, reverse proxies, connection keep-alive.
10. Network diagnostics: latency, packet loss, timeouts, name resolution, connection refusal.

### Learning outcomes
Explain how an application interacts with the operating system and network; distinguish application, transport, and infrastructure failures; and use a disciplined troubleshooting sequence.

### Practical verification
Analyze a connection failure, explain DNS/TLS/HTTP request flow, interpret process/socket symptoms, and distinguish CPU, memory, disk, and network bottlenecks.

## 8. Domain 5 — System Design & Distributed Systems
**Allocation:** 40 Main / 160 Follow-ups / 200 total  
**Target:** L3–L4; **Priority:** P0.

### Competency groups
1. Requirements discovery and problem framing.
2. Capacity estimation and workload characterization.
3. API, data model, and service-boundary design.
4. Monolith, modular monolith, and microservice trade-offs.
5. Synchronous and asynchronous communication.
6. Queues, event-driven architecture, delivery semantics, ordering.
7. Consistency, transactions, idempotency, deduplication, sagas.
8. Partitioning, replication, sharding, read/write paths.
9. Caching, CDN, load balancing, horizontal scaling.
10. Distributed failure: partial failure, retries, timeouts, backpressure.
11. Security, privacy, tenancy, and data isolation.
12. Observability, SLOs, resilience, disaster recovery.
13. Architecture evolution, migrations, technical debt, ADRs.

### Learning outcomes
Lead a structured design discussion from requirements to architecture; identify bottlenecks and failure modes; defend trade-offs; and evolve a design under changing constraints.

### Practical verification
Design services such as an inventory, ordering, notification, or search workflow; discuss scaling and failure; review an existing architecture; and produce a concise design record.

## 9. Domain 6 — Quality, Testing & Code Review
**Allocation:** 25 Main / 100 Follow-ups / 125 total  
**Target:** L3; **Priority:** P0.

### Competency groups
1. Testing pyramid and risk-based test strategy.
2. Unit tests and behavioral contracts.
3. Integration and database tests.
4. API and contract testing.
5. End-to-end and browser automation.
6. pytest fixtures, parametrization, plugins, isolation.
7. Mocking, fakes, stubs, and test doubles.
8. Async testing and concurrency-sensitive tests.
9. Test data, factories, determinism, flaky-test diagnosis.
10. Coverage interpretation and mutation/risk thinking.
11. Static analysis, formatting, typing, and CI quality gates.
12. Code review, maintainability, refactoring, and regression control.

### Learning outcomes
Choose test levels based on risk, create reliable tests, identify weak test design, review code constructively, and balance speed with confidence.

### Practical verification
Build a focused test suite, diagnose a flaky test, review a pull request, and propose a safe refactoring plan with regression protection.

## 10. Domain 7 — Production Engineering & Debugging
**Allocation:** 25 Main / 100 Follow-ups / 125 total  
**Target:** L3–L4; **Priority:** P0.

### Competency groups
1. Application configuration, environment separation, and secrets.
2. Containers and deployment fundamentals.
3. CI/CD pipelines, artifact provenance, release strategies.
4. Health checks, readiness, liveness, startup behavior.
5. Logs, metrics, traces, correlation and context propagation.
6. OpenTelemetry concepts and instrumentation.
7. Incident response, triage, escalation, and communication.
8. Root-cause analysis and blameless postmortems.
9. Performance profiling, latency, throughput, saturation.
10. Reliability patterns: timeouts, retries, backoff, jitter, circuit breakers, bulkheads.
11. Rollbacks, migrations, backups, recovery, disaster readiness.
12. Production security, dependency risk, patching, access control.

### Learning outcomes
Operate services responsibly, diagnose incidents from evidence, instrument useful telemetry, improve reliability, and communicate impact and recovery clearly.

### Practical verification
Analyze logs and traces, troubleshoot an unhealthy service, define an actionable alert, plan a rollback, and conduct a simulated incident review.

## 11. Domain 8 — AI / LLM / RAG / Agent Engineering
**Allocation:** 35 Main / 140 Follow-ups / 175 total  
**Target:** L3–L4; **Priority:** P0 for evaluation, safety, RAG, and production fundamentals.

### Competency groups
1. LLM fundamentals: tokens, context windows, inference, sampling, model limitations.
2. Prompt design and structured outputs.
3. Embeddings, similarity, vector search, and hybrid retrieval.
4. RAG architecture: ingestion, chunking, indexing, retrieval, reranking, grounding.
5. Retrieval and generation evaluation as separate stages.
6. LangGraph concepts: state, nodes, edges, routing, persistence, control flow.
7. Tool calling and agent design: permissions, schemas, validation, bounded autonomy.
8. MCP concepts and integration boundaries.
9. Memory, conversation state, and context management.
10. AI observability: traces, spans, tool calls, latency, token/cost telemetry.
11. Evaluation datasets, regression testing, Ragas and domain-specific metrics.
12. Safety: prompt injection, data exfiltration, authorization, privacy, tenant isolation.
13. Reliability: timeouts, fallbacks, model/provider failures, retries, deterministic controls.
14. Deployment, scaling, model selection, latency and cost trade-offs.

### Required AI/RAG evaluation dimensions
- citation correctness and evidence support;
- medication entity accuracy, including name, dosage/strength, and dosage form;
- negation preservation;
- clinical hallucination rate;
- patient/customer-context isolation;
- multilingual retrieval and answer quality for Russian and English;
- retrieval precision/recall or suitable ranking metrics;
- answer groundedness and completeness;
- tool-call correctness and refusal behavior;
- latency, cost, and regression performance.

Ragas is a candidate evaluation framework, not a complete safety or clinical validation solution. Combine framework metrics with curated domain test sets, expert review, and explicit privacy/security tests.

### Learning outcomes
Design and evaluate an AI-enabled backend feature; separate retrieval failure from generation failure; implement bounded tool use; measure quality; and identify privacy, safety, and operational risks.

### Practical verification
Build or explain a RAG evaluation plan, diagnose retrieval errors, design tenant-isolation tests, trace an agent workflow, evaluate citations, and defend model/tool choices.

## 12. Domain 9 — Project Deep Dive: Pharmaviyum
**Allocation:** 20 Main / 80 Follow-ups / 100 total  
**Target:** L3–L4; **Priority:** P0 for verified architecture and ownership.

### Competency groups
1. Product problem, users, workflows, and domain boundaries.
2. High-level architecture and component responsibilities.
3. Backend/API and frontend integration.
4. Data model, persistence, and migration decisions.
5. Authentication, authorization, and security boundaries.
6. POS and pharmacy workflow design where implemented and verified.
7. AI assistant, RAG, and agent architecture where implemented and verified.
8. Testing, CI, deployment, and environment configuration.
9. Observability, debugging, and production readiness.
10. Technical decisions, alternatives, limitations, and roadmap.
11. Engineering challenges, incident narratives, and lessons learned.
12. Demonstrable outcomes and non-confidential business value.

### Evidence rules
For each story, label facts as implemented, planned, historical, unresolved, or hypothetical. Verify code and deployment status before describing them as current. Do not invent metrics, incident resolutions, or personal ownership. Do not disclose confidential revenue, profit, margin, or monetary savings.

### Learning outcomes
Deliver a concise architecture walkthrough; explain personal contributions precisely; justify technical decisions; discuss failures honestly; and connect engineering work to user and operational value.

### Practical verification
Prepare a 5-minute and 15-minute project walkthrough, architecture diagram, two or more evidence-backed engineering stories, a trade-off discussion, and a production-readiness review.

## 13. Domain 10 — Behavioral, Leadership & Communication
**Allocation:** 25 Main / 100 Follow-ups / 125 total  
**Target:** L3–L4; **Priority:** P0/P1.

### Competency groups
1. Ownership and accountability.
2. Ambiguity and problem solving.
3. Prioritization and trade-off decisions.
4. Conflict resolution and disagreement.
5. Collaboration across functions and teams.
6. Mentoring, feedback, and raising engineering standards.
7. Technical leadership without formal authority.
8. Incident leadership and stakeholder communication.
9. Learning from failure and adapting.
10. Explaining complex technical topics clearly.
11. Negotiating scope, deadlines, and quality.
12. Remote, multicultural, and cross-time-zone collaboration.

### Learning outcomes
Provide concise, credible stories; distinguish individual contribution from team effort; demonstrate sound judgment; and communicate clearly with technical and non-technical stakeholders.

### Practical verification
Prepare evidence-backed STAR/CARE stories, run behavioral mock interviews, practice concise English delivery, and answer probing questions about decisions and outcomes.

## 14. Cross-domain competency mapping

Cross-cutting competencies must be mapped into relevant domains rather than counted as additional domains.

| Cross-cutting capability | Primary domains | Verification |
|---|---|---|
| Learning objectives and mastery gates | All | Assessments and mastery records |
| Coding interview execution | 1, 2, 3, 6 | Live coding and review |
| Requirements analysis | 2, 5, 9 | Problem framing and design |
| Cloud/platform engineering | 3, 5, 7, 9 | Deployment and architecture exercises |
| Data engineering/database internals | 3, 5, 7, 9 | Query, migration, recovery exercises |
| Reliability and resilience | 3, 5, 7, 8, 9 | Failure and incident simulations |
| AI safety and governance | 8, 9 | Evaluation and isolation tests |
| Leadership evidence | 5, 7, 9, 10 | Design/incident/behavioral narratives |
| Documentation and ADRs | 5, 7, 8, 9, 10 | Written design and decision records |

## 15. Suggested learning sequence

The sequence is a dependency-aware recommendation, not a requirement to finish one entire domain before touching another.

1. Python Core foundations and advanced semantics.
2. Algorithms and data structures in parallel with Python practice.
3. Backend and database engineering.
4. Operating systems and networking alongside backend implementation.
5. Testing and code review as a continuous discipline.
6. Production engineering and debugging.
7. System design and distributed systems, revisiting backend/database concepts.
8. AI/LLM/RAG/agent engineering, including evaluation and safety.
9. Pharmaviyum project deep dive, using verified evidence from prior domains.
10. Behavioral, leadership, and communication practice throughout; final hiring-process simulations.

Spaced review and mixed-domain practice should begin early rather than waiting until the end.

## 16. Market validation plan

For each target geography—USA, Europe, Southeast Asia, China, and Vietnam—collect current senior Python/backend/AI job descriptions and record:

- company and role level;
- geography and date captured;
- recurring technical requirements;
- expected system-design and production responsibilities;
- AI/LLM requirements, if any;
- communication and leadership expectations;
- evidence strength and any market-specific qualification.

Use the evidence to validate priorities and allocations. Do not treat a small convenience sample as statistically representative. Keep global senior-engineering fundamentals separate from local market signals.

## 17. Question authoring and quality assurance

Each question record should include:

- stable ID;
- domain and competency group;
- Main or Follow-up designation and parent ID;
- English wording and Russian translation;
- evaluation objective;
- priority and difficulty;
- short and detailed answer;
- mechanics and practical context;
- trade-offs, failure modes, and common mistakes;
- interview-ready English response;
- source/version review date where needed;
- assessment linkage and mastery status.

Quality review checks technical correctness, clarity, senior-level depth, non-duplication, realistic interviewer wording, and consistency with Document 1.

## 18. Assessment and completion gates

### Per-question gate
The candidate can explain the answer accurately, handle its follow-ups, and apply it to a realistic scenario.

### Per-competency gate
The candidate demonstrates level 3 or higher for P0 competencies, with level 4 targeted for critical senior competencies.

### Per-domain gate
The candidate passes a mixed assessment containing explanation, applied problem solving, and scenario-based follow-ups. Domain completion is not defined by reading all questions.

### Program gate
- 300 Main Questions and 1,200 substantive Follow-ups completed and reviewed;
- all ten domains mapped to competencies and learning objectives;
- P0 mastery gates passed;
- practical exercises and mock interviews completed;
- project narrative evidence checked;
- English interview communication assessed;
- hiring-process track rehearsed;
- weak areas documented with remediation and reassessment.

## 19. Change control

This is the recovered baseline for Document 2. Changes to question allocation require:
1. documented reason;
2. evidence from market mapping or diagnostic assessment;
3. impact analysis across domains;
4. confirmation that the total remains 1,500;
5. version increment and changelog.

### Changelog
- **v1.0 — 23 November 2026:** Recovered baseline reconstructed from confirmed decisions: ten domains, 300 Main Questions, 1,200 Follow-ups, domain allocation, competency groups, learning outcomes, practice, market validation, and mastery gates.

---

**End of Document 2 — Version 1.0, Recovered Edition**