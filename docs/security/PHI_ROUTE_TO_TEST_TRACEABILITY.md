# PHI Route-to-Test Traceability — Patient API

**Review date:** 2026-11-21  
**Source baseline:** `main` PHI audit baseline `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`  
**Scope:** patient API routes and patient-purchase read API. Source review only; tests were inspected but not executed by this document. No runtime or patient data was accessed.

## Purpose

This map connects each patient-facing route to its authorization boundary, data returned, test evidence currently present, and next required proof. It is not a security certification.

## Route evidence matrix

| Route | Current authorization / scope behavior | PHI or sensitive data surface | Existing test evidence | Current level | Required next proof |
|---|---|---|---|---|---|
| `GET /api/v1/patients/` | Active user; pharmacy scope resolved. Superuser may omit pharmacy and remain global. | Patient list fields including name, phone, email, location and loyalty data. | `tests/integration/endpoints/test_patients.py` has list/search/pagination tests; no two-tenant isolation assertion was identified in the inspected cases. | L1 | Two-tenant persisted-data integration tests; assert no cross-tenant rows and counts. |
| `GET /api/v1/patients/statistics` | Active user; same scope resolver and superuser global behavior. | Tenant-level patient aggregates. | No route-specific tenant isolation test identified in inspected test set. | L1 | Verify all aggregate queries and test cross-tenant counts/aggregates. |
| `GET /api/v1/patients/phone/{phone}` | Active user; scope resolved; superuser may be global. | Returns broad `PatientResponse`. | No route-specific phone lookup tenant negative test identified. | L1 | Two-tenant phone collision/lookup tests; purpose-specific response DTO contract. |
| `GET /api/v1/patients/{patient_id}` | Active user; scope resolved; superuser may be global. | Returns broad `PatientResponse`, including conditions, treatment notes, allergies, insurance, consultations and purchases. | Integration happy-path/not-found tests exist; no cross-tenant denial test identified in inspected cases. | L1 | Two-tenant allow/deny integration tests; field allowlist tests for detail DTO. |
| `GET /api/v1/patients/{patient_id}/ai-profile` | Active user; scope resolved; superuser may be global. | Patient profile assembled for AI context. | No route-specific tenant isolation test identified in inspected test set. | L1 | Cross-tenant denial tests; verify only approved minimum-necessary fields reach AI context. |
| `POST /api/v1/patients/` | Superuser only; `pharmacy_id` optional. Omission can create a patient without pharmacy ownership. | Creates patient identifiers and patient record. | Integration create/duplicate/unauthorized cases exist; no explicit test that missing pharmacy scope is rejected. | L1 | Require explicit authorized tenant or separately approved unassigned-patient workflow; test null-owner rejection. |
| `PUT /api/v1/patients/{patient_id}` | Superuser only; scope optional; global update path possible when omitted. | Updates patient demographic fields. | Integration update tests exist; no two-tenant denial test identified. | L1 | Purpose-bound privileged update policy; two-tenant deny tests; audit event assertions. |
| `DELETE /api/v1/patients/{patient_id}` | Superuser only; scope optional; global soft-delete path possible when omitted. | Patient lifecycle state. | Integration soft-delete test exists; no two-tenant denial test identified. | L1 | Governed support permission, tenant-scoped delete tests, durable audit. |
| `POST /api/v1/patients/{patient_id}/visit` | Active user; scope resolved; superuser may be global. | Patient visit and linked commercial activity metadata. | No tenant-specific route test identified in inspected test set. | L1 | Two-tenant allow/deny tests; verify visit event minimization and audit. |
| `GET /patient-purchases/` | Superuser only; explicit `pharmacy_id` required; query joins Patient and filters by its pharmacy. | Patient-linked purchase, product, lot, quantity, price and prescription-required metadata. | `tests/unit/test_patient_purchases_scope.py` asserts compiled SQL using mocks, not persisted two-tenant data. | L1 | Integration test with two persisted pharmacies; assert cross-tenant rows are absent and authorization/audit behavior is correct. |

## Cross-cutting observations

1. `resolve_pharmacy_scope` is a tenant resolver, not a complete PHI policy. It does not require purpose-of-use, a patient-specific permission, or a durable access-audit event.
2. The global superuser path is intentional in current source and tests. Do not silently remove it; replace it with a separately granted, time-bounded, reason-coded and audited support-access policy.
3. `Patient.pharmacy_id` is nullable. Patient creation without an explicit pharmacy scope can create an unowned record. Do not infer ownership during remediation.
4. The broad `PatientResponse` should be split into workflow-specific DTOs with explicit field allowlists.
5. Unit tests that inspect generated SQL are useful query-shape evidence, but they do not prove database-backed isolation, transaction behavior, or API denial semantics.

## Test-fixture limitation confirmed

The integration fixture `authenticated_client` in `tests/integration/conftest.py` always authenticates as `is_superuser=True`. Its `PatientFactory.create()` does not set `pharmacy_id` unless a test explicitly overrides it. Therefore the existing patient endpoint integration tests primarily exercise a global superuser against unowned patient rows; they do not demonstrate ordinary-user tenant isolation. This is stronger than a missing assertion: the fixture setup itself does not model two distinct pharmacy tenants. The fixture is not evidence that Production contains unowned patients.

Before using these tests as tenant-isolation evidence, add distinct ordinary users, two persisted pharmacies, active memberships, tenant-owned patient fixtures, and explicit null-owner fixtures. Assert allowed access within the same pharmacy, denied/not-found behavior across pharmacies, denied access to null-owner records, and no cross-tenant leakage through list counts, search, phone lookup, AI profile or purchases.

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
