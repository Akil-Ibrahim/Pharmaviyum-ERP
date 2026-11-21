## Production and Demo Infrastructure Baseline

This is the canonical infrastructure version policy for hosted Production and Demo. Do not copy older infrastructure versions or retired provider references from historical notes into new deployments.

| Component | Production baseline | Demo baseline | Evidence / rule |
|---|---|---|---|
| Application hosting | FastAPI Cloud | FastAPI Cloud | The hosted app is deployed through the protected, manually approved workflow. |
| PostgreSQL | Neon PostgreSQL 18, project `pharmaviyum-production`, project ID `odd-fog-77928192`, default branch `production` | Dedicated isolated PostgreSQL 18 database/branch | Production project and major version were verified in Neon on 2026-11-21. Demo database isolation and its live server version must be verified before claiming Demo readiness. |
| Vector extension | pgvector 0.8.7 target, verify installed extension on the hosted database | pgvector 0.8.7 target, verify installed extension | PostgreSQL server version and pgvector extension version are separate. |
| Redis | Managed Redis integration; Redis 8.8.4 is the compatibility target where the provider permits pinning | Dedicated managed Redis integration; same Redis 8.8.4 target | The managed server's exact version is provider-controlled and was not independently verified here. Verify `INFO server`/provider metadata; never report a target as an observed version. |
| Application Redis client | redis-py 8.1.0 | redis-py 8.1.0 | Pinned in `pyproject.toml` and `uv.lock`. |
| Python runtime | CPython 3.15.0 | CPython 3.15.0 | Pinned in `pyproject.toml`, `.python-version`, and deployment checks. |

### Environment separation and data rules

- Production and Demo must use separate database credentials, database instances/branches, Redis credentials/endpoints, signing secrets, and provider/API credentials. Never point Demo at the Production database or Redis namespace.
- Demo is synthetic-data-only. Never import real patients, prescriptions, customer data, pharmacy transactions, or confidential business data.
- Neon Production is the authoritative hosted relational database. Local Compose PostgreSQL is disposable development/CI infrastructure and is not a Production database.
- Managed Redis is an ephemeral cache/coordination layer, not the authoritative sales, dispensing, inventory, or audit ledger. Persistent business records remain in PostgreSQL.
- Keep connection strings and credentials only in FastAPI Cloud environment variables and protected GitHub Actions secrets. Documentation may identify provider, project, branch, and version, but must never contain credentials or connection URLs.
- A version target is not proof of a running service. Confirm the live server version, extension version, connectivity, backup/PITR policy, and readiness for each environment before marking it verified.
- PostgreSQL major-version changes require a separately approved backup, compatibility, migration, restore-test, maintenance-window, and rollback plan. Never attach an existing data volume to a different PostgreSQL major version.
- Do not use retired Render infrastructure as an active Production or Demo dependency.

The live verification record must be updated whenever a hosted database/cache is replaced. See [FastAPI Cloud deployment](deployment/FASTAPI_CLOUD.md) and [Production operations runbook](operations/PRODUCTION_OPERATIONS_RUNBOOK.md).

