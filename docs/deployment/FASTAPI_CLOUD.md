# Pharmaviyum Demo deployment to FastAPI Cloud

This runbook documents the public Demo deployment only. The workflow at .github/workflows/deploy-fastapi-cloud.yml must never target Production. Production hosting, deployment credentials, release automation, database migrations and operational procedures are maintained outside this public repository.

## 1. Environment boundary

- Public Demo hosting: https://pharmaviyum-erp.fastapicloud.dev.
- Demo uses FastAPI Cloud and isolated Demo PostgreSQL/pgvector and Redis services.
- Demo data must be synthetic. Never connect Demo to Production databases, Redis, identity providers, signing secrets or API credentials.
- The application supports development, staging and production runtime values. The hosted Demo uses ENVIRONMENT=staging to retain staging/production-grade security validation without claiming that it is the Production environment.
- Production uses the same application technology stack, except that it is hosted and deployed on a separately managed platform. Provider details and Production operations are outside this repository.

## 2. Demo deployment workflow

The workflow is manually dispatched from main. It builds the frontend, verifies CI for the exact selected commit, checks the isolated Demo database schema without changing it, deploys to the Demo FastAPI Cloud application, and runs HTTP smoke checks.

The workflow path is:

Pull request -> required CI and security checks -> merge to main -> manually dispatch Deploy Demo to FastAPI Cloud -> Demo environment approval (if configured) -> deploy and Demo smoke checks -> inspect logs and verify the live Demo.

A push or merge does not deploy automatically. This workflow does not deploy Production and does not apply Alembic migrations.

## 3. GitHub Actions secrets

Configure these secrets for the protected GitHub Actions environment demo-pharmaviyum-erp:

- FASTAPI_CLOUD_DEMO_TOKEN — deploy token dedicated to the Demo application.
- FASTAPI_CLOUD_DEMO_APP_ID — FastAPI Cloud application ID for the Demo application only.
- DEMO_DATABASE_URL — connection URL for the isolated Demo database, used for read-only schema compatibility checks.
- VITE_CLERK_PUBLISHABLE_KEY — optional public frontend build key, only if required by the current sign-in configuration.

Do not reuse Production credentials or point any Demo secret at a Production resource. The workflow reads only the Demo-specific GitHub secrets listed above. At deploy time, the Demo token and app ID are mapped to the standard FASTAPI_CLOUD_TOKEN and FASTAPI_CLOUD_APP_ID environment variable names expected by the FastAPI Cloud CLI. For the read-only schema check, DEMO_DATABASE_URL is mapped to the DATABASE_URL process variable. No Production GitHub secret is referenced.

## 4. Demo FastAPI Cloud application configuration

Configure the Demo application Environment Variables separately from Production:

| Variable | Demo requirement |
|---|---|
| ENVIRONMENT | staging (the supported secure runtime profile used by Demo) |
| DEBUG | false |
| LOG_LEVEL | INFO |
| DATABASE_URL | Isolated Demo PostgreSQL async URL |
| PGVECTOR_DATABASE_URL | Demo PostgreSQL/pgvector URL |
| REDIS_URL | Dedicated Demo managed Redis endpoint |
| SECRET_KEY | Unique Demo-only random secret, at least 32 characters |
| CORS_ORIGINS | Exact Demo HTTPS origin |
| USE_CLOUD_LLM | true when the Demo AI profile is enabled |
| CLOUD_LLM_PROVIDER | qwencloud when using the documented Demo profile |
| QwenCloud variables | Demo API key, endpoint, model, timeout and quota guard according to the QwenCloud Demo guide |

The Demo database, vector store and Redis must be provisioned independently. FastAPI Cloud hosting does not provision these services. Verify actual hosted database and extension versions separately; do not treat compatibility targets as observed versions.

## 5. Manual deployment procedure

1. Merge the reviewed change to main after all required CI checks pass.
2. Open the Deploy Demo to FastAPI Cloud workflow in GitHub Actions.
3. Dispatch it from main with an approved Demo change/ticket reference.
4. Complete approval for the demo-pharmaviyum-erp environment if configured.
5. Confirm the workflow completed successfully and verify the live Demo.

The workflow checks out the exact selected commit and embeds its SHA as build metadata; builds the React frontend and stages the static assets; waits for successful CI for that exact main commit; validates the Demo-only deploy token, app ID and database URL; checks the Demo Alembic schema heads and required inventory ledger table using read-only queries; submits the deployment to FastAPI Cloud; waits until /version reports the expected commit, staging for core/application/auth environments, debug disabled and CPython 3.15.0; and checks /health, /ready, frontend SPA routes, invalid-credential handling and protected POS access.

The workflow must fail closed if any required Demo secret is missing or if the live runtime does not match the expected commit and Demo profile.

## 6. Database migrations and data safety

The Demo deployment workflow does not run Alembic migrations. Schema changes require a separately reviewed and approved Demo database operation, a verified backup/restore path and post-migration validation.

Production migrations and Production database operations are not performed by this workflow and are not configured through this public repository. Do not copy Production connection strings, migration credentials or environment variables into Demo.

A successful deployment does not seed a medicine catalog or create pharmacy business data. Use only the documented synthetic-data import and verification procedures.

## 7. Runtime and operational limits

- The workflow pins CPython 3.15.0; verify the deployed /version response rather than assuming the requested version is active.
- Native FastAPI Cloud does not automatically install the system OCR packages from the Dockerfile. Validate OCR separately or use an external OCR service.
- Celery workers/Beat and external OTLP collectors are not started by this web deployment workflow.
- A green CI or deployment run is not evidence that every pharmacy workflow, AI provider quota, OCR process, worker, Edge/offline mode or capacity target is production-ready.

## 8. Security rules

- Keep Demo credentials separate from Production and least-privileged.
- Use synthetic data only; never place patient, prescription, customer or pharmacy transaction data in Demo unless explicitly synthetic.
- Never publish secrets, connection strings or unredacted operational logs.
- Do not bypass branch protection, CI, environment approvals or release gates.
- Never use this workflow to deploy or modify Production.
