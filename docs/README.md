# Documentation

[English](README.md) · [Русский](README.ru.md)

This directory is the engineering documentation home for Pharmaviyum ERP/CRM. English is canonical for engineering and operations; Russian companions are maintained where useful.

## Start here

| Area | English | Русский | What it covers |
|---|---|---|---|
| Pharmacy workflows | [Workflow specification](./workflows/pharmacy-workflow.en.md) | [Спецификация аптечного процесса](./workflows/pharmacy-workflow.ru.md) | Pharmacy operations, POS, dispensing, inventory, procurement, audit and offline boundaries |
| System architecture | [Architecture vision](./architecture/pharmaviyum-architecture.en.md) · [System context](./architecture/system-context.md) | [Архитектурное видение](./architecture/pharmaviyum-architecture.ru.md) · [Системный контекст](./architecture/system-context.ru.md) | Component boundaries, trust model, data ownership and Central/Edge |
| Technology | [Technology Stack & Glossary](./technology-stack.md) | [Стек и глоссарий](./technology-stack.ru.md) | Technology roles, versions and dependency policy |
| AI / LLM | [AI system design](./ai/AI_LLM_SYSTEM_DESIGN.md) · [Mortarium glossary](./ai/MORTARIUM_AI_ARCHITECTURE.md) | [Проектирование AI](./ai/AI_LLM_SYSTEM_DESIGN.ru.md) · [Архитектура Mortarium](./ai/MORTARIUM_AI_ARCHITECTURE.ru.md) | Mortarium, LangGraph, RAG, MCP, safety and evaluation |
| ADRs | [ADR index](./adr/README.md) · [ADR-0008](./adr/ADR-0008-international-medicine-and-device-reference-catalog.md) | [Индекс ADR](./adr/README.ru.md) · [ADR-0008](./adr/ADR-0008-international-medicine-and-device-reference-catalog.ru.md) | Architecture decisions and lifecycle |
| International catalogue | [Source coverage and import plan](./catalog/INTERNATIONAL_CATALOG_SOURCES.md) | [Источники и план импорта](./catalog/INTERNATIONAL_CATALOG_SOURCES.ru.md) | Official medicine/device sources, provenance, ingestion and rollout |
| Development | [Development and testing](./guides/DEVELOPMENT_AND_TESTING.md) | [Разработка и тестирование](./guides/DEVELOPMENT_AND_TESTING.ru.md) | Contributor workflow and quality gates |
| Operations | [Production operations](./operations/PRODUCTION_OPERATIONS_RUNBOOK.md) | [Эксплуатация Production](./operations/PRODUCTION_OPERATIONS_RUNBOOK.ru.md) | Health, incidents, backup and recovery |
| Deployment | [FastAPI Cloud](./deployment/FASTAPI_CLOUD.md) | [FastAPI Cloud](./deployment/FASTAPI_CLOUD.ru.md) | Hosting, secrets and release procedure |
| Observability | [OpenTelemetry](./observability/opentelemetry.md) | [OpenTelemetry](./observability/opentelemetry.ru.md) | Tracing and privacy boundaries |

## Documentation map

- workflows/: business processes and pharmacy operating model.
- architecture/: system context and component boundaries.
- adr/: durable architecture decisions.
- catalog/: international medicine/device reference sources, provenance and import plan.
- ai/: Mortarium, LangGraph RAG, evaluation and AI system design.
- guides/: contributor setup, development and testing.
- operations/: incident, production operations and release procedures.
- deployment/: hosting-specific procedures.
- observability/: telemetry and privacy controls.

## Documentation ownership rules

- Document the implemented repository, not hypothetical infrastructure.
- Keep one canonical procedure per workflow; link rather than duplicate.
- Architectural decisions belong in adr/; operations in operations/; development guides in guides/.
- Label capabilities implemented, proposed, planned or unvalidated. Accepted ADR does not prove production readiness.
- Update canonical documentation with changes to commands, services, paths, API contracts or architectural invariants.
- Never include credentials, real patient/customer data, provider secrets or unredacted logs.
- Use synthetic examples. Clinical thresholds require qualified review.
- Production runbooks identify environment, preconditions, owner, verification and recovery boundary.
