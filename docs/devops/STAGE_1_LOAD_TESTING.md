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

## Route mapping note

The current FastAPI application does not use one uniform prefix for every router. The k6 script follows the paths produced by the currently mounted backend routers, not inferred URL naming conventions:

- Product listing/search: `/products/`, `/products/search`;
- Drug Reference search: `/drug-catalog/search`;
- Orders: `/orders/`, `/orders/{order_id}`, `/orders/{order_id}/status`;
- Patient endpoints: `/api/v1/patients/...`;
- Inventory, batches, suppliers and ERP integration entities: `/api/v1/...`;
- Dashboard: `/api/v1/dashboard/summary`;
- Patient purchases ledger: `/patient-purchases/`.

The POS search calls are corrected in this PR to use `/products/search` and `/drug-catalog/search`, matching the current backend router aggregation. The existing `/api/v1/...` paths remain appropriate for the routers mounted with that prefix (for example patients, inventory and dashboard). Verify the deployed frontend and backend versions together after the change is merged; this PR does not alter backend route mounting.

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

## Representative single-pharmacy operating profile

This profile translates the business scenario into testable assumptions without treating daily visitors as concurrent API users.

### Business assumptions

- **200 customer visits per operating day** for one pharmacy.
- **Opening hours: 08:00–22:00** (14 hours); the opening pharmacist starts using the system at **07:30** for preparation and opening checks.
- **Up to 6 staff per pharmacy, including the manager**, on a 2-on/2-off schedule. Model the working shift as **3 pharmacy staff plus the manager**, pending confirmation of exact shift overlap.
- The **pharmacy manager has a separate computer and application session** and may also serve customers. Count the manager among the six staff, not as an additional employee; the manager's session is separate from the three register sessions unless the manager actually operates a register.
- **3 cash registers** are operated by the three on-shift pharmacy staff. Register workflows are a subset of those staff sessions; do not add three extra staff accounts just because there are three registers.
- For 200 visits across 14 public-facing hours, the arithmetic average is about **14.3 visits/hour**. This is not an arrival schedule: model opening preparation from 07:30, uneven demand and peak periods separately. Until measured traffic is available, use **30–40 visits/hour as a provisional peak-hour assumption**, not a measured fact.
- Customer visits are business events, not automatically HTTP requests or completed sales. The current suite does not implement a verified POS checkout/payment/receipt or dispensing flow, so it cannot yet claim to simulate 200 completed customer sales per day or prove three concurrent cash registers.

### Recommended staged execution

1. **Route smoke:** 5 VUs, read-only, to validate credentials, fixtures and paths.
2. **Staff baseline:** peak 6 VUs, representing six simultaneous staff sessions; keep the three-register share within those sessions.
3. **Peak-hour API stress:** 12 VUs, then 20 VUs if the previous run is stable. This is a technical burst test, not a claim that 20 staff are employed.
4. **Capacity exploration:** 50 VUs, then 100–200 VUs only after reviewing error rates, latency and database/container metrics.
5. **Soak:** after the target profile is stable, run a longer read-only test with the same representative workload. Do not run write scenarios until using a disposable synthetic database and explicit write opt-in.

Example six-staff read-only baseline:

```bash
BASE_URL=http://localhost:8000 \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID="$SYNTHETIC_PHARMACY_ID" \
PEAK_VUS=6 \
./scripts/run_stage1_load_test.sh
```

Example peak-hour burst, after the 6-VU baseline is reviewed:

```bash
BASE_URL=http://localhost:8000 \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID="$SYNTHETIC_PHARMACY_ID" \
PEAK_VUS=20 \
./scripts/run_stage1_load_test.sh
```

These commands exercise the existing mixed read workload. They do **not** create real POS sales, capture payments, issue receipts, allocate FEFO batches, or decrement stock. Those claims require implementation and validation of the corresponding transactional API contracts first. Record actual k6 results; the profile itself is a test plan, not a performance result.

## Required execution order: one pharmacy first, then network synchronization

Do not begin with a 50-pharmacy stress test. Validate in this order and keep a separate report for each stage.

### Stage A — one pharmacy works correctly

Use one synthetic pharmacy with 200 modeled customer visits during 08:00–22:00, opening/preparation activity from 07:30, up to six staff, including the manager, on a 2-on/2-off schedule, a working-shift assumption of three staff plus the manager, and three register workflows within those staff sessions. Confirm actual shift overlap and role permissions before treating the concurrent-session count as final.

- Start with the existing 5-VU read-only smoke test.
- Increase to 6 concurrent staff sessions and review per-endpoint latency, error rate, database pool behavior and application resource usage.
- Progress to the provisional peak-hour profile only after the baseline is stable.
- Exercise checkout, receipt, payment and FEFO stock decrement only after those transactional API contracts and safe synthetic fixtures are verified.
- Establish invariants before/after each write test: stock cannot go negative unexpectedly, expiry/FEFO rules hold, and every mutation is auditable.

**Exit gate:** the one-pharmacy scenarios pass their checks, data invariants hold, and measured latency/error thresholds are reviewed. Do not proceed on the basis of a successful process exit alone.

### Stage A realism checks before the 50-pharmacy stage

The daily visit count is a planning input, not a request rate. Before treating the profile as representative, define and record the following workload assumptions using synthetic data:

- **Arrival distribution:** opening hours, quiet periods, lunch/evening peaks, shift changes and bursts. Do not spread 200 visits evenly across 24 hours.
- **Visit-to-sale ratio:** distinguish footfall, completed checkouts, prescription-only interactions, information/search requests and abandoned carts. Do not assume every visitor produces one sale or a fixed number of HTTP requests.
- **Basket mix:** configurable number of line items, product-search frequency, barcode lookup if supported, stock checks, prescription-related flows where implemented, and receipt/history reads.
- **Transaction correctness:** if the actual API supports the full workflow, verify checkout/payment/receipt and inventory decrement atomically. Test payment failure, cancellation and return paths only where real API contracts exist.
- **Stock contention:** send concurrent synthetic checkout attempts for the last available units of the same product/batch. Assert that the resulting stock and sale records are consistent and that FEFO/expiry rules hold.
- **Operational background work:** include bounded catalog reads, dashboard/reporting reads and any documented import/reconciliation jobs separately before combining them with POS traffic.
- **Network resilience:** test a brief API/worker interruption and recovery in isolated staging; measure failed requests, retry behavior and recovery time. If the product does not support offline checkout, do not assume it does.
- **Observability:** capture p50/p95/p99, throughput, status/error classes, timeouts, CPU/memory, PostgreSQL pool saturation/slow queries/locks, Redis or queue health, and worker backlog where available.

These are additional test-design requirements, not claims that all these workflows or telemetry are currently implemented. First map each item to an existing endpoint/job and test fixture; mark unsupported workflows as gaps rather than fabricating API routes.

### Stage B — synchronize one source pharmacy with a 50-pharmacy network

Keep Stage A as the known-good source. In an isolated environment, create 50 synthetic pharmacy tenants and test the actual supported synchronization path.

1. Make a controlled synthetic change in the source pharmacy (for example, a catalog/price update or an inventory event only if the product's business rules permit that event to be shared).
2. Verify which target pharmacies should receive that event according to the real integration rules. **Do not assume local stock quantities should be copied between branches**; stock is often branch-specific.
3. Record event creation time, delivery time, event ID/version, source pharmacy and intended recipients.
4. Verify delivery, correct ordering/version handling where required, idempotency under duplicate delivery, retry after a controlled worker interruption, and no cross-tenant data leakage.
5. Confirm that each target pharmacy sees only the data it is supposed to receive and that branch-local stock remains branch-local.
6. Measure end-to-end synchronization lag, queue depth, retry count, failed/dead-letter events and database/Redis/worker resource usage.
7. Repeat with controlled event rates, then combine sync traffic with the already-validated one-pharmacy read workload. Increase rates progressively; do not jump straight to 50-branch peak load.

**Important:** the current k6 harness reads sync-event/integration entities but does not yet generate and verify this end-to-end 50-branch propagation flow. Stage B requires a dedicated scenario based on the actual integration/event API contracts; it must not invent routes or claim synchronization is tested just because sync-event records can be listed.

### Stage C — network-wide load

Only after Stage A and Stage B pass, introduce concurrent activity from multiple branches and then a network-wide mixed workload. Track branch count, active staff/register sessions, event rate and API VUs as separate dimensions. VU count alone is not a substitute for customer arrivals or synchronization throughput.

## Representative 50-pharmacy network profile

This profile extends the single-pharmacy assumptions to a network with concurrent activity and central data exchange. It is a planning model, not a measured capacity result.

### Business scale

- **50 pharmacies** connected to the same Pharmaviyum platform or integration layer.
- **200 customer visits per pharmacy per operating day** = **10,000 visits/day network-wide**.
- **Up to 6 staff per pharmacy, including the manager** = **up to 300 rostered staff** across the network; roster size is not the same as simultaneous active sessions.
- Under the modeled shift assumption of three staff plus one manager, plan for up to **200 on-shift staff sessions network-wide** if all 50 pharmacies have that shift active at once; validate shift overlap before treating this as a target.
- **3 registers per pharmacy** = **150 registers**. Register operators are part of the three on-shift staff; do not count them as additional employees.
- Across 14 public-facing hours (08:00–22:00), 10,000 visits/day averages about **714 visits/hour network-wide**. If every branch reaches a provisional 30–40 visits/hour peak at the same time, the synchronized network peak would be **1,500–2,000 visits/hour**. Replace these planning assumptions with actual arrival distributions when available.

A customer visit is not one HTTP request, and a register is not automatically a continuously active virtual user. Model customer arrivals, cashier operations, staff background work and integration events as separate rates.

### Network test stages

1. **Single-branch correctness:** run the existing read-only profile against one synthetic pharmacy, first at 5 VUs and then 6 VUs.
2. **50-branch fan-out:** simulate one or more read-only staff sessions per synthetic branch, using valid branch-scoped credentials/fixtures and measuring latency and errors by branch.
3. **Concurrent staff baseline:** model up to 300 staff accounts across the network, but choose active VUs from observed session activity rather than assuming all 300 continuously issue requests.
4. **Register stress:** progress through 50, 100 and up to 150 concurrent register-like sessions only in isolated synthetic staging, after smaller profiles pass. This is a stress scenario, not a prediction that all tills are busy continuously.
5. **Synchronization load:** independently generate a controlled stream of synthetic stock/catalog/price events from all 50 branches; measure event throughput, queue depth, delivery lag, retries, duplicates, ordering where required, and recovery after a worker restart.
6. **Mixed and soak tests:** combine branch reads with sync only after each has a baseline. Add POS write traffic only when checkout, payment/receipt, inventory decrement and FEFO APIs are verified and test cleanup is safe.

### Important current harness limitation

The current k6 script accepts a single `PHARMACY_ID` and one ordinary `AUTH_TOKEN` per run. It does **not yet constitute a true 50-tenant test** by itself. A valid network test requires parameterized synthetic pharmacy fixtures and an explicit mapping of each virtual user to its pharmacy-scoped identity; do not simply reuse one pharmacy ID and label the result “50 pharmacies.”

Likewise, the current workload reads sync-event/integration entities but does not generate or verify end-to-end exchange events across 50 branches. A dedicated sync scenario must use the actual integration/event API contracts and assert idempotency, tenant isolation, retry behavior and eventual consistency. Never invent routes or send writes to production to simulate this.

Suggested capacity progression after implementing the multi-branch fixture/scenario support: **6 VUs → 20 → 50 → 100 → 150**, then consider higher API-only stress profiles only if the prior run is stable. VUs, branch count, active cashier count and event rate must all be recorded separately in the report.

## Safety requirements

- Never use real patient/customer data, production credentials or a production database.
- Known production hosts and public production-like URLs are rejected by both the runner and the k6 preflight.
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
- for RAG quality runs, Recall@k, Precision@k, MRR/nDCG@k, groundedness,
  citation precision/recall and tenant-isolation violations on a fixed,
  versioned evaluation set;
- token usage and provider cost per query and per successful answer when real
  provider calls are enabled;
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

An offline, test-double-only Mortarium orchestration run is documented in
[`STAGE_1_AI_RAG_OFFLINE_RESULTS.md`](./STAGE_1_AI_RAG_OFFLINE_RESULTS.md).
Its latency and throughput are not live-provider or production-capacity
measurements. Keep such results separate from real-model and pgvector load runs.

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
