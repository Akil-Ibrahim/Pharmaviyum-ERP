# Script inventory and ownership

This inventory classifies the current top-level `scripts/` directory without moving files. Keep scripts at their current paths until every caller (CI, Docker, Compose, Ansible, Makefile, docs, and operator runbooks) has been updated in a coordinated change.

Application startup is defined by `tool.fastapi.entrypoint` in `pyproject.toml` for FastAPI Cloud and the explicit Uvicorn `CMD` in the production Dockerfile. Database migrations are a separate release operation; do not add migration execution to web-process startup.

## Application lifecycle

| Script | Responsibility |
|---|---|
| `start.sh` | Manual API start helper: applies Alembic migrations and starts Uvicorn; the Dockerfile default `CMD` starts Uvicorn directly and does not invoke this helper |
| `start-dev.sh` | Local host development: sync Python and frontend dependencies, start API and Vite |
| `start-docker.sh` | Start the root development Compose stack |
| `dev.sh` | Docker Compose development launcher |
| `stop.sh` | Stop local services |
| `run-main-containers.sh` | Start the core container subset defined in the root Compose file |

Unreferenced historical entrypoint scripts were removed after checking the Dockerfile, root/Codespaces/production Compose definitions, Ansible backend Compose definition, and repository code search. The removed scripts were not wired into the current runtime; two also swallowed Alembic migration failures, which could allow an application process to start against an unmigrated database. Runtime startup and migration ownership must remain explicit in the active deployment configuration.

## Database and operations

| Script | Responsibility |
|---|---|
| `migrate.sh` | Apply or inspect schema migrations |
| `test_migrations.sh` | Migration lifecycle test; destructive because it downgrades to base |
| `backup.sh` | Legacy backup helper using `docker-compose -f docker-compose.prod.yml`; requires `DB_USER` and `DB_NAME` in the calling shell |
| `backup_db.sh` | Backup helper that runs implicit `docker compose exec db`; it does not select the Ansible backend Compose file itself |
| `db_reset.py` | Database reset utility; treat as destructive |
| `seed_database.py` | Seed database data |
| `logs.sh` | Follow application/service logs |
| `setup_secrets.sh` | Local secret setup helper; never commit generated secret material |

The two backup scripts have different and currently fragile invocation contracts. `backup.sh` uses the legacy `docker-compose` v1 command, relies on caller-exported `DB_USER`/`DB_NAME`, and does not enable `pipefail`, so a failed `pg_dump` can be obscured by a successful `gzip`. `backup_db.sh` assumes the current Compose project exposes a service named `db`; the root `docker-compose.yml` exposes `postgres`, and the script does not pass `-f ansible/roles/app-backend/files/docker-compose-backend.yml`. Do not assume either script is safe or runnable from the repository root. Before operational use, define the intended host/project/env-file contract, add failure-safe pipeline handling, and test both backup and restore against a disposable database. Never run either against production as part of repository cleanup.

## Identity and tests

| Script | Responsibility |
|---|---|
| `create_admin.py` | Bootstrap configured administrator using Passlib bcrypt context |
| `create_admin_bcrypt.py` | Compatibility bootstrap using direct bcrypt API; review dependency/runtime behavior before consolidating |
| `test.sh` | Canonical pytest entrypoint (unit, integration, all, coverage) |
| `test-integration.sh` | Legacy live-service smoke test for local API, frontend, and database |
| `test_auth.sh` | Live authentication endpoint smoke test; creates test user data |
| `test_migrations.sh` | Destructive schema migration test; use only against a disposable database |

## AI, catalog, and developer tooling

| Area | Scripts |
|---|---|
| Drug catalog ingestion | `import_ema_catalog.py`, `import_health_canada_dpd.py`, `import_rxnorm_catalog.py` |
| RAG evaluation/maintenance | `evaluate_rag_retrieval.py`, `rag_rebuild.py`, `rag_retrieval_eval_expansion.py` |
| API client | `generate-api-client.sh` |
| Environment/tool setup | `setup-env.sh`, `setup_testing.sh`, `setup-ollama.sh` |
| Compatibility/diagnostics | `check_python315_compat.py`, `ci_diagnostics.py` |
| Load testing | `run_stage1_load_test.sh` |
| Telegram helpers | `telegram.sh`, `telegram_logs.sh`, `telegram_monitor.sh` |

## Rules

1. Keep `scripts/test.sh` as the single canonical pytest runner; do not add another wrapper for the same test modes.
2. Keep data-import and RAG maintenance commands separate: they have different inputs, operational risks, and owners.
3. Treat database reset, migration downgrade, user bootstrap, backup, and catalog import scripts as operational tools, not harmless developer shortcuts.
4. Before removing a script, search for its exact path in GitHub Actions, Dockerfiles, Compose, Ansible, Makefile, docs, and shell scripts. Then verify no runtime references remain.
5. When the repository adopts a subdirectory taxonomy, move files with `git mv` in one PR and update every caller in the same commit.
