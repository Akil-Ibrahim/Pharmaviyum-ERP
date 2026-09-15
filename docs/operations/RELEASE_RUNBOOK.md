# Immutable Release Runbook

## Scope

`dev` is the implementation branch. CI builds one immutable container image per commit and publishes it to GHCR. Deployment is a separate, manually triggered workflow so a passing build cannot mutate an environment by itself.

## Staging target contract

The current release adapter targets a Docker Compose host. The host must have Docker Engine + Compose v2 and network access to PostgreSQL, Redis, the configured LLM endpoint, and GHCR.

The workflow uses these **GitHub Environment = `staging`** secrets:

- `STAGING_SSH_HOST`
- `STAGING_SSH_USER`
- `STAGING_SSH_PRIVATE_KEY`
- `STAGING_SSH_KNOWN_HOSTS`
- `STAGING_GHCR_USERNAME`
- `STAGING_GHCR_TOKEN` — read-only package access is sufficient
- `STAGING_DATABASE_URL`
- `STAGING_PGVECTOR_DATABASE_URL`
- `STAGING_REDIS_URL`
- `STAGING_OLLAMA_BASE_URL`
- `STAGING_OLLAMA_API_KEY` — optional for providers that require it
- `STAGING_URL`

Optional GitHub Environment variables configure model names:

- `STAGING_OLLAMA_FAST_MODEL`
- `STAGING_OLLAMA_MAIN_MODEL`
- `STAGING_OLLAMA_COMPLEX_MODEL`
- `STAGING_OLLAMA_EMBEDDING_MODEL`

`STAGING_SSH_KNOWN_HOSTS` must be populated from a trusted fingerprint/source. Do not use `ssh-keyscan` at deployment time as a substitute for host-key verification.

## Release flow

1. CI on `dev` runs lint/type checks, unit and integration tests, security scans, RAG regression tests, and builds the image.
2. The image is published as `ghcr.io/akil-ibrahim/pharmaviyum-crm:<commit-sha>`.
3. Start **Actions → Release → Run workflow** and enter the exact 40-character commit SHA.
4. The workflow verifies that exact image exists before touching staging.
5. The workflow checks that every staging secret is configured.
6. The migration container runs `alembic upgrade head` exactly once.
7. The API starts from the immutable image with `docker compose up --no-build`.
8. The deployment script waits for `/health` and performs rollback to the previously running image if the release becomes unhealthy.
9. The workflow then performs an external smoke test against `STAGING_URL/health`.

## Rollback

Rollback is an image promotion, not a rebuild. Re-run the Release workflow with the previous known-good commit SHA. The deployment script also attempts an automatic rollback to the image that was running before the failed deployment.

Database rollback is **not** automatic. Schema migrations must be backward-compatible with the previous application version, or have an explicitly reviewed downgrade/forward-fix procedure.

## Production

There is intentionally no production deployment adapter yet. Do not point the staging secrets at production infrastructure. A production adapter must add a separate protected GitHub Environment, approval policy, production credentials, migration target, smoke test, and rollback procedure before production mutation is enabled.
