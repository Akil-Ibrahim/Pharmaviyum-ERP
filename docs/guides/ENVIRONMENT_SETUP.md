# Environment setup — Pharmaviyum ERP/CRM

This guide describes the current configuration contract for local development, the QwenCloud demo profile, and the hosted FastAPI Cloud application. Keep secrets in local ignored files or the relevant secret manager; never commit real credentials.

## 1. Configuration sources and precedence

Use these sources in this order:

1. `src/pharmaviyum/core/config.py` and the provider-specific settings/validation code define what the running application reads.
2. `.env.example` is the local development template.
3. `.env.prod.example` is a Docker/on-premises-oriented example, not a FastAPI Cloud secret export and not a source of truth for the cloud deployment.
4. `docs/deployment/FASTAPI_CLOUD.md` is the hosted deployment runbook.

The application reads environment variables through Pydantic Settings. Names are case-sensitive. Use the exact uppercase names shown in the templates and runbooks.

Do not create deprecated `.env.development` or `.env.production` files. Use `.env` for local development and configure hosted values directly in FastAPI Cloud / GitHub Actions secrets.

## 2. Local development

Start with the tracked template:

```bash
cp .env.example .env
```

Review the values before starting services. The local template contains development-only endpoints and sample values; do not copy it unchanged into a production environment.

The repository's Compose stack includes PostgreSQL with pgvector, Redis, Ollama, FastAPI, a Celery worker/Beat, and local OpenTelemetry components.

```bash
docker compose up --build
docker compose ps
docker compose logs -f api
```

Local endpoints:

| Service | Address |
|---|---|
| FastAPI | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| OpenAPI schema | `http://localhost:8000/openapi.json` |
| Prometheus metrics | `http://localhost:8000/metrics` |
| Jaeger UI (Compose) | `http://localhost:16686` |
| OTLP/gRPC receiver (Compose) | `localhost:4317` |
| OTLP/HTTP receiver (Compose) | `http://localhost:4318` |

Inside Docker Compose, service-to-service connections must use Compose service DNS names (for example, `postgres`, `redis`, and `ollama`), not `localhost`. A process running directly on the developer host normally uses `localhost` and published ports. Keep the host and container database URLs distinct.

Useful commands:

```bash
# Stop services (preserve named volumes)
docker compose down

# Follow worker logs
docker compose logs -f celery-worker

# Run tests
./scripts/test.sh unit
./scripts/test.sh integration
./scripts/test.sh all

# Static checks
uv run ruff check src/
uv run mypy --explicit-package-bases src/pharmaviyum/
```

Do not use `docker compose down -v` unless you intentionally want to delete local database, Redis, and Ollama volumes.

## 3. Core application variables

The following are the principal runtime settings. Provider-specific and optional integrations are described in the following sections.

| Variable | Purpose | Guidance |
|---|---|---|
| `ENVIRONMENT` | Runtime environment | `development`, `staging`, or `production` |
| `DEBUG` | Debug behavior | Keep `false` in hosted production |
| `LOG_LEVEL` | Application log level | Usually `INFO` in production |
| `DATABASE_URL` | Main PostgreSQL connection | Async SQLAlchemy URL; use `postgresql+asyncpg://...` |
| `PGVECTOR_DATABASE_URL` | Vector-store PostgreSQL connection | Async PostgreSQL URL; may use the same database when schema/permissions are suitable |
| `REDIS_URL` | Redis connection | Use a reachable Redis endpoint; never expose it publicly without access controls |
| `SECRET_KEY` | JWT/application signing secret | Required in staging/production; at least 32 characters, randomly generated |
| `API_SECRET_KEY` | Legacy signing-secret alias | Accepted for compatibility; prefer `SECRET_KEY` |
| `CORS_ORIGINS` | Allowed browser origins | Exact trusted origins; do not use wildcard origins with credentials |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | Set deliberately for the deployment capacity |
| `OTEL_ENABLED` | OpenTelemetry instrumentation switch | Enable only when a valid collector/exporter is configured |
| `OTEL_SERVICE_NAME` | Telemetry service identity | Use a stable service name |
| `OTEL_EXPORTER_ENDPOINT` | OTLP collector endpoint | Must be reachable from the application runtime |

Production/staging startup rejects a missing or shorter-than-32-character signing secret. If both `SECRET_KEY` and `API_SECRET_KEY` are supplied, use `SECRET_KEY` as the canonical setting.

Generate secrets locally or in an approved secret manager; never paste them into chat, source files, issue comments, or CI logs. Example local command:

```bash
openssl rand -hex 32
```

## 4. Mortarium AI provider profiles

### Local / on-premises

The local profile uses Ollama. The current example selects Qwen3.5 9B for generation and `mxbai-embed-large` for embeddings:

- `OLLAMA_BASE_URL`
- `OLLAMA_FAST_MODEL`
- `OLLAMA_MAIN_MODEL`
- `OLLAMA_COMPLEX_MODEL`
- `OLLAMA_EMBEDDING_MODEL`

The Ollama service/model must be available to the API process. For Compose, use the service hostname `ollama`; for a host process, use the host endpoint.

### QwenCloud demo

The current demo profile uses **QwenCloud only**, with `qwen3.8-flash`. Do not configure OpenRouter as a fallback. The QwenCloud variables are:

- `USE_CLOUD_LLM=true`
- `CLOUD_LLM_PROVIDER=qwencloud`
- `QWEN_API_KEY` — secret
- `QWEN_BASE_URL=https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1`
- `QWEN_MODEL=qwen3.8-flash`
- `QWEN_FAST_MODEL=qwen3.8-flash`
- `QWEN_COMPLEX_MODEL=qwen3.8-flash`
- `QWEN_FREE_QUOTA_ONLY=true`
- `QWEN_TIMEOUT_SECONDS=30`
- `QWEN_MAX_OUTPUT_TOKENS=500`

Two controls are required to avoid accidental paid usage:

1. The application guard `QWEN_FREE_QUOTA_ONLY=true`.
2. The provider-console **Free quota only** control enabled for the selected model.

The application flag is a fail-closed configuration check. It does not query or enforce provider billing/quota on its own. Check the provider console for quota remaining and expiry before demo sessions. Do not assume free quota is unlimited or automatically renewed.

QwenCloud is the generation provider in this demo profile. Embeddings are configured separately; the Qwen API key does not imply that embeddings are available. Verify the configured embedding provider, credentials, vector dimensions, and ingestion/retrieval tests before enabling cloud RAG.

See [QwenCloud demo operations](../ai/QWENCLOUD_DEMO.md) for implemented versus planned safeguards and the release checklist.

### Other provider variables

The local example also documents optional Gemini, Groq, OpenAI, and Anthropic credentials. Their presence in `.env.example` does not mean they are enabled in the current demo profile. Do not add provider fallbacks or switch the active provider without an explicit architecture/configuration change and tests.

## 5. RAG, agents, MCP, and observability

The project uses LangGraph for Mortarium AI orchestration and has RAG-related settings in the environment template, including:

- `RAG_MAX_CHUNK_TOKENS`
- `RAG_CHUNK_OVERLAP`
- `RAG_TOP_K`
- `RAG_RERANK_TOP_N`
- `RAG_ENABLE_HYDE`
- `RAG_ENABLE_MULTI_QUERY`
- `RAG_ENABLE_CONTEXTUAL_COMPRESSION`

Agent controls include iteration/history bounds, checkpointing, HITL, and a safety-score threshold. MCP server settings include the server identity, tool timeout/retry bounds, RBAC, and analytics. Keep tool permissions least-privileged and pharmacy/patient context isolated.

OpenTelemetry dependencies and local Compose collector/Jaeger services are included. The Compose collector applies a privacy attribute processor that removes sensitive URL, SQL, authorization, user, patient, pharmacy, and session attributes before exporting traces to local Jaeger. Do not assume the same collector exists in FastAPI Cloud: provide a reachable OTLP endpoint before enabling cloud telemetry. Never put patient data, credentials, access tokens, or raw clinical text into span attributes.

Ragas evaluation dependencies are isolated in the CI evaluation job; they are not a required production runtime environment variable.

## 6. FastAPI Cloud configuration

The hosted application runs on FastAPI Cloud. Configure application variables in the FastAPI Cloud app's Environment Variables section and deployment credentials in GitHub Actions secrets / the protected `production` environment.

### FastAPI Cloud application variables

At minimum, configure and verify:

- `ENVIRONMENT=production`
- `DEBUG=false`
- `LOG_LEVEL=INFO`
- `DATABASE_URL` — the production PostgreSQL URL, using `postgresql+asyncpg://...`
- `PGVECTOR_DATABASE_URL` — the vector-store URL
- `REDIS_URL` — reachable managed Redis
- `SECRET_KEY` — unique random secret of at least 32 characters
- `CORS_ORIGINS` — exact deployed origin
- `USE_CLOUD_LLM=true`
- `CLOUD_LLM_PROVIDER=qwencloud`
- the QwenCloud variables listed above, when the demo AI profile is enabled

Use managed PostgreSQL with pgvector and a separate reachable Redis service. FastAPI Cloud deployment does not provision either service.

### GitHub Actions secrets

The manual deploy workflow currently requires:

- `FASTAPI_CLOUD_TOKEN`
- `FASTAPI_CLOUD_APP_ID`
- `DATABASE_URL` — same production database as the FastAPI Cloud application; used by the workflow's read-only catalog checks and temporary smoke-user cleanup.
- `VITE_CLERK_PUBLISHABLE_KEY` — only if required by the frontend build/sign-in configuration.

The workflow no longer requires `PHARMAVIYUM_SMOKE_USERNAME` or `PHARMAVIYUM_SMOKE_PASSWORD`. It creates a unique, temporary, non-privileged pharmacist account with a random per-run password for positive auth/catalog smoke checks, then attempts to delete that exact account. Do not create static smoke credentials and do not use `admin/admin`.

The `DATABASE_URL` GitHub secret is sensitive and must match the application's production database. Do not print it or expose it in logs.

### Release and migration controls

Production deployment is intentionally manual and protected:

1. Merge a reviewed change to `main) after required CI checks pass.
2. Manually dispatch `Deploy to FastAPI Cloud` from `main` with an approved change/ticket reference.
3. Complete any required approval for the GitHub Actions `production` environment.
4. The workflow verifies CI for the exact commit, builds the frontend, deploys the app, and runs read-only/temporary-account smoke checks.
5. Inspect the workflow result and verify the live app.

**The current deploy workflow does not run Alembic migrations.** Schema migrations are a separate, explicitly approved operation. Before a migration, review the migration and rollback implications, confirm a verified backup, obtain production approval, and run it once from a trusted environment against the intended database. Never put migrations into API replica startup.

See [FastAPI Cloud deployment runbook](../deployment/FASTAPI_CLOUD.md) for the exact workflow and smoke checks.

## 7. Edge / on-premises pharmacy installations

The cloud demo and pharmacy Edge nodes are different deployment profiles:

- Edge/on-premises installations use the local Ollama runtime where configured.
- Edge nodes need their own securely provisioned database/Redis and per-site identity/credentials.
- Central synchronization settings such as `PHARMAVIYUM_EDGE_NODE_ID`, `PHARMAVIYUM_EDGE_TOKEN`, `PHARMAVIYUM_CENTRAL_SYNC_URL`, and sync batch/lease/timeout controls are configured per node where the sync worker is deployed.
- Keep the POS transaction path local and operational during WAN/central-service outages; synchronization is asynchronous and must not make POS depend on the LLM or central AI availability.
- Do not reuse one pharmacy's Edge credentials on another pharmacy.

The initial rollout target is 1–10 pharmacies. The architecture and documentation should preserve a path to 100 pharmacies, but capacity at that scale must be validated with load, failure-recovery, backup/restore, and synchronization tests before claiming production readiness.

## 8. Database migrations and data safety

The canonical Alembic tree is at the repository root:

```text
alembic/
alembic.ini
```

The FastAPI Cloud deploy workflow does not apply migrations. Run migrations only as a separately approved release operation, after reviewing the migration and verifying a restorable backup. Use the production database URL supplied through a secure environment, not a committed file or chat message.

A newly provisioned database is empty. A successful app deployment does not import a drug catalog, create inventory, or restore business data. Seed/import catalog data only through a separately reviewed, idempotent import procedure. Do not treat an empty catalog smoke-test failure as a deployment-platform failure.

## 9. Health checks and release verification

Check readiness, not just process liveness:

```bash
curl --fail https://pharmaviyum-erp-crm.fastapicloud.dev/health
curl --fail https://pharmaviyum-erp-crm.fastapicloud.dev/ready
```

The expected ready response reports PostgreSQL, Redis, and AI initialization as healthy. The deployment smoke workflow also verifies the SPA route `/settings/appearance`, authentication negative/positive paths, protected POS search, and non-empty Omeprazole catalog/product search results.

A green CI run does not prove that production secrets, provider quota, database content, or live pharmacy workflows are correct. Complete the live smoke checks before declaring the release successful.

## 10. Security rules

- Never commit `.env`, `.env.prod`, real API keys, tokens, passwords, or production connection strings.
- Use unique credentials per environment and per pharmacy/Edge node.
- Keep production secrets in FastAPI Cloud and protected GitHub Actions secrets/environments.
- Do not use default or shared admin credentials. Never configure `admin/admin`.
- Rotate any credential suspected of exposure.
- Restrict database and Redis network access to trusted services.
- Do not put secrets, patient identifiers, prescriptions, or raw clinical content in logs, traces, test fixtures, or documentation.
- Keep AI/provider failures isolated from POS and core ERP transactions.
- Back up before schema changes and test restore procedures regularly.
- Do not bypass branch protection, CI, production environment approvals, or release gates.
