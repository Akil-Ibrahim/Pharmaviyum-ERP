# P0 Pharmacist Workspace — Implementation and Acceptance Gates

[English](./PHARMACIST_WORKSPACE_P0_ACCEPTANCE.md) · [Русский](./PHARMACIST_WORKSPACE_P0_ACCEPTANCE.ru.md)

**Status:** implementation backlog / acceptance contract  
**Scope:** P0 pharmacist-facing workflow and patient-data safety  
**Baseline:** `main` at `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`  
**Application code changed by this specification:** no

This document converts the source audit into testable P0 delivery gates. It does not claim that any item below is implemented.

## 1. P0.1 — Restore the POS user interface

### Existing evidence
- Transactional backend: `POST /api/v1/pos/checkout`, product search, lot lookup, payment webhook and standalone goods receipt.
- Integration coverage: `tests/integration/test_pos_checkout.py`.
- Current frontend entry: `frontend/shadcn-admin/src/routes/_authenticated/pos.tsx`.
- Current feature implementation: `frontend/shadcn-admin/src/features/pos/index.tsx`, which returns `null`.

### Required implementation
- Replace the null feature with a real cashier workflow using generated/typed API contracts; do not duplicate business rules in the browser.
- Product search must display product identity, strength, dosage form, barcode/SKU and authorized-pharmacy availability.
- Lot selection must show expiry and sellable quantity; backend remains authoritative for FEFO and stock eligibility.
- Cart changes must be validated server-side at checkout; client totals are display-only.
- Show payment state, receipt identity, pending/failed states and actionable recovery without creating duplicate sales.
- Disable repeated submission while a request is in flight, but rely on server idempotency for correctness.
- Keep patient/prescription capture disabled or explicitly marked unavailable until the clinical linkage gate in P0.2 is delivered; do not imply that a generic sale is a prescription-validated dispense.

### Acceptance gates
1. Playwright journey: search → select product → inspect lots → checkout cash → receipt visible → stock reflects committed movement.
2. Playwright journey: non-cash checkout → pending payment state → signed webhook settlement → completed sale and receipt.
3. Retry same idempotency key: one sale, one receipt identity, no duplicate inventory movement.
4. Last-unit concurrency: two cashier attempts cannot oversell; persisted stock and sale state reconcile.
5. Expired/ineligible lots cannot be sold; FEFO allocation is asserted against persisted rows, not just UI order.
6. API authorization and pharmacy scope are tested for every read and write.
7. Empty, loading, timeout, validation, payment failure and server error states are usable and accessible.
8. No real patient data is used in UI fixtures or screenshots.

**Exit criterion:** POS is a usable browser workflow against the real API contract, with automated browser + API/integration coverage. A rendered page or mock-only flow is insufficient.

## 2. P0.2 — Link patient, prescription and dispensing safely

### Existing evidence
- Patient, prescription and POS sale domain records exist independently.
- Checkout request does not currently establish patient/prescription linkage.
- Prescription frontend route returns `null`.
- No end-to-end prescription-to-checkout test was identified in the baseline.

### Required design before implementation
- Define the canonical relationship between sale, patient, prescription, prescription lines and dispensed sale lines. Avoid a single aggregate patient-purchase row as the only clinical trace.
- Resolve pharmacy ownership and patient identity server-side. A client-supplied patient ID is a selector, not authorization.
- Validate prescription status, patient match, pharmacy scope, medicine/product match, strength, dosage form, quantity, repeat/refill constraints, expiry and applicable local rules.
- Preserve pharmacist review/override as an explicit, permissioned, reason-coded and auditable decision. AI must never authorize dispensing.
- Persist who verified, what was dispensed, which prescription line was fulfilled, which lot was allocated, when it happened and the result.
- Define partial dispensing, cancellation, correction and reversal semantics before enabling the flow.
- Do not infer legal prescription rules from AI output; encode jurisdiction-specific rules as reviewed deterministic policy.

### Acceptance gates
1. Cross-patient prescription substitution is rejected.
2. Cross-pharmacy patient/prescription access is rejected.
3. Expired, cancelled, exhausted or otherwise invalid prescriptions are rejected according to configured policy.
4. Product, strength and dosage-form mismatch is rejected or requires a defined pharmacist exception flow.
5. Dispensed quantity cannot exceed authorized remaining quantity.
6. Partial dispensing and retry are idempotent and preserve a correct remaining balance.
7. Sale, prescription fulfilment, lot movement and audit event commit atomically or follow an explicitly tested saga/compensation contract.
8. Pharmacist override requires permission, reason and immutable audit evidence.
9. Tests cover race conditions, duplicate requests, rollback and tenant isolation.

**Exit criterion:** a complete patient → prescription → pharmacist verification → FEFO lot allocation → payment/receipt → patient history chain is reproducible and tested. AI remains decision support only.

## 3. P0.3 — Build a tenant-scoped patient-history API

### Existing evidence
- `GET /api/v1/patient-purchases/` requires `CurrentSuperuser`.
- The current query selects `PatientPurchase` directly; it does not join `Patient`, constrain `Patient.pharmacy_id` or accept a patient selector.
- `Patient.pharmacy_id` is nullable.
- The endpoint is a global administrative listing, not a pharmacist patient-history contract.

### Required implementation
- Keep the current global administrative endpoint inaccessible to ordinary pharmacist roles unless its purpose and authorization are explicitly redesigned.
- Add a separate patient-scoped API requiring authenticated pharmacy membership and a patient selector.
- Resolve patient membership on the server and constrain every returned purchase through the patient's authorized pharmacy scope.
- Define handling for legacy rows whose patient has null/unassigned pharmacy ownership; fail closed for ordinary pharmacist access until records are reconciled.
- Return only fields required for the pharmacist workflow; avoid exposing unrelated identifiers and financial details.
- Add an audit event for access to patient history, including actor, pharmacy, patient reference, purpose/context and timestamp, without copying clinical content into logs.
- Apply pagination, deterministic ordering, bounded date filters and response limits.

### Acceptance gates
1. Pharmacist in Pharmacy A can retrieve history only for a patient authorized in Pharmacy A.
2. Pharmacy A cannot enumerate or retrieve purchases for Pharmacy B patients by changing IDs, filters or pagination.
3. Unassigned/null-pharmacy patient records are not exposed to ordinary pharmacists.
4. Non-pharmacist and unauthenticated callers are denied according to RBAC policy.
5. Superuser administrative access is separately tested and audited.
6. Query plan uses patient/pharmacy indexes appropriate to the final query shape.
7. Negative cross-tenant tests run against PostgreSQL, not only mocked repositories.

**Exit criterion:** separate, explicit admin and pharmacist contracts; cross-tenant denial demonstrated by integration tests.

## 4. P0.4 — Complete staged Mortarium patient-session validation

### Existing evidence
- Patient-scoped API session HMAC v3 and Agent/RAG checkpoint namespaces were merged by PR #287.
- Regression tests exist.
- Architecture documentation explicitly keeps staged PostgreSQL checkpoint + Redis memory validation as a release gate.

### Required validation
Run in an isolated staging environment with synthetic patients and dedicated PostgreSQL/Redis:
1. Reuse one client session for Patient A → Patient B → no patient.
2. Repeat in synchronous and streaming API paths.
3. Verify Redis dialogue memory, summaries and derived facts do not cross scopes.
4. Verify Agent and RAG checkpoint threads remain distinct and contain no raw patient/user/pharmacy identifiers.
5. Verify cache entries cannot cross patient scopes.
6. Verify two application instances derive identical scopes with the same configured secret.
7. Verify missing/rotated secret behavior fails closed and follows documented rotation policy.
8. Verify logs, traces and evaluation artifacts contain no raw patient identifiers or clinical payloads.

**Exit criterion:** reproducible staged evidence attached to the release record. Merge and unit tests alone do not satisfy this gate.

## 5. Delivery order and dependencies

| Order | Work item | Dependency | Release gate |
|---:|---|---|---|
| 1 | P0.3 patient-history authorization contract | Patient/pharmacy ownership and legacy-row policy | Cross-tenant integration tests |
| 2 | P0.2 patient/prescription/dispense domain contract | Clinical policy and audit model | Prescription-to-sale invariants |
| 3 | P0.1 POS browser workflow | Existing POS API; P0.2 linkage before enabling prescription dispensing | Playwright + transactional tests |
| 4 | P0.4 Mortarium staged validation | Stable staging PostgreSQL, Redis and secret configuration | Patient-switch isolation evidence |

Parallelize only work that does not weaken the security boundary. Do not enable patient history or prescription dispensing in the UI before their corresponding gates pass.

## 6. Evidence and release reporting

For every gate record:
- commit SHA and environment;
- test command / workflow run URL;
- synthetic fixture design;
- expected and observed result;
- failures and remediation;
- reviewer and date.

Use precise evidence labels: **Designed**, **Implemented**, **Tested**, **Staged-validated**, **Production-validated**. Never upgrade a status based only on a route, model, passing unit test or merged PR.

No production deployment, real patient data access or application-code change is authorized by this document.

## Follow-up source audit — main 481a86aa

Current `main` includes PHI governance and Patient Repository pharmacy-scope predicates, with regression coverage. See [PHI access governance audit](../architecture/PHI_ACCESS_GOVERNANCE_AUDIT.md), [PHI read-surface inventory](../security/PHI_READ_SURFACE_INVENTORY.md), and `tests/unit/test_patient_repository_tenant_scope.py`. These changes do not replace P0.3: a dedicated pharmacist-facing history API still needs server-resolved pharmacy membership, fail-closed legacy-patient handling, minimal fields, read auditing, pagination, and PostgreSQL cross-tenant negative tests. Do not reuse the superuser-only global endpoint. Source audit only; not production validation.
