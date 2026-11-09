# OpenTelemetry

Pharmaviyum uses the OpenTelemetry SDK for distributed tracing. The FastAPI
application instruments inbound requests, SQLAlchemy database operations,
Redis commands, and outbound HTTPX requests. Trace context propagation uses
the standard W3C Trace Context headers (`traceparent` and `tracestate`).

## Configuration

Tracing is disabled by default to avoid adding instrumentation overhead when no trace backend is configured. Enable it explicitly together with an OTLP endpoint.

| Variable | Default | Purpose |
| --- | --- | --- |
| `OTEL_ENABLED` | `false` | Enable/disable SDK and instrumentation |
| `OTEL_SERVICE_NAME` | `pharmaviyum-ai` | Service identity in the trace backend |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset | Standard OTLP/gRPC collector endpoint |
| `OTEL_EXPORTER_ENDPOINT` | unset | Backward-compatible endpoint variable |
| `OTEL_SAMPLE_RATE` | `0.1` | Root trace sampling ratio, from 0.0 to 1.0 |

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

- FastAPI server requests (health, readiness, metrics and documentation routes
  are excluded to reduce noise).
- SQLAlchemy synchronous engine boundary used by the async SQLAlchemy engine.
- Redis client operations.
- Outbound HTTPX client requests.
- Mortarium RAG retrieval and MCP tool execution, with bounded attributes for source counts, warning counts, tool names, and success state.
- Mortarium model routing and agent execution, without recording prompts, patient data, tool arguments, or retrieved clinical text.

The SDK uses a parent-based, ratio sampler. Child spans follow the sampled state
of their parent. The provider is flushed and shut down during application
lifespan shutdown.

## Observability acceptance criteria

Instrumentation is not considered complete merely because the SDK initializes. Validate the critical request path end to end and report:

- trace coverage for defined FastAPI, database, Redis, Cel​​ery and Mortarium workflows;
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
clinical text to span attributes or events. Keep custom attributes bounded and
prefer route templates over raw URL paths. Apply the collector retention,
access-control, and regional data-residency policies before enabling export in
production.