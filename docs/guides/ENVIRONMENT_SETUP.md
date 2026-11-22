# Environment setup — Pharmaviyum ERP/CRM

This guide describes the configuration contract for local development, the FastAPI Cloud Demo, and Ansible-managed Production on a pharmacy server. Keep secrets in local ignored files or the relevant secret manager; never commit real credentials.

Production runs on the pharmacy server and is provisioned/released through Ansible; its PostgreSQL and supporting services are local to the approved Pharmacy Edge deployment profile. Demo runs on FastAPI Cloud with isolated Demo data services. Never share database credentials, application secrets, cache namespaces or data between environments. See the [Production/Demo deployment boundary](../deployment/PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.md) and [Pharmacy Edge Ansible rollout](../devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md).

## 1. Configuration sources and precedence

Use these sources in this order:

1. `src/pharmaviyum/core/config.py` and the provider-specific settings/validation code define what the running application reads.
2. `.env.example` is the local development template.
3. `.env.prod.example` is a Docker/on-premises-oriented example, not a FastAPI Cloud secret export and not a source of truth for the cloud deployment.
4. `docs/deployment/FASTAPI_CLOUD.md` is the hosted deployment runbook.

The application reads environment variables through Pydantic Settings. Names are case-sensitive. Use the exact uppercase names shown in the templates and runbooks.

Do not create deprecated `.env.development` or `.env.production` files. Use `.env` for local development. Configure Demo application variables in the isolated FastAPI Cloud Demo environment and Demo deployment credentials in the protected Demo GitHub Environment. Production configuration is rendered/applied through the reviewed Ansible Pharmacy Edge profile using protected per-site secret sources; never put live Production values in FastAPI Cloud or public GitHub secrets.

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
uv run --locked ruff check src/
uv run --locked mypy --explicit-package-bases src/pharmaviyum/
```

Do not use `docker compose down -v` unless you intentionally want to delete local database, Redis, and Ollama volumes.

## 3. Core application variables

The following are the principal runtime settings. Provider-specific and optional integrations are described in the following sections.

| Variable | Purpose | Guidance |
|---|---|---|
| `ENVIRONMENT` | Runtime environment | `development`, `staging`, or `production` |
| `DEBUG` | Debug behavior | Keep `false` in Demo, staging and Production |
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

See [QwenCloud demo operations](../ai/QWENCLOUD_DEMO.md) for implemented versus planned safeguards and the Demo release checklist.

### Other provider variables

The local example also documents optional Gemini, Groq, OpenAI, and Anthropic credentials. Their presence in `.env.example` does not mean they are enabled in the current demo profile. Do not add provider fallbacks or switch the active provider without an explicit architecture/configuration change and tests.

## 5. RAG, agents, MCP, and observability

Mortarium uses LangGraph for pharmacist-agent and RAG orchestration. In the audited runtime, these RAG settings are wired into the active graph:

- `RAG_TOP_K`
- `RAG_MAX_CONTEXT_DOCS`
- `RAG_MAX_REWRITES`
- `RAG_MAX_QUERY_VARIATIONS`
- `RAG_ENABLE_HYDE`
- `RAG_ENABLE_MULTI_QUERY`

Several other variables are present in settings or `.env.example` but are not currently effective runtime controls: `RAG_RERANK_TOP_N` (no reranker is injected), `RAG_RRF_K` (hybrid search uses its method default), `RAG_ENABLE_CONTEXTUAL_COMPRESSION` (compression is always enabled in the graph), `RAG_MAX_CHUNK_TOKENS` / `RAG_CHUNK_OVERLAP` (the Celery worker uses job config defaults), and `RAG_DEFAULT_LANGUAGES` (the ingestion loaders have separate defaults). See the [Mortarium architecture audit](../rag_architecture_audit.md) before relying on these variables.

Agent settings include iteration/history limits and checkpoint configuration; declared HITL/safety settings must not be interpreted as proof that a complete approval workflow is enabled. MCP tool execution is role-filtered and requires trusted tenant context. Write tools remain denied until a trusted approval verifier is configured. Keep tool permissions least-privileged and bind conversation memory/checkpoints to the same patient scope as the request.

OpenTelemetry dependencies and local Compose collector/Jaeger services are included. The Compose collector applies a privacy attribute processor that removes sensitive URL, SQL, authorization, user, patient, pharmacy, and session attributes before exporting traces to local Jaeger. Do not assume the same collector exists in FastAPI Cloud: provide a reachable OTLP endpoint before enabling cloud telemetry. Never put patient data, credentials, access tokens, or raw clinical text into span attributes.

Ragas evaluation dependencies are isolated in the CI evaluation job; they are not a required production runtime environment variable.

## 6. FastAPI Cloud Demo configuration

FastAPI Cloud is used for the public Demo only. Production uses the same application technology stack deployed to the pharmacy server through Ansible. The public playbooks define the deployment automation contract; real host inventory, per-site credentials, SSH access and approvals remain operator-controlled and are never committed.

The public Demo application is hosted at https://pharmaviyum-erp.fastapicloud.dev. Configure its application variables in the FastAPI Cloud Environment Variables panel and its deploy credentials in the protected GitHub Actions environment demo-pharmaviyum-erp.

### Demo application variables

- ENVIRONMENT=staging — the supported secure runtime profile used by the Demo application.
- DEBUG=false
- LOG_LEVEL=INFO
- DATABASE_URL — isolated Demo PostgreSQL URL, using postgresql+asyncpg://...
- PGVECTOR_DATABASE_URL — Demo vector-store URL.
- REDIS_URL — dedicated managed Redis endpoint for Demo.
- SECRET_KEY — unique Demo-only random secret of at least 32 characters.
- CORS_ORIGINS — exact Demo HTTPS origin.
- USE_CLOUD_LLM=true and CLOUD_LLM_PROVIDER=qwencloud when the Demo AI profile is enabled.
- QwenCloud API, model, timeout and quota variables as described in the QwenCloud Demo guide.

The application runtime enum supports development, staging and production. The Demo uses staging so the hosted Demo does not misidentify itself as Production while retaining the secure staging configuration. PostgreSQL/pgvector and Redis are provisioned separately; FastAPI Cloud does not create these services.

### GitHub Actions Demo secrets

The Demo deployment workflow requires:

- FASTAPI_CLOUD_DEMO_TOKEN — Demo-only FastAPI Cloud deploy token.
- FASTAPI_CLOUD_DEMO_APP_ID — Demo FastAPI Cloud application ID.
- DEMO_DATABASE_URL — isolated Demo database URL for read-only schema checks.
- VITE_CLERK_PUBLISHABLE_KEY — only if required by the frontend build/sign-in configuration.

The workflow must not read Production credentials or target Production infrastructure. It reads only the Demo-specific secrets above; DEMO_DATABASE_URL is mapped to the DATABASE_URL process variable for the read-only schema check.

### Demo release controls

1. Merge a reviewed change to main after required CI checks pass.
2. Manually dispatch Deploy Demo to FastAPI Cloud from main with an approved Demo change/ticket reference.
3. Complete approval for the demo-pharmaviyum-erp environment if configured.
4. Verify the exact deployed commit, staging runtime identity, CPython version, /health, /ready, frontend routes, invalid-auth handling and protected POS access.

The Demo deployment workflow does not run Alembic migrations. Demo schema changes require a separate approved operation and verified backup/restore path. Production deployment and migrations are operated outside this public repository. See the [FastAPI Cloud Demo deployment runbook](../deployment/FASTAPI_CLOUD.md).
## 7. Edge / on-premises pharmacy installations

The cloud demo and pharmacy Edge nodes are different deployment profiles:

- Edge/on-premises installations use the local Ollama runtime where configured.
- Edge nodes need their own securely provisioned database/Redis and per-site identity/credentials.
- Central synchronization settings such as `PHARMAVIYUM_EDGE_NODE_ID`, `PHARMAVIYUM_EDGE_TOKEN`, `PHARMAVIYUM_CENTRAL_SYNC_URL`, and sync batch/lease/timeout controls are configured per node where the sync worker is deployed.
- Keep the POS transaction path local and operational during WAN/central-service outages; synchronization is asynchronous and must not make POS depend on the LLM or central AI availability.
- Do not reuse one pharmacy's Edge credentials on another pharmacy.

The initial rollout target is 1–10 pharmacies. The architecture and documentation should preserve a path to 100 pharmacies, but capacity at that scale must be validated with load, failure-recovery, backup/restore, and synchronization tests before claiming production readiness.

## 8. Database migrations and data safety

The canonical Alembic tree is at the repository root. The public Demo deployment workflow does not apply migrations.

Demo schema changes require a separately reviewed and approved operation against the isolated Demo database, a verified backup/restore path and post-migration validation. Never use a Production database URL or migration credential for Demo.

Production database migrations and their automation are maintained outside this public repository. Do not add Production database endpoints, migration secrets or privileged Production operations to public workflows.

A newly provisioned Demo database is empty. A successful app deployment does not import a drug catalog, create inventory or restore business data. Seed/import catalog data only through a separately reviewed, idempotent procedure using synthetic data.

## 9. Health checks and Demo release verification

Check the public Demo readiness, not just process liveness:

curl --fail https://pharmaviyum-erp.fastapicloud.dev/health
curl --fail https://pharmaviyum-erp.fastapicloud.dev/ready

The expected ready response reports PostgreSQL, Redis and AI initialization as healthy. The Demo deployment workflow also verifies the SPA routes, runtime identity, invalid-credential handling and protected POS access.

A green CI run does not prove that Demo provider quota, database content, catalog coverage or every pharmacy workflow is correct. Complete the live Demo smoke checks before declaring a Demo release successful. Production health checks and release evidence belong to the separately managed Production environment.

## 10. Security rules

- Never commit .env files, API keys, tokens, passwords or database connection strings.
- Use unique credentials per environment and per pharmacy/Edge node.
- Keep Demo secrets in the protected Demo environment and Demo hosting platform. Production secrets are managed outside this public repository.
- Do not use default or shared admin credentials.
- Rotate any credential suspected of exposure.
- Restrict database and Redis network access to trusted services.
- Do not put secrets, patient identifiers, prescriptions or raw clinical content in logs, traces, test fixtures or documentation.
- Keep AI/provider failures isolated from POS and core ERP transactions.
- Back up before schema changes and test restore procedures regularly.
- Do not bypass branch protection, CI, environment approvals or release gates.