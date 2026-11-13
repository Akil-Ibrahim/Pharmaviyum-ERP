# Repository structure

This document defines the current repository layout and the ownership rules for new files. It is intentionally descriptive: directory moves must be performed separately with all CI, Docker, deployment, tooling, and documentation references updated in the same change.

## Application code

| Path | Responsibility | Rule |
|---|---|---|
| `src/pharmaviyum/` | Python application package: API, domain logic, persistence, integrations, and Mortarium AI | Production Python imports belong here. Do not create a parallel top-level `backend/` package. |
| `frontend/shadcn-admin/` | React, TypeScript, Vite, and shadcn-based admin UI | Frontend dependencies, source, and frontend lockfiles stay with this application. |
| `alembic/` and `alembic.ini` | Database schema migrations | Keep migration history immutable; add revisions through Alembic. |
| `tests/` | Automated backend and cross-layer tests | Organize by test scope/domain; avoid duplicating application code here. |

## Infrastructure and delivery

| Path | Responsibility |
|---|---|
| `.github/workflows/` | CI, security checks, and explicitly controlled deployment workflows |
| `ansible/` | Pharmacy Edge infrastructure automation, inventories, roles, and playbooks |
| `docker/` | Docker-specific assets such as images and container configuration |
| `deploy/` | Deployment-related assets that are not part of the application package |
| `nginx/` | Nginx reverse-proxy configuration for the root Compose topology |
| `docker-compose.yml` | Local/default Compose topology |
| `docker-compose.codespaces.yml` | Codespaces-specific overrides |
| `docker-compose.monitoring.yml` | Monitoring stack |
| `docker-compose.prod.yml` | Production/Edge Compose definition; validate before use and do not assume it is the FastAPI Cloud deployment path |
| `Dockerfile` | Application image build |
| `scripts/start.sh` | Container startup and migration entrypoint |

FastAPI Cloud is a separate production target. Do not treat the root Compose files as its deployment configuration. Do not merge FastAPI Cloud, Pharmacy Edge, local development, and monitoring settings into one ambiguous Compose file.

## Documentation and supporting material

| Path | Responsibility |
|---|---|
| `docs/adr/` | Architecture Decision Records |
| `docs/architecture/` | System architecture and repository conventions |
| `docs/ai/` | Mortarium AI/RAG design and evaluation |
| `docs/deployment/`, `docs/operations/`, `docs/devops/` | Deployment, operational procedures, and engineering operations |
| `docs/guides/`, `docs/workflows/` | Developer and business workflow guidance |
| `assets/` | Images and static assets referenced by documentation/UI |
| `artifacts/` | Small, intentional fixtures or reference artifacts; generated test output belongs in CI artifacts or ignored local directories |

## Root-level configuration

Keep root files only when they are repository-wide entry points or standard tool configuration: `pyproject.toml`, `uv.lock`, `pytest.ini`, `alembic.ini`, `Makefile`, `Dockerfile`, `README.md`, `AGENTS.md`, and shared editor/linter/ignore configuration.

Tool-specific configuration (for example Copilot, Pi, Qwen, or agent skills) may remain in its expected location when that tool is actively supported. Shared engineering rules belong in `AGENTS.md`; avoid copying the same policy into multiple files.

## Rules for future cleanup

1. Do not create a second application root such as `backend/`, `app/`, or a parallel frontend package.
2. Do not add generated coverage, build output, caches, local databases, or secrets to Git.
3. Keep runtime dependencies in the relevant package manifest and lockfile; do not add unpinned ad-hoc installs to helper scripts.
4. Keep operational scripts in `scripts/` until a deliberate subdirectory taxonomy is introduced and every caller is updated.
5. Before removing or moving a file, search workflow YAML, Dockerfiles, Compose files, Ansible, Makefile, package scripts, docs, and other scripts for references.
6. Keep scripts that target distinct deployment topologies separate until those topologies are unified and tested.
7. Do not delete historical evidence, migrations, or operational recovery procedures merely to reduce the file count.
8. Prefer small PRs that include a path/reference audit and CI validation over broad directory moves.
