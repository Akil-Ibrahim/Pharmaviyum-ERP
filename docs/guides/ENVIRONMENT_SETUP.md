# Environment Setup — Pharmaviyum ERP/CRM

## 1. Local development

The canonical local stack is Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```

Main local endpoints:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`
- Metrics: `http://localhost:8000/metrics`

The development Compose stack provides PostgreSQL/pgvector, Redis, Ollama, the FastAPI API, and the Celery ingestion worker.

## 2. Environment files

| File | Purpose |
|---|---|
| `.env.example` | Local configuration template |
| `.env.prod.example` | Production configuration template |
| `.env` | Local developer configuration; never commit |
| `.env.prod` | Production host configuration; never commit |

Do not recreate `.env.development` or `.env.production`; those names are not part of the current configuration contract.

## 3. Required configuration

Copy the appropriate example and set real values for your environment. Production must use unique strong secrets and real database, Redis, and LLM endpoints.

Never place production credentials, API keys, passwords, or tokens in Git.

## 4. Database migrations

The canonical Alembic tree is the repository root:

```text
alembic/
alembic.ini
```

The development API container runs `alembic upgrade head` before its reload server starts. The FastAPI Cloud web deployment workflow does not run database migrations automatically. Apply migrations from a trusted environment with the production database URL supplied securely:

```bash
docker compose exec api alembic upgrade head
```

## 5. LLM deployment profiles

The LLM provider depends on the deployment target:

- **FastAPI Cloud:** Gemini cloud models when configured. Current profile: `gemini-3.5-flash` (main), `gemini-3.5-flash-lite` (fast), `gemini-2.5-pro` (complex/evaluation), and `gemini-embedding-001` (embeddings).
- **Ansible/on-premises:** Ollama with **Qwen3.5 9B Q4_K_M** as the default Mortarium model.

Do not treat the cloud Gemini configuration as the on-premises default. Ansible is responsible for the local Ollama model runtime in pharmacy installations.

## 5. Hosted deployment

The hosted application platform is FastAPI Cloud. The repository includes a manually triggered GitHub Actions workflow at `.github/workflows/deploy-fastapi-cloud.yml`.

The release path is:

```text
Pull request to main
    -> GitHub Actions CI / tests / security checks
    -> merge after required checks pass
    -> manually trigger Deploy to FastAPI Cloud
    -> inspect deployment status and logs
    -> verify health/readiness and critical workflows
```

See [FastAPI Cloud deployment](../deployment/FASTAPI_CLOUD.md) for required secrets, environment variables, database setup, and runtime limitations. Use the FastAPI Cloud deployment runbook and workflow as the hosted deployment source of truth.

## 6. Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Use health/readiness endpoints for deployment checks rather than assuming that a running container means the application is ready.

## 7. Useful commands

```bash
# Start development stack
docker compose up --build

# Stop development stack
docker compose down

# Show service status
docker compose ps

# Follow API logs
docker compose logs -f api

# Follow ingestion worker logs
docker compose logs -f celery-worker

# Run tests
./scripts/test.sh unit
./scripts/test.sh integration
./scripts/test.sh all

# Lint / type-check
uv run ruff check src/
uv run mypy --explicit-package-bases src/pharmaviyum/
```

## 8. Security rules

- Never commit `.env`, `.env.prod`, or other environment files containing secrets.
- Use different credentials between development, staging, and production.
- Rotate credentials when exposure is suspected.
- Keep production databases backed up before schema changes.
- Do not put secrets into documentation, examples, logs, or test fixtures.
- Do not reintroduce deprecated deployment manifests or configuration files without updating the canonical deployment path.
