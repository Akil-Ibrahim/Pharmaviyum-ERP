# Technology Stack and Version Policy

This page records the versions declared by the repository configuration. It is not a claim that every dependency has been independently tested against every newer release.

## Runtime and framework versions

| Area | Version declared in repository | Source of truth |
|---|---|---|
| Python | `>=3.14.7,<3.15`; CI and Docker use Python 3.14.7 | `pyproject.toml`, `.github/workflows/ci.yml`, `Dockerfile` |
| FastAPI | `0.162.0` | `pyproject.toml` |
| Uvicorn | `0.54.0` | `pyproject.toml` |
| Pydantic | `2.14.0` | `pyproject.toml` |
| Pydantic Settings | `2.15.0` | `pyproject.toml` |
| SQLAlchemy | `2.0.53` | `pyproject.toml` |
| Alembic | `1.20.0` | `pyproject.toml` |
| PostgreSQL | Major version 16 | FastAPI Cloud environment configuration and CI service definitions |
| pgvector | `0.4.1` Python package | `pyproject.toml` |
| LangGraph | `1.2.11` | `pyproject.toml` |
| LangChain | `1.4.0` | `pyproject.toml` |
| Redis Python client | `6.2.0` | `pyproject.toml` |
| Celery | `5.5.3` | `pyproject.toml` |
| React / React DOM | `^19.3.0` | `frontend/shadcn-admin/package.json` |
| TypeScript | `~6.0.3` | `frontend/shadcn-admin/package.json` |
| Vite | `^8.3.0` | `frontend/shadcn-admin/package.json` |
| Tailwind CSS | `^4.3.3` | `frontend/shadcn-admin/package.json` |
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

Workflow files are the authoritative source for the exact CI action versions and CI runtime setup. The workflows currently have more than one Bun setup declaration; keep them aligned when changing the frontend toolchain.

## Dependency update procedure

1. Change Python direct dependencies in `pyproject.toml`.
2. Regenerate and commit `uv.lock`; CI uses `uv sync --frozen`, so a stale lockfile will fail reproducible installation.
3. Change frontend dependencies in `frontend/shadcn-admin/package.json` and update the repository's package-manager lockfile if one is introduced or adopted.
4. Run backend lint, formatting, typing, unit and integration checks; run frontend lint, formatting, production build and tests.
5. Check compatibility notes and security advisories for major-version upgrades.
6. Update this document and the README only after the repository configuration has been updated. Do not describe a planned upgrade as already installed.
7. Open a pull request and review GitHub Actions results before merging.

## Runtime infrastructure notes

- PostgreSQL is configured at major version 16.
- The application uses pgvector for vector search where enabled.
- Development Compose/CI uses Redis-compatible services; the managed deployment uses a Redis-compatible Valkey service. These are deployment profiles, not interchangeable version claims.
- Mortarium's LLM provider/model selection is environment-configured. See [AI architecture](./ai_architecture.md) and [FastAPI Cloud deployment](./deployment/FASTAPI_CLOUD.md) for the current deployment profile.

## Documentation rule

When versions change, update the dependency manifests and lockfiles first. Keep README badges, architecture diagrams, setup guides and this page consistent with the actual configuration. Never put secrets, patient information or production credentials in documentation.
