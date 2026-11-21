# Full-Stack Upgrade — November 2026

## Scope

This record describes the repository's current application and hosted data-service baseline. It is not evidence that a deployment or database migration has completed. Production deployment remains a separately approved operation.

## Hosted data-service baseline

- Hosted Production relational database: Neon PostgreSQL 18, project `pharmaviyum-production` (`odd-fog-77928192`), default branch `production`; verified from Neon project metadata on 2026-11-21.
- Demo must use a separate PostgreSQL 18 database/branch and separate credentials. Its live provider version and isolation must be verified before Demo is marked ready.
- Hosted Production and Demo must use separate managed Redis endpoints. Redis 8.8.4 is the compatibility target; the provider-reported server version is not pinned by the application and must be verified for each environment.
- Local disposable development/CI services use PostgreSQL 18 with pgvector 0.8.7 and Redis 8.8.4.
- The application Redis client is redis-py 8.1.0, pinned in `pyproject.toml` and `uv.lock`.

The full environment contract, isolation requirements, and verification rules are maintained in [Production and Demo Infrastructure Baseline](PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.md) and its [Russian version](PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.ru.md).

## Application runtime and framework versions

- CPython 3.15.0 for the application, CI, Docker, and FastAPI Cloud runtime target.
- FastAPI 0.164.0; Uvicorn 0.54.0; Pydantic 2.14.3; SQLAlchemy 2.1.8; Alembic 1.20.1.
- Celery 5.6.3 and redis-py 8.1.0.
- LangGraph 1.2.21 and LangChain 1.4.0.
- Ragas 0.4.3 remains isolated in the evaluation dependency group and is not a production runtime dependency.

Exact direct and resolved dependency versions are controlled by `pyproject.toml`, `uv.lock`, frontend package manifests, and the frontend lockfile. Do not infer hosted runtime state from a repository pin; verify the deployed build through `/version`.

## PostgreSQL and vector extension safety

PostgreSQL major-version compatibility is a data-safety boundary. A major-version change requires a separately approved migration plan, verified full backup, extension compatibility checks, a tested dump/restore or supported upgrade procedure, a maintenance window, a restore test, and a documented rollback path. Never attach a data directory created by another major version to a PostgreSQL server.

Verify both components independently:

```sql
SELECT version();
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

## Redis and Celery

Hosted Production and Demo must not share Redis credentials or namespaces. Redis is used for cache/coordination and background-task infrastructure; it is not the source of truth for sales, dispensing, stock, or audit records. POS request handling and permitted local/offline sales must not depend on Redis, Celery, or AI-provider availability. The durable PostgreSQL outbox remains the source of truth for synchronization work.

Confirm the managed Redis server version, TLS/authentication requirements, memory/connection limits, persistence/eviction policy, and provider recovery guarantees before release. Do not run destructive flush or key-cleanup operations as routine maintenance.

## Release and verification gates

1. Review the exact commit and successful CI checks.
2. Confirm Production and Demo use distinct database and Redis endpoints and credentials.
3. Verify PostgreSQL server and pgvector extension versions independently in each environment.
4. Verify the provider-reported Redis server version and connectivity for each environment.
5. Confirm backup/PITR and restore evidence for PostgreSQL.
6. Apply Alembic migrations only through the separately approved migration procedure.
7. Deploy the public Demo through the protected Demo-only FastAPI Cloud workflow and verify the exact build SHA, staging runtime, startup, health, readiness, authentication, and POS protection smoke checks. Production deployment is managed outside this public repository.

A repository change or successful CI run does not by itself prove that a hosted service has been upgraded or is production-ready.
