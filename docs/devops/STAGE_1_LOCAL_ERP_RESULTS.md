# Stage 1 — Local ERP/CRM Read-Only Load Results

## Run metadata

- Date: 2026-10-15
- Tested revision: `7f1c20ef` plus the uncommitted migration and seed fixes listed in the worktree
- Target: local API at `http://127.0.0.1:8000`
- Load tool: k6 v2.3.0
- Environment: Debian 13, Python 3.14.7, PostgreSQL 17.11, pgvector 0.8.0, Redis 8.0.2
- Test data: synthetic local pharmacy with 20 patients, 59 products, 59 inventory rows and 7 prescriptions
- Workload: guarded, authenticated, read-only pharmacy workload; no AI or write scenario
- Profile: 5 maximum VUs, 6-minute ramp/hold/ramp-down, 440 completed iterations
- Raw k6 metrics: [`artifacts/load-tests/pharmaviyum-erp-20261015T153114Z.json`](../../artifacts/load-tests/pharmaviyum-erp-20261015T153114Z.json)

## Aggregate results

| Measurement | Result |
|---|---:|
| HTTP requests | 440 |
| Completed iterations | 440 |
| Checks | 440/440 passed |
| HTTP failures | 0/440 (0.00%) |
| Throughput | 1.221 requests/s |
| Request latency mean | 18.40 ms |
| Request latency p50 | 10.95 ms |
| Request latency p90 | 41.28 ms |
| Request latency p95 | 49.11 ms |
| Request latency p99 | 196.44 ms |
| Request latency max | 333.59 ms |
| Virtual users | 1–5 (maximum 5) |

The provisional HTTP thresholds passed: error rate below 2%, p95 below 1.5 s,
and p99 below 3 s.

## Endpoint results

| Workload | Requests | HTTP 200 | p50 | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|---:|
| POS product listing | 69 | 69 | 9.53 ms | 20.30 ms | 212.13 ms | 232.92 ms |
| POS product search | 72 | 72 | 8.63 ms | 18.34 ms | 20.55 ms | 20.59 ms |
| Drug reference search | 57 | 57 | 8.62 ms | 14.86 ms | 16.86 ms | 17.97 ms |
| Patient list | 44 | 44 | 12.84 ms | 24.48 ms | 33.14 ms | 33.36 ms |
| Patient statistics | 66 | 66 | 12.46 ms | 25.28 ms | 37.52 ms | 53.90 ms |
| Inventory list | 34 | 34 | 11.41 ms | 18.68 ms | 133.36 ms | 187.22 ms |
| Low-stock inventory | 10 | 10 | 7.56 ms | 15.22 ms | 15.78 ms | 15.92 ms |
| Dashboard summary | 48 | 48 | 46.25 ms | 67.73 ms | 210.20 ms | 333.60 ms |
| Pharmacy list | 18 | 18 | 8.07 ms | 11.72 ms | 16.18 ms | 17.29 ms |
| Product catalog | 22 | 22 | 10.33 ms | 195.95 ms | 222.22 ms | 226.71 ms |

All ten exercised workload checks returned HTTP 200 with no failed checks.

## Scope and limitations

PostgreSQL, Redis and the API were started as local services because Docker CLI
and Docker daemon capabilities are unavailable in this Codespace. The test
therefore validates authenticated application/database/cache behavior on
synthetic data, but it is **not a Docker-based capacity result** and must not be
used to claim production capacity. This profile did not include writes, AI/RAG,
provider costs, sustained soak, or PostgreSQL/Redis/container CPU and memory
time series. Database engine versions also differ from the Docker Compose
targets (PostgreSQL 16 and Redis 7).

Use the guarded profiles in [STAGE_1_LOAD_TESTING.md](./STAGE_1_LOAD_TESTING.md)
after rebuilding the Codespace with Docker-in-Docker to obtain Docker-specific
and infrastructure saturation measurements.
