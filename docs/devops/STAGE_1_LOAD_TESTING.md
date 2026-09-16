# Stage 1 — Capacity & Load Testing

## Goal

Establish a reproducible production-capacity baseline before changing infrastructure. The initial planning target is approximately 100 pharmacies with concurrent CRM and AI workloads.

The repository already had a legacy Locust scenario, but it referenced endpoints and credentials that no longer match the current API. Stage 1 uses k6 as the load-test runner and keeps load-testing dependencies outside the application runtime.

## Current scenarios

`tests/load/k6/stage1_baseline.js` contains two concurrent scenarios:

- **CRM baseline:** ramp from 1 to 50 virtual users while exercising `/health` as a low-cost application-path baseline.
- **AI baseline:** configurable concurrent users calling `POST /api/v1/ai/query`.

The AI request uses the current request contract: `query`, `pharmacy_id`, `country`, `language`, and `session_id`.

## Running locally

Install k6 using the official package for your operating system, then run:

```bash
k6 run tests/load/k6/stage1_baseline.js
```

For an authenticated AI run:

```bash
BASE_URL=http://localhost:8000 \
AUTH_TOKEN="$AUTH_TOKEN" \
PHARMACY_ID=1 \
k6 run tests/load/k6/stage1_baseline.js
```

Optional variables:

- `BASE_URL` — target API URL; defaults to `http://localhost:8000`.
- `AUTH_TOKEN` — JWT for an authorized test user.
- `PHARMACY_ID` — authorized pharmacy tenant; defaults to `1`.
- `AI_VUS` — concurrent AI virtual users; defaults to `2`.
- `AI_DURATION` — AI scenario duration; defaults to `2m`.
- `AI_QUERY` — deterministic test question.
- `COUNTRY` / `LANGUAGE` — AI request context.

Do not use real patient/customer data or production credentials in load tests.

## What to record

Every baseline run should capture:

- request rate and concurrency;
- p50, p95 and p99 latency;
- HTTP error rate;
- PostgreSQL CPU, connections, query latency and slow queries;
- pgvector query latency for RAG workloads;
- Redis CPU, memory and command latency;
- Celery queue depth and worker utilization;
- AI request latency, timeout/error rate and concurrency;
- host/container CPU and memory.

The application thresholds in the script are **initial engineering gates, not measured SLOs**. They must be recalibrated after the first representative run.

## Capacity progression

Run tests in this order:

1. API/health baseline with no AI traffic.
2. Authenticated CRM read workload.
3. Mixed CRM read/write workload using safe synthetic data.
4. RAG retrieval workload.
5. AI synchronous query workload.
6. Combined CRM + RAG + AI workload.
7. Sustained run to identify resource leaks or queue growth.

Do not jump directly to a 100-pharmacy simulation. First establish the behavior of one service instance, then increase concurrency while watching saturation signals.

## Exit criteria

Stage 1 is complete when:

- the load test is reproducible;
- test data and credentials are synthetic/isolated;
- baseline latency and error measurements are recorded;
- the first saturation bottleneck is identified;
- PostgreSQL, Redis, Celery and AI bottlenecks are distinguishable;
- capacity targets for Stage 2+ are based on measurements rather than assumptions.

## Important limitation

The current k6 script intentionally does not claim to model 100 pharmacies yet. The next iteration should add representative authenticated CRM endpoints and safe write scenarios after their current API contracts and tenant setup are verified. This prevents a load test from producing misleading numbers by exercising stale or synthetic endpoints.
