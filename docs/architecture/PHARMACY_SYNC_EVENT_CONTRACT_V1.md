# Pharmacy Synchronization Event Contract v1

**Status:** Partially implemented; production acceptance is not established.  
**Scope:** Pharmacy Edge to Central event delivery.

The repository currently implements a transactional POS outbox, a Celery dispatcher, per-node Edge enrollment/revocation, and durable Central Inbox receipt. It does **not** yet implement the Central domain-event consumer, inventory/finance application, gap recovery, quarantine/DLQ operations, or end-to-end reconciliation. The contract below distinguishes the current v1 wire format from target protocol requirements.

## 1. Delivery guarantees

The protocol uses **at-least-once transport** and **effectively-once business effects**:

- Edge commits the business transaction and its outbox event in one local PostgreSQL transaction.
- A dispatcher may send an event more than once after timeouts, process restarts or lost acknowledgements.
- Central persists the event in an inbox protected by a unique constraint on `event_id`.
- Central currently acknowledges only after the inbox row is committed. `accepted` means durable receipt, not that a domain handler applied the event.
- Duplicate delivery returns the original durable acknowledgement and must not reapply business effects.
- Neither Redis/Valkey nor an in-memory queue is the source of truth.

Exactly-once network delivery is not promised.

## 2. Required event envelope

The table describes the **target** immutable envelope. The current v1 wire envelope contains: `event_id`, `edge_node_id`, `event_type`, `schema_version`, `aggregate_type`, `aggregate_id`, `aggregate_version`, `occurred_at`, and `payload`. Central derives `pharmacy_id` from the authenticated Edge registration. `recorded_at`, `correlation_id`, `causation_id`, and `idempotency_key` are not currently transmitted.

The target envelope fields are:

| Field | Type | Contract |
|---|---|---|
| `event_id` | UUID | Globally unique and stable across every retry. |
| `event_type` | string | Namespaced domain event, e.g. `pos.sale.created`. |
| `schema_version` | positive integer | Version of this event payload contract. |
| `pharmacy_id` | stable ID | Pharmacy/site scope assigned by Central; never trusted from an unverified client claim. |
| `edge_node_id` | stable ID | Registered Edge installation identity; not a hostname or mutable IP address. |
| `aggregate_type` | string | Domain stream type, e.g. `sale`, `inventory_item`. |
| `aggregate_id` | string | Stable identifier within the pharmacy scope. |
| `aggregate_version` | positive integer | Strictly increasing sequence within one aggregate stream. |
| `occurred_at` | UTC timestamp | Edge-reported business event time; informational, not a global ordering authority. |
| `recorded_at` | UTC timestamp | Edge database persistence time. |
| `correlation_id` | UUID/string | Groups events belonging to one workflow. |
| `causation_id` | UUID/string or null | Event/command that directly caused this event. |
| `idempotency_key` | string | Stable command key where the originating operation supports replay protection. |
| `payload` | object | Event-specific, versioned, data-minimized domain facts. |

Current implementation detail: the outbox persists event identity, pharmacy scope, event type/schema, aggregate identity/version, payload and timestamps. The dispatcher adds the registered `edge_node_id` to the wire envelope. It does not yet persist correlation/causation metadata or a command-level idempotency key. Do not treat the target-only fields in the table as present in the current v1 payload.

## 3. Identity and authentication

- Central is the authority for pharmacy/site registration and Edge-node enrollment.
- Every Edge installation receives a unique node identity and its own revocable credential or certificate.
- Current implementation: each enrolled node receives a random high-entropy bearer credential; only its SHA-256 digest is stored, and the credential can be revoked. The dispatcher requires HTTPS and sends the token in `X-Edge-Token`.
- Not yet implemented: mTLS, automated credential rotation/overlap, and certificate lifecycle management.
- Derive the authorized pharmacy scope from the authenticated node registration. Reject an event whose claimed `pharmacy_id` does not match that registration.
- Never ship one fleet-wide static secret in an image, Ansible defaults or source control.
- A revoked node must not be able to submit new events. Credential rotation and overlap controls remain a production-hardening requirement.
- Ansible provisions the identity material securely; the application validates it and enforces event authorization.

## 4. Ordering and inbox processing

The dispatcher currently prevents a later unpublished version from being sent while an earlier version for the same aggregate remains unpublished. Central rejects duplicate aggregate versions, but it does not yet enforce the next expected version or run a domain consumer. The following describes the **target** inbox-processing semantics, not current behavior:

1. Central validates the envelope, node identity, pharmacy scope and supported schema version.
2. Central inserts the raw event into a durable inbox with a unique `event_id`.
3. If the ID already exists, Central returns the stored acknowledgement without reapplying the event.
4. The consumer checks the next expected `aggregate_version`.
5. A future version arriving before a missing predecessor is retained as pending; it is not applied out of order.
6. A duplicate version with a different event ID is a protocol conflict and must be quarantined for investigation.
7. The event is applied through a domain handler and the processing result/checkpoint is committed atomically with the inbox state.
8. Central acknowledges durable acceptance/processing state; the acknowledgement must identify whether the event is accepted, pending, rejected or quarantined.

Do not impose global ordering across pharmacies. Do not use client clocks to resolve inventory or financial conflicts.

## 5. Dispatcher and retry contract

- Claim eligible outbox rows in a short database transaction using row-level locking (PostgreSQL `FOR UPDATE SKIP LOCKED`).
- Use a unique lease token plus lease expiry. Only the worker holding the current token may update the row after delivery.
- Perform HTTP/network I/O outside the database transaction.
- Mark an event delivered only after a durable Central acknowledgement.
- Current implementation retries HTTP errors and unsuccessful HTTP responses using exponential backoff with jitter and a one-hour maximum exponential component. This includes permanent 4xx responses, so invalid credentials/schema/scope can remain in retry indefinitely.
- Not yet implemented: permanent-error classification, dead-letter/quarantine workflow, operator replay endpoint, or alerting for poison events.
- Preserve failed events for inspection and controlled replay. Replay must retain the original `event_id`.
- Track oldest pending event age, backlog count, attempts, last error, last successful sync and per-site acknowledgement lag. These sync-specific operational metrics/dashboards are not yet implemented.

## 6. Domain conflict policy

Never resolve pharmacy stock, sales, payments, dispensing or audit conflicts with last-write-wins.

- A pharmacy Edge is authoritative for its own committed local sale and local stock ledger entries.
- Central builds a consolidated, eventually consistent view from accepted events.
- Stock changes are append-only ledger facts with unique operation IDs; a derived quantity is not an overwriteable replicated field.
- Cross-pharmacy transfers require explicit source reservation/dispatch and destination receipt events.
- Central catalog and policy updates are versioned commands/configuration snapshots with an applied-version acknowledgement from each Edge.
- A stale catalog/policy version must be visible to the operator and must follow a configured restriction policy.
- Events that violate domain invariants are quarantined; do not silently mutate stock to make totals match.

## 7. Data minimization and privacy

- Do not include patient names, phone numbers, addresses, full prescription contents or other direct identifiers in general-purpose synchronization telemetry.
- Prefer opaque references and only the minimum domain facts needed by the receiving workflow.
- Patient/prescription synchronization requires a separately approved authorization, access-control, encryption, retention and audit design.
- Logs, traces, metrics and error messages must not serialize event payloads containing patient or prescription data.
- Keep event payload schemas allow-listed and validated; reject unexpected fields where practical.

## 8. Compatibility and schema evolution

- Event types are versioned independently of application releases.
- Additive optional fields may be introduced only when old consumers safely ignore them.
- Breaking changes require a new schema version and a documented compatibility window.
- Central must advertise supported event types/schema versions to enrolled Edge nodes.
- Edge must not emit an unsupported schema version; retain events locally until a compatible route is available.
- Database migrations use expand/contract. Do not delete old columns or handlers while supported Edge versions can still emit/read the old contract.

## 9. Required failure tests before production

- WAN loss before send, during send and after Central commit but before acknowledgement.
- Edge process restart with pending and leased events.
- Central restart after inbox insert and before domain application.
- Duplicate delivery, duplicate event ID with altered payload, and duplicate aggregate version.
- Out-of-order aggregate versions and missing predecessor recovery.
- Expired lease takeover and stale worker acknowledgement.
- Credential expiry, rotation, revocation and cross-pharmacy scope forgery.
- Unsupported schema version and malformed payload.
- Disk-full/database-unavailable conditions on Edge.
- Replay after operator remediation without duplicate business effects.
- Long disconnection followed by backlog catch-up without starving live traffic.

## 10. Implementation gates

Do not enable a production dispatcher until all are true:

1. Registered Edge identity and per-node authentication are implemented.
2. Event envelope and payload schemas are validated and versioned.
3. Central inbox has durable deduplication, ordering and quarantine semantics.
4. Domain handlers are idempotent and use ledger semantics for inventory/finance.
5. Dispatcher leases, retries, acknowledgements and replay are tested.
6. The offline capability matrix is approved for the deployment jurisdiction and providers.
7. Observability, backup/restore and failure-injection tests pass in a lab environment.
