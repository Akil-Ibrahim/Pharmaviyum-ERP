<p align="center">
  <img src="assets/pharmaviyum.png" alt="Pharmaviyum Pharmacy ERP/CRM" width="100%">
</p>

# Pharmaviyum — Pharmacy ERP/CRM

![Demo](https://img.shields.io/badge/Demo-Safe-green) ![NDA](https://img.shields.io/badge/NDA-Yes-blue) ![Python](https://img.shields.io/badge/Python-3.15.2-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.162.5-009688) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue) ![React](https://img.shields.io/badge/React-19.3.1-61DAFB) ![Vite](https://img.shields.io/badge/Vite-8.3.8-646CFF)

> Pharmacy ERP/CRM platform with Mortarium AI for pharmacy operations, workflow, inventory, procurement, POS, and intelligent decision support.

## Overview

**Pharmaviyum** is a pharmacy-focused ERP/CRM platform with an integrated AI layer, **Mortarium**.

The project evolved from a pharmacy CRM with an AI layer into a broader pharmacy ERP/CRM foundation covering operational workflows such as patients, prescriptions, products, POS, procurement, suppliers, receiving, inventory, batches, expiry control, FEFO dispensing, stock transfers, and auditability.

The system is designed around real pharmacy workflows and can complement existing pharmacy ERP environments during gradual adoption rather than requiring an immediate replacement of existing systems.

The canonical integration and release branch is `main`. Changes should be proposed through pull requests and validated by GitHub Actions before merge.

## Core Pharmacy Workflow

Pharmaviyum is organized around connected pharmacy operations:

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

The domain is designed to keep pharmacy business processes connected instead of treating CRM, inventory, procurement, and POS as isolated features.

## Core Capabilities

Pharmaviyum is being developed with a **pilot-first, offline-first** operating model. The initial Edge rollout is limited to 1–10 pharmacy sites; the architecture documents a future path to 100 sites, but that scale is not yet a validated production capacity.

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

Offline operation does not bypass payment-provider authorization, fiscalization, e-prescription verification, or jurisdiction-specific controls. See the offline capability matrix before treating any workflow as available offline.

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

The pharmacist remains the professional decision-maker. AI output is treated as decision support, not as an authoritative replacement for professional judgment.

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
- FastAPI 0.162.0
- Uvicorn
- Pydantic 2.14.0 / Pydantic Settings 2.15.0
- SQLAlchemy 2.0.53
- Alembic
- asyncpg / psycopg
- Ruff / Black / isort / mypy / pytest

### Data & Infrastructure

- PostgreSQL 16
- pgvector 0.4.1
- Valkey-compatible managed cache in the deployment configuration; Redis-compatible services are used by local development and CI
- Docker / Docker Compose
- Celery

### AI / RAG

- LangGraph
- LangChain
- PostgreSQL + pgvector
- MCP JSON-RPC tool/resource layer
- OpenTelemetry
- Configured LLM provider(s)

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

The API supports OpenTelemetry distributed tracing for FastAPI, SQLAlchemy, Redis, and outbound HTTPX requests. Configure an OTLP endpoint with `OTEL_EXPORTER_OTLP_ENDPOINT`; see [`docs/observability/opentelemetry.md`](docs/observability/opentelemetry.md) for deployment, sampling, and data-protection guidance.

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

```text
.
├── src/pharmaviyum/       # Main FastAPI backend
│   ├── api/               # API routes
│   ├── ai/                # Mortarium AI, RAG and MCP
│   ├── core/              # Core application infrastructure
│   ├── domain/            # Domain models and business concepts
│   └── ...
├── frontend/              # React / TypeScript frontend
├── alembic/               # Database migrations
├── scripts/               # Development and operational scripts
├── docs/                  # Architecture, ADRs and engineering guides
├── tests/                 # Automated tests
├── docker-compose.yml     # Local development infrastructure
├── pyproject.toml         # Python project and tooling configuration
├── uv.lock                # Locked Python dependencies
└── README.md              # Project overview
```

## Deployment

The hosted application deployment target is **FastAPI Cloud**. The repository uses a manually triggered GitHub Actions workflow for deployment; see [`docs/deployment/FASTAPI_CLOUD.md`](docs/deployment/FASTAPI_CLOUD.md) for prerequisites, environment variables, database migrations, and known runtime constraints. No deployment is implied by a successful CI run.

## Development

### Prerequisites

- Python 3.15.2 (project constraint: `>=3.15.2,<3.16`)
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

The local development stack provides the backend and supporting infrastructure required for development.

Typical services include:

- PostgreSQL with pgvector
- Redis-compatible cache/state service
- FastAPI API
- Celery background worker
- AI/LLM services where configured

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
