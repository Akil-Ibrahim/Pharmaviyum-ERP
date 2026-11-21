# PHI Read-Surface Inventory — Follow-up Source Review

**Review date:** 2026-11-21  
**Baseline:** `main` (reviewed against the current default branch; source files and blob SHAs are recorded in the PR discussion)  
**Scope:** targeted read-only review of patient API, patient service/repository, response schemas, MCP patient-history tool, order API, and in-process event bus. No database, runtime, production data, or secrets were accessed.

## Executive summary

This review expands the initial PHI governance audit. It identifies additional source-level risks that should be addressed before claiming complete tenant isolation or PHI access governance.

**No exploit or production disclosure is established by this review.** Some findings are latent repository-layer hazards whose call sites have not yet been exhaustively mapped. Treat them as verification targets, not confirmed externally reachable vulnerabilities.

## Findings

### F-01 — Repository query scope is implemented; database-level isolation proof remains

File: `src/pharmaviyum/repositories/patient.py`

- Current `main` applies `Patient.pharmacy_id == pharmacy_id` in both `get_recent_patients` and `get_top_customers` when a scope is supplied.
- `tests/unit/test_patient_repository_tenant_scope.py` compiles both query statements and asserts the pharmacy predicate.
- Both methods return Patient ORM objects, not an aggregate-only projection.
- The current tests prove query construction, not end-to-end isolation against two persisted pharmacies; all call sites still need mapping.

**Status:** the previously reported missing-predicate defect is not present in the inspected `main` revision. Do not track it as an open source defect.

**Remaining action:** add two-pharmacy integration tests that prove a tenant-scoped call cannot return another tenant's patients, and map all call sites. If a global administrative use case exists, give it a separately named and explicitly authorized method rather than overloading an optional scope.

### F-02 — Broad PatientResponse exposed unrelated PHI across ordinary patient endpoints

Files: `src/pharmaviyum/schemas/patient.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/repositories/patient.py`

- The legacy `PatientResponse` schema contains conditions (including treatment notes/current medications/notes), allergies, insurance, consultations, and purchase history.
- Before this remediation, create, update, list, get-by-phone, get-by-ID, and visit endpoints were configured around the broad Patient response or a closely related list schema.
- The repository detail query eagerly loads all clinical/insurance/consultation relations and purchase lines by default.
- The dedicated AI profile schema and repository result were inconsistent: the schema required `patient_id` and `phone`, while the repository returned `id` and unrelated demographic/purchase aggregates. This could cause response validation failure.

**Risk:** one general patient-read contract exposed several unrelated data classes, violating minimum-necessary design and increasing accidental disclosure and serialization cost.

**Remediation in progress in PR:** introduce `PatientSummaryResponse` as the default contract for list/create/update/get/get-by-phone/visit. Standard patient lookup and mutation paths no longer serialize clinical, insurance, consultation, or purchase relations. Create/update/summary repository reads explicitly disable relationship eager loading. The AI profile is narrowed to a purpose-bound clinical safety context containing only patient_id, allergies, and conditions; its repository query excludes insurance, consultation, and purchase relations. Regression tests assert the response allowlist and AI-profile schema contract.

**Remaining action:** keep the broad `PatientResponse` model out of route contracts; add separately authorized, audited clinical, insurance, consultation, and purchase-history endpoints only when a real workflow requires them. Audit the AI profile endpoint's authorization and PHI access logging before treating it as production-ready.

### F-03 — Patient lifecycle events carry linkable identifiers

File: `src/pharmaviyum/services/patient.py`

- PR #385 removes `patient_id`, `full_name`, `phone`, and `country` from the generic `patient.created` payload; only `pharmacy_id` remains.
- `patient.updated`, `patient.deleted`, and `patient.visit_recorded` still include the stable patient ID in their generic event payloads; these remain open minimization work.
- A source search found no in-repository `event_bus.on(...)` subscribers. This does not establish the absence of dynamically registered or external consumers.
- The patient creation log no longer includes the patient ID.
- The event bus is process-local and best-effort (`src/pharmaviyum/services/event_bus.py`); its generic emit log records event type and handler count, not payload.

**Risk:** stable patient IDs are linkable personal data. Keeping them in generic lifecycle events would allow future subscribers or telemetry integrations to correlate events with patient records outside a purpose-bound workflow.

**Remediation:** remove patient identifiers from generic `patient.created`; keep only tenant-level routing metadata. Remaining lifecycle events require the same review. If a workflow needs a patient reference, define a dedicated permissioned event contract and an explicit lookup authorization path rather than reusing the generic event bus.

### F-04 — Two patient mutation helpers are scoped; other mutation helpers lack explicit tenant scope

File: `src/pharmaviyum/repositories/patient.py`

- Current `main` applies `Patient.pharmacy_id == pharmacy_id` directly in the initial SELECT statements of `soft_delete` and `record_visit`; SQL regression tests assert those predicates and verify no mutation occurs when the scoped lookup returns no row.
- Other repository helpers such as `restore`, `update_loyalty`, `add_allergy`, and `add_condition` do not expose a pharmacy scope in their signatures; their caller authorization was not exhaustively mapped.

**Status:** the previously reported unscoped initial lookup is not present in the inspected `main` revision.

**Remaining action:** map all callers of the unscoped helpers; add explicit trusted tenant context and tenant-scoped database predicates where required. Add cross-tenant integration tests at repository and API layers.

### F-05 — Patient and order APIs preserve global superuser scope when pharmacy is omitted

Files: `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/api/v1/orders.py`

- `resolve_pharmacy_scope` returns the supplied pharmacy ID for superusers and returns `None` when a superuser omits it.
- Patient list/detail/search/statistics routes pass that result to the service/repository; `None` means no pharmacy predicate in the inspected repository methods.
- Order read and mutation handlers similarly allow the superuser to remain global when no pharmacy is supplied.

**Risk:** privileged access is not purpose-bound, time-limited, or read-audited in these inspected handlers. This is a privileged global access design, not evidence of an ordinary-user tenant escape.

**Required action:** implement a separate platform-support authorization decision (grant, reason, expiry, permitted action, patient/tenant scope) and mandatory audit for privileged patient-level access. Do not simply remove superuser support without reviewing operational workflows.

### F-06 — Order and purchase tenant predicates are enforced in SQL

File: `src/pharmaviyum/api/v1/orders.py`

- The order create path originally loaded Patient by ID only, then compared `patient.pharmacy_id` in Python.
- Order detail and status-update paths joined Patient but filtered only by `Order.id`; tenant ownership was checked after materializing the Order/Patient result.
- Order completion reloaded Patient by ID without a pharmacy predicate.
- The duplicate-receipt lookup filtered by receipt number without joining the owning Patient tenant.
- These post-fetch checks denied mismatched non-null scopes before the guarded write, but did not enforce tenant isolation at the database query boundary.

**Risk:** cross-tenant rows could be materialized in the application process before authorization rejection. The receipt lookup also relied on globally unique receipt naming rather than an explicit tenant predicate. This review does not establish a production disclosure or cross-tenant mutation.

**Remediation in PR #387:** shared query builders add `Patient.pharmacy_id == scope` to patient, order, and purchase lookups whenever a tenant scope is resolved. The existing global-superuser behavior when scope is `None` is preserved. PostgreSQL SQL-compilation regression tests and the full CI suite passed. Database-backed two-tenant integration coverage remains required.

## Positive controls observed

- Ordinary users are resolved through active `PharmacyMembership` in `resolve_pharmacy_scope`; ambiguous multiple memberships require an explicit pharmacy ID.
- The MCP patient-history tool obtains pharmacy ID from trusted MCP context and includes it in the patient, prescription-count, and order-count queries.
- The AI API validates a supplied patient ID against the authorized pharmacy before invoking the harness.
- These controls do not replace dedicated PHI access auditing, and they do not compensate for repository methods that ignore an explicitly supplied pharmacy parameter.

## Required next implementation sequence

1. Map all call sites for F-01 and F-04, especially unscoped helpers, plus every Patient ORM response serialization path.
2. Add two-pharmacy integration tests for the already scoped query/mutation methods and add tenant predicates to remaining mutation paths where required.
3. Complete purpose-specific patient DTO rollout; add separately authorized clinical/insurance/purchase endpoints only where required, and audit AI-profile access.
4. Minimize generic patient event payloads and audit every subscriber/forwarder.
5. Implement the dedicated PHI access audit event and privileged-support policy defined in the parent governance audit.
6. Verify API, dashboard, reports, exports, background jobs, MCP, and Edge paths before closing the inventory.

## Acceptance gates

- [ ] Every repository method with a pharmacy parameter demonstrably applies it, or is explicitly documented as global and access-controlled.
- [ ] Two-tenant tests prove patient query and mutation isolation.
- [ ] Patient response schemas expose only fields necessary for each workflow.
- [ ] Generic events and telemetry contain no direct patient identifiers or clinical payloads; stable patient IDs are treated as linkable data.
- [ ] Superuser patient-level access is purpose-bound and audited.
- [ ] All patient read surfaces have an owner, authorization policy, response classification, and audit behavior.

## Limitations

This is a targeted source review, not a complete security assessment. Call-graph coverage, runtime behavior, database row counts, production configuration, and external subscriber behavior remain unverified. It does not establish HIPAA, GDPR, or national-law compliance.
