# Technology Stack and Version Policy

This page records the versions declared by the repository configuration. It is not a claim that every dependency has been independently tested against every newer release.

## Runtime and framework versions

| Area | Version declared in repository | Source of truth |
|---|---|---|
| Python | `>=3.15,<3.16`; app CI and Docker target the tested Python 3.15.2 patch. FastAPI Cloud can resolve an available 3.15.x patch. Ansible controller CI uses Python 3.14.10 as a separate toolchain supported by ansible-core 2.21 | `pyproject.toml`, `.github/workflows/ci.yml`, `.github/workflows/ansible-quality.yml`, `Dockerfile` |
| FastAPI | `0.162.5` | `pyproject.toml` |
| Uvicorn | `0.54.0` | `pyproject.toml` |
| Pydantic | `2.14.3` | `pyproject.toml` |
| Pydantic Settings | `2.16.2` | `pyproject.toml` |
| SQLAlchemy | `2.1.8` | `pyproject.toml` |
| Alembic | `1.20.1` | `pyproject.toml` |
| asyncpg / psycopg | `0.32.0` / `3.3.9` | `pyproject.toml` |
| PostgreSQL | PostgreSQL 18 with pgvector 0.8.7 in disposable development/CI; managed production database migration remains separate | Docker Compose and CI service definitions |
| Redis server | Redis 8.8.4 in disposable development/CI; production compose remains on Redis 7 pending a separate data migration | Docker Compose and CI service definitions |
| pgvector container extension | `0.8.7` | `pgvector/pgvector:0.8.7-pg18` image tag |
| pgvector Python client | `0.4.1` | `pyproject.toml` |
| LangGraph | `1.2.21` | `pyproject.toml` |
| LangChain | `1.4.0` | `pyproject.toml` |
| Redis Python client | `8.1.0` | `pyproject.toml` |
| Celery | `5.6.3` | `pyproject.toml` |
| OpenTelemetry API / SDK / OTLP exporter | `1.45.2` | `pyproject.toml` |
| OpenTelemetry instrumentation packages | `0.66b2` | `pyproject.toml` |
| Ansible Community Package | `14.6.0` | `ansible/requirements.txt` |
| ansible-core | `2.21.6` | `ansible/requirements.txt` |
| Ansible controller Python | `3.14.10` | `.github/workflows/ansible-quality.yml` |
| uv | `0.13.8` | Dockerfile and GitHub Actions workflows |
| React / React DOM | `^19.3.1` | `frontend/shadcn-admin/package.json` |
| TypeScript | `~6.0.3` | `frontend/shadcn-admin/package.json` |
| Vite | `^8.3.8` | `frontend/shadcn-admin/package.json` |
| Tailwind CSS | `^4.3.5` | `frontend/shadcn-admin/package.json` |
| Bun | `1.4.4` | Dockerfile and GitHub Actions workflows |
| TanStack Query | `^5.103.1` | `frontend/shadcn-admin/package.json` |
| TanStack Router | `^1.170.36` | `frontend/shadcn-admin/package.json` |
| Vitest | `^4.1.11` | `frontend/shadcn-admin/package.json` |

Exact resolved Python versions are recorded in `uv.lock`. Frontend dependency ranges are declared in `frontend/shadcn-admin/package.json`; do not assume a version range means a particular patch release is installed.

## Tooling

- Python dependency and command workflow: `uv`
- Python lint and quality checks: Ruff, Black, isort, mypy, pytest
- Frontend package manager and scripts: Bun
- Frontend quality gates: ESLint, Prettier, TypeScript build, Vitest
- Container build: Docker multi-stage build
- CI: GitHub Actions

Monitoring images: Prometheus `3.16.0`, Grafana `13.3.1`, OpenTelemetry Collector Contrib `0.165.1`, Jaeger `1.76.0` in local Compose. Bun is pinned consistently to `1.4.4` across Docker and CI workflows.

## Dependency update procedure

1. Change Python direct dependencies in `pyproject.toml`.
2. Regenerate and commit `uv.lock`; CI uses `uv sync --frozen`, so a stale lockfile will fail reproducible installation.
3. Change frontend dependencies in `frontend/shadcn-admin/package.json` and regenerate the committed `frontend/shadcn-admin/bun.lock`.
4. Run backend lint, formatting, typing, unit and integration checks; run frontend lint, formatting, production build and tests.
5. Check compatibility notes and security advisories for major-version upgrades.
6. Update this document and the README only after the repository configuration has been updated. Do not describe a planned upgrade as already installed.
7. Open a pull request and review GitHub Actions results before merging.

## Runtime infrastructure notes

- Disposable development/CI Compose targets PostgreSQL 18 with the pgvector 0.8.7 extension image; this does not change the managed Neon production major version or existing pharmacy-edge database volumes.
- The application uses the pgvector Python client and PostgreSQL extension for vector search where enabled; these are separately versioned components.
- Disposable development/CI Compose targets Redis 8.8.4. The production Compose profile remains on Redis 7 until a separately approved migration with backup and rollback. The managed Redis/Valkey production services are not upgraded by the application PR.
- The pharmacy-edge Ansible template uses Valkey; that server profile is intentionally kept separate from the local Redis service.
- Mortarium's LLM provider/model selection is environment-configured. See [AI architecture](./ai_architecture.md) and [FastAPI Cloud deployment](./deployment/FASTAPI_CLOUD.md) for the current deployment profile.

## Documentation rule

When versions change, update the dependency manifests and lockfiles first. Keep README badges, architecture diagrams, setup guides and this page consistent with the actual configuration. Never put secrets, patient information or production credentials in documentation.
