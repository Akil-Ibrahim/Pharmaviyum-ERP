# Full-Stack Upgrade — November 2026

## Scope

This change set upgrades the application build and test stack. It does not deploy to FastAPI Cloud, modify Neon, change managed Redis, or run migrations against production databases.

## Target versions

- CPython 3.15.2
- FastAPI 0.162.5
- Pydantic 2.14.3 / pydantic-settings 2.16.2
- SQLAlchemy 2.1.8, Alembic 1.20.1
- asyncpg 0.32.0, psycopg 3.3.9
- Celery 5.6.3, redis-py 8.1.0
- LangGraph 1.2.21
- uv 0.13.8
- React 19.3.1, TypeScript 6.0.3, Vite 8.3.8, Tailwind CSS 4.3.5
- PostgreSQL 18 + pgvector 0.8.7 for disposable development and CI databases
- Redis 8.8.4 for disposable development and CI services (redis-py 8.1.0 documents support through Redis 8.8)
- Prometheus 3.16.0, Grafana 13.3.1, OpenTelemetry Collector Contrib 0.165.1, and Jaeger 1.76.0 for local observability

Versions are pinned in the dependency manifests and image tags where practical. The CI lock-generation workflows regenerate uv.lock and frontend/shadcn-admin/bun.lock and run validation.

## Compatibility gates

Python 3.15.2 is the target runtime for this branch. The optional FastEmbed evaluation helper is excluded on Python 3.15 because its ONNX Runtime dependency does not publish a matching CPython 3.15 wheel yet. CI must prove that native extensions, async database drivers, Celery workers, AI dependencies, and the FastAPI application install and execute successfully on CPython 3.15.2 before this branch is merged or deployed.

The Celery release documentation and some dependency classifiers may lag the newest CPython release. TypeScript remains on the latest compatible 6.0 line until the project's typescript-eslint toolchain supports TypeScript 7. A successful resolver run alone is not sufficient: the full unit, integration, worker-import, Docker build, and smoke-test suite must pass.

## PostgreSQL 18 data safety

PostgreSQL 18 changes the official container image data directory layout. The development Compose files use a new named volume, `postgres_data_pg18`, mounted at `/var/lib/postgresql`, with `PGDATA=/var/lib/postgresql/18/docker`. Existing PostgreSQL 16 volumes are deliberately not reused or deleted.

Do not point a PostgreSQL 18 container at a PostgreSQL 16 data directory. A major-version upgrade requires a separately approved migration plan (for example, a tested dump/restore or `pg_upgrade` procedure), a verified full backup, extension compatibility checks, a maintenance window, and a documented rollback path. Verify the installed extension after migration:

```sql
SELECT version();
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

The Ansible controller CI remains on Python 3.14.10 because the current ansible-core support matrix lists controller Python only through 3.14; this is a separate automation toolchain, not the application runtime. The Ansible pharmacy-edge deployment template, the production Compose PostgreSQL 16/Redis 7 data services, and the managed Neon production database are intentionally not upgraded by this change set. The production Compose file keeps its existing database volume and major versions; do not run a major-version change through the current simple deploy script. Their current server versions and storage state must be confirmed, backed up, and migrated separately.

## Redis and Celery

The development and CI Redis service is upgraded independently of managed Redis. The pharmacy-edge Ansible template currently uses Valkey; it is not silently replaced as part of this change.

Celery remains an asynchronous worker layer. POS request handling and local/offline sales must not depend on Celery, Redis availability, or AI-provider availability. The durable PostgreSQL outbox remains the source of truth for synchronization work.

The current application uses one Redis URL for cache operations and Celery broker/result backend. Before enabling this pattern for production workloads, validate memory sizing and eviction behavior: an `allkeys-lru` policy can evict broker keys. Prefer a dedicated broker instance with a no-eviction policy, or otherwise isolate broker and cache workloads with explicit capacity and failure handling.

## Release procedure

1. Wait for lockfile generation and all CI checks on this pull request.
2. Verify migrations against a fresh PostgreSQL 18 + pgvector 0.8.7 database.
3. Verify POS, offline outbox replay, authentication, catalog search, Celery worker/Beat, RAG evaluation, and frontend browser tests.
4. Review FastAPI Cloud runtime support for CPython 3.15.2 and verify the deployment artifact.
5. Plan and approve Neon and pharmacy-edge database upgrades separately, including backups and rollback.
6. Only after explicit production approval, deploy the application and perform the separately approved database migration.

A green CI run does not itself authorize a production deployment or a database major-version upgrade.
