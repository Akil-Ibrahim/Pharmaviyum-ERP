# Render Deployment Runbook

## Scope

`dev` is the staging implementation branch. `main` is production. Render is the deployment platform; GitHub Actions provides CI validation. Production is never deployed from `dev`.

## Staging

- Render service: `pharmaviyum-api`
- Branch: `dev`
- Environment: `staging`
- Health endpoint: `/health`
- Database migrations: `alembic upgrade head`
- Demo seed data: enabled only for staging.

## Production

- Render service: `pharmaviyum-crm`
- Branch: `main`
- Environment: `production`
- Health endpoint: `/health`
- Database migrations: Render `preDeployCommand`
- Demo seed data: disabled.

## Release flow

1. Implement and validate changes on `dev`.
2. Wait for available CI checks to pass.
3. Review the PR from `dev` to `main`.
4. Merge only after required checks are green.
5. Render deploys the production service from `main`.
6. Verify `/health`, application logs, database migrations and critical smoke paths.
7. If production is unhealthy, stop promotion and use the Render rollback/redeploy mechanism after identifying the failing revision.

## Database safety

Migrations are forward production changes. Prefer backward-compatible expand/contract migrations. Never rely on an automatic schema downgrade as the primary rollback mechanism.

## Current status

The runbook describes the intended Render architecture. Production readiness is not declared until CI, staging smoke tests, backups/restore, observability and rollback are verified.
