# Production Engineering Standard — Pharmaviyum ERP/CRM

This document defines the minimum operational contract for Pharmaviyum CRM. It is intentionally stricter than a development-only workflow.

## 1. Reliability contract

### Service levels
- **Availability target:** 99.9% monthly for the API.
- **API latency target:** p95 < 1.5s for non-LLM endpoints.
- **RAG latency target:** p95 < 5s under the supported workload.
- **Error budget:** 43m 12s/month at 99.9% availability.

These are engineering targets until production traffic establishes real baselines.

### Health semantics
- `/health` is liveness only and must remain cheap.
- `/ready` checks PostgreSQL, Redis, and AI initialization.
- A readiness failure returns HTTP 503, never a successful 200 response.
- Production startup fails fast when critical initialization fails.

## 2. Deployment contract

Every production release must follow:

1. CI passes lint, type checking, unit tests, integration tests, dependency audit, Bandit, and image build.
2. Database migrations are reviewed separately from application changes.
3. Migrations run once as a release operation, not concurrently from every API replica.
4. The new image is started only after the migration operation succeeds.
5. `/ready` must return 200 before traffic is shifted.
6. Rollback means redeploying the previous immutable image tag.

The application image does **not** run `alembic upgrade head` on API startup. This avoids multi-replica migration races.

## 3. Observability

Required signals:

- Structured request logs with correlation/request IDs.
- Prometheus metrics at `/metrics`.
- OpenTelemetry traces when enabled.
- RAG retrieval latency and tool-call metrics.
- LLM token/cost metrics where provider metadata is available.
- Evaluation score and pass-rate metrics for offline evaluation runs.

Never put secrets, authorization headers, raw patient/customer data, or full prompt contents into logs.

## 4. RAG quality gates

Before changing retrieval or generation behavior, run an evaluation set containing:

- factual answerability cases;
- unanswerable questions;
- retrieval misses;
- prompt-injection documents;
- multilingual queries;
- safety/compliance cases;
- regression cases from previously fixed incidents.

A release must not knowingly reduce safety or groundedness to improve answer rate.

## 5. Security gates

CI treats dependency vulnerabilities and Bandit findings as blocking failures. Exceptions require an explicit, reviewed suppression with a reason and expiry date.

Production configuration must provide explicit CORS origins. Development may remain permissive.

## 6. Incident response

For a production incident:

1. Identify whether the failure is availability, latency, data, security, or AI quality.
2. Check `/health`, `/ready`, metrics, and recent deploys.
3. Stop rollout if the current release is implicated.
4. Roll back to the previous immutable image if user impact is ongoing.
5. Preserve logs/traces/metrics needed for diagnosis.
6. Create a regression test before closing the incident when code caused the failure.

## 7. Change management

Changes to production behavior must be made through reviewed commits/PRs. Direct edits to production infrastructure are emergency-only.

The `dev` branch is the staging/implementation branch. Production uses `main` and Render's production Blueprint. Production readiness still depends on verified secrets, migrations, health checks, backups/restore, observability and rollback.
