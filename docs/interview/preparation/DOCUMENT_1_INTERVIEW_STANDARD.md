# Senior Software Engineer — Python Backend & AI Engineering
## Interview Preparation Standard
**Document:** 1 — Master Standard  
**Version:** 1.3 — Recovered Edition  
**Date:** 23 November 2026  
**Status:** Reconstructed from confirmed decisions and available project context; not a verbatim recovery of the prior writing block.

---

## 1. Purpose and target role

This standard governs a rigorous, competency-based preparation program for international hiring processes targeting **Senior Software Engineer — Python Backend & AI Engineering**.

The program is based on the engineering capabilities expected in real international software teams and job descriptions. It must not become an arbitrary list of language trivia. Every topic must connect to engineering judgment, implementation, production operation, communication, or demonstrable outcomes.

The target is senior-level performance, with emphasis on L3–L4 reasoning: explaining mechanisms, making trade-offs, diagnosing failure modes, designing robust systems, and defending decisions under follow-up questioning.

## 2. Governing principles

1. **Market-driven:** align topics with real role expectations across the USA, Europe, Southeast Asia, China, Vietnam, and international remote hiring.
2. **Competency-based:** measure what the candidate can explain, implement, diagnose, design, and communicate—not merely what has been read.
3. **Depth before memorization:** answers must explain why a mechanism works, when it is appropriate, its trade-offs, and its failure modes.
4. **Production relevance:** connect theory to observability, reliability, security, performance, maintainability, and operational ownership.
5. **Technical accuracy:** verify version-sensitive claims against official documentation and reputable primary sources.
6. **Traceability:** every question maps to a competency, priority, level, learning objective, and verification method.
7. **Evidence-based project discussion:** use Pharmaviyum as a source of real project examples only where facts are known and verified. Never invent implementation details, metrics, incidents, or outcomes.
8. **Clear bilingual delivery:** explanations and learning discussion may be in Russian; interview-ready responses must be expressed in professional English.

## 3. Program size and accounting

The core question bank contains exactly:

- **300 Main Questions**
- **1,200 Follow-up Questions**
- **1,500 questions total**

Practical exercises, mock interviews, coding tasks, system-design sessions, review sessions, and assessment prompts are tracked separately. They do not inflate the 1,500-question count.

A follow-up is a distinct interviewer probe that tests additional depth, a boundary condition, a trade-off, a failure mode, or an applied scenario. It must not be a superficial rephrasing of its parent question.

## 4. Ten technical competency domains

The program has ten domains. Cross-cutting capabilities are embedded into these domains and do not create additional top-level domains.

1. **Python Core & Advanced Python** — language semantics, object model, data model, memory behavior, iterators, generators, decorators, context managers, typing, concurrency, performance, and runtime internals.
2. **Algorithms & Data Structures** — complexity analysis, core data structures, algorithmic patterns, problem decomposition, correctness, and interview execution.
3. **Backend & Database Engineering** — HTTP/API design, FastAPI and backend architecture, validation, authentication and authorization, SQL, PostgreSQL, transactions, indexing, ORM behavior, caching, and data consistency.
4. **Operating Systems & Networking** — processes, threads, scheduling, memory, filesystems, sockets, TCP/IP, DNS, TLS, HTTP, and Linux troubleshooting.
5. **System Design & Distributed Systems** — requirements, capacity, APIs, data modeling, service boundaries, queues, consistency, partitioning, replication, distributed failure, scalability, and architecture trade-offs.
6. **Quality, Testing & Code Review** — test strategy, unit/integration/contract/E2E testing, pytest, mocks, test data, CI quality gates, static analysis, code review, and maintainability.
7. **Production Engineering & Debugging** — deployment, configuration, containers, CI/CD, observability, logs/metrics/traces, incident response, debugging, performance, reliability, rollback, and operational readiness.
8. **AI / LLM / RAG / Agent Engineering** — LLM fundamentals, prompting, structured output, embeddings, retrieval, RAG architecture, LangGraph, tool use, MCP, evaluation, safety, tracing, and production operations.
9. **Project Deep Dive — Pharmaviyum** — architecture narrative, domain model, engineering decisions, implementation evidence, trade-offs, debugging stories, AI/RAG design, deployment, security, testing, and lessons learned.
10. **Behavioral, Leadership & Communication** — ownership, collaboration, conflict, prioritization, mentoring, technical influence, ambiguity, incident communication, and explaining decisions to different audiences.

## 5. Standard structure for every Main Question

Each Main Question must contain the following elements, adapted to the topic:

1. **Question (English)** — realistic interviewer wording.
2. **Russian translation** — accurate translation preserving technical meaning.
3. **What the interviewer evaluates** — competency and signal being tested.
4. **Short answer** — concise response suitable for an initial interview exchange.
5. **Detailed answer** — technically complete explanation with correct terminology.
6. **Internal mechanics** — how the relevant runtime, framework, protocol, database, or system behaves.
7. **Practical example** — realistic engineering scenario; use code where it materially improves understanding.
8. **Best practices** — current, context-sensitive engineering practices.
9. **Trade-offs and alternatives** — when the approach is appropriate and when it is not.
10. **Common mistakes and misconceptions** — including misleading simplifications.
11. **Senior-level perspective** — production implications, edge cases, risk, and decision criteria.
12. **Interview-ready answer (English)** — a coherent answer the candidate can deliver aloud.
13. **Follow-up questions with answers** — each probe has its own substantive answer.

Not every question needs a large code sample. Code must clarify the concept, not replace explanation. Examples should be realistic and maintainable.

## 6. Follow-up question standard

Follow-ups must progressively deepen the parent competency. Useful dimensions include:

- mechanism and internal behavior;
- edge cases and boundary conditions;
- complexity and performance;
- concurrency and race conditions;
- security and privacy;
- failure modes and recovery;
- scaling and capacity;
- alternatives and trade-offs;
- testing and observability;
- production incident scenarios;
- architecture evolution;
- communication and decision justification.

Every follow-up includes a direct answer, reasoning, and—where relevant—an example, trade-off, or senior-level implication. The answer must stand on its own and must not merely say “as above.”

## 7. Difficulty and priority

### Difficulty levels

- **L1 — Fundamentals:** definitions, basic semantics, and straightforward use.
- **L2 — Applied:** implementation choices, common scenarios, and practical debugging.
- **L3 — Advanced/Senior:** internals, trade-offs, concurrency, performance, failure analysis, and system-level reasoning.
- **L4 — Expert/Staff-adjacent:** ambiguous constraints, architecture consequences, cross-system failure, organizational impact, and defensible decision-making.

Target emphasis is L3–L4 while retaining sufficient L1–L2 coverage to ensure there are no foundational gaps.

### Priority levels

- **P0 — Core:** expected for the target role; must be mastered.
- **P1 — Important:** frequently useful and differentiating.
- **P2 — Specialized:** role-, company-, or system-dependent depth.

Each question must have a level and priority. These labels describe preparation priority, not a claim that every employer asks the exact question.

## 8. Learning objectives and measurable outcomes

Every competency group must state observable learning objectives. A learner should be able to demonstrate outcomes such as:

- explain a mechanism accurately without relying on memorized slogans;
- compare alternatives and justify a choice against explicit constraints;
- implement a correct solution and analyze its complexity;
- identify likely failure modes and propose mitigations;
- design meaningful tests and observability;
- diagnose a realistic production symptom;
- communicate a concise, structured answer in English.

Progress is assessed through explanation, implementation, debugging, design, and communication—not completion of reading alone.

## 9. Competency mastery and progression gates

Use a consistent mastery scale:

- **0 — Not assessed**
- **1 — Awareness:** recognizes terminology but cannot explain reliably.
- **2 — Working knowledge:** explains fundamentals and handles common cases with guidance.
- **3 — Independent:** solves realistic problems, explains trade-offs, and handles normal follow-ups.
- **4 — Senior-ready:** reasons independently about edge cases, failure modes, production constraints, and alternatives.

A domain is not considered mastered solely because its questions have been read. P0 competencies require demonstrated level 3 or higher; critical senior competencies should target level 4. Reassess weak areas after spaced review.

## 10. Coding interview execution standard

For coding tasks, follow a repeatable process:

1. clarify requirements, inputs, outputs, constraints, and assumptions;
2. identify edge cases and ask focused questions;
3. propose a straightforward baseline;
4. explain the algorithm and data structures;
5. analyze time and space complexity;
6. implement readable, correct code;
7. test normal, boundary, and adversarial cases;
8. discuss optimization and trade-offs;
9. state limitations and possible extensions.

Evaluation includes correctness, complexity, code clarity, testing, communication, and ability to respond to hints. Do not optimize prematurely or silently assume requirements.

## 11. Requirements analysis and problem decomposition

For ambiguous engineering problems, identify:

- functional requirements;
- non-functional requirements and service-level objectives;
- actors, workflows, and system boundaries;
- data ownership and lifecycle;
- constraints, assumptions, and dependencies;
- failure and abuse cases;
- acceptance criteria;
- unresolved questions and decision risks.

Candidates should make assumptions explicit and prioritize the questions that materially change the solution.

## 12. Cross-cutting engineering capabilities

The following capabilities are required across the ten domains:

### 12.1 Cloud, infrastructure, and platform engineering
Cloud primitives, deployment models, containers, networking, secrets, configuration, infrastructure automation, managed services, cost-awareness, and platform trade-offs.

### 12.2 Data engineering and database internals
Data lifecycle, schema evolution, migrations, query planning, indexing, transactions, isolation, locks, connection pools, backups, restore, and data integrity.

### 12.3 Reliability engineering and resilience
SLIs/SLOs, error budgets, graceful degradation, timeouts, retries with backoff and jitter, idempotency, circuit breakers, bulkheads, health checks, disaster recovery, and incident learning.

### 12.4 AI evaluation, safety, and governance
Groundedness, citation correctness, entity accuracy, negation preservation, hallucination measurement, privacy isolation, multilingual retrieval, prompt injection, data leakage, evaluation datasets, human review, and auditability.

### 12.5 Behavioral and leadership evidence
Use specific situations and verifiable actions. Explain context, personal responsibility, options considered, decisions, measurable or observable outcomes, and lessons. Do not fabricate metrics or claim sole ownership of team outcomes.

### 12.6 Engineering documentation and decision records
Write useful design documents, runbooks, API contracts, architecture diagrams, incident reviews, and Architecture Decision Records (ADRs). Explain decisions, alternatives, consequences, and revisit triggers.

## 13. AI / LLM / RAG quality standard

For AI-enabled systems, especially retrieval and medication-related workflows, evaluation must include:

- citation correctness: cited sources actually support the claims;
- medication entity accuracy: correct medicine name, dosage, strength, and form;
- negation preservation: “not”, “without”, contraindications, and exclusions are not lost;
- clinical hallucination rate: unsupported clinical claims are measured and minimized;
- patient-context isolation: information from one patient/customer must never leak into another context;
- multilingual retrieval: evaluate English and Russian retrieval and answer quality;
- retrieval quality and answer quality as separate stages;
- tool-call correctness, refusal behavior, latency, cost, and regression performance.

Ragas may be used as one evaluation component where appropriate, but no single framework metric substitutes for domain-specific test sets, expert review, and safety controls. LangGraph is treated as the user's established RAG/agent implementation context when discussing Pharmaviyum; details must be verified before being presented as facts.

## 14. Project Deep Dive — Pharmaviyum evidence rules

Pharmaviyum is the user's real-world project context for architecture and engineering examples. The preparation material must distinguish:

- verified implemented behavior;
- planned or proposed functionality;
- historical issues and their confirmed status;
- assumptions or hypotheses;
- outcomes supported by evidence.

Do not invent code, architecture, deployment status, performance figures, business impact, or resolution of incidents. Confidential commercial figures—including revenue, profit, margin, and monetary savings—must not be disclosed. Discuss value through non-confidential operational dimensions where supported, such as reduced task time, administrative effort, medicine lookup time, and task completion quality.

## 15. Market alignment and validation

Validate the curriculum against current job descriptions and hiring expectations for relevant markets:

- USA;
- Europe;
- Southeast Asia;
- China;
- Vietnam;
- international and remote roles.

Separate broad senior-engineering expectations from regional or company-specific preferences. Maintain a market evidence log with source, date, role level, geography, recurring competency, and resulting curriculum impact. Do not claim statistical representativeness unless a defensible sample and method exist.

## 16. Hiring-process track

Prepare a separate hiring-process track, distinct from the ten technical domains:

1. Recruiter / HR screening;
2. Hiring Manager interview;
3. Technical interviews;
4. Practical assessment / take-home task;
5. System Design interview;
6. AI specialization interview, where relevant;
7. Final / leadership / team-fit interview.

This track maps to the same competencies and question bank but is not an eleventh technical domain. Include communication expectations, likely evaluation signals, preparation strategy, and candidate questions.

## 17. Practice and assessment system

Track practical work separately from the 1,500 questions:

- live coding and algorithmic problem solving;
- code review and refactoring;
- debugging and root-cause analysis;
- testing strategy and test implementation;
- performance profiling and optimization;
- API and database design;
- system design and architecture trade-offs;
- production readiness and incident response;
- AI/RAG evaluation and safety;
- behavioral mock interviews and English communication.

Each exercise should specify objective, constraints, expected deliverable, evaluation rubric, and review notes.

## 18. Coverage matrix and traceability

Maintain a matrix linking each question and exercise to:

- domain and competency group;
- learning objective;
- Main Question ID and parent-child follow-up relationship;
- L1–L4 level;
- P0–P2 priority;
- market relevance/evidence;
- practical verification;
- mastery status;
- last review and next review.

No competency should be considered covered merely because it appears in a heading. Coverage requires an actual question, answer, and suitable assessment.

## 19. Technical source and version policy

Prefer official documentation, language specifications, framework documentation, database manuals, standards, and primary engineering publications. For disputed or version-sensitive details:

1. identify the relevant version;
2. verify against primary sources;
3. distinguish guaranteed behavior from implementation detail;
4. record the source and review date;
5. update explanations when versions materially change.

Avoid unsupported absolutes such as “always,” “never,” or “the fastest” unless the claim is precisely qualified.

## 20. Completion criteria

The preparation program is complete when:

- the 300 Main Questions and 1,200 substantive Follow-ups are authored and reviewed;
- all ten domains have mapped competencies and learning objectives;
- P0 competencies meet mastery gates;
- practical assessments demonstrate applied capability;
- the candidate can deliver clear interview-ready English answers;
- system-design, production, AI, and project narratives withstand senior-level follow-ups;
- market alignment has been reviewed against documented evidence;
- weak areas have remediation plans and reassessment results.

## 21. Document governance

Document 1 is the master standard. Other curriculum documents must conform to its terminology, question format, levels, priorities, evidence rules, and assessment model.

Changes must include a version, date, rationale, affected sections, and impact on dependent documents. The 1,500-question total and ten-domain structure are controlled constraints; changes require explicit review rather than silent drift.

---

**End of Document 1 — Version 1.3, Recovered Edition**