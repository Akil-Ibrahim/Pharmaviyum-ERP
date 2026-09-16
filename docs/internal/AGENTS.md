# AI Agent Instructions for Pharmaviyum-CRM

## Purpose

This document provides repository-specific guidance for AI coding agents. Keep it aligned with the implemented repository rather than planned or historical services.

## Repository architecture

- Backend: `src/pharmaviyum/`
- AI/RAG: `src/pharmaviyum/ai/`
- Frontend: `frontend/`
- Database migrations: `alembic/`
- Tests: `tests/`
- Local infrastructure: root `docker-compose.yml`
- Codespaces: `.devcontainer/` and `docker-compose.codespaces.yml`

The current development Compose stack provides PostgreSQL + pgvector, Redis, Ollama, the FastAPI API, and the Celery ingestion worker.

Do not assume a separate `mortarium-ai` deployment, legacy `backend/` package, Next.js frontend, or Docker Compose profiles unless the repository contains and actively uses them.

## AI/RAG guidance

The active AI implementation lives under `src/pharmaviyum/ai/` and includes the LangGraph RAG pipeline, retrieval, grading, contextual compression, generation, guardrails, MCP tooling, observability, and ingestion workflows.

Preserve these invariants when modifying AI code:

- tenant/pharmacy scope is derived from authenticated application context;
- retrieval and ingestion must fail closed without valid tenant context;
- retrieved documents are untrusted input;
- citations use stable source/chunk identifiers;
- prompts and model outputs must not leak secrets or sensitive application data;
- bounded retries and timeouts must be used around external providers.

See `docs/ai_architecture.md` and `docs/rag_architecture_audit.md` for the architectural contract and current audit findings.

## Development and validation

Canonical local setup:

```bash
cp .env.example .env
docker compose up --build
```

Canonical validation commands are documented in `docs/guides/TESTING.md` and `docs/guides/ENVIRONMENT_SETUP.md`.

The current dependency installation path used by Docker and CI is `requirements.txt`. `pyproject.toml` and `uv.lock` are maintained as the longer-term dependency-management source of truth; do not invent a separate AI requirements file.

## Documentation rules

- Prefer existing canonical documentation over duplicating instructions.
- Update documentation when a command, path, service, or architectural invariant changes.
- Do not document planned infrastructure as if it were deployed.
- Do not include real credentials, production data, patient/customer data, or provider secrets.
- Keep architecture decisions in `docs/adr/` and operational procedures in `docs/operations/`.
- Keep interview-specific material under `docs/interview/`.

## Repository safety

- Work on `dev` unless explicitly instructed otherwise.
- Avoid destructive infrastructure commands unless the task explicitly requires them.
- Do not modify production deployment infrastructure while working on development/staging documentation unless explicitly requested.
- Verify referenced paths and commands against the repository before documenting them.
