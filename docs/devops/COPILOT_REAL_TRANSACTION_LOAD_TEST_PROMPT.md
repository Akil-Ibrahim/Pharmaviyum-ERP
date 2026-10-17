# Copilot Prompt — Real Transaction-Level Pharmacy-Day Load Test

Repository: Akil-Ibrahim/Pharmaviyum-ERP-CRM
Work on branch: test/full-pharmacy-day-load-simulation (or create a new feature branch from the current branch if this branch is unavailable).

Act as a senior FastAPI/Python engineer, pharmacy domain engineer, QA engineer, database engineer and k6 performance engineer. Implement and validate a **real transaction-level pharmacy-day test**, not a read-only endpoint benchmark and not a fake simulation.

## Safety and working rules

1. Inspect git status, current branch and HEAD first. Preserve all existing changes. Never run git reset/clean or overwrite unrelated edits.
2. Never merge or push to main. Do not modify Render, production services, production data, or production configuration.
3. Use a local, isolated, disposable database populated with synthetic fixtures. If you cannot prove that the database is isolated/disposable, do not execute write scenarios; continue with static inspection and tests that do not mutate external systems.
4. Do not print tokens, secrets, connection strings or patient information. Never use real patient data.
5. Inspect actual FastAPI routers, schemas, SQLAlchemy models, migrations, services, authorization, frontend requests, and existing tests before changing code. Do not invent API paths or payloads.
6. Use pyproject.toml/uv; do not add requirements.txt.
7. Do not report a workflow as covered because a list endpoint responds. Do not claim a test passed unless you executed it and captured the actual result.
8. Do not change business rules simply to make tests pass. Record every missing capability and blocker.
9. Use bounded, configurable workload and a hard timeout. Start with one worker and a handful of synthetic transactions. Do not run a high-load write test first.
10. Preserve test results under artifacts/load-tests/ with secrets and personal data excluded.

## Goal: model a full pharmacy operating day

Business assumptions:
- Opening preparation begins at 07:30; pharmacy opens at 08:00 and closes at 21:00.
- 200 customer visits is the first daily profile; 300 visits is the stress profile.
- Six staff are employed, but they have mixed schedules. Do not assume all six are simultaneously active without evidence. Start with 3 cashier workflows plus 1 manager workflow; optionally model up to 6 concurrent staff workflows as a separate profile.
- A visit may include one or more supported operations; document the workload distribution and think time. The accelerated test must complete in a bounded time and label itself as an accelerated day, not 13 hours of real time.
- Daily visitor counts are not RPS. Measure actual RPS and completed business transactions independently.

## Phase 1 — map real transaction contracts

Inspect and create a workflow coverage matrix for:
- Login/token and role permissions.
- Opening a cash shift, if implemented.
- Search by brand/generic/active ingredient/barcode and local product lookup.
- Product selection and available batch retrieval.
- Patient lookup and prescription validation when applicable.
- Cart creation and line-item changes.
- Checkout/sale confirmation.
- Payment record and receipt generation.
- FEFO batch allocation, inventory decrement and inventory movement.
- Order creation, update and cancellation/void semantics.
- Returns/refunds/reversal semantics, if implemented.
- Low-stock detection and procurement suggestions.
- Supplier selection and purchase-order creation.
- Purchase-order cancellation/update, if implemented.
- Goods receiving with quantities, batch/lot and expiry.
- Receiving discrepancies and stock reconciliation.
- Inter-pharmacy transfer lifecycle if implemented.
- Expiry control/write-off/quarantine where implemented.
- End-of-day cash/payment/stock reconciliation and shift close, if implemented.
- Audit trail and ERP sync events.
- Mortarium AI separately; never let an LLM decide price, payment state, expiry eligibility, FEFO allocation, stock quantity or authorization.

For each workflow mark exactly one: IMPLEMENTED AND TESTABLE, PARTIAL, MISSING, or BLOCKED. Include source paths and existing API contracts. A feature described in documentation is not proof that code exists.

## Phase 2 — implement the real business workflows that are missing

For each required missing workflow:
1. Find the intended domain model and service boundaries; reuse existing patterns.
2. Specify invariants before coding.
3. Implement the smallest cohesive service/API/schema/migration changes needed, with authorization and pharmacy/tenant scoping.
4. Use database transactions and appropriate locking/constraints for concurrent stock changes.
5. Add idempotency where retries can repeat a sale, payment, receiving event or integration event.
6. Add audit events and deterministic error responses.
7. Add unit, API, integration and concurrency regression tests.
8. Do not use placeholder responses, hard-coded success, in-memory-only state or invented mock success in the real integration suite.
9. For payment, use a deterministic test payment adapter/provider in the isolated test environment only; never contact a real payment gateway.
10. Do not automatically expose these changes to production. Keep them on the feature branch.

Critical invariants:
- Expired, blocked, quarantined or recalled batches cannot be sold.
- FEFO selects the earliest-expiring eligible batch, deterministically.
- A successful sale atomically records sale/line items, payment state, receipt, batch allocation, stock movement, inventory decrement and audit event as required by the implemented domain.
- A failed/rolled-back sale leaves no partial stock decrement or successful payment/receipt state.
- Two cashiers competing for the last units cannot oversell stock or make inventory negative.
- Retried requests do not duplicate sales, payments, receipts, stock movements or receiving records.
- Cancel/void/refund/return must preserve original history and create correct reversals; never silently delete the original transaction.
- Receiving updates stock only for physically accepted quantities and records batch/expiry/discrepancies.
- Tenant/pharmacy access is enforced server-side; cross-tenant IDs cannot be used.
- Reference-drug records are not sellable unless linked to a locally stocked/priced pharmacy product.
- Audit events include actor, operation, object, timestamp, pharmacy scope, outcome and reason where applicable.

Do not implement payment-provider integrations or regulatory decisions beyond the existing project requirements. If an invariant needs a domain decision that cannot be safely inferred, stop that part and report the exact decision required.

## Phase 3 — create a k6 transaction journey

Update tests/load/k6/stage1_baseline.js or add a dedicated file under tests/load/k6/ using only verified endpoints and valid payloads. Keep read-only, writes, and Mortarium profiles separately selectable.

The real customer journey should perform real state transitions where supported:
1. Search product and resolve a local sellable product.
2. Retrieve eligible batches and assert expired/blocked stock is excluded.
3. Attach a synthetic patient/prescription only when applicable.
4. Create cart/order and line items.
5. Checkout through the actual sale service/API.
6. Record deterministic test payment and verify receipt.
7. Verify FEFO allocation, inventory movement and exact stock decrement.
8. Verify the resulting transaction in read-back endpoints/database test assertions.
9. Exercise a cancellation/void or return/refund workflow where implemented, checking reversal and audit invariants.
10. Include separate manager journeys for low-stock review, purchase order creation, receiving, discrepancy handling, expiry/write-off and end-of-day reconciliation only where the real contracts exist.
11. Include retry/idempotency cases and concurrent last-stock contention in dedicated controlled tests, not every iteration of the broad load test.
12. If an endpoint or workflow is missing, tag the journey as blocked and fail/skip with a clear reason. Never count a skipped transaction as successful.

Use k6 checks and custom metrics such as:
- successful_business_transactions and failed_business_transactions;
- checkout/dispensing lifecycle latency;
- procurement/receiving lifecycle latency;
- cancellation/refund lifecycle latency;
- per-endpoint p50/p90/p95/p99;
- RPS, completed iterations and completed business transactions per second;
- HTTP failure rate and status distribution;
- failed checks, timeouts and retries.

A transaction is successful only when all required postconditions are verified, not merely when the initial POST returns 200/201.

## Phase 4 — safe execution profiles

Provide explicit environment variables and documentation for:
- Static/read-only route smoke.
- 1-5 synthetic transaction smoke.
- 200-visit accelerated pharmacy day.
- 300-visit accelerated stress day.
- Optional 4 concurrent workstation workflows.
- Optional 6 concurrent staff workflows only as a separate profile.
- Short soak run after all prior profiles pass.
- Optional Mortarium profile, isolated from transaction measurements and disabled by default.

The runner must:
- Reject production/Render/public targets and require explicit staging opt-in for remote environments.
- Require explicit write confirmation and a disposable test database marker for writes.
- Validate fixture IDs and token roles without logging their values.
- Enforce hard upper bounds for VUs, iterations and duration.
- Stop or abort on sustained high error rate, resource exhaustion, invariant failure, or unexpected environment.
- Use unique per-run fixture identifiers and reliable cleanup/rollback.
- Preserve evidence even on test failure without leaking credentials.
- Not automatically run high-volume writes just because a user runs the default command.

## Phase 5 — tests and actual run

Run in order:
1. Syntax/lint checks for changed Python and k6 files.
2. Unit tests for business rules.
3. API/integration tests against isolated test DB.
4. FEFO/expiry/tenant/idempotency/concurrency regression tests.
5. Read-only smoke.
6. 1-5 actual synthetic transactions.
7. 200-visit profile.
8. Only if 200 passes, 300-visit profile.
9. Short soak only if all prior profiles pass.

Before any write run, print a safe preflight summary (environment name, local host, database isolation confirmation, fixture IDs without credentials, VU/iteration cap) and require an explicit user-controlled confirmation step. If running in an unattended environment, stop before writes unless the disposable DB and confirmation are already configured in the supported workflow.

Capture:
- exact commands and exit codes;
- commit SHA and branch;
- tests executed, passed, failed and skipped;
- p50/p90/p95/p99, RPS, completed business transactions/sec and error rate;
- DB pool wait, connections, locks, slow queries, CPU/memory and Redis/Valkey metrics where available;
- post-run data invariants and cleanup verification;
- limitations and unimplemented workflows.

Do not invent values for unavailable metrics. A k6 zero exit code is not sufficient if business invariants fail.

## Required final response

Report:
1. Branch/commit and changed files.
2. Coverage matrix with evidence/source paths.
3. Which transaction APIs were already present and which were implemented.
4. Commands actually executed and exit codes.
5. Real results from each run, clearly separated from historical results.
6. Failures and root causes.
7. Safety/invariant test results.
8. Remaining blockers and decisions required.
9. Exact command to reproduce the verified run.

Start by inspecting the repository and report the real workflow gaps. Then implement, test, and run the highest-priority safe slice. Do not stop after merely writing a plan, but do not fake an end-to-end workflow if the domain contract is missing.
