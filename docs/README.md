# Documentation

This directory is the engineering documentation home for Pharmaviyum ERP/CRM. The English documentation is canonical for engineering and operations; a Russian pharmacy workflow companion is maintained where useful.

## Start here

| Area | Canonical entry | What it covers |
|---|---|---|
| Pharmacy workflows | [Workflow index](./workflows/README.md) | Pharmacy operations, POS, dispensing, inventory, procurement, audit and offline boundaries |
| System architecture | [System context](./architecture/system-context.md) | Component boundaries, trust model, data ownership and Central/Edge target |
| Technology | [Technology stack](./technology-stack.md) | Runtime versions, dependency sources of truth and upgrade policy |
| AI / LLM system design | [AI system design](./ai/AI_LLM_SYSTEM_DESIGN.md) | Mortarium lifecycle, Agent Harness, LangGraph, RAG, MCP, safety, evaluation and observability |
| AI architecture | [AI architecture](./ai_architecture.md) | Current implementation details |
| LangGraph RAG | [RAG graph architecture](./ai/langgraph-rag-architecture.md) | Graph nodes, state, retrieval, bounded execution and persistence |
| RAG audit | [RAG architecture audit](./rag_architecture_audit.md) | Dated findings, gaps and remediation priorities |
| Pharmaceutical evaluation | [Ragas evaluation](./ai/ragas-pharmaceutical-evaluation.md) | Offline evaluator and pharmacy-specific quality metrics |
| LLM standards | [LLM engineering standards](./llm_engineering_standards.md) | Context, token budgets, model routing, cache, memory and MCP standards |
| ADRs | [ADR index](./adr/README.md) | Accepted and proposed architecture decisions |
| Development | [Development and testing handbook](./guides/DEVELOPMENT_AND_TESTING.md) | Contributor workflow and quality gates |
| Environment | [Environment setup](./guides/ENVIRONMENT_SETUP.md) | Local services, configuration and prerequisites |
| Testing | [Testing guide](./guides/TESTING.md) | Test layout, markers and CI gates |
| Operations | [Production operations runbook](./operations/PRODUCTION_OPERATIONS_RUNBOOK.md) | Health checks, incident triage, backup and recovery |
| Release | [Release runbook](./operations/RELEASE_RUNBOOK.md) | Controlled release and rollback |
| Hosted deployment | [FastAPI Cloud](./deployment/FASTAPI_CLOUD.md) | Hosting, secrets, runtime constraints and manual deployment |
| DevOps roadmap | [Engineering stages](./devops/ENGINEERING_ROADMAP.md) | Stage goals, workstreams and exit criteria |
| DevOps detail | [DevOps roadmap](./devops/README.md) | Capacity, observability, reliability, security and recovery |
| WebSocket | [WebSocket protocol](./websocket-protocol.md) | Proposed v1 contract and current scaffold limitations |
| Observability | [OpenTelemetry](./observability/opentelemetry.md) | Tracing configuration and privacy boundaries |
| Pharmacy Edge | [Ansible rollout](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) | Controlled rollout and fleet guardrails |
| Interview material | [Interview index](./interview/README.md) | Separate learning and interview preparation material |

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
