# Pharmaviyum deployment to FastAPI Cloud

This runbook targets the repository `main` branch and the FastAPI Cloud native Python deployment flow.

## Deployment flow

The GitHub Actions workflow `.github/workflows/deploy-fastapi-cloud.yml` supports both manual deployment and automatic deployment after a successful `CI/CD Pipeline` run on `main`. It:

1. Checks out the exact commit selected for deployment.
2. Installs Bun and builds `frontend/shadcn-admin`.
3. Verifies that CI succeeded for that exact commit.
4. Installs the Python project using `uv`.
5. Runs `uv run alembic upgrade head` against the production database using the GitHub Actions secret `DATABASE_URL`.
6. Runs `uv run fastapi cloud deploy .` with the FastAPI Cloud deploy token and app ID. The command uses its normal wait/verification behavior; the workflow fails if the command reports a deployment error.

Migrations run once in the release workflow before the app deployment, not in every API replica's startup command. Do not also enable migrations in application startup.

A successful workflow run is necessary but does not replace post-deploy verification of database/Redis readiness and critical pharmacy workflows.

## GitHub Actions secrets required

Configure these repository Actions secrets:

- `FASTAPI_CLOUD_TOKEN`: deploy token issued by FastAPI Cloud.
- `FASTAPI_CLOUD_APP_ID`: ID of the target FastAPI Cloud app.
- `DATABASE_URL`: async SQLAlchemy URL for the production PostgreSQL database, using `postgresql+asyncpg://...`. **This must point to the same production database configured in FastAPI Cloud**, because the workflow applies Alembic migrations through this secret before deploying.
- `VITE_CLERK_PUBLISHABLE_KEY`: Clerk publishable key used at React build time if the Clerk sign-in route is enabled. This is a public frontend key, not a private key, but the workflow reads it from Actions secrets.

Do not put token values, database credentials, or API keys in source files or commit them. Never paste secret values into chat or logs.

## FastAPI Cloud environment variables

Configure these in the FastAPI Cloud app environment before deploying:

- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `CORS_ORIGINS`: the exact HTTPS origin of the deployed frontend (for a same-origin frontend, use the app's origin; do not use `*` with credentials).
- `DATABASE_URL`: async SQLAlchemy URL for the production PostgreSQL database, using `postgresql+asyncpg://...`.
- `PGVECTOR_DATABASE_URL`: async PostgreSQL URL for the vector store. It can point to the same database if the schema and permissions are suitable.
- `REDIS_URL`: URL of a reachable Redis-compatible service.
- `SECRET_KEY`: a newly generated random secret of at least 32 characters. The API accepts this documented name and the legacy `API_SECRET_KEY` alias. Production/staging startup fails if neither is configured.
- `ADMIN_PASSWORD` (optional): an explicit bootstrap-admin password, at least 16 characters. If omitted, the bootstrap login path is disabled; existing users authenticate only against their stored password hashes. Never rely on a default admin password.
- `USE_CLOUD_LLM=true`
- `CLOUD_LLM_PROVIDER=qwencloud`
- `QWEN_API_KEY`: QwenCloud API key, stored only as a FastAPI Cloud secret.
- `QWEN_BASE_URL=https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1`
- `QWEN_MODEL=qwen3.8-flash`
- `QWEN_FAST_MODEL=qwen3.8-flash`
- `QWEN_COMPLEX_MODEL=qwen3.8-flash`
- `QWEN_FREE_QUOTA_ONLY=true`
- `QWEN_TIMEOUT_SECONDS=30`
- `QWEN_MAX_OUTPUT_TOKENS=500`

For the demo, QwenCloud is the sole configured cloud LLM provider. The code uses the OpenAI-compatible ChatOpenAI adapter with automatic retries disabled, a finite timeout, and a bounded output-token target. The application setting `QWEN_FREE_QUOTA_ONLY=true` is required (it defaults to false, so omission blocks Qwen calls) and is a fail-closed configuration guard; it does **not** query QwenCloud quota or override billing policy. In the QwenCloud console, enable the provider's **Free quota only** switch for the selected model. Verify that switch and quota expiry in the console before enabling live requests.

Token usage is emitted through the attached LangChain callback/Prometheus instrumentation. Review the provider console for authoritative quota consumption; local metrics are operational telemetry, not a billing ledger. The existing per-request AI token budget limits prompt/output size, but does not guarantee an exact provider-side daily quota cap.

QwenCloud supplies generation only in this configuration. Embeddings remain independently configured: the current cloud embedding path uses the configured OpenAI embedding credentials/model. Do not assume the Qwen API key provides embeddings. Configure a supported embedding provider separately before enabling cloud RAG ingestion/retrieval.

The provider adapter is selected by `CLOUD_LLM_PROVIDER`; changing the model is configuration-only. Changing provider requires a supported adapter and credentials. Never put API keys in source control or logs.

Use the exact variable names; the application reads configuration from environment variables. Do not use example/local credentials in production.


## QwenCloud demo operations

The QwenCloud variables above describe the **demo profile only**; they are not a production provider recommendation or a guarantee of free/unlimited service. Follow the [QwenCloud demo operations guide](../ai/QWENCLOUD_DEMO.md) for the full configuration contract, provider-console **Free quota only** requirement, current-versus-planned safeguards, embedding separation, quota-expiry checks, and release gates. In particular, `QWEN_FREE_QUOTA_ONLY=true` is an application-side fail-closed guard; it does not independently enforce provider billing. The provider-console control remains mandatory.

## Database preparation

1. Provision a PostgreSQL database with the pgvector extension available.
2. Set `DATABASE_URL` and `PGVECTOR_DATABASE_URL` in FastAPI Cloud.
3. Set the GitHub Actions secret `DATABASE_URL` to the same production database. The deployment workflow uses it for `uv run alembic upgrade head` before deploying. The migration URL is normalized for asyncpg by `alembic/env.py`.
4. Confirm the GitHub Actions identity can connect to that database and has permission to create/alter the application schema.
5. Verify `/health` and `/ready` after the database and Redis are reachable.

The workflow applies migrations automatically as a single release step before deployment. Do not run the migration concurrently from multiple application replicas.

A newly provisioned database starts empty. Restore or migrate existing data only through a separately planned, verified database procedure.

## Important runtime compatibility notes

- FastAPI Cloud uses the Python project configuration and does not build the Dockerfile's Bun stage. The workflow handles the frontend build explicitly.
- The project currently pins Python to `>=3.14.7,<3.15`. Keep this pin until the dependency set is tested on another version; a package/native-wheel incompatibility may fail the cloud build.
- The Dockerfile installs the Tesseract system executable and OCR language packs. The native FastAPI Cloud deployment does not automatically install those apt packages. OCR paths that invoke Tesseract need a separate compatible runtime or an external OCR service before they can be considered production-ready.
- Redis and PostgreSQL are separate managed services; deploying the FastAPI app does not provision them.
- Celery/background jobs require a separate worker process and are not started by this web deployment workflow.

## First deployment checklist

- [ ] FastAPI Cloud app exists.
- [ ] GitHub Actions secrets `FASTAPI_CLOUD_TOKEN`, `FASTAPI_CLOUD_APP_ID`, `DATABASE_URL`, and (if required by the frontend) `VITE_CLERK_PUBLISHABLE_KEY` are configured.
- [ ] The GitHub Actions `DATABASE_URL` and FastAPI Cloud `DATABASE_URL` point to the same production database.
- [ ] PostgreSQL + pgvector and Redis endpoints are provisioned.
- [ ] Required FastAPI Cloud environment variables are configured securely.
- [ ] Run the `Deploy to FastAPI Cloud` workflow manually if an automatic run has not already deployed the latest successful `main` commit.
- [ ] Confirm the migration step succeeded before the deploy step.
- [ ] Confirm the deployment and inspect logs.
- [ ] Check `/health`, `/ready`, and a basic frontend route.
- [ ] Validate authentication, database operations, and AI requests before using real pharmacy data.
