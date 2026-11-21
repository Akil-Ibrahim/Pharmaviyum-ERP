# Pharmaviyum deployment to FastAPI Cloud

This runbook describes the current manually triggered deployment workflow in `.github/workflows/deploy-fastapi-cloud.yml`. It is the hosted-release source of truth; do not infer deployment behavior from older workflow descriptions.

## 1. Release policy

Production deployment is intentionally manual. A push or merge to `main` does not deploy automatically and must not run database migrations as a side effect.

The release path is:

```text
Pull request
  -> required CI, security, frontend, backend, integration and RAG checks
  -> merge to main
  -> manually dispatch Deploy to FastAPI Cloud from main
  -> production environment approval (if configured)
  -> deploy and smoke checks
  -> inspect logs and verify live application
```

The workflow uses the exact commit selected on `main`, verifies successful CI for that same SHA, and serializes production deployments through a concurrency group.

Coding-agent setup and the FastAPI Cloud plugin are documented in [Library Skills and FastAPI agent tooling](../development/library-skills.md). The plugin may help inspect logs or prepare cloud operations, but it must not bypass this repository's manual production workflow, exact-commit CI gate, production checks, or approval controls. Do not deploy Pharmaviyum production directly from an agent session.

## 2. GitHub Actions secrets

Configure the following as repository Actions secrets or secrets on the protected GitHub Actions `production` environment:

- `FASTAPI_CLOUD_TOKEN`: FastAPI Cloud deploy token.
- `FASTAPI_CLOUD_APP_ID`: target FastAPI Cloud application ID.
- `DATABASE_URL`: PostgreSQL URL for the restricted production runtime role, matching the FastAPI Cloud application's `DATABASE_URL`. The deploy workflow uses it for read-only catalog exclusion checks and temporary smoke-user cleanup.
- `MIGRATION_DATABASE_URL`: separate login URL for the production migration workflow only. It must target the same verified Neon host/database, use a different non-superuser role, and inherit the required privileges from `neondb_owner`. Do not configure it in FastAPI Cloud or use it for application traffic.
- `VITE_CLERK_PUBLISHABLE_KEY`: optional build-time public frontend key when required by the current frontend sign-in configuration.

Never put secret values in the repository, workflow inputs, issue comments, or chat. Never echo credentials into CI logs.

**No smoke-test username/password secrets are required.** The workflow creates a unique temporary pharmacist account with a random per-run password using the existing registration endpoint, tests login/profile/catalog access, and attempts to delete only that exact non-superuser account. Do not configure static `PHARMAVIYUM_SMOKE_USERNAME` / `PHARMAVIYUM_SMOKE_PASSWORD` values. Do not use default `admin/admin` credentials.

## 3. FastAPI Cloud application environment

Configure these in the FastAPI Cloud app Environment Variables panel:

| Variable | Requirement / notes |
|---|---|
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `DATABASE_URL` | Production PostgreSQL async URL, normally `postgresql+asyncpg://...` |
| `PGVECTOR_DATABASE_URL` | Reachable PostgreSQL/pgvector URL |
| `REDIS_URL` | Reachable Redis-compatible URL |
| `SECRET_KEY` | Unique random secret, at least 32 characters |
| `CORS_ORIGINS` | Exact trusted HTTPS origin; no wildcard with credentials |
| `USE_CLOUD_LLM` | `true` for the demo AI profile |
| `CLOUD_LLM_PROVIDER` | `qwencloud` |
| `QWEN_API_KEY` | QwenCloud API key, secret |
| `QWEN_BASE_URL` | `https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1` |
| `QWEN_MODEL` | `qwen3.8-flash` |
| `QWEN_FAST_MODEL` | `qwen3.8-flash` |
| `QWEN_COMPLEX_MODEL` | `qwen3.8-flash` |
| `QWEN_FREE_QUOTA_ONLY` | `true`; application fail-closed guard |
| `QWEN_TIMEOUT_SECONDS` | `30` |
| `QWEN_MAX_OUTPUT_TOKENS` | `500` |

The QwenCloud values describe the current demo profile, not an unlimited/free production SLA. Enable the provider-console **Free quota only** switch for the selected model and verify the remaining quota and expiry before enabling requests. The application flag alone does not enforce provider billing. QwenCloud generation and embeddings are separate; configure and verify the embedding provider independently before enabling cloud RAG.

The FastAPI Cloud `DATABASE_URL` and GitHub Actions `DATABASE_URL` must use the same restricted runtime role. The production migration workflow uses the separate `MIGRATION_DATABASE_URL` credential and verifies that it is a distinct role with owner-level migration membership. Keep database and Redis network access restricted to the required application/workflow sources.

## 4. Manual deployment procedure

1. Confirm the target change is merged into `main`.
2. Confirm all required checks passed for the exact `main` commit.
3. Open the [Deploy to FastAPI Cloud workflow](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/actions/workflows/deploy-fastapi-cloud.yml).
4. Select **Run workflow**, select branch `main`, and enter an approved change/ticket reference in `change_reference`.
5. Start the workflow and complete any required approval for the `production` environment.
6. Monitor the workflow. Do not declare success until the deploy and all required verification steps complete successfully.

The workflow:
- checks out the selected commit;
- installs Bun (with a package-manager fallback) and builds `frontend/shadcn-admin`;
- verifies CI succeeded for the exact commit SHA;
- validates the change reference and required deployment secrets;
- injects the immutable `DEPLOY_SHA` into the packaged application as build metadata, submits the deployment with `uv run fastapi cloud deploy . --no-wait`, and requires the live `/version` endpoint to report that exact SHA before running production smoke checks;
- performs a read-only production catalog exclusion check;
- verifies `/health` and `/ready`;
- verifies `/version` reports the exact deployed commit SHA, `production` for API/core, application, and authentication settings, confirms API and authentication debug modes are disabled, and checks the FastAPI Cloud managed runtime is exactly CPython `3.15.0`;
- verifies `/settings/appearance` and `/system-status` return the SPA HTML;
- verifies invalid credentials return HTTP 401 and unauthenticated POS search is protected by HTTP 401;
- creates a temporary pharmacist account, verifies authentication/profile and non-empty Omeprazole catalog/product searches, and attempts to remove the exact temporary account.

The temporary-account smoke test is a production write, not a read-only check. Cleanup is attempted on normal exit and catchable `INT` / `TERM` signals, including when the registration request has an ambiguous outcome. Forced runner termination or host loss can still prevent cleanup. The smoke checks must not create sales, receive stock, or alter inventory. If cleanup fails, the workflow reports failure; inspect the run before retrying and remove only the exact run-scoped temporary account through an approved cleanup procedure.

## 5. Database migrations are separate

**The current deployment workflow does not run Alembic migrations.** It must not be described as a migration workflow.

Schema changes require a separate, explicitly approved operation:

1. Review the migration script and its compatibility/rollback implications.
2. Verify a recent backup and a tested restore path.
3. Obtain production approval for the schema change.
4. Run `uv run alembic upgrade head` once from a trusted environment with the intended production database URL supplied securely.
5. Verify the schema version and application readiness before proceeding with the application release.

Do not run migrations from application startup or concurrently from multiple replicas. Do not use the deployment workflow's catalog-check/smoke-test database access as a reason to run schema changes.

## 6. Post-deployment verification

At minimum, verify:

```bash
curl --fail https://pharmaviyum-erp-crm.fastapicloud.dev/health
curl --fail https://pharmaviyum-erp-crm.fastapicloud.dev/ready
```

Expected readiness response:

- `status`: `ready`
- `checks.database.status`: `healthy`
- `checks.redis.status`: `healthy`

The `/ready` endpoint checks only PostgreSQL and Redis. AI initialization is a startup-critical dependency in the production application lifespan; it is not a field in the `/ready` response. The deployment workflow separately verifies `/version` and the application startup outcome.

Also verify:
- `/version` reports the exact release commit SHA, production environment, and expected Python runtime;
- `/settings/appearance` and `/system-status` serve the built frontend (HTTP 200);
- login and `/api/v1/auth/me` work with an authorized non-privileged test account;
- POS endpoints reject unauthenticated requests;
- Omeprazole returns non-empty results from both the drug-catalog and product search endpoints;
- no excluded catalog entries are active;
- no unexpected sales, stock movements, or inventory mutations occurred.

A green GitHub Actions workflow is necessary but does not prove that all pharmacy business workflows, provider quota, OCR, background workers, or Edge/offline behavior are production-ready.

## 7. Runtime limitations and operational notes

- FastAPI Cloud native deployment uses the Python project configuration; the workflow explicitly builds the React frontend.
- The application pins `requires-python = "==3.15.0"` in `pyproject.toml` and `3.15.0` in the root `.python-version`. CI, Docker, catalog-import workflows and the deployment workflow require exactly CPython 3.15.0. This is the project's standardized interpreter version; do not change the patch version without an approved compatibility review and successful CI/runtime verification. Production is not considered updated until `/version` reports the expected build SHA and CPython 3.15.0, and startup, `/health`, `/ready`, authentication, and POS protection smoke checks pass. The production Neon PostgreSQL major version is not changed by this application upgrade.
- The Dockerfile installs Tesseract and OCR language packs; native FastAPI Cloud does not automatically install those system packages. OCR features requiring the Tesseract executable need a separately validated runtime or external OCR service.
- PostgreSQL/pgvector and Redis are separately provisioned services; deploying the app does not create them.
- Celery worker/Beat processes are not started by the web deployment workflow. Deploy and monitor workers separately where required.
- OpenTelemetry cloud export requires a reachable OTLP collector endpoint; the local Compose Jaeger/collector stack is not automatically present in FastAPI Cloud.
- Keep AI provider outages and quota exhaustion isolated from POS and core ERP transactions.
- The first rollout target is 1–10 pharmacies; capacity up to 100 is an architectural target, not a production capacity claim until validated.

## 8. Troubleshooting

| Symptom | First checks |
|---|---|
| Workflow refuses deployment inputs | Confirm `FASTAPI_CLOUD_TOKEN`, `FASTAPI_CLOUD_APP_ID`, `DATABASE_URL`, and a non-empty change reference exist in the correct Actions/production secret scope |
| Exact-commit CI validation fails | Verify CI completed successfully for the same `main` SHA selected by the workflow |
| `/ready` is not ready | Inspect FastAPI Cloud logs and verify PostgreSQL, Redis, and AI provider configuration/connectivity |
| `/settings/appearance` returns JSON 404 | Inspect frontend build/staging and static-file packaging in the deployed artifact |
| Smoke catalog search returns empty results | Treat as a catalog/data readiness issue; verify import status and search indexing separately—do not fabricate catalog rows or mark the smoke check successful |
| Temporary smoke account cleanup fails | Inspect the exact run ID/attempt and cleanup logs; remove only the generated temporary account after confirming it is non-superuser |
| AI calls fail or quota is exhausted | Verify QwenCloud credentials, model access, provider-console Free quota only setting, quota expiry, and embedding configuration; do not switch silently to a paid fallback |

## 9. Security and change control

- Keep production deployment manual and protected by the GitHub Actions `production` environment.
- Do not bypass CI, branch protection, approvals, or concurrency controls.
- Never use `admin/admin` or static smoke credentials.
- Never expose secrets or patient data in workflow logs, traces, screenshots, or issue comments.
- Do not change production data, schema, or real pharmacy hosts as part of a routine app deployment without a separately approved change.
