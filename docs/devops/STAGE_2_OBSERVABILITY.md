# Stage 2 — Observability

## Purpose

Build a production-safe observability foundation before capacity conclusions are drawn from the Stage 1 200 VU / 400 VU tests.

The project already has OpenTelemetry tracing and AI-specific Prometheus instrumentation. Stage 2 consolidates application and AI metrics behind one Prometheus registry and defines the low-cardinality contract used by dashboards and alerts.

## Telemetry contract

### Correlation

Every HTTP request receives or propagates `X-Request-ID`. The ID is returned in the response and attached to the active OpenTelemetry span as `request.id`.

Request IDs are for logs/traces and **must not be Prometheus labels**.

### Prometheus labels

Allowed labels must describe bounded dimensions such as:

- `method`
- normalized `route`
- `status_class`
- stable `operation`
- stable task/tool/model names where explicitly bounded
- configured worker queue names

Never use these as Prometheus labels:

- user ID
- tenant/pharmacy ID
- patient ID
- session ID
- request ID / trace ID
- email
- query or prompt text
- document/chunk ID
- exception message
- arbitrary URL path parameters
- Redis keys or values

## HTTP metrics

The API exposes:

- `http_requests_total`
- `http_request_duration_seconds`
- `http_requests_in_flight`

HTTP duration uses explicit latency buckets suitable for p50/p95/p99 calculations in Prometheus/Grafana.

## PostgreSQL metrics

The SQLAlchemy engine now exposes pool and statement metrics:

- `db_pool_size`
- `db_pool_checked_out`
- `db_pool_overflow`
- `db_pool_timeouts_total`
- `db_connection_hold_duration_seconds`
- `db_query_total`
- `db_query_duration_seconds`
- `db_query_errors_total`

Query metrics use only a bounded operation classification (`select`, `insert`, `update`, `delete`, `merge`, `call`, `other`). SQL text, parameters, IDs and exception text are never metric labels.

`db_connection_hold_duration_seconds` measures how long checked-out connections remain in use. It is deliberately not called pool-wait time: the current SQLAlchemy pool event boundary does not provide a reliable pre-checkout wait timestamp. Pool saturation should therefore be inferred from `db_pool_checked_out`, `db_pool_overflow`, and `db_pool_timeouts_total` until a dedicated checkout timing hook is introduced.

## Redis metrics

The shared Redis client/pool exports:

- `redis_commands_total{operation,status}`
- `redis_command_duration_seconds{operation}`
- `redis_command_errors_total{operation}`
- `redis_connections`
- `redis_connections_available`
- `redis_connections_in_use`
- `redis_connection_limit`

The operation label is a bounded Redis command name (`ping`, `get`, `setex`, `delete`, `exists`). Redis keys, values, prompts, IDs and exception text are never metric labels. Pool state is sampled from the shared `redis-py` connection pool and is exposed only as aggregate counts.

## Celery metrics

Celery task execution exports:

- `celery_tasks_total{task,queue,status}`
- `celery_task_duration_seconds{task,queue}`
- `celery_tasks_in_flight{queue}`

Task and queue labels are bounded by the configured application routes (`ingest_document`, `ingest_batch`, `reindex_collection`, `cleanup_old_jobs` and their `ingestion`/`maintenance`/`default` queues). Task arguments, tenant IDs, document IDs, exception messages and request IDs are never metric labels.

## Custom worker metrics

The Redis-backed application worker exports:

- `worker_tasks_total{task,queue,status}`
- `worker_task_duration_seconds{task,queue}`
- `worker_tasks_in_flight{queue}`
- `worker_queue_depth{queue}`
- `worker_queue_poll_errors_total{queue}`
- `worker_up`

Queue depth is sampled every five seconds from the configured Redis sorted-set queues. Queue names are allow-listed from `TaskQueue`; arbitrary queue input is not emitted as a metric label. Worker task execution duration is recorded for both successful and failed executions. `worker_up` is set while the worker process is serving and cleared during graceful shutdown.

These metrics complement, rather than replace, Celery telemetry because the repository contains both a Celery ingestion worker and a separate Redis-backed custom worker.

## AI/RAG metrics

The RAG graph records one duration sample per stage invocation and increments `ai_stage_errors_total` only when that stage actually fails. Retrieval also records a separate RAG retrieval metric. The full pipeline records one request outcome and one `rag_pipeline` duration sample per invocation.

AI metrics must use bounded dimensions only. User-provided country/language values, prompts, tenant IDs, request IDs, document IDs and arbitrary tool/model names must not become Prometheus label values. If a future metric needs such dimensions, normalize them to an explicit allow-list or remove the label.

## Existing telemetry

OpenTelemetry application tracing is initialized from `src/pharmaviyum/core/telemetry.py` and instruments FastAPI, SQLAlchemy, Redis and HTTPX when enabled. AI tracing is implemented separately in `src/pharmaviyum/ai/observability/tracer.py` with sensitive AI content redacted unless explicitly opted in.

Do not create a second tracing implementation. Extend the existing telemetry boundary.

## Prometheus and Grafana deployment

The monitoring stack is intentionally **opt-in** and separate from the base application compose file. Start the application stack first so the `pharmaviyum-network` Docker network exists, then start `docker-compose.monitoring.yml`.

Prometheus and Grafana bind to `127.0.0.1` by default. This avoids exposing monitoring endpoints publicly. Grafana anonymous access is disabled and `GRAFANA_ADMIN_PASSWORD` is required before startup.

Example:

```bash
# application stack
docker compose up -d

# monitoring stack
export GRAFANA_ADMIN_PASSWORD='use-a-secret-from-your-secret-manager'
docker compose -f docker-compose.monitoring.yml up -d
```

Optional bind overrides:

- `PROMETHEUS_BIND` — default `127.0.0.1`
- `GRAFANA_BIND` — default `127.0.0.1`
- `PROMETHEUS_RETENTION` — default `15d`

Do not expose ports `9090` or `3000` directly to the Internet. If remote access is required, put Grafana behind the existing authenticated reverse proxy/VPN and keep Prometheus private.

The provisioned Grafana dashboard is read-only and uses the provisioned Prometheus datasource. The current monitoring compose intentionally does not add PostgreSQL/Redis/node exporters because those services are not part of the repository's deployed monitoring stack; application-level pool/cache metrics remain the source of truth for Stage 2.

## Alerts

Prometheus alert rules cover API 5xx rate, API p95 latency, PostgreSQL pool saturation/query latency, Redis errors, custom worker backlog and AI stage failure rate. Thresholds are operational starting points, not final production SLOs; validate them against the Stage 1 200/400 VU baseline before treating them as paging thresholds.

## Validation sequence

1. Confirm application `/metrics` exposes HTTP, PostgreSQL, Redis, Celery, worker and AI metrics.
2. Start the opt-in monitoring stack and confirm Prometheus can scrape `api:8000`.
3. Confirm Grafana loads the provisioned dashboard and Prometheus datasource.
4. Run Stage 1 at 200 VU and then 400 VU while observing API, database, Redis, worker and AI panels.
5. Use the resulting saturation/error/latency data to define production SLI/SLO thresholds.

## SLO policy

Do not invent final production SLOs before representative measurements exist. Stage 1 establishes the baseline; Stage 2 turns that baseline into documented SLI/SLO targets.

## Security and privacy

Telemetry must not export patient data, prompts, model responses, authorization tokens or other sensitive application content by default. Detailed AI content export remains an explicit opt-in and must not be enabled for ordinary production operation.
