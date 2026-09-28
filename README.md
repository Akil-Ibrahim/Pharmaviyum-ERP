<p align="center">
  <img src="assets/pharmaviyum.png" alt="Pharmaviyum CRM Banner" width="100%">
</p>

# Pharmaviyum CRM

![Demo](https://img.shields.io/badge/Demo-Safe-green) ![NDA](https://img.shields.io/badge/NDA-Yes-blue) ![Python](https://img.shields.io/badge/Python-3.14.7-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-009688) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue) ![React](https://img.shields.io/badge/React-19.3.0-61DAFB) ![Vite](https://img.shields.io/badge/Vite-8.3.1-646CFF)

> Pharmacy ERP/CRM platform with an AI layer — Mortarium — designed to support pharmacy operations, inventory, dispensing, procurement, defectura, suppliers, goods receiving, stock transfers, and AI-assisted pharmacy workflows.

## Overview

Pharmaviyum is a modular pharmacy ERP/CRM platform built around a FastAPI backend, a React 19 frontend, PostgreSQL with pgvector, Redis, and an AI/RAG layer. It is designed around the real operational cycle of a pharmacy network: receiving medicines, registering batches and expiry dates, storing products under defined conditions, managing stock and defectura, reordering from suppliers, transferring stock between locations, and dispensing products.

The system is designed to centralize pharmacy workflows and client interactions without replacing the pharmacy's core ERP. The AI layer provides application-level orchestration, retrieval-augmented generation (RAG), dialogue memory, guardrails, tool access, and observability.

Pharmaviyum is a pharmacy workflow platform with an AI layer, where Mortarium assists the pharmacist by retrieving evidence, interacting with authorized pharmacy tools, and supporting routine work while keeping the final professional decision with the pharmacist.

The repository is currently developed and reviewed through the `dev` branch.

## Demo / NDA Notice

This repository is intended for technical evaluation and architectural review.

- Demo data is synthetic.
- No real client data is included.
- Proprietary production integrations and business logic are not exposed here.
- Access and redistribution are subject to the applicable NDA and author permission.

### Legal Notice

This project and its contents are protected by applicable confidentiality and NDA obligations. The repository must not be copied, redistributed, or used outside the permitted evaluation scope without explicit written permission from the author.

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
                         |  Auth / Tenant / API |
                         +----------+-----------+
                                    |
             +----------------------+----------------------+
             |                      |                      |
             v                      v                      v
      +-------------+        +-------------+        +-------------+
      | PostgreSQL  |        |    Redis    |        |  AI / RAG   |
      | + pgvector  |        | cache/state |        | Agent/MCP    |
      +-------------+        +-------------+        +------+------+ 
                                                             |
                                                     +-------+-------+
                                                     | Ollama / LLM |
                                                     +---------------+

                         Background ingestion
                                  |
                                  v
                           Celery worker
```

The main backend lives under `src/pharmaviyum`. The AI/RAG functionality is integrated into the backend and the development Docker Compose stack runs the API, PostgreSQL/pgvector, Redis, Ollama, and Celery ingestion worker.

## Core Capabilities

- Pharmacy CRM workflows and client-oriented operations
- User, patient, product, order, and audit-oriented domain functionality
- Authentication and tenant/pharmacy context
- FastAPI REST API with OpenAPI documentation
- AI-assisted queries and streaming responses
- Retrieval-augmented generation over application documents
- Tenant-safe document retrieval and source citations
- Dialogue memory, guardrails, caching, and model routing
- MCP tool/resource integration
- Background document ingestion through Celery
- Application metrics and optional distributed tracing

## Technology Stack

### Backend

- Python 3.14.7
- FastAPI 0.141.1
- Uvicorn
- Pydantic 2.13.5 / Pydantic Settings 2.15.0
- SQLAlchemy 2.0.53
- Alembic 1.20.0
- asyncpg 0.30.0 / psycopg 3.3.5
- Uvicorn 0.35.0
- Redis Python client 6.2.0 / Celery 5.5.3
- Ruff / Black / isort / mypy / pytest

### Data & Infrastructure

- PostgreSQL 16
- pgvector
- Redis 7
- Docker / Docker Compose
- Ollama for local LLM execution

### AI / RAG

- LangGraph 1.2.12
- LangGraph PostgreSQL Checkpoint 3.1.2
- LangChain 1.4.2
- LangChain OpenAI 1.6.6
- LangChain Google GenAI 4.4.0
- LangChain Groq 1.1.3
- LangChain Ollama 1.1.0
- Ollama / configured LLM provider
- PostgreSQL + pgvector for vector retrieval
- MCP JSON-RPC tool layer
- OpenTelemetry instrumentation

### Frontend

- React 19.3.0
- React DOM 19.3.0
- TypeScript 6.0.3
- Vite 8.3.1
- TanStack Query 5.103.1
- TanStack Router 1.170.39
- Axios 1.20.0
- Vitest 4.1.11
- Playwright 1.59.1

Dependency source of truth:

- Python: `pyproject.toml` and generated `uv.lock`
- Compatibility installation: `requirements.txt`
- Frontend: `frontend/shadcn-admin/package.json` (Bun lockfile is not currently committed)

## AI / RAG

The AI layer is implemented under `src/pharmaviyum/ai` and exposed through the FastAPI application.

The current RAG pipeline follows this flow:

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
- country and language carried through query context;
- retrieved documents treated as untrusted input before generation;
- stable source identifiers for citations;
- explicit checkpoint/thread scope derived from authenticated context;
- low-cardinality observability labels.

The repository's detailed AI architecture is documented in [`docs/ai_architecture.md`](docs/ai_architecture.md).

## Project Structure

```text
.
├── src/pharmaviyum/       # Main FastAPI backend
│   ├── api/               # API routes
│   ├── ai/                # AI, RAG and MCP
│   ├── core/              # Core application infrastructure
│   ├── domain/            # Domain models and business concepts
│   └── ...
├── frontend/              # React / TypeScript frontend
├── alembic/               # Database migrations
├── scripts/               # Development and operational scripts
├── docs/                  # Architecture, ADRs and engineering guides
├── tests/                 # Automated tests
├── docker-compose.yml     # Main local backend/infrastructure stack
├── pyproject.toml         # Python project and tooling configuration
└── README.md              # Project overview
```

## Development

### Prerequisites

- Python 3.14.7
- Docker and Docker Compose
- Bun 1.4.2
- Node.js 20.19+ or 22.12+ for the Vite 8 toolchain

### Backend

Preferred development workflow uses `uv`:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn src.pharmaviyum.main:app --reload --port 8000
```

For compatibility environments that use pip:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn src.pharmaviyum.main:app --reload --port 8000
```

Local API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Metrics: `http://localhost:8000/metrics`

### Frontend

```bash
cd frontend
bun install
bun run dev
```

Frontend scripts include build, unit tests, E2E tests, linting, and OpenAPI client generation.

## Quality & CI

The project uses automated quality gates for formatting, linting, type checking, security checks, and tests.

Python quality tooling includes:

```bash
ruff check .
black --check .
isort --check-only .
mypy --explicit-package-bases src
pytest
```

The repository's CI is treated as a required engineering gate. Changes should be kept small and focused, dependency upgrades should be validated incrementally, and documentation changes should not be mixed with unrelated implementation fixes.

## Testing

Backend tests use `pytest` with automatic asyncio support:

```bash
uv run pytest
```

Frontend tests:

```bash
cd frontend
bun run test
bun run test:e2e
```

Production-oriented frontend build:

```bash
cd frontend
bun run build
```

## Docker

The primary local Docker Compose stack provides the backend and infrastructure services required for development:

- PostgreSQL 16 with pgvector
- Redis 7
- Ollama
- FastAPI API
- Celery ingestion worker

The React frontend is developed separately from this Compose stack.

Start the backend/infrastructure stack with:

```bash
docker compose up --build
```

For the frontend, use the development commands in the [Frontend](#frontend) section.

## Security & Data Handling

Security is treated as a cross-cutting concern across the application.

- Authentication and authorization are part of the application boundary.
- Tenant/pharmacy isolation is enforced before AI retrieval and generation.
- Retrieved documents are considered untrusted input.
- AI output is not treated as an authoritative source of truth.
- Observability avoids high-cardinality user, session, and tenant identifiers.
- Demo data is synthetic and does not represent real client records.

## Project Status

**Current development branch:** `dev`

The project is under active engineering development. Current work focuses on establishing a clean production-oriented architecture and maintaining CI quality gates across formatting, linting, type checking, tests, security, and deployment tooling.

The repository contains both application code and deployment infrastructure; documentation describes implemented repository behavior rather than unimplemented future infrastructure.

## Documentation

Additional technical documentation is available under `docs/`, including:

- [`docs/README.md`](docs/README.md) — documentation index and ownership rules
- AI/RAG architecture and retrieval audit
- Architecture Decision Records (ADRs)
- Development, testing, and Codespaces guides
- Operations and release runbooks
- DevOps roadmap and engineering stages
- WebSocket protocol documentation
- Senior Python / AI / LLM interview and system-design material

## License / NDA / Contact

This repository is not currently presented as an open-source project. Usage, copying, redistribution, and access are governed by the applicable NDA and explicit permission from the author.

For technical walkthroughs, architectural discussion, or evaluation access, contact the repository owner through the private project channel.

© 2026 Pharmaviyum. All rights reserved.
