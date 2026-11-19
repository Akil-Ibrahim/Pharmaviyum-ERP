# Central Inbox Consumer — Readiness Audit

**Review date:** 2026-11-19  
**Decision:** durable receipt only; domain application remains disabled.  
**Scope:** read-only inspection of current `main`. This is an implementation gate, not a claim of production readiness.

## 1. Verified current behavior

The current Central ingress in `src/pharmaviyum/api/v1/sync.py` authenticates an enrolled Edge node, derives `pharmacy_id` from that node registration, rejects a mismatched node identity, validates and stores the event in `CentralInboxEvent`, and returns `accepted` only after the Inbox transaction commits. Identical duplicate event IDs return durable acceptance; reusing an event ID with different content is rejected.

The current inbox model (`src/pharmaviyum/models/sync.py`) stores event identity, pharmacy/node scope, event/schema/aggregate identity, timestamps, payload, `processing_status` and `processing_error`. It does not yet define worker lease/fencing fields, bounded retry scheduling, attempt counters, or an aggregate checkpoint model.

There is no Central domain consumer in the inspected implementation. `accepted` means durable receipt only; it does not mean inventory, sale, or payment state has been applied.

## 2. Current event coverage

The strict v1 schema in `src/pharmaviyum/schemas/sync.py` currently allows only:

- `pos.sale.created` — sale aggregate version 1;
- `pos.sale.cancelled` — sale aggregate version 2;
- `pos.payment.succeeded` — sale aggregate version 2;
- `pos.payment.failed` — sale aggregate version 2.

The v1 payload validates decimal-string money, sale totals, item quantities, lot allocation totals, payment state, inventory effect, extra-field rejection, and a 256 KiB payload limit.

This is a POS sale lifecycle contract, not a complete stock synchronization contract. It does not currently model independent goods receipts, adjustments, write-offs, expiry disposal, transfer dispatch/receipt, or opening balances as separate events. Do not implement a generic stock consumer by guessing these event semantics.

A sale's version-2 outcome is mutually exclusive: cancellation or payment settlement/failure. Central must reject/quarantine conflicting event IDs for the same aggregate version; it must not choose a winner by arrival time.

## 3. Existing domain records and mapping constraints

### Pharmacy-scoped inventory

`Inventory` is the current pharmacy-scoped lot/balance record. Its natural uniqueness is `(product_id, pharmacy_id, lot_number)`; it also has a composite identity constraint on `(id, pharmacy_id, product_id)`.

`InventoryMovement` is the append-only movement journal. It has a pharmacy-scoped idempotency key, a composite foreign key tying inventory/pharmacy/product together, before/after quantity and reservation balances, movement-type/delta invariants, actor identity and optional business reference/correlation fields.

Central application must preserve these constraints and create movement facts, not overwrite a replicated quantity.

### POS projection

The current `Sale`, `SaleItem`, `SaleItemAllocation` and `Payment` models persist sale, line, allocation and payment state. Sale and payment idempotency constraints are scoped to their parent records/pharmacy.

The Edge event payload carries `product_sku`, `lot_number` and allocation quantity, not the Edge `product_id` or `inventory_id`. Central therefore needs an explicit pharmacy-scoped SKU crosswalk and lot-resolution rule before it can safely resolve each line to a Central product and inventory lot.

Do not assume SKU is globally unique. Do not resolve a lot by `lot_number` alone. Resolution must identify exactly one active Central product for the authenticated pharmacy and exactly one compatible lot under that product/pharmacy scope. Missing or ambiguous mappings are quarantined; never create a product or lot implicitly from a sale event.

The event does not include the Edge cashier's user ID as a Central identity. Do not copy a local integer user ID into `cashier_user_id`. Define auditable actor mapping or a distinct source-originated sale projection before creating Central sale rows.

### Legacy and patient-oriented models

`ProductBatch` has no pharmacy scope and is not authoritative for Central FEFO or stock mapping. It must not be used by the consumer.

The legacy `Order` / `PatientPurchase` path is patient-oriented and is not a substitute for the POS sale/payment/lot model. Do not merge these aggregates or introduce patient identifiers into general POS synchronization.

## 4. Required Central consumer design

Before implementation, approve a bounded event-handler contract and then implement:

1. **Claim:** short transaction using `FOR UPDATE SKIP LOCKED`, eligible status and due retry time.
2. **Lease:** unique lease token, expiry, attempt number and fencing check on every completion/failure update. A stale worker must not commit after lease takeover.
3. **Ordering:** durable checkpoint keyed by `(pharmacy_id, aggregate_type, aggregate_id)`. Apply only the next expected version. Retain future versions as pending; do not advance across a gap.
4. **Idempotency:** event ID and aggregate version remain unique. A repeated identical event is a no-op; same identity with different content is a protocol conflict.
5. **Atomic application:** in one database transaction, lock the Inbox row/checkpoint, validate mappings and business invariants, write sale/payment projection and inventory movement facts, update balance projection, advance checkpoint, and mark the event processed.
6. **Failure handling:** transient database/worker failures retry with bounded exponential backoff and jitter. Permanent mapping/domain conflicts enter quarantine with structured reason codes and durable operator audit. Replay retains original event ID and payload.
7. **Reconciliation:** compare Edge-originated sale/payment and movement references with Central projections; report missing, duplicate, unmapped and mismatched records without silently changing balances.
8. **Observability:** measure oldest accepted/pending age, backlog, attempts, lease expirations, gap age, quarantine count, replay outcomes and per-pharmacy acknowledgement lag. Never log raw payloads or patient data.

## 5. Release gates before any domain side effects

- [ ] Pharmacy-scoped product/SKU crosswalk with uniqueness and lifecycle rules.
- [ ] Deterministic lot resolution and expiry/lot conflict policy.
- [ ] Explicit actor provenance for Edge cashier identity; no fabricated Central user IDs.
- [ ] Agreed Central sale/payment projection and financial ledger semantics.
- [ ] Complete event contract for stock movement beyond POS allocations.
- [ ] Atomic transaction and concurrency tests for last-unit sales and duplicate events.
- [ ] Gap recovery, stale-lease fencing, worker crash and retry/quarantine tests.
- [ ] Replay audit and reconciliation tests.
- [ ] Synthetic multi-pharmacy integration tests on disposable PostgreSQL.
- [ ] Backup/restore and staged rollout/rollback runbooks.

## 6. Decision

**GO:** continue read-only contract/mapping design, build fixtures and tests, and implement worker infrastructure behind a disabled feature flag after domain contracts are approved.

**NO-GO:** do not apply accepted Inbox events to production sales, payments, inventory balances or patient records yet. Do not infer missing product/lot/actor mappings. Do not enable a consumer merely because the Inbox row is durable.

This gate preserves the durable-receipt boundary and avoids turning a transport acknowledgement into an unverified financial or stock posting.
