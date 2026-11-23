# Senior Python Backend Engineer | AI/LLM — Interview Curriculum

**Status:** Learning and interview-preparation plan  
**Target level:** Senior Python Backend Engineer with AI/LLM engineering depth  
**Repository case study:** Pharmaviyum ERP/CRM and Mortarium AI  
**Target bank:** 260 primary questions and 700 follow-up questions, each with model answers  
**Language format:** English interview prompt, Russian translation, Russian model answer, professional English model answer

## 1. Purpose and scope

This curriculum prepares the candidate to explain, design, review, debug and defend production software decisions in the style of international product-company interviews. It is not a claim that the candidate has implemented every technology or that every target capability is production-ready.

The question bank combines:
- language and runtime fundamentals;
- backend and data engineering;
- architecture and distributed systems;
- production reliability and security;
- AI/LLM engineering;
- project-specific architecture deep dives;
- technical communication and engineering leadership.

Pharmaviyum is the recurring case study, not a substitute for general engineering fundamentals. Questions must distinguish verified repository behavior from proposed designs, roadmap items and unverified production claims.

## 2. Question allocation

The initial target is **260 primary questions**. The allocation below is a planning baseline; it may be adjusted after reviewing the actual repository and interview requirements, but the total must remain explicit.

| # | Domain | Primary questions |
|---:|---|---:|
| 1 | Python Core: object model, data model, collections, exceptions, iterators, generators, context managers, typing fundamentals | 30 |
| 2 | Advanced Python: memory management, CPython internals, descriptors, decorators, metaclasses, profiling, performance | 25 |
| 3 | OOP, SOLID, design principles and design patterns | 20 |
| 4 | SQL fundamentals and query reasoning | 25 |
| 5 | PostgreSQL: MVCC, isolation, locks, indexes, query plans, schema design, migrations and connection management | 25 |
| 6 | Backend engineering and FastAPI: API contracts, validation, dependency injection, middleware, authentication and application boundaries | 25 |
| 7 | AsyncIO, concurrency and parallelism: event loop, tasks, cancellation, threads, processes and backpressure | 20 |
| 8 | Distributed systems: messaging, delivery semantics, idempotency, retries, outbox, caching and failure isolation | 20 |
| 9 | System design and architecture: modular monoliths, service boundaries, multi-tenancy, scalability and trade-offs | 20 |
| 10 | Security and privacy: threat modelling, authorization, tenant isolation, secrets, audit and AI-specific risks | 15 |
| 11 | Testing, CI/CD and production engineering: test strategy, observability, SLOs, incidents, deployment and recovery | 15 |
| 12 | AI/LLM engineering: LLM fundamentals, RAG, LangGraph, Agent Harness, MCP, Ragas, evaluation and OpenTelemetry | 20 |
| | **Total** | **260** |

The first learning sequence prioritizes Python Core, SQL/PostgreSQL and OOP/SOLID, as requested. The remaining domains follow in the order shown unless the candidate explicitly changes the plan.

## 3. Follow-up question target

For the 260 primary questions, plan approximately **700 follow-up questions** (an average of about 2.7 follow-ups per primary question). A reasonable working range is 650–750.

Follow-ups must test depth rather than paraphrase the primary question. Use them to probe:
- implementation mechanics and runtime behavior;
- assumptions, constraints and alternatives;
- failure modes and recovery;
- concurrency, consistency and security boundaries;
- performance and operational consequences;
- trade-offs and decision criteria;
- a concrete Pharmaviyum scenario.

Each follow-up must have a concise, technically correct model answer. Follow-up counts may vary by topic; difficult system-design questions may need more than simple definition questions.

## 4. Required structure for every primary question

Each question entry must contain:

1. **Question (EN):** natural wording used by an international technical interviewer.
2. **Перевод (RU):** accurate Russian translation preserving technical meaning.
3. **Model answer (RU):** a structured, technically rigorous answer suitable for Senior level.
4. **Model answer (EN):** a natural professional English version, not a literal machine translation.
5. **Follow-up questions (EN/RU):** normally two or three probing questions, with translations.
6. **Follow-up answers (RU/EN):** concise answers for each follow-up.
7. **Pharmaviyum connection:** relevant modules, code paths, architecture documents, tests or a clearly labelled hypothetical scenario.
8. **Evaluation rubric:** what a weak, competent and strong Senior answer demonstrates.
9. **Common pitfalls:** inaccurate claims, missing trade-offs or unsafe assumptions.
10. **References:** primary documentation or repository evidence where useful.

Answers should teach reasoning and terminology. They must not encourage memorizing scripts as a substitute for understanding.

## 5. Interview practice protocol

Use two distinct modes.

### Learning mode

1. Show the English question.
2. Show its Russian translation.
3. Explain the expected scope.
4. Present and discuss the Russian model answer.
5. Present the professional English answer.
6. Rehearse the answer in short segments.
7. Ask follow-ups one at a time.

### Mock interview mode

1. Ask one English question and immediately provide its Russian translation.
2. Do not reveal the model answer before the candidate responds.
3. Let the candidate answer in English or Russian, according to the agreed exercise.
4. Ask follow-ups based on the actual answer.
5. Score the response and explain gaps.
6. Provide improved Russian and English versions after the attempt.

For spoken practice, keep turns short, allow the candidate to finish, and do not interrupt pauses or hesitation unless the candidate asks for help.

## 6. Senior-level evaluation rubric

Score each competency from 1 to 5 and support the score with evidence from the answer.

| Score | Interpretation |
|---:|---|
| 1 | Incorrect or materially incomplete; cannot explain the concept |
| 2 | Basic familiarity; relies on definitions and misses important constraints |
| 3 | Competent implementation-level understanding; handles common cases |
| 4 | Senior-level reasoning; explains internals, trade-offs, failure modes and operational impact |
| 5 | Strong Senior / Staff-level reasoning; frames ambiguity, compares alternatives, quantifies where possible and connects technical choices to system outcomes |

Assess at least:
- technical correctness and depth;
- architecture and trade-off reasoning;
- data correctness and security;
- reliability and operational thinking;
- clarity of communication;
- professional English terminology and fluency.

A high score requires a defensible explanation, not merely the use of advanced terminology.

## 7. Pharmaviyum case-study rules

Use the repository as evidence, and verify relevant files before writing project-specific answers. Useful starting points include:
- `src/pharmaviyum/` — backend implementation;
- `src/pharmaviyum/ai/` — AI implementation;
- `docs/architecture/` — architecture contracts and system context;
- `docs/ai/` and `docs/ai_architecture.md` — AI/RAG design;
- `docs/adr/` — recorded architecture decisions;
- `tests/` — automated evidence;
- `docs/devops/` and `docs/operations/` — deployment and operational contracts.

Every project-specific statement must be labelled accurately:
- **Implemented:** present in the inspected source revision.
- **Test-verified:** supported by a named test and its result for the relevant revision.
- **Proposed / planned:** a design target, not an implemented capability.
- **Not verified:** evidence is insufficient.
- **Hypothetical interview scenario:** an exercise, not a statement about current production.

Do not invent throughput, fleet capacity, availability, security certification, clinical validation or Production deployment evidence. Do not disclose NDA-protected business results, private Production implementation details, secrets or real customer/patient data.

## 8. Technical coverage expectations

The curriculum must go beyond definitions. For example:
- Python: object identity, mutability, hashability, reference counting, cyclic GC, GIL implications, event-loop behavior and profiling.
- SQL/PostgreSQL: relational modelling, joins, query plans, MVCC, isolation anomalies, locking, deadlocks, indexes, migrations and transaction boundaries.
- SOLID/design: cohesion, coupling, dependency inversion, composition, pattern selection and the cost of over-abstraction.
- Backend: API compatibility, validation, authentication/authorization, dependency lifetimes, async correctness and error contracts.
- Distributed systems: at-least-once delivery, idempotency, transactional outbox, retries, timeouts, circuit breakers and consistency.
- System design: requirements, capacity assumptions, data ownership, boundaries, bottlenecks, failure domains and evolution strategy.
- AI/LLM: retrieval quality, grounding, citations, multilingual retrieval, patient/tenant isolation, prompt injection, tool permissions, LangGraph state, MCP boundaries, Ragas evaluation and trace/metric design.

## 9. Maintenance and acceptance criteria

- Keep the English curriculum canonical and maintain the Russian companion with equivalent technical meaning.
- Update both language versions in the same change.
- Link to canonical architecture and implementation documents instead of duplicating their claims.
- Review examples and technical answers against current official documentation when version-sensitive.
- Mark questions as drafted, reviewed or validated; a drafted answer is not automatically authoritative.
- Keep the 260-question allocation and follow-up target synchronized in both language versions.
- Do not claim the full question bank is complete until all entries and answers exist and have been reviewed.

**Initial acceptance:** curriculum structure and allocation are recorded. The full 260 primary questions and approximately 700 answered follow-ups are to be authored and reviewed incrementally.
