<p align="center">
  <img src="assets/pharmaviyum.png" alt="Pharmaviyum Pharmacy ERP/CRM" width="100%">
</p>

# Pharmaviyum — Pharmacy ERP/CRM

![Demo](https://img.shields.io/badge/Demo-Safe-green) ![NDA](https://img.shields.io/badge/NDA-Yes-blue) ![Python](https://img.shields.io/badge/Python-3.15.2-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.162.5-009688) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-dev%2FCI-blue) ![React](https://img.shields.io/badge/React-19.3.1-61DAFB) ![Vite](https://img.shields.io/badge/Vite-8.3.8-646CFF)

> An integrated pharmacy ERP/CRM foundation for pharmacy operations, dispensing, point of sale, inventory, procurement, and AI-assisted decision support.

## Overview

**Pharmaviyum** is a pharmacy-focused ERP/CRM platform with an integrated AI layer, **Mortarium**.

The platform brings connected workflows for patients, prescriptions, product reference, POS, dispensing, procurement, suppliers, goods receiving, inventory, batches, expiry control, FEFO handling, stock transfers, and audit trails into one application architecture.

Its pilot-first approach is intended to support gradual adoption alongside existing pharmacy systems, rather than requiring an immediate replacement.

The canonical integration branch is `main`. Changes are reviewed through pull requests and validated by GitHub Actions before merge. Production deployment is a separate, manually approved release process.

## At a Glance

- **Application:** FastAPI backend with a React, TypeScript, and Vite frontend.
- **Pharmacy domain:** POS, dispensing, product reference, inventory, procurement, and pharmacy operations.
- **AI layer:** Mortarium, with LangGraph-based RAG and MCP integration.
- **Infrastructure:** PostgreSQL, Redis-compatible services, Docker, and Pharmacy Edge automation.
- **Delivery:** GitHub Actions CI with a separately controlled FastAPI Cloud deployment workflow.

## Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Core Pharmacy Workflow](#core-pharmacy-workflow)
- [Core Capabilities](#core-capabilities)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [RAG Evaluation & Quality](#rag-evaluation--quality)
- [Observability](#observability)
- [AI / RAG Architecture](#ai--rag-architecture)
- [Pharmacy Edge Automation](#pharmacy-edge-automation-ansible)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Development](#development)
- [Quality & CI](#quality--ci)
- [Testing](#testing)
- [Docker](#docker)
- [Security & Data Handling](#security--data-handling)
- [Project Status](#project-status)
- [Documentation](#documentation)
- [Demo / NDA Notice](#demo--nda-notice)
- [License / NDA / Contact](#license--nda--contact)

## Repository Structure

The repository follows clearly defined architectural boundaries and directory ownership rules to keep the codebase consistent, maintainable, and easy to navigate.

The **[Repository Structure Guide](docs/architecture/repository-structure.md)** is the source of truth for:

- Directory responsibilities and ownership.
- Where application code, infrastructure, tests, and documentation belong.
- Rules for adding new files and organizing new components.
- Safe procedures for moving, renaming, or removing existing files.
- Repository-wide conventions for keeping tooling and deployment references in sync.

Review this guide before introducing new directories or changing the location of existing files. Any structural change must update affected imports, CI workflows, Docker and Compose definitions, deployment assets, scripts, and documentation in the same change.

## Core Pharmacy Workflow

The workflow connects the pharmacy's clinical, commercial, and inventory operations. A typical domain flow is:

```text
Patients / Prescriptions
        |
        v
Products / Drug Reference
        |
        v
POS / Orders / Dispensing
        |
        v
Inventory / Batches / FEFO
        |
        +------------------+
        |                  |
        v                  v
Procurement          Stock Transfers
        |                  |
        v                  v
Suppliers / Receiving  Pharmacy Network
        |
        v
Expiry / Quarantine / Audit
```

These are connected domain workflows: a sale or dispensing event affects stock and traceability, while procurement and receiving replenish inventory through auditable transactions.

## Core Capabilities

Pharmaviyum follows a **pilot-first, offline-capable** operating model. The documented initial Pharmacy Edge rollout is limited to 1–10 sites. A 100-site fleet is a future architecture objective, not a validated production capacity.

### Pharmacy Operations

- Patient and customer workflows
- Prescription and dispensing workflows
- POS and order processing
- Patient purchase history
- Pharmacy and tenant context
- Audit logging and transaction traceability

### Pharmacy Edge & Offline Operations

- Pharmacy-local Edge deployment for site-level operational continuity
- Local POS and inventory workflows designed to continue during WAN/Central outages, subject to workflow-specific policy
- Durable outbox-based synchronization with Central when connectivity returns
- Per-pharmacy site identity and credentials
- Explicit separation between supported, restricted, online-only, and validation-blocked offline workflows
- Ansible-based infrastructure automation for controlled Edge host provisioning, deployment, backup, restore drills, and rollback

Offline behavior is policy-controlled, not universal. Local persistence does not make an unavailable payment provider, fiscal authority, e-prescription service, or other external authority available. Consult the [Pharmacy Offline Capability Matrix](docs/devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md) before treating any workflow as available offline.

### Inventory Management

- Product and batch management
- FEFO-aware stock handling
- Inventory transactions
- Expiry monitoring and control
- Expired-stock quarantine
- Storage locations
- Temperature logging
- Stock transfers between pharmacies

### Procurement & Supply

- Suppliers and supplier products
- Purchase orders
- Goods receiving
- Batch-aware inventory receiving
- Defectura / stock replenishment workflows
- Procurement-to-inventory traceability

### Product & Drug Reference

Pharmaviyum separates the international drug reference layer from local pharmacy products.

The intended relationship is:

```text
Drug Reference / INN / ATC
            |
            v
     Medicinal Products
            |
            v
     Local Products
            |
            v
      Batches / FEFO / POS
```

Searching by an active ingredient or INN, such as **Omeprazole**, can provide a reference product and related generic products without mixing the reference/original and generic concepts into a single product record.

### Mortarium AI

**Mortarium** is the AI layer of Pharmaviyum.

It is designed to work with authorized pharmacy application context rather than functioning as a generic chatbot.

Current architectural areas include:

- Retrieval-Augmented Generation (RAG)
- Pharmacy-scoped retrieval
- Source-aware answers and citations
- Dialogue and conversation context
- Guardrails and validation
- MCP tools and resources
- LangGraph orchestration
- AI-assisted analytics and forecasting
- Application observability (OpenTelemetry traces + Prometheus metrics)
- Access-controlled AI workflows
- Offline RAG evaluation with Ragas plus pharmaceutical-specific checks for citation support, medication entities, negation, patient-context isolation, and Russian/English retrieval

The pharmacist remains the professional decision-maker. Mortarium provides decision support; it does not authorize dispensing, replace professional judgment, or serve as an independent clinical authority.

## Architecture

```text
                         +----------------------+
                         |   React 19 Frontend  |
                         | TypeScript / Vite 8  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |     FastAPI API      |
                         | Auth / Tenant / API |
                         +----------+-----------+
                                    |
             +----------------------+----------------------+
             |                      |                      |
             v                      v                      v
      +-------------+        +-------------+        +-------------+
      | PostgreSQL  |        | Valkey/Redis |       | Mortarium   |
      | + pgvector  |        | cache/state |        | AI / RAG    |
      +-------------+        +-------------+        +------+------+
                                                           |
                                                  +--------+--------+
                                                  | LLM / AI Tools  |
                                                  +-----------------+

                         Background processing
                                  |
                                  v
                           Celery worker
```

The main backend lives under `src/pharmaviyum`.

The application combines a FastAPI backend, PostgreSQL/pgvector, Redis-compatible caching/state infrastructure, a React frontend, background processing, and the Mortarium AI/RAG layer.

## Technology Stack

### Backend

- Python 3.15.2
- FastAPI 0.162.5
- Uvicorn
- Pydantic 2.14.3 / Pydantic Settings 2.16.2
- SQLAlchemy 2.1.8
- Alembic
- asyncpg 0.32.0 / psycopg 3.3.9
- Redis Python client 8.1.0
- Ruff / Black / isort / mypy / pytest

### Data & Infrastructure

- PostgreSQL 18 with pgvector 0.8.7 for disposable development/CI environments; the managed production PostgreSQL version is unchanged by this setup and requires a separately approved migration to upgrade.
- Redis 8.8.4 for disposable development/CI environments; the production Compose profile remains on Redis 7 pending a separately approved migration.
- Valkey for the Pharmacy Edge Ansible deployment profile; it remains distinct from the local Redis service.
- Docker / Docker Compose
- uv 0.13.8 / Bun 1.4.4
- Celery 5.6.3

### AI / RAG

- LangGraph 1.2.21
- LangChain
- PostgreSQL + pgvector
- MCP JSON-RPC tool/resource layer
- OpenTelemetry
- QwenCloud for the current demo profile

### Frontend

- React 19.3
- TypeScript 6.0.x
- Vite 8.x
- TanStack Query
- TanStack Router
- Axios
- Vitest
- Playwright

### Dependency Source of Truth

Python dependency definitions are maintained in:

- `pyproject.toml`
- `uv.lock`

The lockfile is used for reproducible CI/development installation. Dependency changes should be made through the project configuration and lockfile rather than maintaining a second authoritative dependency list.

For the exact declared runtime versions and the dependency-upgrade procedure, see [`docs/technology-stack.md`](docs/technology-stack.md).

## RAG Evaluation & Quality

RAG orchestration uses LangGraph. Ragas is isolated to offline evaluation and is not imported into the production request path. Evaluation includes standard Ragas measures (faithfulness, answer relevancy, context precision/recall) and domain-specific regression checks for citation correctness, medication name/strength/form, negation preservation, clinical hallucinations, patient/pharmacy isolation, and Russian/English retrieval. LLM-judge scores are regression signals—not clinical validation or regulatory certification. Evaluation datasets must be synthetic or de-identified.

See [`docs/ai/ragas-pharmaceutical-evaluation.md`](docs/ai/ragas-pharmaceutical-evaluation.md).

## Observability

The application uses the OpenTelemetry SDK for distributed tracing. Automatic FastAPI, SQLAlchemy, and HTTPX instrumentation is disabled by default and requires an explicit development/test opt-in; Redis command auto-instrumentation remains disabled. Configure tracing with `OTEL_ENABLED=true` and `OTEL_EXPORTER_OTLP_ENDPOINT`. See [`docs/observability/opentelemetry.md`](docs/observability/opentelemetry.md) for instrumentation boundaries, sampling, and data-protection requirements.

## AI / RAG Architecture

The AI layer is implemented under `src/pharmaviyum/ai` and exposed through the FastAPI application.

The RAG pipeline follows the general flow:

```text
Query
  -> transform_query
  -> retrieve
  -> grade_documents
  -> compress
  -> generate
  -> guardrails
```

Key design properties include:

- retrieval scoped to the authenticated pharmacy/tenant context;
- patient-specific access controls where applicable;
- country and language carried through query context;
- retrieved documents treated as untrusted input before generation;
- stable source identifiers for citations;
- explicit conversation/checkpoint scope;
- low-cardinality observability labels.

Detailed AI architecture is documented in [`docs/ai_architecture.md`](docs/ai_architecture.md).

## Pharmacy Edge Automation (Ansible)

The repository includes an Ansible operations layer under `ansible/` for controlled Pharmacy Edge infrastructure management. It is separate from application business logic and does not replace the application Sync Engine.

Current repository assets include deployment, migration, backup, restore, rollback, fleet-validation playbooks, reusable roles, a lab inventory, and Ansible CI quality checks. The operating guardrails are:

- Active rollout limit: **10 pharmacy sites**, with serial/fail-fast deployment.
- Future architecture objective: **up to 100 sites**; this is not a claim of completed fleet validation.
- Unique pharmacy/site identity and per-site credentials; secrets belong in an approved secret manager or encrypted runtime variables.
- Immutable application image references and pinned infrastructure package versions.
- Database migrations and restore operations require separate review and approval.
- A repository playbook is not proof of a successful real-site deployment; lab and pharmacy acceptance evidence is required.

See [`docs/devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md`](docs/devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md) and [`docs/devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md`](docs/devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md).

## Project Structure

The repository is organized by responsibility, with clear boundaries between application code, frontend, database migrations, infrastructure automation, tests, and documentation.

| Path | Responsibility |
|---|---|
| `src/pharmaviyum/` | FastAPI application, domain logic, integrations, and Mortarium AI |
| `frontend/shadcn-admin/` | React, TypeScript, Vite, and shadcn-based admin interface |
| `alembic/` | Database schema migrations |
| `ansible/` | Pharmacy Edge infrastructure automation |
| `docker/`, `deploy/`, and Compose files | Container and deployment assets |
| `tests/` | Automated backend and cross-layer tests |
| `docs/` | Architecture decisions, engineering guides, and operational runbooks |

For directory ownership, root-level configuration rules, and safe file-movement procedures, use the canonical [Repository Structure Guide](docs/architecture/repository-structure.md).

## Deployment

The hosted application target is **FastAPI Cloud**. Production deployment is intentionally manual: merging to `main` or passing CI does not deploy the application or run production migrations. The release workflow verifies CI for the exact selected commit before deployment. See [`docs/deployment/FASTAPI_CLOUD.md`](docs/deployment/FASTAPI_CLOUD.md) for secrets, environment configuration, release steps, smoke checks, and rollback constraints.

## Development

### Prerequisites

- Python 3.15.2 for development and primary CI; the application supports `>=3.13,<3.16`, and the FastAPI Cloud release workflow pins its uploaded runtime to Python 3.13.
- `uv` for Python dependency installation and execution
- Docker and Docker Compose
- Bun for the frontend toolchain

### Backend

Preferred development workflow uses `uv`:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn src.pharmaviyum.main:app --reload --port 8000
```

Local API documentation:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Metrics: `http://localhost:8000/metrics`

### Frontend

```bash
cd frontend/shadcn-admin
bun install
bun run dev
```

Frontend scripts include build, unit tests, E2E tests, linting, and OpenAPI client generation.

## Quality & CI

GitHub Actions is the primary CI system.

Quality gates cover:

- Ruff
- Black
- isort
- MyPy
- pytest
- security checks
- build and integration verification where applicable

Typical Python checks:

```bash
uv run ruff check .
uv run black --check .
uv run isort --check-only .
uv run mypy --explicit-package-bases src
uv run pytest
```

CI is treated as a required engineering gate. Changes should remain focused, dependency upgrades should be validated incrementally, and documentation changes should not be mixed with unrelated implementation changes.

## Testing

Backend tests:

```bash
uv run pytest
```

Frontend tests:

```bash
cd frontend/shadcn-admin
bun run test
bun run test:e2e
```

Production-oriented frontend build:

```bash
cd frontend/shadcn-admin
bun run build
```

## Docker

The default local development Compose stack uses PostgreSQL 18 with pgvector 0.8.7 and Redis 8.8.4, alongside the application and supporting services. These are disposable development targets—not production upgrades.

Typical services include:

- PostgreSQL 18 with pgvector 0.8.7
- Redis 8.8.4 for cache/state
- FastAPI API
- Celery background worker
- Ollama and local observability services where configured

The separate docker-compose.prod.yml profile remains on PostgreSQL 16 and Redis 7. Managed production databases/caches and Pharmacy Edge PostgreSQL 16/Valkey are separate environments; changing the development Compose images does not migrate or upgrade them.

Start the development stack with:

```bash
docker compose up --build
```

The React frontend can be developed separately using the frontend commands above.

## Security & Data Handling

Security is treated as a cross-cutting concern across the application.

- Authentication and authorization are part of the application boundary.
- Pharmacy/tenant isolation is enforced before protected retrieval and AI operations.
- Patient-specific data is subject to access control and filtering.
- Retrieved documents are considered untrusted input.
- AI output is not treated as an authoritative source of truth.
- Audit and transaction records support operational traceability.
- Observability avoids unnecessary high-cardinality identifiers.
- Demo data is synthetic and does not represent real client records.

## Project Status

**Canonical branch:** `main`

**Current stage:** Pharmacy ERP Foundation + Production Hardening

The project is under active engineering development. Current work focuses on hardening the ERP/POS workflows, establishing the Pharmacy Edge and Central synchronization contract, validating the Ansible rollout for 1–10 sites, and improving Mortarium AI/RAG evaluation. The 100-site fleet is an architecture target only. A successful CI run or application deployment does not, by itself, establish production readiness; live smoke tests, site acceptance, recovery drills, and capacity evidence remain necessary.

The development approach is **pilot-first**: where appropriate, Pharmaviyum can integrate alongside existing pharmacy ERP systems before broader replacement or migration decisions.

## Documentation

Additional technical documentation is available under `docs/`, including:

- [`docs/README.md`](docs/README.md) — documentation index
- [`docs/devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md`](docs/devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md) — Ansible operating guide for Pharmacy Edge
- [`docs/devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md`](docs/devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) — 1–10 rollout guardrails and future 100-site architecture target
- [`docs/devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md`](docs/devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md) — workflow-by-workflow offline policy and limitations
- [`docs/ai/ragas-pharmaceutical-evaluation.md`](docs/ai/ragas-pharmaceutical-evaluation.md) — Ragas and pharmaceutical RAG evaluation contract
- Pharmacy workflow documentation
- AI/RAG architecture
- Architecture Decision Records (ADRs)
- Development and testing guides
- Operations and release runbooks
- DevOps roadmap and engineering stages
- WebSocket protocol documentation
- AI / LLM system-design material

## Demo / NDA Notice

This repository is intended for technical evaluation and architectural review.

- Demo data is synthetic.
- No real client data is included.
- Proprietary production integrations and business logic are not exposed here.
- Access and redistribution are subject to the applicable NDA and author permission.

### Legal Notice

This project and its contents are protected by applicable confidentiality and NDA obligations. The repository must not be copied, redistributed, or used outside the permitted evaluation scope without explicit written permission from the author.

## License / NDA / Contact

This repository is not currently presented as an open-source project. Usage, copying, redistribution, and access are governed by the applicable NDA and explicit permission from the author.

For technical walkthroughs, architectural discussion, or evaluation access, contact the repository owner through the private project channel.

© 2026 Pharmaviyum. All rights reserved.
