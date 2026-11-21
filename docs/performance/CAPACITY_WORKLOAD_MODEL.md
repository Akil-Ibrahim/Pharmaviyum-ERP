# Pharmaviyum — Capacity Workload Model

**Status:** Planning model; not a measured capacity result.  
**Canonical source:** [Engineering Benchmark Requirements](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md)  
**Applies to:** synthetic local/staging performance and capacity validation only.

## 1. Canonical business sizing inputs

| Dimension | Per pharmacy | 100-pharmacy network |
|---|---:|---:|
| Pharmacies | 1 | 100 |
| Employees (all roles) | 6 | 600 |
| Public operating hours | 14 hours/day (08:00–22:00 local time) | 14 hours/day (08:00–22:00 local time) |
| POS cash registers / checkout stations | 3 | 300 |
| Dedicated manager-office computer/workstation | 1 | 100 |
| Total physical workstation/computer positions | 4 | 400 |
| Customer visits per operating day | 200 | 20,000 |

The six employees are total staff, not six pharmacists. The pharmacist/manager/cashier role split is not specified by the canonical benchmark. The existing Stage 1 scenario proposes a 2-on/2-off roster, up to three on-shift pharmacy staff plus a manager, and opening preparation from 07:30; treat these as provisional workload assumptions until pharmacy operations confirms them. The three register workflows are included within the six staff positions, not additional employees. Each pharmacy also has one dedicated manager-office computer in addition to the three POS stations. This is an equipment/workstation count, not an additional employee or an automatic extra concurrent virtual user.

Three POS stations are physical/logical checkout capacity per pharmacy. This is not proof that three checkouts are continuously active, nor that 300 network-wide transactions occur at the same instant. A three-cashier-per-pharmacy concurrent checkout test is a deliberate stress scenario to validate register concurrency; 300 concurrent register sessions across the network is an upper-bound synthetic profile, not a forecast.

## 2. What the inputs mean — and do not mean

- **20,000 visits/day** is a daily business-volume planning input.
- A visit is not necessarily a sale, authenticated session, API request, prescription dispense or AI interaction.
- **600 employees** is a staffing assumption, not a concurrent-user count.
- The 14-hour public operating window is 08:00–22:00 local pharmacy time. Opening preparation and closing tasks may occur outside it.
- **300 POS stations** is installed checkout capacity, not observed concurrent use.
- **100 manager-office computers** are additional workstation equipment across the network; do not convert them into 100 additional employees or VUs without an approved usage/shift model.
- No RPS, arrival-rate curve, peak-hour multiplier, concurrent session count, transaction-per-visit ratio, AI-request ratio or background-job volume can be derived safely from these inputs alone.
- Do not multiply daily visits by guessed endpoint counts or convert visits/day directly into VUs.

## 3. Workload dimensions that must be measured or approved

| Dimension | Current state | Required evidence / decision |
|---|---|---|
| Public operating hours | 14 hours/day (08:00–22:00 local pharmacy time) | Operating days and any seasonal exceptions still require business confirmation; model opening/closing work separately. |
| Arrival distribution and peak periods | NOT SPECIFIED | Arithmetic mean is 200 / 14 ≈ 14.3 visits/hour/pharmacy (≈1,429/hour across 100 pharmacies); this is not an arrival curve. The older 30–40 visits/hour/pharmacy peak is provisional only. Obtain anonymized pilot/operational observations; document weekday/seasonality and peak profile. |
| Visit-to-sale conversion | NOT SPECIFIED | Measure or approve a synthetic scenario ratio; do not assume every visitor buys. |
| Average basket / sale lines | NOT SPECIFIED | Define representative basket-size distribution. |
| Pharmacist vs other staff roles | NOT SPECIFIED | Confirm role split within six employees per pharmacy. |
| Shift overlap and active staff sessions | PROVISIONAL | Stage 1 proposes 2-on/2-off, three on-shift pharmacy staff plus a manager (up to 4 staff sessions); confirm roster and overlap with operations before calling it representative. |
| Register utilization / concurrent checkout | NOT SPECIFIED | Observe pilot telemetry; retain 3 simultaneous cashiers/pharmacy as a controlled stress case. |
| API calls per workflow | NOT SPECIFIED | Derive from traced, versioned user journeys, not guessed multipliers. |
| AI requests per visit / task | NOT SPECIFIED | Measure separately; isolate model latency, quota and cost. |
| Background jobs / ingestion | NOT SPECIFIED | Measure event and queue volume, oldest-message age and processing time. |
| Infrastructure limits | NOT VERIFIED HERE | Capture staging compute, DB pool, connections, Redis, network and provider quotas. |

## 4. Progressive validation strategy

Run only with synthetic tenants, products, inventory, patients and transactions. Use an isolated disposable staging environment for writes. Default to read-only until the POS scenario has verified cleanup/rollback and durable postcondition checks.

1. **Single-pharmacy functional baseline:** one synthetic pharmacy, six employee identities (role split only when approved), three POS stations configured. Validate the business journey and baseline resource consumption.
2. **Single-pharmacy register concurrency:** run three independent cashier sessions concurrently against the real transactional POS checkout contract. Assert idempotency, stock conservation, FEFO, expiry exclusion, payment state, receipt identity, inventory movements and tenant scope. Do not count a successful HTTP response alone as a completed sale.
3. **Multi-pharmacy isolation:** increase tenant count progressively (for example 1 → 10 → 25 → 50 → 100), with synthetic data and explicit per-tenant identities. Verify no cross-tenant reads, writes or shared mutable state.
4. **Network register upper-bound:** 300 synthetic register sessions (3 × 100 pharmacies) may be used as an explicitly labelled stress profile after smaller stages pass. It is not the expected normal concurrency. Record achieved throughput and saturation; stop on security invariant failure, sustained errors or unsafe data changes.
5. **Daily-volume simulation:** model 200 visits per pharmacy and 20,000 across the network using an approved arrival curve and workflow mix. Until those inputs are approved, report the scenario as NOT CONFIGURED rather than inventing an arrival rate.
6. **Soak and recovery:** run the approved representative mix for a defined duration; observe queue growth, DB/cache saturation, resource leaks, recovery and error budgets.
7. **AI workload:** execute separately with controlled concurrency, provider quotas and cost ceilings; then run a deliberately bounded mixed test to measure its impact on core ERP/POS latency.

Suggested tenant-count steps are test stages, not forecasts. Suggested concurrency values in other benchmark documents remain stress profiles unless tied to observed traffic.

## 5. Required POS invariants

For concurrent checkout tests, independently query persisted state after the run and assert:

- no negative stock and no overselling beyond the defined reservation model;
- no duplicate sale/payment/receipt on idempotent retries;
- deterministic FEFO allocation and exclusion of expired/unavailable lots;
- payment success/failure transitions are consistent with stock reservation/release;
- sale lines, lot allocations, inventory movements and outbox records reconcile;
- tenant A cannot read or mutate tenant B's sale, inventory or register state;
- timeouts and retries do not create ambiguous duplicate outcomes.

Only test API behavior that exists in the current route/schema contract. Do not fabricate endpoints for shift opening/closing, cash reconciliation, returns or prescription-linked dispensing.

## 6. Reporting contract

Every run must record:

- commit SHA, branch, timestamp and environment;
- staging topology and resource limits (API replicas/CPU/memory, DB compute/pool, Redis limits);
- tenant count, pharmacy count, employees/roles, POS stations, manager-office workstations and active cashier/manager sessions;
- visit arrival curve, journey mix, basket distribution and think time;
- VUs, arrival rate, duration, ramp-up and warm-up;
- API throughput, completed business workflows, p50/p90/p95/p99, errors/timeouts and failed checks;
- PostgreSQL pool wait, query latency, connections, locks and saturation;
- Redis latency, memory, connections, evictions and queue metrics;
- CPU, memory, network, restarts and recovery;
- synthetic dataset version and artifact/report references;
- limitations and whether the result is MEASURED, ESTIMATED, NOT TESTED or UNAVAILABLE.

Never describe local/Codespaces results as production capacity. Do not promote the capacity traceability row above L0 until a repeatable staging run with representative approved workload and retained artifacts exists.

## 7. Existing scenario reconciliation

The repository also contains older single-pharmacy load-test scenarios that mention six staff, 200–300 visits, a 14-hour opening window and provisional peak-hour rates. Six staff and the 14-hour window now align with the canonical benchmark. The 200 visits/day value is the canonical baseline; 300 visits/day remains a higher-volume stress profile, not the baseline. Provisional peak-hour rates are assumptions, not measured traffic.

## 8. Network target and intermediate milestone

The canonical target is 100 pharmacies, 600 rostered employees, 300 POS stations, 100 dedicated manager-office computers (400 workstation/computer positions total) and 20,000 visits per operating day. The existing 50-pharmacy profile is an intermediate Stage B milestone (10,000 visits/day and 150 POS stations), not the final network target. Progress to 100 only after one-pharmacy correctness and 50-pharmacy synchronization/isolation gates pass. Do not assume all 100 branches peak simultaneously without an approved arrival correlation model.

## 9. Exit criteria

Capacity planning is ready for representative execution only when the business owner has approved the unresolved workload dimensions in section 3. A capacity claim requires successful staged execution, workload representativeness review, infrastructure saturation analysis, repeatability and retained artifacts. Passing a synthetic stress test does not itself prove clinical correctness, tenant isolation or production readiness; those remain independent release gates.

## 10. Current k6 harness constraints (source-verified)

The current `tests/load/k6/stage1_baseline.js` and `scripts/run_stage1_load_test.sh` have these boundaries:

- `pharmacy_day` uses `shared-iterations`, `CUSTOMER_VISITS` and `STAFF_VUS`; the script validates a maximum of 10,000 visits and 20 VUs.
- The journey mix is randomized across product search/list, drug-reference search, patient/order reads and manager reads. It does not model three named cashier sessions or a register queue.
- The current read journey does not call `POST /api/v1/pos/checkout`.
- The optional `ENABLE_WRITES` scenario creates/deletes a zero-stock inventory record and creates/cancels a generic order. It is not POS checkout and must not be counted as a sale.
- The script has production-like target guards and remote-target staging opt-in. Preserve these guards in any extension.
- The current 20,000-visit network target exceeds the single-run `CUSTOMER_VISITS` validation ceiling and is not a ready-to-run network workload.

The backend checkout contract is source-observed at `POST /api/v1/pos/checkout`. Existing integration tests construct a request with `pharmacy_id`, `idempotency_key`, `items` (product ID and quantity), `payment_method`, and `cash_received` for cash. Card-terminal flows additionally require signed payment webhook settlement. See `tests/integration/test_pos_checkout.py`. This is an API/test contract reference, not evidence that k6 exercises it.

### Required implementation sequence for transactional k6

1. Add a separate opt-in `pos_checkout` scenario; do not overload or relabel `pharmacy_day`.
2. Require an explicit staging-only opt-in, disposable synthetic database, dedicated tenant-scoped cashier identities, valid synthetic product/lot fixtures, and verified cleanup/restore.
3. Model exactly three cashier VUs per pharmacy in the single-pharmacy concurrency profile. Each VU must have a stable cashier identity and unique idempotency key per intended sale; retries of the same sale must reuse the same key.
4. For network-scale testing, provision isolated tenant fixtures and distribute cashier sessions across pharmacies. A 300-VU run is an upper-bound profile and must only follow stable smaller runs.
5. Validate persisted postconditions independently after the run: sale/payment/receipt counts, lot allocations, inventory movements, outbox events, stock conservation, and tenant isolation. Failed or ambiguous outcomes must fail the scenario.
6. Keep card-terminal webhook tests separately controlled; do not synthesize provider signatures from production secrets or use a live payment provider.
7. Keep the current production-like URL rejection and remote staging guards. Never add a production override.

Until this scenario exists and passes on a recorded commit in isolated staging, transactional POS capacity remains **NOT TESTED**. The existing read-only pharmacy-day workload remains a search/lookup simulation.
