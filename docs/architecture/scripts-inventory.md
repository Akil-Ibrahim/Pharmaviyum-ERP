# Script inventory and ownership

This inventory classifies the current top-level `scripts/` directory without moving files. Keep these scripts at their current paths until every caller (CI, Docker, Compose, Ansible, Makefile, docs, and operator runbooks) has been updated in a coordinated change.

Application startup is defined by `tool.fastapi.entrypoint` in `pyproject.toml` for FastAPI Cloud and the explicit Uvicorn `CMD` in the production Dockerfile. Database migrations are a separate release operation; do not add migration execution to web-process startup.

## Application lifecycle

| Script | Responsibility |
|---|---|
| `start.sh` | Container entrypoint: apply Alembic migrations and start Uvicorn |
| `entrypoint.sh` | Legacy/alternate container entrypoint; verify Dockerfile and Compose references before consolidation |
| `start-dev.sh` | Local host development: sync Python and frontend dependencies, start API and Vite |
| `start-docker.sh` | Start the root development Compose stack |
| `dev.sh` | Legacy Compose development launcher; review service assumptions before retiring |
| `stop.sh` | Stop local services |
| `run-main-containers.sh` | Start the core container subset; verify current Compose service names before use |

## Database and operations

| Script | Responsibility |
|---|---|
| `migrate.sh` | Apply schema migrations |
| `test_migrations.sh` | Migration lifecycle test; destructive because it downgrades to base |
| `backup.sh` | Backup path for the `postgres` service in `docker-compose.prod.yml` |
| `backup_db.sh` | Backup path for the `db` service in the default Compose topology |
| `db_reset.py` | Database reset utility; treat as destructive |
| `seed_database.py` | Seed database data |
| `logs.sh` | Follow application/service logs |
| `setup_secrets.sh` | Local secret setup helper; never commit generated secret material |

The two backup scripts target different Compose service names and database layouts. They are not interchangeable; do not consolidate until the production and development backup contracts are explicitly defined and restore-tested. Never run either against production as part of repository cleanup.

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
