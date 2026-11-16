# ADR-0006: Append-only Inventory Movement Ledger

**Status:** Accepted — implementation in progress; not production-complete  
**Date:** 2026-11-16  
**Owners:** Pharmaviyum engineering

## Context

The Inventory model is the operational source of current lot balances. POS checkout, payment settlement, payment failure, cancellation, stock receipt and the administrative inventory endpoint currently mutate on-hand and/or reserved quantities through separate code paths.

The current model enforces non-negative quantities and reserved_quantity <= quantity, and POS uses row locks for stock allocation. These controls protect important invariants, but they do not provide a complete, append-only explanation of how a balance was produced. A current balance alone cannot reliably answer who changed stock, why, under which sale/receipt, or whether a retry duplicated a stock effect.

SaleItemAllocation records which lots were allocated to a sale, and the transactional outbox records integration events. Neither is a general inventory audit ledger: allocation does not represent receipts, adjustments or reservation lifecycle; outbox is an integration-delivery mechanism, not the authoritative stock journal.

## Current implementation status (2026-11-16)

The append-only ledger has been introduced in the codebase. This is a code-level status, not a production-readiness claim.

| Path | Current implementation |
|---|---|
| `InventoryMovement` | Append-only movement model, database check constraints, pharmacy-scoped unique idempotency constraint, and PostgreSQL UPDATE/DELETE rejection trigger. |
| `apply_inventory_movement` | Shared transactional service: pharmacy-scoped advisory lock, replay comparison, inventory row lock, balance invariant checks, balance update and movement insert in the caller's transaction. |
| POS goods receipt | Requires an idempotency key and records a `goods_receipt` movement atomically with the lot balance change. |
| POS cash checkout | Records a `cash_sale` movement for each FEFO lot allocation. |
| POS external checkout | Records a `payment_reservation` movement for each lot allocation. |
| Payment webhook | Records `payment_settlement` or `payment_failure` movements atomically with the sale/payment transition. |
| Pending sale cancellation | Records `sale_cancellation` reservation-release movements. |
| `POST /api/v1/inventory` | Creates zero-balance lots only; non-zero balances must use a movement workflow. |
| `PATCH /api/v1/inventory/{id}` | Metadata-only fields; physical and reserved balances are not writable through this endpoint. |
| Inventory adjustment | A reasoned, actor-attributed, idempotent adjustment endpoint uses the shared movement service. |
| Lot deletion | Requires zero balances and no movement history. |

The API write paths above no longer directly assign on-hand or reserved balances outside the shared movement service. Demo seeding still constructs initial inventory rows directly and must remain a non-production fixture; production opening balances require a separately approved, auditable migration/reconciliation process.

## Remaining validation and rollout gaps

- The current integration tests cover atomic movement, idempotent replay, conflicting key reuse, and reservation bounds. Dedicated tests are still required for database trigger immutability, concurrent requests, rollback/failure injection, and full ledger-to-balance reconciliation.
- Verify the migration against a clean PostgreSQL database and the existing production schema before rollout; do not infer production migration success from the migration file alone.
- Add an operator-approved opening-balance process for legacy stock. Do not fabricate historical movements from unverified balances.
- Add lot archival/closure semantics before removing historical lots from operational views.
- The Edge Central consumer must apply accepted POS events through the same domain movement service, with its own event-to-movement idempotency mapping. The Central Inbox currently stores durable receipts only.
- Production acceptance requires evidence from concurrency, retry, recovery, tenant-isolation, and reconciliation tests.

## Decision

Introduce an append-only InventoryMovement journal while retaining Inventory as the authoritative, query-efficient current-balance projection. Do not introduce a second competing stock-balance table.

Each movement records, at minimum:

- tenant and lot identity: pharmacy_id, inventory_id, product_id;
- a constrained movement_type;
- quantity_delta for on-hand stock and reserved_quantity_delta for reservations;
- before/after snapshots for both on-hand and reserved quantities;
- actor identity when known, with an explicit system actor classification for verified system operations;
- reason, reference type and reference identifier (for example sale receipt, receipt document, payment, adjustment);
- a stable idempotency key scoped to the pharmacy and operation;
- correlation/event identifier and UTC creation timestamp.

The ledger row and corresponding Inventory balance update MUST be committed in the same PostgreSQL transaction. The write service must lock the inventory row, validate both resulting balances, reject duplicate idempotency keys, apply the deltas and append the movement. A failed transaction must leave neither a balance update nor a movement behind.

### Movement semantics

| Operation | on-hand delta | reserved delta |
|---|---:|---:|
| Goods receipt | +n | 0 |
| Cash sale / successful payment settlement | -n | 0 |
| External payment reservation | 0 | +n |
| Failed payment / pending sale cancellation | 0 | -n |
| External payment settlement | -n | -n |
| Physical count adjustment | signed difference | 0 |
| Write-off / expiry disposal | -n | 0 |
| Return accepted back into sellable stock | +n | 0 |

A reservation is not an on-hand stock decrement. Settlement of a reserved sale changes both dimensions in one movement. Returns must be represented only after inspection and an explicit disposition decision; quarantined or damaged returns must not increase sellable Inventory.quantity.

### Immutability and deletion

Application roles must not update or delete movement rows. Corrections are compensating movements with references to the original movement; history is never rewritten. Database permissions/triggers and retention/backup controls must reinforce append-only behavior rather than relying only on ORM conventions.

Inventory lots referenced by movements must not be deleted. A later lifecycle change should close/archive a lot instead of deleting its history. Existing delete guards remain in place and must be strengthened when the ledger is introduced.

### Migration and rollout

1. Add the ledger table and constraints through an additive Alembic migration. Inspect and reconcile all Alembic heads before adding the migration; do not guess a parent revision.
2. Do not fabricate historical movements from current balances. If no trustworthy receipt/count history exists, record a clearly labelled opening-balance event with an explicit migration provenance and migration timestamp, or leave legacy balances marked as unverified until an authorized physical reconciliation. The chosen approach must be reviewed before rollout.
3. Introduce one transactional movement service and tests for its constraints/idempotency.
4. Migrate every stock-changing path: receipt, cash checkout, external reservation, settlement, failure, cancellation, administrative adjustment, and subsequent returns/write-offs/transfers.
5. Remove direct administrative writes to reserved_quantity; replace direct quantity edits with an explicit reasoned adjustment workflow before declaring the ledger complete.
6. Roll out behind a controlled migration/reconciliation plan; verify existing data and concurrency behavior before enabling the new write path.

## Invariants

- quantity >= 0
- reserved_quantity >= 0
- reserved_quantity <= quantity
- available_quantity = quantity - reserved_quantity
- every post-rollout stock/reservation delta has exactly one corresponding ledger movement;
- movement idempotency is pharmacy-scoped and replay produces no second balance effect;
- tenant identity in a movement matches the referenced inventory lot;
- movement and balance changes are atomic;
- sale/payment state transitions and inventory movements remain atomic;
- no patient-identifying data is copied into inventory movement metadata.

## Validation required

- migration upgrade/downgrade and clean PostgreSQL migration lifecycle;
- append-only enforcement tests;
- idempotent receipt, checkout, webhook, cancellation and adjustment tests;
- concurrency tests for competing receipts, reservations and checkouts;
- invariant reconciliation comparing ledger deltas with Inventory balances;
- tenant isolation and actor attribution tests;
- failure injection proving transaction rollback leaves both ledger and balances unchanged.

## Consequences

This provides an auditable explanation of stock changes and supports reconciliation, incident analysis and future Edge synchronization. It adds write volume, migration complexity and a requirement that every inventory mutation use the same service. The ledger is not considered implemented or production-ready until every mutation path is migrated and the validation evidence above passes.
