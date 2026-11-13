# GitHub Codespaces Guide

This guide describes the current Codespaces workflow for Pharmaviyum ERP/CRM.

## 1. Create a Codespace

Create a Codespace from the `dev` branch using the repository's `.devcontainer` configuration.

The post-create setup runs `.devcontainer/setup.sh`.

The devcontainer uses Docker-in-Docker to run the application stack. If Docker
is not available in an existing Codespace after changing `.devcontainer`, run
**Codespaces: Rebuild Container** from the VS Code Command Palette. Rebuilding
the container preserves the Codespace workspace; do not delete database
volumes unless you intentionally want to reset local data.

## 2. What setup does

The setup script currently:

1. installs Python dependencies from `pyproject.toml + uv.lock`;
2. builds and starts PostgreSQL, Redis, the API (including the frontend build),
   and the Celery worker from `docker-compose.codespaces.yml`;
3. waits for PostgreSQL and Redis health checks, then checks that the API
   `/health` endpoint responds;
4. runs database migrations in the API container before the API starts;
5. prints the Codespaces API/Docs URLs.

There is no `requirements-ai.txt` dependency file in the current project.

## 3. Configure the environment

Start from the repository template:

```bash
cp .env.example .env
```

Add the provider configuration required for your environment. The application can be configured for a cloud LLM provider or local Ollama, depending on the environment and available resources.

Never commit `.env` or provider API keys.

## 4. Verify the environment

After Codespaces setup completes:

```bash
docker compose -f docker-compose.codespaces.yml ps
curl --fail http://localhost:8000/health
```

The setup starts the API and serves the built frontend from the API container.
To restart or inspect the full stack:

```bash
docker compose -f docker-compose.codespaces.yml restart api celery-worker
docker compose -f docker-compose.codespaces.yml logs -f api
```

For an ERP/CRM load test, use only synthetic records and a dedicated test
account. Follow the profiles and guardrails in
[`STAGE_1_LOAD_TESTING.md`](../devops/STAGE_1_LOAD_TESTING.md); a healthy
`/health` response alone does not verify database-backed workflows.

Then use the forwarded port 8000:

```text
https://<codespace-name>-8000.app.github.dev/docs
```

Health check:

```bash
curl http://localhost:8000/health
```

## 5. Run tests

```bash
./scripts/test.sh unit
./scripts/test.sh integration
./scripts/test.sh all
```

For the full development stack:

```bash
docker compose up --build
```

## 6. Useful commands

```bash
# Codespaces infrastructure
docker compose -f docker-compose.codespaces.yml ps
docker compose -f docker-compose.codespaces.yml logs -f api
docker compose -f docker-compose.codespaces.yml logs -f postgres
docker compose -f docker-compose.codespaces.yml logs -f redis
docker compose -f docker-compose.codespaces.yml logs -f celery-worker

# Database migrations run once as part of API container startup.
docker compose -f docker-compose.codespaces.yml exec postgres \
  pg_isready -U postgres -d pharmaviyum

# Stop Codespaces dependencies
docker compose -f docker-compose.codespaces.yml stop

# Remove dependencies and their volumes
docker compose -f docker-compose.codespaces.yml down -v
```

## 7. Architecture in Codespaces

```text
GitHub Codespace
      |
      +--> FastAPI application
      |       +--> AI Agent Harness
      |       +--> RAG pipeline
      |       +--> MCP tools
      |       +--> API / health / metrics
      |
      +--> PostgreSQL + pgvector
      +--> Redis
      |
      +--> configured LLM provider / Ollama
```

Codespaces is a development environment. Hosted application deployment is handled separately through the manually triggered FastAPI Cloud GitHub Actions workflow.

## 8. Troubleshooting

### `ModuleNotFoundError`

Reinstall the current dependency set:

```bash
python -m uv sync --frozen
```

### PostgreSQL or Redis is unavailable

```bash
docker compose -f docker-compose.codespaces.yml ps
docker compose -f docker-compose.codespaces.yml restart postgres redis
```

### Docker command is missing

The Docker-in-Docker feature is applied when the devcontainer is built. Rebuild
the container from the VS Code Command Palette and then check Docker:

```bash
docker info
```

### API or migration startup failure

```bash
docker compose -f docker-compose.codespaces.yml logs --tail 200 api
docker compose -f docker-compose.codespaces.yml logs --tail 100 postgres
```

### LLM requests fail

Verify the provider configuration in `.env` and restart the API after changing environment variables.
The base ERP/API can start without a provider key, but AI/RAG calls require a
configured provider key. Do not commit `.env` or send provider keys in chat.

## 9. Keep this guide current

The Codespaces source of truth is:

- `.devcontainer/devcontainer.json`
- `.devcontainer/setup.sh`
- `docker-compose.codespaces.yml`
- `.env.example`

If those files change, update this guide instead of introducing a second setup procedure.
