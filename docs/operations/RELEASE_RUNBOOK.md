# FastAPI Cloud Demo Release Runbook

## Scope

FastAPI Cloud hosts the public Pharmaviyum Demo only. GitHub Actions runs CI and the manually dispatched `.github/workflows/deploy-fastapi-cloud.yml` deploys only the isolated Demo application. Production uses the same application technology stack deployed to the pharmacy server through Ansible. Its implementation/source and release artifacts are private under NDA and are produced by the controlled Production release pipeline. Public Ansible playbooks define the deployment automation contract; real Production inventory, per-site secrets, host access and execution approvals remain operator-controlled and are never committed.

This runbook describes the repository's Demo workflow. It does not claim that a deployment has succeeded or that Production readiness has been verified.

## Demo deployment prerequisites

- A dedicated FastAPI Cloud Demo application is created and linked to this repository.
- The protected GitHub Actions environment demo-pharmaviyum-erp contains FASTAPI_CLOUD_DEMO_TOKEN and FASTAPI_CLOUD_DEMO_APP_ID.
- DEMO_DATABASE_URL points only to the isolated Demo database.
- Demo application environment variables are configured as documented in the [FastAPI Cloud Demo runbook](../deployment/FASTAPI_CLOUD.md).
- PostgreSQL with pgvector and a separate managed Redis endpoint are provisioned for Demo.
- Demo contains synthetic data only.

## Demo release flow

1. Open a pull request targeting main.
2. Review changes and wait for required GitHub Actions checks to pass.
3. Merge only after required checks are green.
4. Manually start Deploy Demo to FastAPI Cloud from main with an approved Demo change reference.
5. Complete the Demo environment approval if configured.
6. Inspect deployment status and logs.
7. Verify /version, /health, /ready, authentication negative-path handling, frontend routes and protected POS access.

A submitted deployment is not necessarily a successful deployment. The workflow must report the exact commit SHA and the staging runtime profile used by the Demo.

## Demo database safety

The public Demo deployment workflow performs read-only schema compatibility checks and does not run Alembic migrations. Demo schema changes require a separate approved operation, backup/restore evidence and post-migration verification. Never use Production database credentials or data for Demo.

## Runtime limitations to verify

- Native FastAPI Cloud deployment does not automatically install the Dockerfile's Tesseract executable and OCR language packs.
- Celery/background jobs require a separate worker process and are not started by the web deployment workflow.
- PostgreSQL/pgvector and Redis-compatible infrastructure are provisioned separately from the web application.
- Verify environment-variable names against active application settings before each Demo release.

## Production boundary

This runbook and its GitHub Actions workflow apply only to the public Demo; they do not deploy, migrate or administer Production. Production application releases are performed through the reviewed Ansible playbooks in this repository. Real Production inventory, host access, per-site credentials, migration approvals and site-specific execution approvals remain restricted under the applicable confidentiality controls. See the [Pharmacy Edge Ansible rollout plan](../devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) and [Ansible guide](../devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md).
