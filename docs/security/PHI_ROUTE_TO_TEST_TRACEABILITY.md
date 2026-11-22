# PHI Route-to-Test Traceability — Patient API

**Review date:** 2026-11-22  
**Source baseline:** `main` at `2616b4209fc037b1e4f1899b876478bf72258641`; historical findings are retained where explicitly labelled.  
**Scope:** patient API routes and patient-purchase read API. Source review only; tests were inspected but not executed by this document. No runtime or patient data was accessed.

## Purpose

This map connects each patient-facing route to its authorization boundary, data returned, test evidence currently present, and next required proof. It is not a security certification.

## Route evidence matrix

| Route | Current authorization / scope behavior | PHI or sensitive data surface | Existing test evidence | Current level | Required next proof |
|---|---|---|---|---|---|
| `GET /api/v1/patients/` | Active user; pharmacy scope resolved. Superuser may omit pharmacy and remain global. | `PatientSummaryResponse` allowlist: demographic/contact and loyalty summary fields; no clinical, insurance, consultation or purchase relations. | `tests/integration/endpoints/test_patients.py` has list/search/pagination tests; legacy fixture is superuser-oriented and does not prove ordinary-user two-tenant isolation. | L1 | Add persisted two-tenant tests using ordinary members; assert rows and counts cannot cross pharmacies. |
| `GET /api/v1/patients/statistics` | Active user; same scope resolver and superuser global behavior. | Tenant-level patient aggregates. | No route-specific tenant isolation test identified in inspected test set. | L1 | Verify all aggregate queries and test cross-tenant counts/aggregates. |
| `GET /api/v1/patients/phone/{phone}` | Active user; scope resolved; superuser may be global. | `PatientSummaryResponse`; no clinical/insurance/consultation/purchase relations. | No route-specific phone lookup tenant-negative test identified. | L1 | Two-tenant phone collision/lookup tests and ordinary-user authorization assertions. |
| `GET /api/v1/patients/{patient_id}` | Active user; scope resolved; superuser may be global. | `PatientSummaryResponse`; broad legacy `PatientResponse` is not the current standard route contract. | Integration happy-path/not-found tests exist; ordinary-user cross-tenant denial coverage remains incomplete. | L1 | Two-tenant allow/deny integration tests; assert the response field allowlist. |
| `GET /api/v1/patients/{patient_id}/ai-profile` | Non-superuser; explicit `pharmacy_id` and purpose; active membership and active patient ownership required. Superusers are denied. | Minimum AI context: `patient_id`, allergies and conditions. Allowed/denied metadata is written to `PHIAccessAudit`. | `tests/integration/test_ai_patient_profile_access.py` covers allowed, missing membership, cross-pharmacy denial and superuser denial. | L1 | Add audit-persistence failure injection and include this route in broader exact-commit tenant tests. |
| `POST /api/v1/patients/` | Superuser only; `pharmacy_id` optional. Omission can create a patient without pharmacy ownership. | Creates patient identifiers and patient record. | Integration create/duplicate/unauthorized cases exist; no explicit test that missing pharmacy scope is rejected. | L1 | Require explicit authorized tenant or separately approved unassigned-patient workflow; test null-owner rejection. |
| `PUT /api/v1/patients/{patient_id}` | Superuser only; scope optional; global update path possible when omitted. | Updates patient demographic fields. | Integration update tests exist; no two-tenant denial test identified. | L1 | Purpose-bound privileged update policy; two-tenant deny tests; audit event assertions. |
| `DELETE /api/v1/patients/{patient_id}` | Superuser only; scope optional; global soft-delete path possible when omitted. | Patient lifecycle state. | Integration soft-delete test exists; no two-tenant denial test identified. | L1 | Governed support permission, tenant-scoped delete tests, durable audit. |
| `POST /api/v1/patients/{patient_id}/visit` | Active user; scope resolved; superuser may be global. | Patient visit and linked commercial activity metadata. | No tenant-specific route test identified in inspected test set. | L1 | Two-tenant allow/deny tests; verify visit event minimization and audit. |
| `GET /patient-purchases/` | Superuser only; explicit `pharmacy_id` required; query joins `Patient` and filters by `Patient.pharmacy_id`. | Broader administrative purchase projection including product, lot, receipt, quantity and price fields; no new PHI read-audit event in this handler. | `tests/unit/test_patient_purchases_scope.py` checks query construction with mocks, not persisted two-tenant behavior. | L1 | Govern and audit this privileged route; add database-backed authorization/audit tests or replace it with a narrower admin contract. |

| `GET /api/v1/patient-purchases/{patient_id}/history` | Non-superuser pharmacist; explicit `pharmacy_id` and purpose; active membership and active patient ownership required. Superusers are denied. | Minimum fields only: purchase ID, product name, category, quantity and timestamp. Allowed/denied metadata is written to `PHIAccessAudit`. | `tests/integration/test_patient_history_tenant_scope.py` covers allowed, cross-pharmacy denial, missing membership, null-owner denial and superuser denial. | L1 | Add audit-persistence failure injection and retain exact-commit CI evidence. |

## Cross-cutting observations

1. `resolve_pharmacy_scope` remains a tenant resolver, not a complete PHI policy. General patient/order routes still allow a global superuser scope and do not uniformly require purpose-of-use or durable read auditing.
2. The global superuser path is intentional in current source and tests. The new pharmacist AI-profile/history routes explicitly deny superusers; general patient/order and legacy administrative paths still require a separately governed, time-bounded, reason-coded support-access policy.
3. `Patient.pharmacy_id` is nullable. Superuser patient creation can still omit pharmacy scope and create an unowned record. The new pharmacist history route fails closed for such records; do not infer ownership during remediation.
4. Standard patient routes now use `PatientSummaryResponse`, and the AI-profile/history routes have narrower projections. Keep the broad legacy `PatientResponse` out of route contracts and continue reviewing all response DTOs.
5. Unit tests that inspect generated SQL are useful query-shape evidence, but they do not prove database-backed isolation, transaction behavior, or API denial semantics. The new route-specific PostgreSQL integration tests provide stronger evidence for the two scoped routes only; they do not cover every patient/order/admin read path.

## Test-fixture limitation confirmed

The shared `authenticated_client` fixture in `tests/integration/conftest.py` authenticates as a superuser and the generic patient endpoint tests still primarily exercise that privileged path. The newer route-specific tests create an ordinary pharmacist principal, active pharmacy membership and tenant-owned patient fixtures; they cover AI-profile and pharmacist-history route behavior. These targeted tests do not establish ordinary-user tenant isolation for every general patient/order route. The fixture is not evidence that Production contains unowned patients.

Before using these tests as tenant-isolation evidence, add distinct ordinary users, two persisted pharmacies, active memberships, tenant-owned patient fixtures, and explicit null-owner fixtures. Assert allowed access within the same pharmacy, denied/not-found behavior across pharmacies, denied access to null-owner records, and no cross-tenant leakage through list counts, search, phone lookup, AI profile or purchases.

## Follow-up source review — 2026-11-22

`PHIAccessAudit` is an append-only metadata-only table enforced by Alembic triggers against UPDATE, DELETE and TRUNCATE. `tests/integration/test_phi_access_audit_immutability.py` exercises these operations and the migration's refusal to remove retained evidence. This is implementation evidence, not a claim that every PHI access path writes an audit event. The legacy administrative purchase listing and general patient/order reads remain outside complete purpose-bound audit coverage.

## Evidence maturity rules for this map

- Source and test-file presence alone do not exceed L1 until the relevant tests have passed on the exact commit and their artifacts are recorded.
- L2 requires current exact-commit unit-test results.
- L3 requires database-backed/API integration tests with two tenants, positive and negative assertions, null-owner behavior and audit failure behavior.
- L4 requires complete browser/API workflows with durable outcome and audit assertions.
- No route is L5 or L6 based on this source review.

## P0 acceptance criteria

- [ ] All routes have explicit tenant and permission policy, including superuser/support behavior.
- [ ] Missing or ambiguous patient ownership fails closed for pharmacy workflows.
- [ ] Patient create cannot silently create a PHI record with null tenant ownership.
- [ ] Purpose-specific response DTOs exclude unrelated clinical/commercial fields.
- [ ] Allowed and denied PHI access is durably audited without PHI payloads.
- [ ] Audit storage is append-only for the application role and failure behavior is tested.
- [ ] Two-tenant integration tests cover every route above, including AI profile and patient purchases.
- [ ] Synthetic fixtures only; no real patient data in tests or Demo.

**Conclusion:** the current source contains meaningful tenant-aware controls, but the patient-facing route set is not yet proven end-to-end isolated or fully governed. Keep the affected PHI workflow below L3 until database-backed two-tenant integration evidence exists.
