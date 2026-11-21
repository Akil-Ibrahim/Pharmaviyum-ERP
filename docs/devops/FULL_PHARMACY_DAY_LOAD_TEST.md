# Full Pharmacy-Day Load Simulation

## Purpose

Simulate a pharmacy operating day with the canonical baseline of 200 customer visits over 14 public operating hours (08:00–22:00 local pharmacy time), six total staff members, three POS registers and one additional dedicated computer in the pharmacy manager's office (four physical workstation/computer positions in total). A 300-visit profile is a higher-volume stress scenario. Include concurrent cashier and manager activity. This is an accelerated workload model; it does not require a 14-hour wall-clock run.

## Important coverage boundary

The backend now exposes a transactional POS contract at `POST /api/v1/pos/checkout`, including sale lines, payment state, receipt identity, FEFO lot allocation, inventory movements and an outbox event. Cash checkout decrements stock; non-cash checkout reserves stock until a signed payment webhook settles or fails the payment. Integration tests in `tests/integration/test_pos_checkout.py` cover key checkout, FEFO, idempotency and payment-settlement invariants.

However, the current k6 scenario does **not** call this POS contract. It remains a customer-facing search/lookup workload plus manager reads; it cannot claim completed sales, payment capture, FEFO dispensing or stock decrement as measured load-test behavior. The active POS frontend route currently renders `null`, and checkout is not linked to patient/prescription validation. A standalone lot-receipt endpoint exists, but there is no verified supplier purchase-order and delivery-document lifecycle. Cash-shift reconciliation, returns/refunds and end-of-day close are also not established.

The existing opt-in k6 write scenario only creates/deletes an inventory record and creates/cancels a basic order. It is not a substitute for transactional POS journeys. Do not add guessed endpoints to k6.

## Operating-day model

- One synthetic pharmacy.
- 200 visits as the canonical daily workload over 14 public operating hours (08:00–22:00); 300 visits as a higher-volume stress profile.
- Six total staff members per pharmacy across the day, including manager and cashier roles. The three register operators are included within those six positions, not additional staff. The manager-office computer is additional equipment, not a seventh employee; only model an additional manager session when the approved shift/workflow model says it is active. The test uses six concurrent virtual users as a deliberately conservative concurrency approximation; it does not claim all staff are continuously active at once.
- Customer-facing journeys include product listing/search, drug-reference search, and supported patient/order lookups when the required fixture IDs are configured.
- Manager activity includes inventory/low-stock, dashboard, pharmacy and product views, but is currently sampled inside the shared `pharmacy_day` VU pool; it is not a separately modelled manager-office workstation session.
- The dedicated manager-office computer is counted in provisioned equipment totals only. Its active hours, manager login concurrency, workstation utilization and workload mix remain unapproved/unknown; do not add a seventh VU or infer concurrency from the extra computer.
- A journey is one simulated visit, not one HTTP request.
- Think time and endpoint mix are approximate and must be tuned against anonymized operational observations if available. Before adding a separate manager-office VU, obtain the manager's actual usage window, concurrent-session assumptions and representative task mix.
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
- provisioned equipment: three POS stations and one manager-office workstation per pharmacy (four total workstation/computer positions);
- active sessions/VUs by role and workstation type, where instrumented; explicitly mark manager-office session utilization as not modelled until its usage profile is approved;
- request rate and completed visits per second;
- p50/p90/p95/p99 request latency;
- HTTP errors, failed checks and status distribution;
- results by endpoint and journey type;
- CPU/memory, PostgreSQL connections/pool wait/locks/query latency and Redis/Valkey metrics where available;
- test commit, environment, configuration and fixture description.

Unavailable infrastructure metrics must be marked unavailable, not zero.

## Required next step for genuine end-to-end coverage

Add transaction-aware k6 journeys and invariant checks for the existing POS checkout contract, using synthetic data and an isolated disposable database. Include concurrency tests for two cashiers competing for the last units, idempotent retries, no negative stock, no duplicate movements, expiry exclusion, FEFO ordering, payment settlement/failure and tenant isolation. Add independent postcondition checks for persisted sale, payment, receipt, allocation, movement and outbox records.

Implement or verify the remaining API contracts and isolated fixtures for:
1. patient/prescription validation linked to dispensing;
2. purchase-order create/update/cancel and supplier-document matching;
3. purchase-linked goods receiving with batch, expiry and discrepancy handling;
4. cross-pharmacy transfer dispatch/receipt;
5. returns/refunds/voids and controlled write-offs;
6. cashier shift opening/closing and end-of-day sales/payment/stock reconciliation.

Until the k6 transactional journey itself exists and passes, label this profile **customer-day workload simulation**, not a complete transactional pharmacy-day test.
