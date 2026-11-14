# FastAPI Cloud Release Runbook

## Scope

FastAPI Cloud is the hosted application deployment platform. GitHub Actions runs CI; the dedicated workflow `.github/workflows/deploy-fastapi-cloud.yml` is manually triggered and deploys the application after its required configuration is present. `main` is the canonical integration/release branch.

This runbook describes the repository workflow; it does not claim that a deployment has succeeded or that production readiness has been verified.

## Deployment prerequisites

- FastAPI Cloud application created and linked to this repository/project.
- GitHub Actions secrets configured: `FASTAPI_CLOUD_TOKEN` and `FASTAPI_CLOUD_APP_ID`.
- Required FastAPI Cloud environment variables configured securely; see [FastAPI Cloud deployment](../deployment/FASTAPI_CLOUD.md).
- PostgreSQL with pgvector and a reachable Redis-compatible service provisioned separately.
- Database migrations applied once from a trusted environment before production traffic.
- Frontend build configuration set, including the Clerk publishable key if that sign-in route is enabled.

## Release flow

1. Open a pull request targeting `main`.
2. Review changes and wait for required GitHub Actions checks to pass.
3. Merge only after required checks are green.
4. Start the `Deploy to FastAPI Cloud` workflow manually when a release is intended.
5. Inspect the FastAPI Cloud deployment status and logs; a submitted deployment is not necessarily a successful deployment.
6. Verify `/health`, `/ready`, authentication, database connectivity, critical pharmacy workflows, and AI requests before using real pharmacy data.
7. If the deployment fails, stop promotion, inspect build/runtime logs, and use FastAPI Cloud's supported deployment recovery process after identifying the failing revision.

## Database safety

Migrations are forward production changes. Prefer backward-compatible expand/contract migrations. Never rely on an automatic schema downgrade as the primary rollback mechanism. Keep backups and restore procedures for the separately provisioned database.

## Runtime limitations to verify

- Native FastAPI Cloud deployment does not automatically install the Dockerfile's Tesseract executable and OCR language packs.
- Celery/background jobs require a separate worker process and are not started by the web deployment workflow.
- PostgreSQL/pgvector and Redis-compatible infrastructure are separate from the web application deployment.
- Verify environment-variable names against the active application settings before each release.

## Current status

The repository contains a manually triggered FastAPI Cloud deployment workflow. Production readiness remains unconfirmed until CI, deployment smoke tests, backups/restore, observability, background-worker operation, and recovery procedures have been verified.
