# Full Pharmacy-Day Load Simulation

## Purpose

Simulate a pharmacy operating day for 200–300 customer visits with six staff members, including concurrent cashier and manager activity. This scenario is an accelerated workload model; it does not require a 14-hour wall-clock run.

## Important coverage boundary

The current verified API contracts do not expose a complete POS checkout/payment/receipt/dispensing transaction or a verified procurement receiving lifecycle. Therefore the current k6 scenario can simulate customer-facing search and lookup journeys plus manager operations, but it cannot honestly claim to simulate completed sales, payment capture, FEFO dispensing, stock decrement, supplier order creation, receiving, cancellations of real procurement orders, or end-of-day financial reconciliation.

The existing opt-in write scenario only creates/deletes an inventory record and creates/cancels a basic order. It is not a substitute for those workflows. Do not add guessed endpoints to k6.

## Operating-day model

- One synthetic pharmacy.
- 200 visits as the initial daily workload; 300 visits as the higher profile.
- Six staff members across the day. The test uses six concurrent virtual users as a deliberately conservative concurrency approximation; it does not claim all staff are continuously active at once.
- Customer-facing journeys include product listing/search, drug-reference search, and supported patient/order lookups when the required fixture IDs are configured.
- Manager activity includes inventory/low-stock, dashboard, pharmacy and product views.
- A journey is one simulated visit, not one HTTP request.
- Think time and endpoint mix are approximate and must be tuned against anonymized operational observations if available.
- All data and credentials must be synthetic.

## Preconditions

1. Run only against a local API and a dedicated synthetic database.
2. Confirm the target pharmacy, user token and any configured patient/order IDs are synthetic and authorized.
3. Verify that the API is healthy and k6 is installed.
4. Start with 200 visits and inspect errors before attempting 300.
5. Do not enable writes until a disposable database snapshot and cleanup/rollback have been verified.
6. Keep Mortarium AI out of this profile; measure AI separately with cost controls.

## Run

### Phase 1 — health-only baseline (default)

Start the local API in Codespaces, then run the health-only profile first. This phase sends only `GET /health`; it requires no auth token or pharmacy fixture, performs no writes, and does not call Mortarium AI.

```bash
BASE_URL=http://localhost:8000 \
PEAK_VUS=10 \
./scripts/run_stage1_load_test.sh
```

Review the JSON report and local API/container metrics before proceeding. If health checks fail, stop and diagnose rather than moving to business endpoints.

### Phase 2 — authenticated read-only pharmacy workload

Only after Phase 1 passes, provide a dedicated synthetic user token and pharmacy fixture. The profile below is read-only and does not represent completed sales.

```bash
BASE_URL=http://localhost:8000 \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID="$SYNTHETIC_PHARMACY_ID" \
LOAD_PROFILE=pharmacy_day \
CUSTOMER_VISITS=200 \
STAFF_VUS=6 \
./scripts/run_stage1_load_test.sh
```

After reviewing the 200-visit report, the higher-volume profile can be run explicitly:

```bash
BASE_URL=http://localhost:8000 \
AUTH_TOKEN="$LOAD_TEST_USER_TOKEN" \
PHARMACY_ID="$SYNTHETIC_PHARMACY_ID" \
LOAD_PROFILE=pharmacy_day \
CUSTOMER_VISITS=300 \
STAFF_VUS=6 \
./scripts/run_stage1_load_test.sh
```

The runner writes a timestamped JSON stream to `artifacts/load-tests/`. Review k6 thresholds, failed checks, latency percentiles, HTTP status distribution, API logs and database metrics. A zero exit code by itself is not proof of business correctness. The default profile is deliberately health-only; authenticated business reads require `LOAD_PROFILE=baseline` or `LOAD_PROFILE=pharmacy_day` explicitly.

## Metrics

Report:
- total simulated visits and completed iterations;
- request rate and completed visits per second;
- p50/p90/p95/p99 request latency;
- HTTP errors, failed checks and status distribution;
- results by endpoint and journey type;
- CPU/memory, PostgreSQL connections/pool wait/locks/query latency and Redis/Valkey metrics where available;
- test commit, environment, configuration and fixture description.

Unavailable infrastructure metrics must be marked unavailable, not zero.

## Required next step for genuine end-to-end coverage

Implement or verify explicit API contracts and isolated fixtures for:
1. POS cart/checkout, payment and receipt;
2. batch-level FEFO allocation and dispensing;
3. stock movement and audit trail;
4. purchase-order create/update/cancel;
5. goods receiving with batch, expiry and discrepancy handling;
6. returns/write-offs where supported;
7. end-of-day sales/payment/stock reconciliation.

Then add transaction-aware k6 journeys and invariant checks. Include concurrency tests for two cashiers competing for the last units, idempotent retries, no negative stock, no duplicate movements, expiry exclusion, and tenant isolation. Until those contracts exist and pass, label this profile **customer-day workload simulation**, not a complete transactional pharmacy-day test.
