# OpenTelemetry

Pharmaviyum uses the OpenTelemetry SDK for distributed tracing. AI/RAG/MCP
application spans use reviewed, bounded attributes. Automatic FastAPI request,
SQLAlchemy, and HTTPX instrumentation is disabled by default and can be enabled
only in development/test after checking URL, SQL, and request-data redaction.
Redis command auto-instrumentation remains disabled. Trace context propagation
uses the standard W3C Trace Context headers (`traceparent` and `tracestate`).

## Configuration

Tracing is disabled by default to avoid adding instrumentation overhead when no trace backend is configured. Enable it explicitly together with an OTLP endpoint.

| Variable | Default | Purpose |
| --- | --- | --- |
| `OTEL_ENABLED` | `false` | Enable/disable SDK and instrumentation |
| `OTEL_SERVICE_NAME` | `pharmaviyum-ai` | Service identity in the trace backend |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset | Standard OTLP/gRPC collector endpoint |
| `OTEL_EXPORTER_ENDPOINT` | unset | Backward-compatible endpoint variable |
| `OTEL_SAMPLE_RATE` | `0.1` | Root trace sampling ratio, from 0.0 to 1.0 |
| `OTEL_INCLUDE_FASTAPI_REQUEST_SPANS` | `false` | Development/test-only opt-in for FastAPI request auto-spans |
| `OTEL_INCLUDE_SENSITIVE_CLIENT_SPANS` | `false` | Development/test-only opt-in for SQLAlchemy and HTTPX auto-spans |

Set one endpoint on the FastAPI Cloud application, for example:

```dotenv
OTEL_ENABLED=true
OTEL_SERVICE_NAME=pharmaviyum-api
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-otlp-collector.example.com:4317
OTEL_SAMPLE_RATE=0.1
```

The local Docker Compose stack starts an OTLP Collector and Jaeger. After `docker compose up`, open `http://localhost:16686` to inspect traces. The collector forwards traces to Jaeger over OTLP/gRPC. For a local collector without TLS, use an `http://` endpoint. OTLP exporter
authentication headers can be supplied through the standard
`OTEL_EXPORTER_OTLP_HEADERS` environment variable. Never commit collector
tokens or credentials to the repository.

When tracing is enabled without an endpoint, spans are created in-process but
are not exported. The application logs a warning; the API remains available.
If an exporter cannot initialize, observability setup is non-fatal and must not
prevent the pharmacy API from starting.

## Instrumented boundaries

- FastAPI request auto-spans are disabled by default. The
  `OTEL_INCLUDE_FASTAPI_REQUEST_SPANS` opt-in is accepted only in development
  and test; verify that URL paths and headers cannot expose patient or tenant
  identifiers before enabling it.
- SQLAlchemy and HTTPX auto-instrumentation are disabled by default. The
  `OTEL_INCLUDE_SENSITIVE_CLIENT_SPANS` opt-in is accepted only in development
  and test; do not enable it against production or PHI-bearing data.
- Redis command auto-instrumentation is always disabled. Command arguments can
  contain prompts, memory content, and clinical payloads. Use only bounded
  application-level operation metrics/spans that never include Redis keys,
  values, or command arguments.
- Mortarium RAG retrieval and MCP tool execution, with bounded attributes for source counts, warning counts, tool names, and success state.
- Mortarium model routing and agent execution, without recording prompts, patient data, tool arguments, or retrieved clinical text.

The SDK uses a parent-based, ratio sampler. Child spans follow the sampled state
of their parent. The provider is flushed and shut down during application
lifespan shutdown.

## Observability acceptance criteria

Instrumentation is not considered complete merely because the SDK initializes. Validate the critical request path end to end and report:

- trace coverage for defined FastAPI, database, Redis, Celery and Mortarium workflows;
- W3C trace-context propagation across process/service boundaries;
- parent/child span relationships and error status;
- exporter/collector delivery failures and dropped telemetry;
- log/trace correlation;
- metrics coverage for API, data services, workers, RAG, model calls and MCP tools;
- alert rule evaluation and notification delivery in a controlled test.

Measure p50/p95/p99 for defined API and AI workflow stages. Keep metric labels bounded; do not use pharmacy, user, patient, session, prompt or raw URL identifiers as Prometheus labels. Full metric definitions and benchmark evidence requirements live in [`../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md`](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md).

## Data protection

Do not attach patient names, patient identifiers, prescription contents,
access tokens, API keys, database connection strings, raw prompts, or retrieved
clinical text to span attributes or events. Do not enable automatic request or
client instrumentation in production; prefer explicit application spans with
allowlisted attributes over raw URLs, SQL statements, headers, or request
bodies. Apply the collector retention,
access-control, and regional data-residency policies before enabling export in
production.