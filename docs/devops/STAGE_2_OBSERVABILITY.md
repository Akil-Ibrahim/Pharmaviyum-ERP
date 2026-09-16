# Stage 2 — Observability

## Purpose

Build a production-safe observability foundation before capacity conclusions are drawn from the Stage 1 200 VU / 400 VU tests.

The project already has OpenTelemetry tracing and AI-specific Prometheus instrumentation. Stage 2 consolidates application and AI metrics behind one Prometheus registry and defines the low-cardinality contract used by dashboards and alerts.

## Telemetry contract

### Correlation

Every HTTP request receives or propagates `X-Request-ID`. The ID is returned in the response and attached to the active OpenTelemetry span as `request.id`.

Request IDs are for logs/traces and **must not** be Prometheus labels.

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

### HTTP metrics

The API exposes:

- `http_requests_total`
- `http_request_duration_seconds`
- `http_requests_in_flight`

HTTP duration uses explicit latency buckets suitable for p50/p95/p99 calculations in Prometheus/Grafana.

The `/metrics` endpoint exposes the standard Python/process runtime metrics together with application and AI metrics through the shared Prometheus registry.

## Existing telemetry

OpenTelemetry application tracing is initialized from `src/pharmaviyum/core/telemetry.py` and instruments FastAPI, SQLAlchemy, Redis and HTTPX when enabled. AI tracing is implemented separately in `src/pharmaviyum/ai/observability/tracer.py` with sensitive AI content redacted unless explicitly opted in.

Do not create a second tracing implementation. Extend the existing telemetry boundary.

## Next implementation slices

1. Add PostgreSQL pool/query metrics at the database abstraction boundary.
2. Add Redis command/connection metrics where the shared client/pool is created.
3. Add Celery queue depth, active workers, task duration and failure counters.
4. Complete AI/RAG request and generation latency metrics without high-cardinality labels.
5. Deploy an OpenTelemetry Collector for traces and a Prometheus scrape configuration.
6. Add Grafana dashboards for API, database, Redis, Celery, AI/RAG and overall capacity.
7. Add alerts for error rate, latency and saturation only after Stage 1 establishes representative thresholds.
8. Validate the complete telemetry path during the 200 VU and 400 VU tests.

## SLO policy

Do not invent final production SLOs before representative measurements exist. Stage 1 establishes the baseline; Stage 2 turns that baseline into documented SLI/SLO targets.

## Security and privacy

Telemetry must not export patient data, prompts, model responses, authorization tokens or other sensitive application content by default. Detailed AI content export remains an explicit opt-in and must not be enabled for ordinary production operation.
