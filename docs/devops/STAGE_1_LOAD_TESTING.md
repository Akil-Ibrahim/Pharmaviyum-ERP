# Pharmaviyum ERP/CRM — Stage 1 Load Testing

## Purpose

Create a repeatable, safe capacity baseline for the API workflows that exist in the current Pharmaviyum codebase. The default scenario is read-only. It must run against a local environment or an isolated staging deployment populated with synthetic data.

This is a test plan, not evidence of production capacity. The VU counts and thresholds below are initial engineering assumptions until actual results are recorded.

## Workloads mapped to the project

### Pharmacist / POS workflow

The current API supports product and medicinal-reference lookup, inventory reads, patient search/profile, and dashboard metrics. The route prefixes are not fully uniform in the current router: product and drug-catalog handlers are mounted at `/products` and `/drug-catalog`, while dashboard, patient, inventory and Mortarium routes use `/api/v1`. This test follows the route declarations currently registered by the FastAPI application instead of assuming every route has the same prefix. Route-prefix normalization should be handled as a separate API compatibility change. The workload exercises:

- Sellable product listing and search used by POS;
- international drug-catalog search (INN, ATC, ingredient, brand and product metadata);
- pharmacy-scoped inventory and low-stock queries;
- patient listing and optional patient detail;
- the real `/api/v1/dashboard/summary` endpoint.

**Important:** the current API router does not expose a dedicated POS checkout/dispense transaction endpoint. The test measures the live product-search and operational read paths, not a fictional checkout API. Add checkout, FEFO allocation, batch decrement and sale-finalization traffic only after those API contracts exist and have dedicated synthetic fixtures.

### Pharmacy manager workflow

The manager workload emphasizes dashboard summary, low-stock monitoring, inventory, product catalog, patient list/statistics and pharmacy list. It uses a human think-time pause rather than sending requests continuously.

### Privileged ERP operations

If `SUPERUSER_TOKEN` is provided, an additional read-only scenario exercises existing privileged endpoints for batches, prescriptions, suppliers, ERP integrations, sync events and the patient-purchases sales ledger. Use a dedicated synthetic superuser and confirm its access to the staging tenant before running.

### Mortarium AI

Mortarium is disabled by default because each request may invoke a paid or rate-limited model provider. To include it, explicitly set `ENABLE_AI=true`, choose a small `AI_VUS`, and use a deterministic non-patient-specific `AI_QUERY`. The scenario calls the implemented `POST /api/v1/ai/query` endpoint and records latency separately. Do not use real patient details, production prompts or production credentials.

## Load profiles

The default `PEAK_VUS=20` profile is a low-risk smoke/baseline run. Scale only after reviewing the previous run and confirming the environment has sufficient capacity.

| Profile | Example | Intended use |
|---|---|---|
| Smoke | `PEAK_VUS=5` | Validate auth, route contracts and test data |
| Baseline | `PEAK_VUS=20` | Establish first latency/error baseline |
| Medium | `PEAK_VUS=50` | Observe early saturation and DB pool behavior |
| Business-model target | `PEAK_VUS=200` | Synthetic model of ~2 active staff per pharmacy across 100 pharmacies |
| Upper bound | `PEAK_VUS=400` | Synthetic model of ~4 active staff per pharmacy across 100 pharmacies |

These user counts are concurrency scenarios, not a claim that Pharmaviyum already supports that capacity. They are not concurrent requests-per-second: each virtual user waits between journeys.

The primary scenario ramps through 25%, 50%, peak, 50% and zero over six minutes. Adjust `PEAK_VUS` only after checking API, PostgreSQL, Redis and host/container metrics.

## Safety and data rules

- The baseline is read-only; there is no write scenario in this version.
- `AUTH_TOKEN` must belong to a dedicated synthetic test user with access to `PHARMACY_ID`.
- `PHARMACY_ID` is required; do not assume that ID 1 exists or is authorized.
- `PRODUCT_ID`, `PATIENT_ID` and `ORDER_ID` are optional IDs for synthetic records; when set, the scenario includes product-scoped inventory, patient profile or order-detail reads. Use only records belonging to the test environment.
- `SUPERUSER_TOKEN` is optional and enables the privileged read workload.
- Remote targets require both `ALLOW_REMOTE_TARGET=true` and `LOAD_TEST_ENV=staging`.
- Known production Render hosts and production-like URLs are rejected by the runner.
- Do not bypass the guardrails or run the 200/400 VU profiles against production.
- AI is opt-in and may incur model-provider costs. Start with 1–2 VUs and a short duration.
- Never use real patient/customer data, production credentials or a production database.

## Prerequisites and commands

Install k6 using the official package for your operating system. Start the API with a synthetic/staging database, then run the guarded script from the repository root.

Local smoke test:

```bash
BASE_URL=http://localhost:8000 \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID=1 \
PEAK_VUS=5 \
./scripts/run_stage1_load_test.sh
```

Staging baseline:

```bash
BASE_URL="$STAGING_API_URL" \
ALLOW_REMOTE_TARGET=true \
LOAD_TEST_ENV=staging \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID="$STAGING_PHARMACY_ID" \
PEAK_VUS=20 \
./scripts/run_stage1_load_test.sh
```

Include privileged reads only if a dedicated staging superuser token is available:

```SUPERUSER_TOKEN="$STAGING_SUPERUSER_TOKEN"`

Include Mortarium in a separate run to distinguish API/database latency from model latency:

```bash
BASE_URL="$STAGING_API_URL" \
ALLOW_REMOTE_TARGET=true \
LOAD_TEST_ENV=staging \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID="$STAGING_PHARMACY_ID" \
PEAK_VUS=20 \
ENABLE_AI=true \
AI_VUS=1 \
AI_DURATION=2m \
AI_QUERY="Summarize low-stock risks for this synthetic pharmacy. Do not guess if data is unavailable." \
./scripts/run_stage1_load_test.sh
```

The runner writes a timestamped k6 JSON stream to `artifacts/load-tests/`. Keep it with the tested commit SHA, deployment/environment details, VU profile, data-volume description and corresponding service metrics. Do not commit tokens or sensitive result payloads.

## Metrics to report

For every run, record actual measured values rather than planned targets:

- requests/second, completed iterations and active VUs;
- p50, p95 and p99 latency overall and for each tagged endpoint;
- HTTP failure rate, status-code distribution and failed checks;
- `dashboard_summary_latency` and `drug_catalog_search_latency`;
- PostgreSQL CPU, active connections, pool checked-out/overflow/timeouts, slow queries and query latency;
- Redis CPU, memory and command latency;
- container CPU and memory, restarts and network throughput;
- when AI is enabled: `mortarium_query_latency`, HTTP errors/timeouts, model/provider rate limits and provider cost.

Current thresholds in the script are **provisional engineering gates**, not achieved SLOs:

- HTTP failure rate below 2%;
- aggregate p95 below 1.5 seconds and p99 below 3 seconds;
- dashboard-summary p95 below 1.5 seconds;
- drug-catalog-search p95 below 1 second;
- Mortarium p95 below 20 seconds when the AI scenario is enabled.

Do not report a run as passed solely because the script completed. Review failed checks, status codes and infrastructure metrics; verify that the test exercised valid synthetic records and the expected API routes.

## Capacity progression

1. Run the 5-VU smoke profile and verify every exercised route returns the expected status.
2. Run 20 VUs and capture the first stable read-only baseline.
3. Increase to 50 VUs; inspect PostgreSQL pool, slow queries, cache and container resources.
4. Run 200 VUs only on a representative isolated staging environment.
5. Attempt 400 VUs only if the 200-VU run has no unexplained failures or resource exhaustion.
6. Run privileged operations separately, then Mortarium AI separately.
7. Combine CRM and AI only after both isolated baselines are understood.
8. Add write/dispensing/FEFO load later, after transactional API contracts, fixture creation and cleanup are implemented and tested.

## Known coverage limits

This test currently measures real read paths for the product catalog, drug reference, inventory, patients, dashboard, and optional privileged ERP/dispensing views. It does not claim to test end-to-end POS checkout, batch allocation/FEFO, stock transfer, procurement lifecycle or ERP write synchronization because the corresponding API contracts are not all available as complete transactional flows in the current router. Extend coverage only against verified routes and safe, deterministic staging fixtures.
