<p align="center">
  <img src="assets/pharmaviyum.png" alt="Pharmaviyum Pharmacy ERP/CRM" width="100%">
</p>

# Pharmaviyum — Pharmacy ERP/CRM

![Demo](https://img.shields.io/badge/Demo-Safe-green) ![NDA](https://img.shields.io/badge/NDA-Yes-blue) ![Python](https://img.shields.io/badge/Python-3.15.0-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.164.0-009688) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-dev%2FCI-blue) ![React](https://img.shields.io/badge/React-19.3.1-61DAFB) ![Vite](https://img.shields.io/badge/Vite-8.3.8-646CFF)

[English](README.md) · [Русский](README.ru.md)

> An integrated pharmacy ERP/CRM foundation for pharmacy operations, dispensing, point of sale, inventory, procurement, and AI-assisted decision support.

## Overview

**Pharmaviyum** is a pharmacy-focused ERP/CRM platform with an integrated AI layer, **Mortarium**.

The platform brings connected workflows for patients, prescriptions, product reference, POS, dispensing, procurement, suppliers, goods receiving, inventory, batches, expiry control, FEFO handling, stock transfers, and audit trails into one application architecture.

Its pilot-first approach is intended to support gradual adoption alongside existing pharmacy systems, rather than requiring an immediate replacement.

The canonical integration branch is `main`. Changes are reviewed through pull requests and validated by GitHub Actions before merge. Public Demo releases are manually dispatched to FastAPI Cloud. Production releases use the reviewed Ansible playbooks to deploy the same application technology stack to the pharmacy server; live host inventory, per-site credentials and execution approvals remain under operator control.

## At a Glance

- **Application:** FastAPI backend with a React, TypeScript, and Vite frontend.
- **Pharmacy domain:** POS, dispensing, product reference, inventory, procurement, and pharmacy operations.
- **AI layer:** Mortarium, with LangGraph-based RAG and MCP integration.
- **Infrastructure:** PostgreSQL, pgvector, and Redis for data and state; Docker for local development and Pharmacy Edge automation.
- **Deployment:** FastAPI Cloud hosts the public Demo only. Production uses the same application technology stack deployed to the pharmacy server through Ansible. Public playbooks and general operating procedures are documented here; real host inventory, per-site credentials, SSH access and live execution approvals remain restricted.

## Demo System Access

Use the demo environment to review the current Pharmaviyum system status:

- **System Status:** https://pharmaviyum-erp.fastapicloud.dev/system-status

**Public Demo credentials (test account only):**

- **Demo login:** `admin`
- **Demo password:** `V9#qL2!mR7@xP4$kT8&nW5zB`

These published credentials are a shared test account for the isolated public Demo only. They are not Production credentials and must never be reused in Production or any other environment. The account's permissions apply only to synthetic Demo data and must not expose any Production resource. The Demo environment must contain synthetic data only; do not store real patient, prescription, customer, or other confidential information in it.

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
- [Project Status & Intellectual Property](#project-status--intellectual-property)

## Repository Structure

The repository follows clearly defined architectural boundaries and directory ownership rules to keep the codebase consistent, maintainable, and easy to navigate.

The **[Repository Structure Guide](docs/architecture/repository-structure.md) · [Русская версия](docs/architecture/repository-structure.ru.md)** is the source of truth for:

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
- Synchronization contracts must define stable event identity, idempotent processing, retry/backoff behavior, and observable handling of poison messages; a dead-letter workflow must not silently discard business events.
- Ordering and conflict handling must be explicit at the aggregate/business-entity level. Concurrent updates to stock, batches, prescriptions, or sales must not be resolved by blind last-write-wins.
- Reconciliation must compare Edge and Central state and surface discrepancies for controlled resolution; replay and recovery procedures must be safe to execute more than once.

**Consistency boundary:** an outbox provides durable publication intent, but does not by itself guarantee exactly-once delivery, conflict-free replication, or globally consistent inventory. The effective guarantee depends on transaction boundaries, idempotent consumers, ordering rules, conflict policy, and reconciliation evidence.

Offline behavior is policy-controlled, not universal. Local persistence does not make an unavailable payment provider, fiscal authority, e-prescription service, or other external authority available. Consult the [Pharmacy Offline Capability Matrix](docs/devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md) · [Русская версия](docs/devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.ru.md) before treating any workflow as available offline.

### POS & Transaction Integrity

POS is a financial and inventory boundary, not merely a checkout screen. The design and implementation must preserve the following invariants:

- A sale, its line items, payment state, and stock movements must have explicit transaction boundaries and auditable relationships.
- Database constraints and domain validation must reject invalid quantities, invalid batch references, and prohibited stock transitions.
- Concurrency control must prevent two simultaneous sales from overselling the same available batch; the chosen locking or reservation strategy must match the transaction model.
- Retries from clients, payment callbacks, and synchronization consumers must be idempotent and must not create duplicate sales, payments, or stock movements.
- Reversals, refunds, voids, and corrections must be represented as traceable compensating operations rather than silent edits to historical transactions.
- Inventory allocation must retain batch/lot traceability and apply FEFO where the product and workflow policy require it.

These are correctness requirements; a successful API response or passing unit test alone is not proof of end-to-end financial or fiscal compliance. External payment and fiscal-authority behavior remains subject to the relevant provider and jurisdiction.

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
- Versioned prompts, model configuration, retrieval configuration, and evaluation datasets so behavior changes can be reviewed and reproduced
- Structured output schemas and validation at tool/API boundaries
- Explicit tool allowlists, scoped credentials, and least-privilege execution for agent actions
- Human review for workflows that require professional authorization or consequential decisions
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

Pharmaviyum is built with the following technology stack, grouped by architectural layer:

- **Backend & API:** Python 3.15, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic, OpenAPI.
- **Data & persistence:** PostgreSQL, pgvector, Redis; Valkey for the separate Pharmacy Edge profile.
- **Background processing:** Celery and Redis-compatible task infrastructure.
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Radix UI, TanStack Query/Router.
- **AI / LLM:** Mortarium AI, LangChain, LangGraph, RAG, embeddings, hybrid search, MCP, Agent Harness, Ragas.
- **Observability:** OpenTelemetry, OTLP, Prometheus, Grafana, Jaeger, OpenTelemetry Collector.
- **Infrastructure & delivery:** Docker, Docker Compose, GitHub Actions, Ansible, uv, Bun; FastAPI Cloud is used for Demo hosting.
- **Testing & security:** Pytest, Playwright, Vitest, Ruff, Black, isort, mypy, Bandit, pip-audit, ESLint, Prettier.
- **Email testing:** Mailpit.

For definitions, each component's role, architecture boundaries, declared versions, environment differences and dependency-update policy, see the complete [Technology Stack & Glossary](docs/technology-stack.md) · [Русская версия](docs/technology-stack.ru.md).

## RAG Evaluation & Quality

RAG orchestration uses LangGraph. Ragas is declared in the `eval` dependency group in `pyproject.toml`, locked in `uv.lock`, and installed explicitly by the CI evaluation job (`uv sync --frozen --group eval`). The production installation excludes this group, so Ragas is not part of the production runtime or request path. Evaluation includes standard Ragas measures (faithfulness, answer relevancy, context precision/recall) and domain-specific regression checks for citation correctness, medication name/strength/form, negation preservation, clinical hallucinations, patient/pharmacy isolation, and Russian/English retrieval. LLM-judge scores are regression signals—not clinical validation or regulatory certification. Evaluation datasets must be synthetic or de-identified.

See [`docs/ai/ragas-pharmaceutical-evaluation.md`](docs/ai/ragas-pharmaceutical-evaluation.md) · [Русская версия](docs/ai/ragas-pharmaceutical-evaluation.ru.md), the [hallucination detection and red-team strategy](docs/ai/hallucination-detection-and-red-team.md) · [Русская версия](docs/ai/hallucination-detection-and-red-team.ru.md), and the [Mortarium chunking pipeline](docs/ai/chunking-pipeline.md) · [Русская версия](docs/ai/chunking-pipeline.ru.md). DeepEval is isolated to evaluation dependencies; HHEM is documented as an optional evaluator; Promptfoo is intended for controlled red-team scans against non-production targets. None is represented as a production response gate until runtime enforcement is implemented and tested. The current chunker supports medical/section-heuristic, sentence-grouping and recursive strategies; parent-child retrieval, table-aware parsing and tokenizer-accurate chunk budgets are documented as target capabilities, not assumed to be complete.

## Observability

The application uses the OpenTelemetry SDK for distributed tracing. Automatic FastAPI, SQLAlchemy, and HTTPX instrumentation is disabled by default and requires an explicit development/test opt-in; Redis command auto-instrumentation remains disabled. Configure tracing with `OTEL_ENABLED=true` and `OTEL_EXPORTER_OTLP_ENDPOINT`. See [`docs/observability/opentelemetry.md`](docs/observability/opentelemetry.md) · [Русская версия](docs/observability/opentelemetry.ru.md) for instrumentation boundaries, sampling, and data-protection requirements.

Observability should correlate traces, application logs, and service/business metrics without placing patient identifiers, credentials, prompts, or other sensitive payloads in telemetry. Operational dashboards and alerts should be tied to measurable SLIs/SLOs (for example API availability/latency, synchronization lag, outbox backlog, failed sync/reconciliation counts, and background-job failures). These are monitoring objectives; do not imply an SLO is active until its target, measurement, alert, and owner are configured.

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

Detailed AI architecture is documented in [`docs/ai_architecture.md`](docs/ai_architecture.md) · [Русская версия](docs/ai_architecture.ru.md).

## Pharmacy Edge Automation (Ansible)

The repository includes an Ansible operations layer under `ansible/` for controlled Pharmacy Edge infrastructure management. It is separate from application business logic and does not replace the application Sync Engine.

Current repository assets include deployment, migration, backup, restore, rollback, fleet-validation playbooks, reusable roles, a lab inventory, and Ansible CI quality checks. The operating guardrails are:

- Active rollout limit: **10 pharmacy sites**, with serial/fail-fast deployment.
- Future architecture objective: **up to 100 sites**; this is not a claim of completed fleet validation.
- Unique pharmacy/site identity and per-site credentials; secrets belong in an approved secret manager or encrypted runtime variables.
- Immutable application image references and pinned infrastructure package versions.
- Database migrations and restore operations require separate review and approval.
- A repository playbook is not proof of a successful real-site deployment; lab and pharmacy acceptance evidence is required.

- See [`docs/devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md`](docs/devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md) · [Русская версия](docs/devops/ANSIBLE_PHARMACY_EDGE_GUIDE.ru.md) and [`docs/devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md`](docs/devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) · [Русская версия](docs/devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.ru.md).

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

For directory ownership, root-level configuration rules, and safe file-movement procedures, use the canonical [Repository Structure Guide](docs/architecture/repository-structure.md) · [Русская версия](docs/architecture/repository-structure.ru.md).

## Production System Status

Open the live Pharmaviyum system status page:

- **System status:** https://pharmaviyum-erp.fastapicloud.dev/system-status
- **Admin login:** `admin`
- **Demo access:** Use the public Demo test account listed above. Production access and credentials are managed separately and are not part of this repository.

## Deployment

The public Demo application is hosted on **FastAPI Cloud**. Production uses the same application technology stack and is deployed to the pharmacy server through **Ansible**. Real Production host details, inventory and credentials remain private and are never committed. See the [deployment boundary](docs/deployment/PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.md) and [Pharmacy Edge Ansible rollout plan](docs/devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md).

## Development

### Prerequisites

- CPython 3.15.0 (exact project pin in `pyproject.toml` and `.python-version`)
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

Local Compose is disposable and must not be treated as the hosted data plane. Pharmacy Edge is a separately governed deployment profile.

Start the development stack with:

```bash
docker compose up --build
```

The React frontend can be developed separately using the frontend commands above.

## Security & Data Handling

Security is treated as a cross-cutting concern across the application.

- Authentication and authorization are part of the application boundary; authorization should follow RBAC/least-privilege principles and be checked server-side for every protected operation.
- Pharmacy/tenant isolation is enforced before protected retrieval and AI operations.
- Patient-specific data is subject to access control and filtering.
- Retrieved documents are considered untrusted input.
- AI output is not treated as an authoritative source of truth.
- Audit and transaction records support operational traceability.
- Observability avoids unnecessary high-cardinality identifiers.
- Secrets must be supplied through managed secret/configuration mechanisms and must never be committed to source control or exposed in logs.
- Data in transit and at rest must use the protections provided by the deployment and storage layers; key ownership, rotation, and backup access require operational controls.
- Audit events should record actor, tenant/site scope, action, target, timestamp, and outcome without copying unnecessary patient or credential data.
- Data retention, deletion, backup, and restore policies must be defined for each data class and deployment boundary.
- Security controls require negative tests for cross-tenant access, patient-context leakage, privilege escalation, and unauthorized tool invocation.
- Demo data is synthetic and does not represent real client records.

## Project Status

**Canonical branch:** `main`

**Current stage:** Pharmacy ERP Foundation + Production Hardening

The project is under active engineering development. Current work focuses on hardening the ERP/POS workflows, establishing the Pharmacy Edge and Central synchronization contract, validating the Ansible rollout for 1–10 sites, and improving Mortarium AI/RAG evaluation. The 100-site fleet is an architecture target only. A successful CI run or application deployment does not, by itself, establish production readiness; live smoke tests, site acceptance, recovery drills, and capacity evidence remain necessary.

The development approach is **pilot-first**: where appropriate, Pharmaviyum can integrate alongside existing pharmacy ERP systems before broader replacement or migration decisions.

## Documentation

Browse the documentation in your preferred language. Repository-wide documentation rules, evidence labels and the Demo/Production boundary are defined in [Documentation Governance](docs/DOCUMENTATION_GOVERNANCE.md):

- **English:** [Engineering documentation index](docs/README.md)
- **Русский:** [Индекс инженерной документации](docs/README.ru.md)

| Topic | English | Русский |
|---|---|---|
| Technology stack | [Technology Stack & Glossary](docs/technology-stack.md) | [Технологический стек и глоссарий](docs/technology-stack.ru.md) |
| Repository structure | [Repository Structure Guide](docs/architecture/repository-structure.md) | [Руководство по структуре репозитория](docs/architecture/repository-structure.ru.md) |
| Offline operations | [Pharmacy Offline Capability Matrix](docs/devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md) | [Матрица офлайн-возможностей](docs/devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.ru.md) |
| RAG evaluation | [Ragas pharmaceutical evaluation](docs/ai/ragas-pharmaceutical-evaluation.md) | [Фармацевтическая оценка RAG](docs/ai/ragas-pharmaceutical-evaluation.ru.md) |
| AI safety | [Hallucination detection & red-team](docs/ai/hallucination-detection-and-red-team.md) | [Выявление галлюцинаций и red-team](docs/ai/hallucination-detection-and-red-team.ru.md) |
| Chunking | [Mortarium chunking pipeline](docs/ai/chunking-pipeline.md) | [Pipeline чанкинга Mortarium](docs/ai/chunking-pipeline.ru.md) |
| Pharmacy workflow | [Pharmacy workflow specification](docs/workflows/pharmacy-workflow.en.md) | [Спецификация аптечного процесса](docs/workflows/pharmacy-workflow.ru.md) |
| System architecture | [Architecture vision](docs/architecture/pharmaviyum-architecture.en.md) | [Архитектурное видение](docs/architecture/pharmaviyum-architecture.ru.md) |
| Architecture decisions | [ADR index](docs/adr/README.md) | [Индекс архитектурных решений](docs/adr/README.ru.md) |

Russian translations are maintained for selected documents rather than every file. The [Russian documentation index](docs/README.ru.md) lists the available translations; where an EN/RU pair exists, both versions are kept aligned.

## Project Status & Intellectual Property

**Pharmaviyum — Public Demo Version**

This repository contains a demonstration version of Pharmaviyum, showcasing its software architecture, pharmacy workflows, engineering practices, and AI capabilities.

- Intended for technical evaluation and portfolio demonstration.
- Uses synthetic demonstration data.
- May differ from the production implementation.

**Production Version**

The production implementation is maintained separately and is not included in this repository. Access to the Production version, its proprietary source code, business logic, and confidential materials is restricted under applicable NDAs and confidentiality agreements.

**Copyright & Intellectual Property**

© 2026 Pharmaviyum. All rights reserved.

Both Demo and Production versions of Pharmaviyum, including their original source code, architecture, documentation, and related materials, are protected by applicable copyright and intellectual property laws.

Public access to the Demo repository does not grant permission to reproduce, redistribute, modify, or commercially use its contents without explicit authorization. No license is granted unless expressly stated.

**Disclaimer:** The Demo version is provided for technical evaluation and portfolio demonstration purposes and does not represent the complete Production system.
