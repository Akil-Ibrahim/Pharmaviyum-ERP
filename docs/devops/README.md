# DevOps & Production Engineering — Pharmaviyum ERP/CRM

## Purpose

This document defines the production engineering roadmap for Pharmaviyum ERP/CRM. The target is a reliable, observable and secure platform for approximately 100 pharmacies with high visitor traffic and an AI/LLM workload.

The project deliberately evolves the existing deployment model instead of introducing infrastructure for its own sake.

## Current baseline

The current delivery chain is:

```text
Pull request targeting main
    -> GitHub Actions CI / tests / security / RAG evaluation
    -> merge after required checks pass
    -> manually triggered FastAPI Cloud deployment workflow
    -> deployment status, logs, and smoke checks
```

FastAPI Cloud hosts the application. Database, Redis-compatible services, and separate Celery workers must be provisioned and operated according to the deployment runbook.

The current repository also contains an opt-in monitoring Compose stack for controlled deployments. Nginx/edge infrastructure, OpenTelemetry Collector, managed data services and multi-node orchestration are target capabilities, not assumptions about the current base deployment.

GitHub Actions is the CI quality gate. The dedicated FastAPI Cloud workflow is the current hosted application deployment path. Docker image build jobs may support container-based workflows, but they are not the hosted deployment target.

## Target production principles

1. **Measure before scaling.** Capacity decisions must be based on load-test data and production metrics.
2. **Keep services replaceable.** Containers must be stateless where practical; persistent state belongs in managed or explicitly backed-up systems.
3. **Automate recovery.** Backups, rollback and restore procedures must be executable and tested.
4. **Observe the whole request path.** API, database, Redis, workers and AI/RAG operations need correlated telemetry.
5. **Fail safely.** Timeouts, bounded retries, circuit breakers, rate limits and graceful degradation prevent cascading failures.
6. **Secure the supply chain.** Immutable images, SBOM, provenance, dependency scanning and least privilege are release requirements.
7. **Avoid unnecessary platform complexity.** Kubernetes is an optional later stage, not a prerequisite for production readiness.

## Roadmap

### Stage 1 — Capacity & Load Testing

Establish a measurable baseline before changing infrastructure.

- Use `tests/load/k6/stage1_baseline.js` as the reproducible load-test entry point.
- Start with the current `/health` path and authenticated `/api/v1/ai/query` workload; do not load-test stale API endpoints.
- Progressively add verified CRM reads/writes, search and RAG scenarios using synthetic tenant data.
- Measure RPS, concurrent users, p50/p95/p99 latency, error rate and saturation.
- Measure PostgreSQL connections, query latency and pgvector performance.
- Measure Redis latency and Celery queue depth.
- Measure AI concurrency, model latency and timeouts.
- Record a baseline and repeat tests after every major infrastructure change.

The current k6 thresholds are initial engineering gates, not final SLOs. Recalibrate them after representative measurements.

**Exit criteria:** a reproducible load-test suite and documented capacity baseline.

See `docs/devops/STAGE_1_LOAD_TESTING.md` for execution, variables, measurement requirements and exit criteria.

The offline synthetic RAG orchestration benchmark and its limitations are
documented in
[`STAGE_1_AI_RAG_OFFLINE_RESULTS.md`](./STAGE_1_AI_RAG_OFFLINE_RESULTS.md).

### Stage 2 — Observability

Build a unified telemetry layer around OpenTelemetry.

Target stack:

```text
FastAPI / Celery / AI
        |
OpenTelemetry SDK
        |
OpenTelemetry Collector
   |        |        |
Metrics   Traces    Logs
   |        |        |
Prometheus Tempo     Loki
        \     |     /
           Grafana
```

Track at minimum:

- API request rate and error rate.
- p50/p95/p99 latency.
- Database query and pool latency.
- Redis latency and health.
- Celery queue depth and task duration.
- RAG retrieval/generation latency.
- LLM request latency, errors and concurrency.
- Host/container CPU, memory, disk and network saturation.

Define SLI/SLO targets after Stage 1 measurements rather than inventing arbitrary numbers.

**Exit criteria:** dashboards, alert rules, correlated traces and documented SLOs.

### Stage 3 — Application Reliability

Harden request and background-work execution.

- Explicit connect/read/write/request timeouts.
- Bounded retries with exponential backoff and jitter.
- Circuit breakers around external dependencies.
- Graceful shutdown and startup/readiness handling.
- Database connection-pool limits.
- Redis connection-pool limits.
- API rate limiting and request-size limits.
- Idempotency for retried write operations where required.
- Celery task time limits and retry policies.
- Backpressure for expensive AI operations.

Avoid unbounded retries and avoid retrying non-idempotent operations blindly.

**Exit criteria:** dependency failures and traffic spikes degrade predictably instead of cascading through the system.

### Stage 4 — PostgreSQL & Redis Reliability

PostgreSQL is both the transactional database and the pgvector store, so it is a primary capacity and availability concern.

PostgreSQL:

- Connection pooling / PgBouncer where justified by measured connection pressure.
- Automated backups.
- Point-in-time recovery.
- Restore verification.
- Replication or managed PostgreSQL when availability requirements justify it.
- `pg_stat_statements` and slow-query monitoring.
- Index and autovacuum review.
- pgvector index and query-plan monitoring.

Redis:

- Define which data is cache, queue state or durable application state.
- Persistence and HA according to workload requirements.
- Monitor memory pressure and eviction policy.
- Monitor Celery broker health and queue depth.
- Prefer managed Redis when operational requirements exceed a single-node deployment.

**Exit criteria:** tested backup/restore procedure and documented failure modes for PostgreSQL and Redis.

### Stage 5 — AI/LLM Reliability

AI is a separate capacity domain and must not be allowed to saturate the core CRM API.

Target controls:

```text
Agent Harness / AI Gateway
        |
        +-- model routing
        +-- concurrency limits
        +-- per-tenant quotas
        +-- timeouts
        +-- bounded retries
        +-- circuit breaker
        +-- response/cache policy
        +-- fallback/degraded mode
```

Monitor:

- AI request rate.
- Queue depth.
- Model latency.
- Context/retrieval latency.
- Generation failures.
- Token usage and cost where applicable.
- Per-tenant concurrency.
- RAG quality and safety regression metrics.

**Exit criteria:** AI saturation cannot take down normal CRM traffic, and degraded AI behaviour is observable.

### Stage 6 — Security & Software Supply Chain

Extend the existing CI security baseline.

- Container vulnerability scanning with Trivy or an equivalent scanner.
- Dependency vulnerability scanning.
- SBOM generation and retention.
- Image provenance and signing/verification.
- Secret management through a dedicated secret store in production.
- Least-privilege runtime configuration.
- Network segmentation where required.
- WAF and edge rate limiting where internet exposure requires it.
- Automated dependency update workflow with controlled review.
- Regular base-image updates.

Never place credentials in repository files, Docker images or build logs.

**Exit criteria:** every production image has traceable provenance, an SBOM and a repeatable security verification path.

### Stage 7 — CI/CD & Release Engineering

Keep GitHub Actions as the CI gate and FastAPI Cloud as the hosted application deployment target. Ansible remains a separate on-premises deployment capability.

Required capabilities:

- Immutable image identified by commit SHA/digest.
- CI gates before image publication.
- Database migration validation.
- Explicit deployment health checks.
- Automatic rollback procedure.
- Release metadata and audit trail.
- Environment separation.
- Controlled production approval.
- Deployment smoke tests.
- No bypasses such as `continue-on-error` for required checks.

Progressively evaluate canary or blue/green deployment only when the traffic and topology justify it.

**Exit criteria:** a failed release can be detected quickly and rolled back using a documented procedure.

### Stage 8 — Disaster Recovery & Production Validation

Production readiness is not complete until recovery has been tested.

- Define RPO and RTO with the business.
- Document database restore.
- Test restore from a real backup.
- Document Redis recovery expectations.
- Document application redeployment from an immutable image.
- Test dependency outages.
- Test worker failure and queue recovery.
- Run periodic load tests after infrastructure changes.
- Perform controlled failure/chaos tests where appropriate.
- Review SLOs and incident response procedures.

**Exit criteria:** the team can demonstrate recovery rather than only describing it.

## Kubernetes policy

Kubernetes is intentionally **not** part of the mandatory first eight stages.

Introduce Kubernetes only if measured requirements justify orchestration capabilities that Docker Compose + Ansible cannot provide efficiently, such as multi-node scheduling, frequent independent deployments, automated horizontal scaling or substantially larger service fleets.

The target is production reliability, not technology count.

## Target architecture

```text
                         Internet
                            |
                     CDN / WAF / LB
                            |
                    Nginx / edge layer
                            |
                 +----------+----------+
                 |                     |
              API #1                 API #2
                 |                     |
                 +----------+----------+
                            |
                    OpenTelemetry
                            |
                       Collector
                    /       |       \
               Metrics   Traces     Logs
                  |         |          |
             Prometheus   Tempo       Loki
                    \       |       /
                       Grafana
                            |
          +-----------------+-----------------+
          |                 |                 |
      PostgreSQL          Redis            Celery
      + pgvector          / HA             workers
          |                 |                 |
          +-----------------+-----------------+
                            |
                     Agent Harness
                            |
                 RAG / MCP / LLM routing
                            |
                    Model infrastructure
```

The exact topology remains subject to capacity measurements and deployment constraints.

## Production checklist

### Reliability

- [ ] Load baseline established.
- [ ] SLOs defined from measured workload.
- [ ] Timeouts configured.
- [ ] Retry policies bounded.
- [ ] Rate limiting enabled.
- [ ] Graceful shutdown verified.
- [ ] Database pooling reviewed.
- [ ] Celery backpressure and task limits configured.

### Observability

- [ ] OpenTelemetry instrumentation enabled where required.
- [ ] Collector deployed.
- [ ] Metrics dashboards available.
- [ ] Distributed tracing available.
- [ ] Centralized logs available.
- [ ] Alert rules tested.

### Data

- [ ] Automated PostgreSQL backups.
- [ ] PITR available where required.
- [ ] Restore test completed.
- [ ] pgvector performance monitored.
- [ ] Redis recovery procedure documented.

### Security

- [ ] Container scanning enabled.
- [ ] Dependency scanning enabled.
- [ ] SBOM retained.
- [ ] Image provenance verified.
- [ ] Production secrets stored outside Git.
- [ ] Runtime least privilege verified.
- [ ] Edge/WAF controls reviewed.

### Delivery

- [ ] Immutable image releases.
- [ ] CI gates enforced.
- [ ] Migration process tested.
- [ ] Smoke tests run after deployment.
- [ ] Rollback procedure tested.
- [ ] Production approval controlled.

### Recovery

- [ ] RPO/RTO documented.
- [ ] Database restore demonstrated.
- [ ] Application redeployment demonstrated.
- [ ] Dependency failure tested.
- [ ] Incident runbook maintained.

## Related documentation

- `docs/devops/STAGE_1_LOAD_TESTING.md` — Stage 1 load-test procedure.
- `docs/ai_architecture.md` — AI, RAG, memory, guardrails and MCP architecture.
- `docs/guides/ENVIRONMENT_SETUP.md` — environment configuration and deployment prerequisites.
- `docs/deployment/FASTAPI_CLOUD.md` — hosted application deployment runbook.
- `docs/guides/TESTING.md` — test and CI strategy.
- `docker-compose.monitoring.yml` — opt-in Prometheus/Grafana monitoring stack.
- `.github/workflows/ci.yml` — CI quality, security, evaluation and image build gates.
