# Stage 1 — Local Smoke Load Results

## Run metadata

- Date: 2026-10-15
- Revision: `d260db20`
- Target: local API at `http://127.0.0.1:8000`
- Workload: `GET /health` only
- Generator: Python standard-library HTTP client with a 10-thread pool
- Requests: 200 total (20 per thread)
- Environment: Python 3.14.7; API-only mode

## Results

| Measurement | Result |
|---|---:|
| Requests | 200 |
| HTTP 2xx | 200 (100%) |
| Errors | 0 |
| Elapsed time | 0.649 s |
| Throughput | 308.03 requests/s |
| Latency min | 14.329 ms |
| Latency mean | 31.442 ms |
| Latency p50 | 28.017 ms |
| Latency p95 | 43.001 ms |
| Latency p99 | 111.305 ms |
| Latency max | 116.442 ms |

All responses contained the healthy status body.

## Scope and limitations

This is a local liveness-endpoint smoke test, not the Stage 1 ERP load or capacity test. It does not exercise authenticated pharmacy routes, database or Redis workloads, write transactions, AI/RAG, or sustained load. The API started without reachable Redis, and Docker, k6, `AUTH_TOKEN`, and `PHARMACY_ID` were unavailable in the environment. Consequently, these numbers must not be compared to the ERP workload thresholds or used to claim supported capacity.

Run the guarded k6 profiles in [STAGE_1_LOAD_TESTING.md](./STAGE_1_LOAD_TESTING.md) against an isolated synthetic staging environment to collect the full report, including per-endpoint latency, database/Redis/container metrics, and transaction invariants.
