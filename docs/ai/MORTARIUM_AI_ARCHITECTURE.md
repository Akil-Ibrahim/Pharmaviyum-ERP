# Mortarium AI Architecture & Glossary

**Purpose:** Define the role, boundaries and terminology of the Pharmaviyum AI layer. This document distinguishes current repository behavior from target capabilities; a term appearing here does not by itself prove that a feature is deployed or production-validated.

## 1. Official definition

**Mortarium AI is the secure, context-aware, agentic pharmaceutical intelligence layer integrated into Pharmaviyum ERP/CRM.** It combines language-model reasoning, LangGraph orchestration, retrieval-augmented generation (RAG), pharmaceutical document processing, scoped memory, and controlled tool integrations to provide traceable, evidence-grounded assistance to pharmacy professionals. Its design includes patient- and pharmacy-aware authorization, evaluation, and observability.

Mortarium is a decision-support subsystem, not a system of record, clinical authority, autonomous prescriber, dispensing authorization engine, or replacement for a qualified pharmacist. Deterministic application services remain authoritative for identity, permissions, calculations, inventory, transactions, and regulated workflows.

## 2. Conceptual architecture

\`\`\`text
Pharmaviyum ERP/CRM (React UI, FastAPI API)
                    |
          Authentication & authorization
                    |
       Mortarium AI Harness / Agent Runtime
       |            |                 |
   LangGraph      Memory          Guardrails
       |          (scoped)             |
       +------------+-----------------+
                    |
       +------------+-------------+
       |                          |
   LangGraph RAG              AI Agents
       |                          |
 Query transformation         MCP / API tools
 Retrieval + filters             |
 Hybrid search              Authorized services
       |
 PostgreSQL + pgvector
       |
 Evidence-grounded LLM response
       |
 Citation / output checks
       |
 Pharmacist review

Supporting capabilities:
Celery ingestion | Redis | Ragas evaluation | OpenTelemetry
\`\`\`

This is a logical component view, not a claim that every box is a separate service or that all target integrations are active in production.

## 3. Core concepts

### AI layer
An application architectural layer that brings together models, retrieval, agents, tools, memory, security controls, evaluation and telemetry. In Pharmaviyum, Mortarium is this layer.

### LLM — Large Language Model
A model trained to understand and generate natural language. It interprets pharmacist questions and drafts responses. An LLM can produce plausible but unsupported statements; it must be grounded in trusted evidence and constrained by deterministic application policy.

### Model configuration: Demo, local development and Production
The repository separates the chat/generation model from the embedding model. The provider and model are selected by environment settings; the values below describe checked-in defaults and the documented FastAPI Cloud demo profile, not proof of the model currently active in a running deployment.

| Profile | Chat provider / model | Embedding provider / model | Status and constraints |
|---|---|---|---|
| Local development default | Ollama / `qwen3.5:9b` for fast, main and complex tasks | Ollama / `mxbai-embed-large` (1024 dimensions) | Code defaults when `USE_CLOUD_LLM=false`; requires a reachable Ollama service and pulled models |
| FastAPI Cloud demo profile | QwenCloud / `qwen3.8-flash` for main, fast and complex tasks | Separate OpenAI embeddings / `text-embedding-3-small` (1024 dimensions) when configured | Demo profile documented in the deployment runbook; QwenCloud free-quota-only guard and provider-console setting are required. QwenCloud chat generation does not itself provide the embedding model |
| Production | No distinct production-only model is defined in the repository configuration | Must be explicitly configured and validated independently | The public FastAPI Cloud runbook documents the Demo QwenCloud profile only. Production model selection is managed separately and must be verified from protected runtime configuration and provider telemetry before release |

The code also contains optional Gemini and Groq provider settings. Their presence in configuration does not mean they are active. In particular, never infer the live model solely from defaults: inspect the effective `USE_CLOUD_LLM`, `CLOUD_LLM_PROVIDER`, provider-specific model variables and embedding credentials in the deployment environment without exposing secret values. A production profile must have an explicitly approved provider, model/version, quota/billing policy, data-processing approval, timeout/retry policy and fallback behavior. Do not silently fall back to a paid provider.

### RAG — Retrieval-Augmented Generation
A pattern in which the system retrieves relevant external knowledge before asking an LLM to generate an answer. In Mortarium, the intended sequence is query preparation → scoped retrieval → evidence grading/selection → context assembly → generation → output checks and citations. RAG reduces reliance on model-parametric knowledge but does not guarantee correctness.

### LangGraph
A framework for defining stateful, graph-based workflows and agents. Nodes perform steps, edges control transitions, conditional edges select paths, and state carries workflow data. Checkpointing can persist graph state. Mortarium uses LangGraph to orchestrate the pharmacist agent and RAG workflow. LangGraph is not an LLM, vector database, or authorization system.

### AI Harness / Agent Harness
The execution-control layer surrounding model and agent calls. In Mortarium it is responsible for cross-cutting input/output controls, bounded memory and cache orchestration, model routing, execution limits, structured responses and telemetry. The Harness establishes operating constraints; LangGraph defines the workflow graph. They complement each other.

### MCP — Model Context Protocol
A protocol for exposing tools and resources to AI applications through a standardized interface. Mortarium can use MCP to connect agents to approved Pharmaviyum capabilities and external information sources. MCP standardizes communication; it does not grant permissions. The server must authenticate the caller, authorize each operation, validate arguments and minimize returned data.

### AI agent
A model-driven workflow that can choose among explicitly permitted steps and tools to complete a task. In a pharmacy workflow, an agent may retrieve product information or summarize authorized records. The model may propose a tool call, but deterministic server-side policy decides whether it is allowed. Model intent is never approval for a write or clinical action.

## 4. Retrieval and data concepts

### Embeddings
Numerical vectors representing text or other content in a model's embedding space. Similar meanings can have nearby vectors. An embedding model creates vectors; pgvector stores and searches them.

### Vector store
A data store that persists embeddings and supports nearest-neighbor similarity search. Mortarium's documented storage design uses PostgreSQL with pgvector.

### PostgreSQL
PostgreSQL is the primary relational database management system (RDBMS) used by Pharmaviyum. It stores durable, structured application data and provides transactions, constraints, indexes, SQL queries and migrations. It is the system of record for business entities and transactional state; AI-generated text must never become authoritative database state without validated application workflows.

In Mortarium, PostgreSQL also stores RAG chunk records and supports durable LangGraph checkpoint persistence. Production connections are supplied through the protected `DATABASE_URL` / `PGVECTOR_DATABASE_URL` settings; credentials must never appear in documentation or logs. Creation of `document_chunks`, pgvector indexes, and LangGraph checkpoint tables is owned by the Alembic migration role. Runtime AI code performs read-only schema verification and does not execute `CREATE EXTENSION`, `CREATE TABLE`, `CREATE INDEX`, or `AsyncPostgresSaver.setup()`. The embedding vector dimension is fixed at 1024 by the migration; changing it requires a separate schema migration.

### pgvector
A PostgreSQL extension that adds a vector data type and similarity-search operators/indexes, including HNSW and IVFFlat. It enables vector retrieval alongside relational data and SQL filters. pgvector does not generate embeddings and does not independently enforce application authorization. PostgreSQL remains the database; pgvector is an extension, not a separate database.

### Chunking
Splitting a source document into bounded retrievable units while preserving meaning, structure, provenance and metadata. Pharmaceutical chunking must keep medicine identity, strength, units, dosage form, route, conditions, warnings and negation attached to the relevant text.

**Current implementation boundary:** the repository's `MedicalChunker` exposes three strategies: `medical`, `semantic` and `recursive`. Medical mode recognizes a limited set of section headings (indications, dosage, contraindications, interactions and side effects), then splits oversized sections. Semantic mode groups sentence-like spans up to the configured budget; it is not embedding-based semantic boundary detection. Recursive mode falls back through paragraph/newline/sentence/whitespace separators. The default is 512 estimated tokens with 50 overlap units. The estimate uses `len(text) // 4`, not the embedding model's tokenizer. The Celery ingestion task defaults to `medical` unless `chunking_strategy` overrides it. Table-aware parsing, exact tokenizer budgets, full bilingual section parsing, parent-child retrieval and page anchors must not be described as shipped unless separately implemented and tested. See [chunking pipeline](./chunking-pipeline.md).

### Metadata
Structured attributes attached to documents/chunks, such as source, document type, language, jurisdiction, pharmacy scope, access level and patient scope. Metadata supports filtering, provenance and lifecycle management; it must be derived from trusted ingestion context, not invented by the model.

### Pharmacy and patient scope
The pharmacy identifier is the tenant boundary. Patient-level evidence additionally requires an exact, authorized patient identifier. Public and pharmacy-level chunks must not carry a patient identifier. Without a selected patient, patient-level chunks must be excluded, never wildcard-matched. All retrieval stages, parent expansion, memory, caches and checkpoints must preserve the same scope and fail closed.

### Hybrid search
A retrieval strategy combining lexical/keyword search (for exact drug names, strengths, codes and phrases) with vector similarity search (for semantic matches). The two result sets can be fused and then ranked. Exact pharmaceutical identifiers should not rely on semantic similarity alone.

### Reranker
A model or scoring component that reorders initial retrieval candidates by their relevance to the query. It is an optional second-stage retrieval component. Do not claim it is active in runtime unless a concrete implementation is wired, configured and tested.

### Context engineering
Selecting, structuring and budgeting the information supplied to a model: the user request, trusted application context, retrieved evidence, conversation state, instructions and available tools. It includes prompt design but is broader than prompt engineering.

### Citation and provenance
A citation links an answer claim to a stable source and, where available, a specific document version, section or page. A citation identifier alone is insufficient: the cited material must actually support the claim.

## 5. Runtime, integration and background processing

### Redis
An in-memory data platform commonly used for bounded caches, ephemeral state, queues and coordination. In Mortarium it may support scoped conversational memory and caching. Redis is not the authoritative patient record. Cache and memory keys must include all authorization-relevant scope dimensions and must not leak patient-specific content across users or patients.

### Celery
A distributed task queue for asynchronous background work. Mortarium's ingestion path uses background tasks to process documents, chunk, embed and persist them. Tasks should be idempotent, bounded, observable and safe to retry. Patient-level ingestion remains blocked unless a separately authorized workflow validates patient membership and applicable consent/retention requirements.

### API tools
Deterministic application services exposed to agents through controlled interfaces. Read operations return the minimum authorized data. Writes require explicit server-side authorization and a separate approval flow; the model cannot authorize its own actions.

## 6. Evaluation, safety and observability

### Ragas
A framework for evaluating RAG pipelines using metrics such as faithfulness, answer relevancy, context precision and context recall. In this project it is intended for offline evaluation, not as a production request-path dependency. Its scores are regression signals, not clinical validation or regulatory certification.

### Pharmaceutical evaluation
Generic RAG metrics must be supplemented with domain-specific tests:
- claim-level citation correctness;
- medication name, ingredient, strength, units, dosage form and route accuracy;
- preservation of negation and conditional statements;
- unsupported clinical-claim rate;
- patient/pharmacy isolation;
- English and Russian retrieval quality;
- safe abstention for missing, stale or conflicting evidence.

Use synthetic or de-identified evaluation data and qualified review for clinical thresholds.

### Guardrails
Deterministic and model-assisted controls that constrain inputs, tool use and outputs. They include authorization checks, schema validation, prompt-injection defenses, refusal/abstention rules, output validation and execution budgets. Guardrails supplement rather than replace server-side authorization.

### Patient-context isolation
The security property that data, memory, retrieval results, caches and checkpoints belonging to one patient cannot be exposed in another patient's context. It must be enforced at every stage, not only in the final prompt. Repository code includes patient-aware scope validation and HMAC-based session/checkpoint namespaces; end-to-end PostgreSQL/Redis integration tests and production verification remain separate release gates.

### OpenTelemetry
A vendor-neutral standard and set of APIs/SDKs for collecting traces, metrics and logs. It helps diagnose latency, failures and workflow behavior across API, graph, retrieval and background tasks. Telemetry must avoid patient identifiers, prescription content, prompts, completions and retrieved clinical text unless a separately approved privacy design explicitly permits it.

## 7. Component responsibility map

| Concern | Main component(s) | Responsibility |
|---|---|---|
| Language understanding and generation | LLM | Interpret requests and draft evidence-bounded responses |
| Workflow orchestration | LangGraph | Manage graph state and execution paths |
| Cross-cutting runtime controls | AI Harness | Apply execution limits, memory/cache policy and guardrails |
| Knowledge retrieval | RAG | Retrieve evidence before generation |
| Vector similarity | Embeddings + pgvector | Represent and retrieve semantically similar content |
| Exact-term retrieval | PostgreSQL lexical search | Find exact names, codes, strengths and phrases |
| External capabilities | MCP / API tools | Expose approved tools and resources |
| Background ingestion | Celery | Process and index documents asynchronously |
| Ephemeral state | Redis | Support scoped memory/cache/coordination |
| Quality measurement | Ragas + deterministic tests | Evaluate retrieval and answer regressions |
| Diagnostics | OpenTelemetry | Trace and measure system behavior |

## 8. Non-negotiable engineering principles

1. Deterministic application code owns authentication, authorization, calculations and writes.
2. Never trust patient, pharmacy, user or role identifiers supplied by an LLM.
3. Apply pharmacy and patient filters before retrieval and again during parent/source expansion.
4. Fail closed when scope is missing, malformed or ambiguous; never retry unscoped.
5. Preserve source provenance, version, language, jurisdiction, dosage units and negation.
6. Treat retrieved documents and tool outputs as untrusted input.
7. Do not log patient identifiers, prescription data, prompts, completions or retrieved clinical text.
8. Do not describe a target capability as implemented until code, tests and operational evidence support the claim.
9. The pharmacist remains responsible for professional decisions.

## Related documentation

- [Mortarium AI / LLM System Design](./AI_LLM_SYSTEM_DESIGN.md)
- [Pharmaceutical chunking pipeline](./chunking-pipeline.md)
- [Ragas pharmaceutical evaluation](./ragas-pharmaceutical-evaluation.md)
- [LangGraph RAG architecture](./langgraph-rag-architecture.md)
- [Patient-scoped state ADR](../adr/ADR-0003-patient-scoped-ai-state.md)
- [OpenTelemetry policy](../observability/opentelemetry.md)
- [RAG architecture audit](../rag_architecture_audit.md)
