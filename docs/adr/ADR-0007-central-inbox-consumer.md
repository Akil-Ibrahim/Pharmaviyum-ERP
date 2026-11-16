# ADR-0007: Central Inbox Consumer and Ordered Domain Application

**Status:** Proposed — architecture defined; implementation blocked by domain prerequisites  
**Date:** 2026-11-16  
**Owners:** Pharmaviyum engineering

## Context

Pharmacy Edge currently writes POS events to its transactional outbox. The Edge dispatcher delivers them at least once to the Central API. Central authenticates the enrolled Edge identity, validates the v1 event contract, and commits a durable `CentralInboxEvent` receipt with `processing_status=accepted`.

There is no Central domain-event consumer in the current implementation. The Celery task `dispatch_outbox_batch` is an Edge-side outbox publisher; it is not a Central inbox consumer. A durable `accepted` acknowledgement therefore means receipt only, not application of a sale, payment or inventory effect.

The current inbox schema has event deduplication and aggregate-version uniqueness, but it does not yet have consumer leases, retry scheduling, attempt history, quarantine semantics or an applied-version checkpoint.

## Decision

Build a Central consumer as a separate application service and worker. Keep the HTTP ingress path limited to authentication, schema validation, durable receipt and acknowledgement. PostgreSQL remains the source of truth; Celery/Redis may wake or schedule the worker but must never own event durability or processing state.

The protocol provides **at-least-once delivery with idempotent business effects**. It does not claim exactly-once network delivery.

### 1. Processing state machine

Use the following durable states:

| State | Meaning |
|---|---|
| `accepted` | Inbox receipt committed; eligible for processing |
| `processing` | A worker has claimed the event with a fenced lease |
| `retry_wait` | A transient failure occurred; retry is scheduled |
| `processed` | All domain effects and the aggregate checkpoint committed atomically |
| `quarantined` | A permanent contract/domain conflict requires operator action |

Allowed transitions:

- `accepted -> processing`
- `retry_wait -> processing` when `next_attempt_at <= now()`
- `processing -> processed` only in the same transaction as all domain effects and checkpoint advancement
- `processing -> retry_wait` for transient failures
- `processing -> quarantined` for permanent domain/contract violations or exhausted retry policy
- expired `processing` leases may be reclaimed by a new worker; the old lease token must no longer authorize state changes

Do not mark a domain event processed before its effects commit. Do not delete poison events or silently skip them.

### 2. Durable claim and concurrency control

Extend `central_inbox_events` additively with bounded operational metadata:

- `attempt_count` (non-negative integer)
- `next_attempt_at` (UTC timestamp)
- `locked_until` (UTC timestamp, nullable)
- `lease_token` (random UUID/string, nullable)
- `last_attempt_at` and `processed_at` (UTC timestamps, nullable)
- `processor_version` (string, nullable, for audit/debugging)

Add a partial/compound index that supports polling due `accepted`/`retry_wait` events and expired `processing` leases. Keep `processing_error` bounded and redacted; never persist a full event payload, credentials, patient identifiers or provider secrets in error text.

Claim a bounded batch in a short transaction using PostgreSQL `FOR UPDATE SKIP LOCKED`. Assign a fresh lease token and expiry and increment the attempt count. The worker must re-check the current lease token after locking the inbox row before processing or changing its state. A stale worker must not acknowledge or reschedule a newer claim.

### 3. Aggregate ordering and gap recovery

Create a durable aggregate checkpoint keyed by:

`(pharmacy_id, aggregate_type, aggregate_id)`

The checkpoint stores the last successfully applied `aggregate_version` and the last applied `event_id`.

- A new aggregate starts at version 0; version 1 is the first applicable event.
- An event is eligible only when its version equals `last_applied_version + 1`.
- A later version with a missing predecessor remains pending/retryable; it is not applied out of order.
- A conflicting event for an already-used aggregate version is a protocol conflict and must be quarantined or rejected at ingress.
- Do not impose global ordering across pharmacies or unrelated aggregates.
- Advance the checkpoint in the same transaction as the domain effects and inbox `processed` transition.

The existing unique constraint on `(pharmacy_id, aggregate_type, aggregate_id, aggregate_version)` remains the final duplicate-version guard.

### 4. Atomic domain application

Each event is processed in one PostgreSQL transaction:

1. Lock the inbox event and verify its current lease token.
2. Lock/create the aggregate checkpoint and verify the expected next version.
3. Validate the event again at the domain boundary; ingress validation alone is not authorization to mutate business data.
4. Resolve every product by canonical SKU and every lot by the authenticated pharmacy, product and lot number. Never trust local Edge integer IDs.
5. Verify product/lot identity, expiry metadata and pharmacy scope. Unknown or ambiguous mappings are quarantined; never create a lot or product implicitly from a sale event.
6. Apply each stock/reservation delta through the shared `apply_inventory_movement` service.
7. Derive a deterministic, bounded movement idempotency key from `event_id` plus stable item/allocation positions. Use the event ID as the correlation reference.
8. Persist any Central sale/payment projection and advance the aggregate checkpoint.
9. Set the inbox state to `processed` and commit.

All allocation movements for one event, the sale/payment projection, checkpoint advancement and inbox completion must commit or roll back together. A crash before commit leaves no partial business effect. A retry after commit observes `processed` and creates no second effect.

Use `actor_type=system` for the Central integration actor when no Central user identity is present; preserve the source Edge node and event reference in correlation/reference metadata. Do not invent or reuse a Central cashier user for an Edge cashier.

### 5. Required domain prerequisites before enabling POS consumption

The current v1 contract is insufficient for safe stock projection:

- It emits sale creation, cancellation and payment events, but does not yet define a complete stream of goods receipts, adjustments, write-offs, returns, transfers and an approved opening-balance/snapshot baseline.
- A sale decrement must not be applied to a Central lot whose opening quantity is unknown or unverified.
- Product SKU and lot number are portable identifiers, but Central must have an explicit catalog/lot mapping policy and detect ambiguous or conflicting expiry metadata.
- The local `Sale` model requires a local `cashier_user_id`; the Edge contract intentionally does not transmit local numeric user IDs. Central reporting must use a separate source-aware sale projection (or a separately approved stable actor mapping), not fabricate a local cashier identity.
- Payment events must be reconciled against a Central sale/payment projection using receipt number, pharmacy scope and immutable event identity. Do not infer provider settlement from a client-supplied status alone.

Until these prerequisites are implemented and reconciled, keep Central Inbox in durable-receipt-only mode. Do not enable inventory or financial side effects.

### 6. Failure classification and quarantine

Retry transient infrastructure failures (database unavailable, deadlock, temporary dependency outage) with bounded exponential backoff and jitter.

Quarantine permanent failures, including unsupported schema/event type, impossible state transition, unknown/ambiguous product or lot mapping, pharmacy-scope mismatch, impossible balance transition and incompatible aggregate version. A missing predecessor is a version gap, not a poison event; keep it pending and alert when its age exceeds the operational threshold.

Operator replay must retain the original immutable `event_id` and payload. Corrections require a compensating/new event or an audited mapping fix; never rewrite a received event payload.

### 7. Operational requirements

Expose low-cardinality metrics and alerts for:

- inbox backlog count and oldest accepted/retry age;
- processing attempts, retries, quarantines and permanent failures;
- aggregate version gaps and gap age;
- processing latency and transaction failures;
- movement idempotency conflicts and unknown catalog/lot mappings;
- per-pharmacy accepted-to-processed lag.

Provide an operator workflow to inspect, resolve and replay quarantined events with RBAC and an audit trail. Do not expose raw payloads to general application logs or metrics.

## Alternatives considered

- **Apply domain effects inside the ingress request:** rejected because network acknowledgement latency, retry coupling and partial failures would make the API path fragile.
- **Use Redis/Celery as the durable queue:** rejected because PostgreSQL Inbox is the durable receipt and Redis loss must not lose events.
- **Mark processed before applying effects:** rejected because a crash would permanently lose business effects.
- **Last-write-wins or skip aggregate versions:** rejected because inventory and payment are financial/auditable facts.
- **Create missing products/lots from POS payloads:** rejected because an event is not an authoritative catalog or stock-receipt command.

## Implementation and acceptance gates

1. Approve the complete Edge-to-Central event inventory, including opening balance/snapshot and every stock-changing operation.
2. Define Central product/lot mapping and source-aware sale/payment projection models.
3. Add additive Inbox processing metadata and aggregate checkpoint migrations; inspect all Alembic heads first.
4. Implement the fenced, ordered consumer and deterministic event-to-movement idempotency mapping.
5. Add integration tests for duplicate delivery, concurrent workers, lease expiry/stale worker, out-of-order versions, missing predecessor recovery, unknown SKU/lot, cross-pharmacy mismatch, multi-allocation atomicity, injected rollback and replay after commit.
6. Reconcile Central inventory projections against Edge ledgers for a controlled test pharmacy.
7. Complete security, observability, backup/restore and failure-injection validation before a pilot.

**Production status:** Not implemented; Central Inbox remains receipt-only. No Central POS inventory/payment consumer may be enabled until all gates above pass.
