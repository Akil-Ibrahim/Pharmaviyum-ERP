# Stage 1 — Capacity & Load Testing

## Goal

Establish a reproducible production-capacity baseline before changing infrastructure.

The synthetic business model is:

- 100 pharmacies;
- 2–3 checkout stations per pharmacy;
- 1 manager per pharmacy;
- approximately 4–6 pharmacists per pharmacy in the roster;
- approximately 2–4 staff active at a time per pharmacy;
- approximately 120 customer visits per pharmacy per day on the working baseline;
- mixed global, Southeast Asian/local and generic medicines plus medical and related goods;
- ERP handles operational transactions, while Pharmaviyum CRM handles customer, staff and relationship workflows;
- AI is a smaller but latency-sensitive part of the workload.

The customer mix is represented conceptually as prescription medicines, OTC medicines, medical goods, related products, and vitamins/supplements. The workload also needs to evolve toward doctor and medical-representative workflows as those API contracts become available.

These are **synthetic engineering assumptions**, not measured production statistics. They are deliberately explicit so they can be changed when real customer data is available.

## Current scenarios

`tests/load/k6/stage1_baseline.js` contains two concurrent scenarios:

- **Pharmacy workload:** ramps to 200 active CRM users by default. This represents roughly 2 active staff per pharmacy across 100 pharmacies. Use `PEAK_VUS=400` for an upper-bound scenario representing roughly 4 active staff per pharmacy.
- **AI workload:** configurable concurrent users calling `POST /api/v1/ai/query`.

The CRM workload currently exercises authenticated read paths that exist in the current API: products, patients, inventory, orders, pharmacies. Writes are intentionally excluded from this baseline so repeated runs do not create unbounded database state.

The AI request uses the current request contract: `query`, `pharmacy_id`, `country`, `language`, and `session_id`.

## Running locally

Install k6 using the official package for your operating system, then run:

```bash
k6 run tests/load/k6/stage1_baseline.js
```

For an authenticated run against a synthetic/staging dataset:

```bash
BASE_URL=http://localhost:8000 \
AUTH_TOKEN="$AUTH_TOKEN" \
PHARMACY_ID=1 \
PEAK_VUS=200 \
AI_VUS=10 \
k6 run tests/load/k6/stage1_baseline.js
```

Optional variables:

- `BASE_URL` — target API URL; defaults to `http://localhost:8000`.
- `AUTH_TOKEN` — JWT for an authorized test user.
- `PHARMACY_ID` — authorized pharmacy tenant; defaults to `1`.
- `PATIENT_ID` / `PRODUCT_ID` / `ORDER_ID` / `INVENTORY_ID` — existing synthetic fixture IDs used for detail reads.
- `PEAK_VUS` — peak CRM concurrency; defaults to `200`.
- `AI_VUS` — concurrent AI virtual users; defaults to `10`.
- `AI_DURATION` — AI scenario duration; defaults to `7m`.
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
2. Authenticated CRM read workload at one pharmacy.
3. Scale the same workload toward 100 pharmacies / 200 active staff users.
4. Run the upper-bound 400-user scenario.
5. Add safe synthetic write scenarios in an isolated dataset.
6. Add RAG retrieval workload.
7. Run combined CRM + RAG + AI workload.
8. Run a sustained test to identify resource leaks or queue growth.

Do not run the 100-pharmacy scenario against production. Use an isolated staging/load-test environment with synthetic data.

## Exit criteria

Stage 1 is complete when:

- the load test is reproducible;
- test data and credentials are synthetic/isolated;
- baseline latency and error measurements are recorded;
- the first saturation bottleneck is identified;
- PostgreSQL, Redis, Celery and AI bottlenecks are distinguishable;
- capacity targets for Stage 2+ are based on measurements rather than assumptions.

## Known API coverage gap

The business model includes doctors, medical representatives, prescription workflows and ERP transactions. The current API exposes only part of that surface as production-ready routes; for example, the prescription module still contains placeholder list/detail routes, while ERP status is currently a lightweight adapter endpoint. The load test therefore does **not** invent endpoints for these workflows. They should be added to the workload only after their real API contracts are implemented and verified.
