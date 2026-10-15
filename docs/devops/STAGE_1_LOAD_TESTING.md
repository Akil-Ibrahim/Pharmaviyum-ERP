# Pharmaviyum ERP/CRM — Integrated Load, Stress and Transaction Testing

## Purpose and status

This suite combines read-heavy pharmacy operations with an explicitly opt-in synthetic transaction workload. It is intended for local development or an isolated staging environment containing synthetic data only.

The test plan and thresholds are engineering targets, not evidence of achieved capacity. The k6 workload must be executed and its output reviewed before any pass/capacity claim is made.

## Coverage map

### Read-heavy mixed workload

- POS product listing and product search;
- international Drug Reference search;
- pharmacy-scoped inventory and low-stock monitoring;
- patients, patient profile/statistics, and optional order detail;
- Dashboard summary;
- privileged batches, prescriptions, suppliers, ERP integrations, sync events and patient-purchases ledger;
- optional Mortarium AI query with its own latency/error metrics.

### Opt-in synthetic transaction workload

Set `ENABLE_WRITES=true` only after verifying the target is an isolated staging environment and that the database is disposable. This scenario uses currently verified API contracts:

1. **Inventory lot create → delete** — creates a uniquely named lot for an existing synthetic product and pharmacy, then deletes only the inventory record ID returned by that successful create.
2. **Order create → cancel** — creates a low-value synthetic order for an existing synthetic patient, then transitions that order to cancelled using the current order-status API.

The order is intentionally left as a cancelled record; it is not hard-deleted. Therefore, run write testing against a disposable staging database/snapshot and restore or recreate it after the run. A failed cleanup/cancellation must be treated as a failed test and may require staging-data cleanup. Do not run write scenarios against a shared or production database.

The order API currently does not model product lines, payment capture, receipt lines, batch allocation or inventory decrement. These order transactions are **not a POS checkout or dispensing test**.

### Mortarium AI

AI is disabled by default because calls can incur provider costs or rate limits. Enable it only in a separate, cost-controlled run with a deterministic prompt containing no patient data. AI latency has separate thresholds so it does not distort the interactive ERP API latency target.

## Explicit API coverage gaps

The current backend does not expose a verified end-to-end transactional API contract for all of the following workflows:

- POS checkout/payment/receipt;
- batch-level FEFO allocation and dispensing;
- stock transfer lifecycle and receiving;
- procurement purchase-order creation/receiving;
- returns, write-offs and stock adjustments with full audit semantics.

The test deliberately does not invent endpoints or pretend these workflows are covered by reading list endpoints. Add their scenarios when their API contracts, business invariants, fixture strategy and cleanup/rollback procedures exist. The future transaction suite should verify concurrency, idempotency, stock conservation, expiry exclusion, FEFO ordering, tenant isolation and audit records.

## Load profiles

| Profile | Example peak VUs | Intended use |
|---|---:|---|
| Smoke | 5 | Validate credentials, route contracts and synthetic fixtures |
| Baseline | 20 | Establish initial latency/error baseline |
| Medium | 50 | Observe saturation and database pool behavior |
| Capacity candidate | 100–200 | Explore representative staging load after smaller runs pass |
| Upper-bound exploration | 400 | Only after the 200-VU run is stable and infrastructure capacity is understood |

VU counts represent concurrent virtual-user journeys, not a fixed requests-per-second value. Each journey includes think time. Increase load progressively and stop on sustained errors, resource exhaustion, unexpected data changes or staging instability.

The default read workload ramps over six minutes. Optional privileged reads, synthetic writes and Mortarium AI are separate scenarios so their resource impact can be identified. To evaluate the whole platform, first establish individual baselines, then run a controlled mixed profile.

## Safety requirements

- Never use real patient/customer data, production credentials or a production database.
- Known production Render hosts and production-like URLs are rejected by both the runner and the k6 preflight.
- Remote targets require `ALLOW_REMOTE_TARGET=true` and `LOAD_TEST_ENV=staging`.
- `AUTH_TOKEN` must be a dedicated synthetic test-user token with access to `PHARMACY_ID`.
- For privileged reads, provide a dedicated staging `SUPERUSER_TOKEN`.
- For write tests, set `ENABLE_WRITES=true`, `CONFIRM_SYNTHETIC_WRITES=YES`, `SUPERUSER_TOKEN`, a valid synthetic `PRODUCT_ID`, `PATIENT_ID`, and `PHARMACY_ID`.
- The write workload is capped at 20 VUs. Begin with `WRITE_VUS=1` and `WRITE_DURATION=30s`; do not jump directly to a high-volume write run.
- Write tests create cancelled order records and should run only on a disposable database snapshot. Review the result and restore/recreate the database after the run.
- Mortarium is opt-in and may incur model-provider costs. Begin with 1 VU and a short duration.
- Do not bypass guardrails or run 200/400 VU profiles against production.

## Prerequisites and commands

Install k6 and start the API against a synthetic local database.

### 1. Read-only smoke profile

```bash
BASE_URL=http://localhost:8000 \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID="$SYNTHETIC_PHARMACY_ID" \
PEAK_VUS=5 \
./scripts/run_stage1_load_test.sh
```

### 2. Staging baseline

```bash
BASE_URL="$STAGING_API_URL" \
ALLOW_REMOTE_TARGET=true \
LOAD_TEST_ENV=staging \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID="$STAGING_PHARMACY_ID" \
PEAK_VUS=20 \
./scripts/run_stage1_load_test.sh
```

### 3. Synthetic transaction run

Use a disposable staging database snapshot and synthetic records only. Do not paste tokens into source control.

```bash
BASE_URL="$STAGING_API_URL" \
ALLOW_REMOTE_TARGET=true \
LOAD_TEST_ENV=staging \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
SUPERUSER_TOKEN="$STAGING_SUPERUSER_TOKEN" \
PHARMACY_ID="$SYNTHETIC_PHARMACY_ID" \
PRODUCT_ID="$SYNTHETIC_PRODUCT_ID" \
PATIENT_ID="$SYNTHETIC_PATIENT_ID" \
ENABLE_WRITES=true \
CONFIRM_SYNTHETIC_WRITES=YES \
WRITE_VUS=1 \
WRITE_DURATION=30s \
PEAK_VUS=5 \
./scripts/run_stage1_load_test.sh
```

### 4. Mortarium AI run

```bash
BASE_URL="$STAGING_API_URL" \
ALLOW_REMOTE_TARGET=true \
LOAD_TEST_ENV=staging \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID="$STAGING_PHARMACY_ID" \
PEAK_VUS=5 \
ENABLE_AI=true \
AI_VUS=1 \
AI_DURATION=1m \
AI_QUERY="Summarize low-stock risks for this synthetic pharmacy. Do not guess if data is unavailable." \
./scripts/run_stage1_load_test.sh
```

The runner writes a timestamped JSON stream to `artifacts/load-tests/`. Preserve it with the tested commit SHA, deployment/environment details, VU profile, fixture volume and corresponding infrastructure metrics. Do not commit tokens or sensitive payloads.

## Metrics and provisional thresholds

Record actual measurements for each run:

- request rate, completed iterations and active VUs;
- p50/p95/p99 latency overall and by endpoint/workload;
- HTTP failure rate, status-code distribution and failed checks;
- dashboard and drug-catalog latency;
- synthetic inventory create/delete and order create/cancel lifecycle duration;
- PostgreSQL CPU, active connections, pool checkout/overflow/timeouts, slow queries and query latency;
- Redis CPU, memory and command latency;
- application/container CPU, memory, restarts and network throughput;
- Mortarium latency, errors/timeouts, provider rate limits and cost when enabled;
- before/after data invariants for the disposable test database.

Current thresholds are **provisional engineering gates**, not achieved SLOs:

- HTTP failure rate below 2%;
- interactive ERP p95 below 1.5 seconds and p99 below 3 seconds;
- privileged admin p95 below 2 seconds and p99 below 4 seconds;
- dashboard-summary p95 below 1.5 seconds;
- drug-catalog-search p95 below 1 second;
- synthetic transaction workload p95 below 2 seconds;
- Mortarium p95 below 20 seconds when enabled.

Do not report a run as passed solely because k6 exited successfully. Check thresholds, failed checks, route validity, database/Redis/container metrics and business-data invariants.

## Execution sequence

1. Verify each exercised route with 1–5 VUs and valid synthetic fixtures.
2. Run the 20-VU read-only baseline.
3. Run the opt-in write workload at 1 VU for 30 seconds on a disposable database.
4. Verify all created inventory records were removed, all synthetic orders were cancelled, and inspect logs for failed cleanup.
5. Increase read load to 50 VUs, then consider 100–200 VUs after reviewing metrics.
6. Scale write VUs/duration independently; do not automatically reuse read-only VU targets for writes.
7. Test Mortarium separately before adding it to a mixed workload.
8. Only claim POS/FEFO/procurement/transfer coverage after real transaction APIs and invariant checks are implemented.
9. Repeat selected tests as a soak run only after the system is stable at the target load.

## Reporting template

Each run report should include:

- commit SHA and deployment identifier;
- local/staging environment and sanitized fixture description;
- profile, VUs, duration, enabled scenarios and think time;
- requests/second, iterations, p50/p95/p99 and failure rate;
- per-endpoint error/status distribution;
- PostgreSQL, Redis and container metrics;
- business invariants and cleanup verification;
- threshold result: pass/fail/inconclusive;
- top bottlenecks and next engineering actions.
