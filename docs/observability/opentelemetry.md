# OpenTelemetry

Pharmaviyum uses the OpenTelemetry SDK for distributed tracing. Tracing is
disabled by default. When enabled, FastAPI request spans and bounded Mortarium
AI spans are available without exporting prompts, patient data or tool payloads.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OTEL_ENABLED` | `false` | Enable/disable SDK and tracing |
| `OTEL_SERVICE_NAME` | `pharmaviyum-ai` | Service identity |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset | OTLP/gRPC collector endpoint |
| `OTEL_EXPORTER_ENDPOINT` | unset | Backward-compatible endpoint |
| `OTEL_SAMPLE_RATE` | `0.1` | Root trace sampling ratio, 0.0–1.0 |
| `OTEL_ENABLE_SENSITIVE_CLIENT_INSTRUMENTATION` | `false` | Development-only SQLAlchemy, Redis and HTTPX spans |

Example production configuration:

```dotenv
OTEL_ENABLED=true
OTEL_SERVICE_NAME=pharmaviyum-api
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-otlp-collector.example.com:4317
OTEL_SAMPLE_RATE=0.1
```

Production OTLP export requires TLS. Do not put collector credentials or
tokens in source control. Configure authentication headers through the runtime
environment or secret manager.

## Instrumentation and privacy defaults

- FastAPI server spans are enabled when OpenTelemetry is enabled. Health,
  readiness, metrics and documentation routes are excluded.
- SQLAlchemy, Redis and HTTPX auto-instrumentation are **disabled by default**.
  These instrumentations can capture SQL text, Redis keys/commands, URL paths
  or query parameters. They may be enabled only in non-production environments
  with `OTEL_ENABLE_SENSITIVE_CLIENT_INSTRUMENTATION=true`.
- Production must not enable that development-only switch. Add reviewed,
  bounded manual spans for database/cache/client operations where needed.
- The local Collector also deletes SQL text, URL/query values, auth/cookie
  headers, exception messages/stack traces, user/patient/pharmacy/session IDs
  and messaging destination names as a second privacy boundary. This local
  filter is defense-in-depth, not a substitute for production collector policy.
- Mortarium spans should contain only bounded operational attributes such as
  model name, source count, tool count, latency, cache outcome and execution
  status. Never attach prompts, model outputs, retrieved clinical text,
  patient/user identifiers, prescription data, raw tool arguments, credentials,
  SQL statements or connection strings.
- Error telemetry should record exception type and stable error codes, not
  exception messages or stack traces that may include PHI.

## LangSmith

LangSmith manual runs are metadata-only by default. Automatic LangChain content
tracing is forced off unless `AI_TELEMETRY_INCLUDE_CONTENT=true` is explicitly
set in a non-production environment. Production always redacts content even if
that variable is accidentally enabled. Session identifiers are not exported.
Only allowlisted numeric/boolean operational metadata and fixed low-cardinality
tags are sent.

## Local development

The local Docker Compose stack starts an OTLP Collector and Jaeger. Open
`http://localhost:16686` to inspect traces. Local collectors may use HTTP
without TLS; this is not permitted for production endpoints.

Before enabling production export, verify collector authentication, TLS,
retention, access control, regional data residency and attribute filtering.
A successful application startup does not prove that an OTLP collector is
reachable or that exported data satisfies the privacy policy.
