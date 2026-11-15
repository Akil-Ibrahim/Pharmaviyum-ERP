# Documentation

[English](README.md) · [Русский](README.ru.md)

This directory is the engineering documentation home for Pharmaviyum ERP/CRM. The English documentation is canonical for engineering and operations; a Russian pharmacy workflow companion is maintained where useful.

## Start here

| Area | English | Русский | What it covers |
|---|---|---|---|
| Pharmacy workflows | [Workflow specification](./workflows/pharmacy-workflow.en.md) | [Спецификация аптечного процесса](./workflows/pharmacy-workflow.ru.md) | Pharmacy operations, POS, dispensing, inventory, procurement, audit and offline boundaries |
| System architecture | [Architecture vision](./architecture/pharmaviyum-architecture.en.md) | [Архитектурное видение](./architecture/pharmaviyum-architecture.ru.md) | Component boundaries, trust model, data ownership and Central/Edge target |
| Technology | [Technology Stack & Glossary](./technology-stack.md) | [Стек и глоссарий](./technology-stack.ru.md) | Definitions, architectural roles, version policy, environment boundaries and dependency updates |
| Repository structure | [Repository Structure Guide](./architecture/repository-structure.md) | [Структура репозитория](./architecture/repository-structure.ru.md) | Directory ownership, file placement and safe moves |
| AI / LLM system design | [AI system design](./ai/AI_LLM_SYSTEM_DESIGN.md) | Перевод готовится | Mortarium lifecycle, Agent Harness, LangGraph, RAG, MCP, safety, evaluation and observability |
| Mortarium glossary | [Architecture & glossary](./ai/MORTARIUM_AI_ARCHITECTURE.md) | [Архитектура и глоссарий](./ai/MORTARIUM_AI_ARCHITECTURE.ru.md) | AI/LLM, PostgreSQL, pgvector, Redis, MCP, Ragas and OpenTelemetry |
| Pharmacy operations AI | [Mortarium pharmacy operations](./ai/mortarium-pharmacy-operations.md) | [Операционная работа Mortarium](./ai/mortarium-pharmacy-operations.ru.md) | Available read-only tools and safety boundaries |
| Patient session isolation | [Patient-scoped state](./ai/patient-session-isolation.md) | [Изоляция состояния пациента](./ai/patient-session-isolation.ru.md) | Session, memory and checkpoint isolation requirements |
| QwenCloud demo | [QwenCloud demo](./ai/QWENCLOUD_DEMO.md) | Перевод готовится | Demo provider configuration and quota safeguards |
| AI architecture | [AI architecture](./ai_architecture.md) | Перевод готовится | Current implementation details |
| LangGraph RAG | [RAG graph architecture](./ai/langgraph-rag-architecture.md) | [Архитектура LangGraph RAG](./ai/langgraph-rag-architecture.ru.md) | Graph nodes, state, retrieval, bounded execution and persistence |
| RAG audit | [RAG architecture audit](./rag_architecture_audit.md) | Перевод готовится | Dated findings, gaps and remediation priorities |
| Pharmaceutical evaluation | [Ragas evaluation](./ai/ragas-pharmaceutical-evaluation.md) | [Оценка RAG](./ai/ragas-pharmaceutical-evaluation.ru.md) | Offline evaluator and pharmacy-specific quality metrics |
| Hallucination and red-team | [Safety evaluation](./ai/hallucination-detection-and-red-team.md) | [Выявление галлюцинаций и red-team](./ai/hallucination-detection-and-red-team.ru.md) | Groundedness, adversarial testing and safe abstention |
| Chunking | [Chunking pipeline](./ai/chunking-pipeline.md) | [Pipeline чанкинга](./ai/chunking-pipeline.ru.md) | Current chunking implementation and target architecture |
| LLM standards | [LLM engineering standards](./llm_engineering_standards.md) | Перевод готовится | Context, token budgets, model routing, cache, memory and MCP standards |
| ADRs | [ADR index](./adr/README.md) | [Индекс архитектурных решений](./adr/README.ru.md) | Accepted and proposed architecture decisions | Accepted and proposed architecture decisions |
| Development | [Development and testing handbook](./guides/DEVELOPMENT_AND_TESTING.md) | Перевод готовится | Contributor workflow and quality gates |
| Environment | [Environment setup](./guides/ENVIRONMENT_SETUP.md) | Перевод готовится | Local services, configuration and prerequisites |
| Testing | [Testing guide](./guides/TESTING.md) | Перевод готовится | Test layout, markers and CI gates |
| Operations | [Production operations runbook](./operations/PRODUCTION_OPERATIONS_RUNBOOK.md) | Перевод готовится | Health checks, incident triage, backup and recovery |
| Release | [Release runbook](./operations/RELEASE_RUNBOOK.md) | Перевод готовится | Controlled release and rollback |
| Hosted deployment | [FastAPI Cloud](./deployment/FASTAPI_CLOUD.md) | Перевод готовится | Hosting, secrets, runtime constraints and manual deployment |
| DevOps roadmap | [Engineering stages](./devops/ENGINEERING_ROADMAP.md) | Перевод готовится | Stage goals, workstreams and exit criteria |
| DevOps detail | [DevOps roadmap](./devops/README.md) | Перевод готовится | Capacity, observability, reliability, security and recovery |
| WebSocket | [WebSocket protocol](./websocket-protocol.md) | Перевод готовится | Proposed v1 contract and current scaffold limitations |
| Observability | [OpenTelemetry](./observability/opentelemetry.md) | Перевод готовится | Tracing configuration and privacy boundaries |
| Pharmacy Edge offline | [Offline capability matrix](./devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md) | [Матрица офлайн-возможностей](./devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.ru.md) | Offline workflow policy and controls |
| Pharmacy Edge | [Ansible rollout](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) | Перевод готовится | Controlled rollout and fleet guardrails |
| Interview material | [Interview index](./interview/README.md) | Перевод готовится | Separate learning and interview preparation material |

## Documentation map

- workflows/: business processes and pharmacy operating model.
- architecture/: system context, component boundaries and repository architecture.
- adr/: durable architectural decisions and their lifecycle.
- ai/: Mortarium operations, LangGraph RAG, evaluation and AI system design.
- guides/: contributor setup, development and testing.
- operations/: incident, production operations and release procedures.
- devops/: engineering roadmap, benchmarks, load tests, observability and Pharmacy Edge operations.
- deployment/: hosting-specific deployment instructions.
- observability/: telemetry configuration and privacy controls.

## Documentation ownership rules

- Document the implemented repository, not historical or hypothetical infrastructure. Python dependencies are declared in pyproject.toml and resolved in uv.lock; frontend dependencies are declared in frontend/shadcn-admin/package.json.
- Keep one canonical procedure for each workflow; link to it rather than copying it into several documents.
- Architectural decisions belong in adr/. Operational procedures belong in operations/. Development procedures belong in guides/. Roadmaps and benchmark plans belong in devops/.
- Label every capability as implemented, proposed, planned or not validated. An Accepted ADR does not prove implementation or production readiness.
- When a command, service, path, API contract or architectural invariant changes, update the canonical document in the same change.
- Never place credentials, real customer/patient data, provider secrets or unredacted logs in documentation.
- Use synthetic examples. Any clinical evaluation threshold requires qualified pharmacy/clinical review.
- Every production runbook must identify its environment, preconditions, owner, verification and rollback/recovery boundary.
