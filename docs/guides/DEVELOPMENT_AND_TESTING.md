# Development and Testing Handbook

This is the practical entry point for contributors. Focused setup and testing documents remain canonical for detailed environment-specific steps.

## Sources of truth
- Python project metadata and dependency constraints: pyproject.toml.
- Resolved Python dependency graph: uv.lock.
- Frontend package manifest: frontend/shadcn-admin/package.json.
- Backend application entry point: src.pharmaviyum.main:app.
- Backend tests: tests/.
- Frontend tests: frontend/shadcn-admin.
- CI workflows: .github/workflows/.

Do not add a second Python dependency manifest or hand-edit the lockfile.

## Local environment
Follow [Environment Setup](./ENVIRONMENT_SETUP.md) for prerequisites, environment variables and local services.

Typical local Docker startup:

    cp .env.example .env
    docker compose up --build

Direct API startup after dependencies and local infrastructure are ready:

    uv sync --frozen
    uv run alembic upgrade head
    uv run uvicorn src.pharmaviyum.main:app --reload --port 8000

Run migrations only against the intended local/test database. Never copy production credentials into a development environment.

## Backend quality gates

    uv run ruff check .
    uv run black --check .
    uv run isort --check-only .
    uv run mypy --explicit-package-bases src
    uv run pytest

For a focused test, pass its path to pytest, for example:

    uv run pytest tests/unit/ai/

Integration tests must use isolated disposable services and must not depend on production data.

## Frontend quality gates

    cd frontend/shadcn-admin
    bun install --frozen-lockfile
    bun run lint
    bun run test
    bun run test:e2e
    bun run build

Use package scripts as the source of truth if script names change.

## AI / RAG evaluation
Ragas is an offline evaluation dependency, not a runtime dependency:

    uv run --with-requirements requirements-eval.txt python -m pytest tests/unit/ai/test_ragas_evaluation.py

See [Ragas Pharmaceutical Evaluation](../ai/ragas-pharmaceutical-evaluation.md) for dataset rules and metric semantics. A passing adapter/unit test does not prove measured clinical quality is acceptable.

## Test pyramid and evidence

| Layer | Purpose | Required evidence |
|---|---|---|
| Unit | Pure logic, validation, serializers and graph helpers | Deterministic assertions |
| API | Authenticated request/response and tenant authorization | Role/tenant fixtures |
| Integration | PostgreSQL, Redis and worker boundaries | Disposable services and cleanup |
| Contract | Frontend/backend, event and MCP schemas | Versioned schema checks |
| E2E | Critical pharmacist workflows | Reproducible browser scenario with synthetic data |
| Load | Throughput, latency and saturation | k6 report and workload assumptions |
| AI evaluation | Retrieval, citations, grounding and pharmaceutical metrics | Versioned report and human adjudication |

Do not infer end-to-end business coverage from an endpoint returning HTTP 200 or a UI screen rendering.

## Pull request checklist
- [ ] Focused scope and linked issue/decision.
- [ ] Authorization and tenant/patient boundaries tested.
- [ ] Database changes backward-compatible or migration plan reviewed.
- [ ] Dependencies justified and lockfile current.
- [ ] Lint, format, types and relevant tests pass.
- [ ] Security and dependency scans pass.
- [ ] Documentation and ADRs updated.
- [ ] No secrets or real patient data included.
- [ ] CI results correspond to the latest PR head SHA.
- [ ] Production deployment and migrations are not triggered unintentionally.

## Related guides
- [Environment setup](./ENVIRONMENT_SETUP.md)
- [Testing guide](./TESTING.md)
- [Codespaces guide](./CODESPACES_GUIDE.md)
- [Technology stack](../technology-stack.md)
- [Release runbook](../operations/RELEASE_RUNBOOK.md)
