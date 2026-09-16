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

Celery task execution now exports:

- `celery_tasks_total{task,queue,status}`
- `celery_task_duration_seconds{task,queue}`
- `celery_tasks_in_flight{queue}`

Task and queue labels are bounded by the configured application routes (`ingest_document`, `ingest_batch`, `reindex_collection`, `cleanup_old_jobs` and their `ingestion`/`maintenance`/`default` queues). Task arguments, tenant IDs, document IDs, exception messages and request IDs are never metric labels.

Queue depth and worker availability are intentionally not inferred from task counters. They require broker/worker-level telemetry and will be added before capacity conclusions are drawn from the load tests.

## Existing telemetry

OpenTelemetry application tracing is initialized from `src/pharmaviyum/core/telemetry.py` and instruments FastAPI, SQLAlchemy, Redis and HTTPX when enabled. AI tracing is implemented separately in `src/pharmaviyum/ai/observability/tracer.py` with sensitive AI content redacted unless explicitly opted in.

Do not create a second tracing implementation. Extend the existing telemetry boundary.

## Next implementation slices

1. Complete Redis instrumentation coverage for application-created Redis clients so all production Redis traffic uses the shared instrumentation boundary.
2. Add Celery broker queue depth and worker availability telemetry.
3. Complete AI/RAG request and generation latency metrics without high-cardinality labels.
4. Deploy an OpenTelemetry Collector for traces and a Prometheus scrape configuration.
5. Add Grafana dashboards for API, database, Redis, Celery, AI/RAG and overall capacity.
6. Add alerts for error rate, latency and saturation only after Stage 1 establishes representative thresholds.
7. Validate the complete telemetry path during the 200 VU and 400 VU tests.

## SLO policy

Do not invent final production SLOs before representative measurements exist. Stage 1 establishes the baseline; Stage 2 turns that baseline into documented SLI/SLO targets.

## Security and privacy

Telemetry must not export patient data, prompts, model responses, authorization tokens or other sensitive application content by default. Detailed AI content export remains an explicit opt-in and must not be enabled for ordinary production operation.
