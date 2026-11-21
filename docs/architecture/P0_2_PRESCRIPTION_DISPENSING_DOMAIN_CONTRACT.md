# P0.2 — Patient, Prescription and Dispensing Domain Contract

**Status:** proposed domain contract; implementation not started  
**Source baseline:** `main` at `7a1534e0dd3442480a9956c16ff414a64310c41a` (2026-11-21)  
**Scope:** canonical patient/prescription/sale linkage, pharmacist authorization, dispensing ledger, transaction semantics and acceptance tests.

This document is a design gate for P0.2. It is not evidence that prescription dispensing is implemented, clinically validated, legally compliant in any jurisdiction, or production-ready.

## 1. Verified baseline and gaps

The source audit found:

- `Patient.pharmacy_id` is nullable and is not a sufficient authorization proof by itself.
- `Prescription` has a patient, optional product, globally unique prescription number, free-text dosage/instructions, status and issue/expiry timestamps. It has no pharmacy ownership field, normalized prescription lines, authorized quantity, refill accounting or dispense ledger. The global uniqueness constraint may be too broad for external prescription identifiers reused across pharmacies; do not change it to tenant-scoped uniqueness until issuer namespace and jurisdiction semantics are defined.
- The prescription-to-patient foreign key currently uses `ON DELETE CASCADE`. A patient hard-delete can therefore erase prescription history. P0.2 migration must replace this with an explicitly approved retention-safe policy and verify all dependent delete paths; do not rely on ORM soft-delete alone as the only retention control.
- The existing prescription record uses `issued_at` and `expires_at`; the MCP verification implementation reads `date_issued` and `date_expires`, and reads `prescriber_name`, which is not present on the model. Its current item collection is deliberately empty. Existing unit tests construct matching `SimpleNamespace` fixtures and therefore do not prove model-to-database integration.
- The privileged prescription CRUD in `api/v1/pharmacy_entities.py` requires `CurrentSuperuser`; it is not a pharmacist workflow. A separate `endpoints/prescriptions.py` router is a placeholder.
- `Sale` has pharmacy and cashier ownership, but no patient reference. `SaleItem` links to product and inventory allocations, but not to a prescription line.
- POS checkout already has PostgreSQL transaction boundaries, tenant membership checks, FEFO lot allocation, inventory movement journaling, payment reservation/settlement, outbox events and idempotency. P0.2 must extend these contracts, not bypass them.
- Pending-payment cancellation exists. A completed-sale return/refund/reversal workflow is not established by the inspected POS API.
- The current pharmacy model does not expose a trusted regulatory jurisdiction. Patient residence or an AI-generated country must never be used as a substitute.

## 2. Domain invariants

1. A patient, prescription, prescription line, sale and dispense record must resolve to the same authorized pharmacy.
2. A client-supplied patient, prescription, product or pharmacy ID is a selector, never proof of authorization.
3. Ordinary pharmacist access requires an authenticated active pharmacy membership. Platform superuser access is not a substitute for the pharmacist dispensing workflow.
4. New prescriptions must be created with explicit server-validated pharmacy ownership. Legacy prescriptions with unresolved pharmacy ownership remain inaccessible to ordinary pharmacists until reconciled.
5. A prescription cannot be dispensed when patient identity, status, expiry, medication identity, strength, dosage form, quantity, refill allowance or applicable configured policy cannot be validated.
6. Product matching is deterministic and based on normalized medication identity plus strength and dosage form. A reference-drug match alone does not make a local product sellable or legally substitutable.
7. An override is a pharmacist action requiring a dedicated permission, a bounded reason code, free-text rationale where policy requires it, and immutable audit evidence. AI cannot grant the permission or authorize dispensing.
8. Every dispensed quantity must be traceable to a prescription line, sale item, inventory lot allocation, pharmacist, timestamp and outcome.
9. No dispense quantity may be counted twice across concurrent requests, retries, payment callbacks or multiple application instances.
10. Historical clinical and dispense evidence must not disappear through cascading patient deletion. Retention and anonymization must be explicit.

## 3. Proposed canonical relationships

### Prescription header

Retain `Prescription` as the header and add:

- pharmacy ownership (nullable only for legacy rows during migration);
- issuer/prescriber identity and source/provenance fields;
- explicit issue and expiry timestamps with consistent timezone semantics;
- controlled lifecycle status (for example: draft, active, on_hold, cancelled, expired, exhausted);
- jurisdiction/policy reference only when sourced from trusted pharmacy configuration;
- created/verified actor references and timestamps.

Do not store a single product as the complete prescription. Preserve the existing `product_id` only as a legacy compatibility field until its consumers are migrated.

### Prescription lines

Introduce `PrescriptionLine` with:

- prescription header reference;
- normalized medication identity (reference identifier where available) and immutable name snapshot;
- optional explicitly prescribed local product reference;
- prescribed strength and dosage form snapshots;
- quantity per authorized fill and unit of measure;
- authorized refill count and explicit fill-cycle policy;
- directions/instructions and clinically relevant route/frequency fields where supported;
- line status and timestamps.

A product may be resolved at dispense time only through a deterministic policy. Do not infer substitution from similarity or AI output.

### Sale and sale items

- Add optional patient ownership to `Sale`; enforce that every prescription-backed line in one sale belongs to that same patient and pharmacy.
- Add an optional prescription-line reference to `SaleItem`. OTC items may remain unlinked.
- When a prescription line is supplied, derive/validate patient and pharmacy ownership from the persisted prescription; do not trust a client-supplied patient association.
- Preserve the existing FEFO lot allocations as the inventory trace. A prescription dispense must reference the sale item whose allocations identify the actual lots.
- Update request idempotency comparison to include patient and prescription-line associations, not just product and quantity.

### Dispense ledger

Introduce a durable `PrescriptionDispense` ledger linking one prescription line to one sale item and recording:

- quantity and unit;
- fill-cycle number;
- pharmacy, pharmacist/actor and timestamps;
- idempotency key;
- lifecycle state (reserved, dispensed, released, reversed);
- reason code and reference to any correction/reversal.

The ledger is the source of truth for fulfilled quantity and refill-cycle use. Any cached counters on prescription lines are projections only and must be reconciled from ledger entries. Do not delete dispense history to undo a transaction.

A separate append-only transition/audit record must capture every state transition, actor, reason and correlation reference. Do not put clinical payloads into generic logs or outbox events.

## 4. State and transaction semantics

| Event | Inventory effect | Dispense ledger effect | Sale/payment effect |
|---|---|---|---|
| Cash checkout accepted | FEFO stock decrement in transaction | Create dispensed ledger entry | Sale completed; cash payment succeeded |
| External-payment checkout | FEFO stock reservation | Create reserved ledger entry | Sale awaiting payment; payment pending |
| Signed payment success | Commit reserved stock decrement | Reserved → dispensed | Sale completed; payment succeeded |
| Signed payment failure | Release reserved stock | Reserved → released | Sale cancelled; payment failed |
| Pending-sale cancellation | Release reserved stock exactly once | Reserved → released | Sale cancelled |
| Completed-sale correction/reversal | Only an explicitly authorized inventory compensation, if policy permits | Append reversal/correction evidence; never erase original dispense | Separate audited sale correction/refund workflow |

Prescription-line row locks must be acquired in deterministic ID order before calculating remaining quantity or refill availability. Inventory rows must continue to be locked in deterministic order. The sale, payment, dispense ledger, inventory movement journal and outbox event must commit in one PostgreSQL transaction for synchronous checkout and payment settlement.

Use a pharmacy-scoped idempotency key for dispense requests and a database uniqueness constraint as the final duplicate guard. On transaction failure, all related writes roll back together. For any future multi-service operation, document and test the saga/compensation contract rather than claiming database atomicity across services.

Partial dispensing is represented by multiple ledger entries within the same authorized fill cycle. A later refill cycle must not begin until the configured policy says the prior cycle is complete and the refill is authorized. The exact rule is policy-driven; do not assume one universal legal rule.

## 5. Authorization and validation boundary

- Resolve active pharmacy membership on the server for every read and write.
- Validate the patient with a pharmacy-scoped SQL predicate before loading prescription or clinical context.
- Validate prescription header and every line against the same pharmacy and patient.
- Validate status, issue/expiry, medication identity, strength, dosage form, quantity remaining, fill cycle, refill allowance and product sellability.
- Fail closed when the pharmacy jurisdiction or applicable rule set is missing, stale or unsupported.
- Do not rely on the MCP `verify_prescription` result as an authorization token or dispensing command. It is advisory and must be corrected/tested independently against the canonical model.
- Keep the pharmacist as the final accountable decision-maker. AI may explain checks and cite sources but cannot approve an exception, mutate prescription state or dispense.

## 6. Migration and compatibility strategy

1. Add new nullable pharmacy ownership and normalized line/ledger tables without inventing ownership for historical records.
2. Backfill prescription pharmacy ownership only from an unambiguous, existing patient-to-pharmacy relation. Keep unresolved rows explicitly unassigned and inaccessible to ordinary pharmacists.
3. Preserve the existing prescription number and free-text fields during migration; do not reinterpret old dosage text as structured quantity, strength or form.
4. Replace the patient foreign-key cascade with a retention-safe restriction only after confirming deletion paths and data-retention policy. Historical prescriptions and dispense evidence must not be silently deleted.
5. Preserve old privileged endpoints temporarily, but do not expose them to pharmacist roles. Migrate consumers to purpose-bound, tenant-scoped contracts.
6. Do not make a migration depend on production data assumptions. Test upgrade and downgrade behavior on clean PostgreSQL and a synthetic legacy dataset containing both assigned and unassigned patients.
7. Do not change or deploy the production database as part of source-level implementation work.

## 7. Required API behavior

The implementation should provide pharmacist-facing, versioned contracts for:

- listing and reading prescriptions within the authenticated pharmacy and patient scope;
- creating/importing a prescription with provenance and validated ownership;
- reading prescription lines and remaining authorized quantities;
- validating a prescription for a proposed dispense (read-only, advisory result);
- creating a dispense through the POS transaction boundary;
- recording a permissioned, reason-coded override;
- cancelling/releasing a pending dispense;
- recording a correction or reversal without deleting historical evidence.

The POS checkout contract must remain backward-compatible for ordinary OTC sales. Prescription-backed checkout must be explicitly identified and validated server-side. Do not enable the prescription workflow in the browser until these API and database gates pass.

## 8. Acceptance tests

Run against PostgreSQL with synthetic data, not mocks alone:

- Patient A prescription cannot be used for Patient B.
- Pharmacy A cannot read or dispense Pharmacy B prescriptions by changing IDs, filters or pagination.
- Missing/unassigned legacy pharmacy ownership fails closed.
- Inactive membership and superuser-only access paths are rejected for pharmacist dispensing.
- Expired, cancelled, on-hold, exhausted or otherwise invalid prescriptions are rejected.
- Product, medication identity, strength or dosage-form mismatch is rejected.
- Quantity above the remaining authorized amount is rejected.
- Refill beyond the authorized count or before the configured fill-cycle condition is rejected.
- Partial dispense updates the correct remaining quantity and does not consume an extra refill.
- Two concurrent attempts for the last authorized units cannot over-dispense.
- Cash checkout creates exactly one dispense and one inventory decrement.
- External-payment checkout reserves exactly once; signed success commits once; failure/cancellation releases once.
- Duplicate request and duplicate webhook are idempotent; reuse of a key with a different payload returns conflict.
- Transaction rollback leaves no orphan sale, dispense, movement or outbox event.
- Override requires permission and reason and produces immutable audit evidence.
- Reversal/correction preserves the original ledger and produces a compensating record.
- Prescription and dispense history survives prohibited patient deletion paths.
- No AI/MCP tool can authorize or perform dispensing.

## 9. Release evidence labels

Track each capability independently as **Designed**, **Implemented**, **Tested**, **Staged-validated** or **Production-validated**. Passing model tests or merging the PR does not establish a complete pharmacist workflow or production readiness.

## 10. Explicit non-goals

- No country-specific legal rule is asserted by this contract.
- No automatic therapeutic substitution or AI clinical authorization.
- No migration or repair of real patient data without a separately approved reconciliation plan.
- No production database changes, payment-provider configuration or deployment.
