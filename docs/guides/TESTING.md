# Testing Guide

This guide describes the current test layout and the same quality gates used by the repository CI pipeline.

## Quick start

```bash
# Unit tests
./scripts/test.sh unit

# Integration tests
./scripts/test.sh integration

# Full local suite
./scripts/test.sh all

# Coverage
./scripts/test.sh coverage
```

For a focused test:

```bash
pytest tests/<path_to_test>.py -v
pytest -m unit -v
pytest -m integration -v
```

## Test layout

The repository separates tests by responsibility:

```text
tests/
├── unit/
├── integration/
├── security/
├── architecture/
├── evaluation/
├── conftest.py
└── ...
```

The exact file layout evolves with the implementation. Prefer the filesystem and pytest collection over maintaining a static list of every test module in this document.

## Test categories

The project uses pytest markers where applicable:

```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

Not every test requires an external LLM. RAG, agent, security, and integration tests should be run with the dependencies required by their category.

## Dependencies

The current runtime/test dependency file used by Docker and CI is:

```bash
uv sync --frozen
```

Do **not** use or create the obsolete `requirements-ai.txt` file.

The repository also maintains `pyproject.toml` and `uv.lock`; dependency management is being consolidated toward that toolchain, but the current CI/Docker path still installs `pyproject.toml + uv.lock`.

## Local infrastructure

Integration tests use PostgreSQL and Redis. The development Compose stack provides these services:

```bash
docker compose up -d postgres redis
```

For tests that require the full stack:

```bash
docker compose up -d
```

## RAG tests

RAG tests should cover the production invariants of the current pipeline, especially:

- pharmacy/tenant isolation;
- country and language context;
- retrieval behavior;
- stable `src-{chunk_uuid}` citations;
- generation from retrieved sources;
- guardrails;
- retrieval observability without high-cardinality labels.

Do not write tests that assume a separate Kubernetes RAG deployment; the current architecture is an application-level RAG pipeline.

## Security tests

Security checks are part of CI and include dependency auditing and Bandit. Repository security tests live under `tests/security`.

Keep security fixtures free of real credentials and personal data.

## CI/CD quality gates

The canonical workflow is `.github/workflows/ci.yml`.

The pipeline currently includes:

1. Ruff linting;
2. Black formatting checks;
3. isort checks;
4. mypy type checking;
5. unit tests;
6. integration tests with PostgreSQL/Redis and pgvector where required;
7. uv run pip-audit;
8. Bandit;
9. RAG evaluation / golden-dataset checks;
10. Docker build/publish after the required checks succeed.

The canonical CI workflow is `.github/workflows/ci.yml`; do not document CircleCI or a legacy test workflow as active infrastructure.

## Debugging

Useful commands:

```bash
pytest -v -s tests/<test>.py
pytest --showlocals tests/<test>.py
pytest -x tests/<test>.py
pytest --pdb tests/<test>.py
```

Check service logs when an integration test fails because of infrastructure:

```bash
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f api
```

## Best practices

- Keep unit tests deterministic and isolated from external services.
- Mock LLM/provider calls in unit tests.
- Use integration tests for real database/Redis behavior.
- Prefer fixtures for reusable setup and cleanup.
- Use Arrange → Act → Assert.
- Test security boundaries explicitly, especially tenant isolation.
- Never weaken CI checks to make a failing test pass.
- Update this document when the canonical test commands or CI workflow change.
