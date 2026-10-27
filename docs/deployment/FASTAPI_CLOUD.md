# Pharmaviyum deployment to FastAPI Cloud

This runbook targets the repository `main` branch and the FastAPI Cloud native Python deployment flow. It does not use Render or the repository Dockerfile.

## Deployment flow

The GitHub Actions workflow `.github/workflows/deploy-fastapi-cloud.yml` is manually triggered. It:

1. Installs Bun and builds `frontend/shadcn-admin`.
2. Installs the Python project using `uv`.
3. Runs `uv run fastapi deploy`.

The workflow is intentionally manual so an ordinary push cannot deploy an incompletely configured production app.

## GitHub Actions secrets required

Configure these repository Actions secrets after creating the app in FastAPI Cloud:

- `FASTAPI_CLOUD_TOKEN`: deploy token issued by FastAPI Cloud.
- `FASTAPI_CLOUD_APP_ID`: ID of the target FastAPI Cloud app.

Do not put token values in source files or commit them.

## FastAPI Cloud environment variables

Configure these in the FastAPI Cloud app environment before deploying:

- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `DATABASE_URL`: async SQLAlchemy URL for the new PostgreSQL database, using `postgresql+asyncpg://...`.
- `PGVECTOR_DATABASE_URL`: async PostgreSQL URL for the vector store. It can point to the same database if the schema and permissions are suitable.
- `REDIS_URL`: URL of a reachable Redis-compatible service.
- `API_SECRET_KEY`: a newly generated random secret of at least 32 characters.
- `USE_CLOUD_LLM=true`
- `CLOUD_LLM_PROVIDER=gemini`
- `GEMINI_API_KEY`: Gemini API key, stored as a secret.
- `GEMINI_MODEL=gemini-3.5-flash`
- `GEMINI_FAST_MODEL=gemini-3.5-flash-lite`
- `GEMINI_COMPLEX_MODEL=gemini-2.5-pro`
- `GEMINI_EMBEDDING_MODEL=gemini-embedding-001`
- `GEMINI_EMBEDDING_DIMENSIONS=1024`

Use the exact variable names; the application reads configuration from environment variables. Do not use example/local credentials in production.

## Database preparation

1. Provision a new PostgreSQL database with the pgvector extension available.
2. Set `DATABASE_URL` and `PGVECTOR_DATABASE_URL` in FastAPI Cloud.
3. Apply Alembic migrations once against that database before sending production traffic:
   `uv run alembic upgrade head`
4. Verify `/health` and `/ready` after the database and Redis are reachable.

The deployment workflow does not run migrations automatically, avoiding concurrent or accidental schema changes during deploys. Run migrations from a trusted environment with the production database URL supplied securely.

A new database starts empty. This runbook does not restore any deleted Render database or data.

## Important runtime compatibility notes

- FastAPI Cloud uses the Python project configuration and does not build the Dockerfile's Bun stage. The workflow handles the frontend build explicitly.
- The project currently pins Python to `>=3.14.7,<3.15`. Keep this pin until the dependency set is tested on another version; a package/native-wheel incompatibility may fail the cloud build.
- The Dockerfile installs the Tesseract system executable and OCR language packs. The native FastAPI Cloud deployment does not automatically install those apt packages. OCR paths that invoke Tesseract need a separate compatible runtime or an external OCR service before they can be considered production-ready.
- Redis and PostgreSQL are separate managed services; deploying the FastAPI app does not provision them.
- Celery/background jobs require a separate worker process and are not started by this web deployment workflow.

## First deployment checklist

- [ ] FastAPI Cloud app exists.
- [ ] GitHub Actions secrets are configured.
- [ ] PostgreSQL + pgvector and Redis endpoints are provisioned.
- [ ] Required environment variables are configured securely.
- [ ] Alembic migrations have been applied once.
- [ ] Manually run the `Deploy to FastAPI Cloud` workflow.
- [ ] Confirm the deployment and inspect logs.
- [ ] Check `/health`, `/ready`, and a basic frontend route.
- [ ] Validate authentication, database operations, and AI requests before using real pharmacy data.
