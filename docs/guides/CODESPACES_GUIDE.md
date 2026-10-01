# GitHub Codespaces Guide

This guide describes the current Codespaces workflow for Pharmaviyum ERP/CRM.

## 1. Create a Codespace

Create a Codespace from the `dev` branch using the repository's `.devcontainer` configuration.

The post-create setup runs `.devcontainer/setup.sh`.

## 2. What setup does

The setup script currently:

1. installs Python dependencies from `pyproject.toml + uv.lock`;
2. starts PostgreSQL and Redis from `docker-compose.codespaces.yml`;
3. waits for the services;
4. runs `alembic upgrade head`;
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
```

Run the API manually if it is not already running:

```bash
uvicorn src.pharmaviyum.main:app --host 0.0.0.0 --port 8000 --reload
```

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
docker compose -f docker-compose.codespaces.yml logs -f postgres
docker compose -f docker-compose.codespaces.yml logs -f redis

# Database migrations
alembic upgrade head

# Application logs when running through Compose
docker compose logs -f api

# Stop Codespaces dependencies
docker compose -f docker-compose.codespaces.yml stop postgres redis

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

Codespaces is a development environment. Production deployment is handled separately through GitHub Actions for CI, then Render for staging/production deployment.

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

### Migration failure

Check the database first:

```bash
docker compose -f docker-compose.codespaces.yml exec postgres pg_isready -U postgres -d pharmaviyum
```

Then retry:

```bash
alembic upgrade head
```

### LLM requests fail

Verify the provider configuration in `.env` and restart the API after changing environment variables.

## 9. Keep this guide current

The Codespaces source of truth is:

- `.devcontainer/devcontainer.json`
- `.devcontainer/setup.sh`
- `docker-compose.codespaces.yml`
- `.env.example`

If those files change, update this guide instead of introducing a second setup procedure.
