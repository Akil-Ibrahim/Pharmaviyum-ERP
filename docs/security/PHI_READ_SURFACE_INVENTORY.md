# PHI Read-Surface Inventory — Follow-up Source Review

**Review date:** 2026-11-21  
**Baseline:** `main` (reviewed against the current default branch; source files and blob SHAs are recorded in the PR discussion)  
**Scope:** targeted read-only review of patient API, patient service/repository, response schemas, MCP patient-history tool, order API, and in-process event bus. No database, runtime, production data, or secrets were accessed.

## Executive summary

This review expands the initial PHI governance audit. It identifies additional source-level risks that should be addressed before claiming complete tenant isolation or PHI access governance.

**No exploit or production disclosure is established by this review.** Some findings are latent repository-layer hazards whose call sites have not yet been exhaustively mapped. Treat them as verification targets, not confirmed externally reachable vulnerabilities.

## Findings

### F-01 — Repository methods accept pharmacy scope but ignore it

File: `src/pharmaviyum/repositories/patient.py`

- `get_recent_patients(limit, pharmacy_id)` accepts `pharmacy_id` but the query does not apply it.
- `get_top_customers(limit, pharmacy_id)` accepts `pharmacy_id` but the query does not apply it.
- Both methods return Patient ORM objects, not an aggregate-only projection.
- Their call sites were not fully enumerated in this pass.

**Risk:** any caller that relies on the parameter contract to enforce tenant isolation can receive cross-pharmacy rows. This is a repository-level isolation defect if these methods are called in tenant-scoped workflows.

**Required action:** map all call sites; add pharmacy predicates to both queries; add two-pharmacy negative tests proving a tenant-scoped call cannot return another tenant's patients. If a global administrative use case exists, give it a separately named and explicitly authorized method rather than overloading an optional scope.

### F-02 — Patient response schema returns broad clinical and commercial relationships

Files: `src/pharmaviyum/schemas/patient.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/repositories/patient.py`

- `PatientResponse` includes conditions (including treatment notes/current medications/notes), allergies, insurance, consultations, and purchase history.
- `get_patient` and `get_patient_by_phone` return this broad response model.
- The repository eagerly loads allergies, conditions, insurances, consultations and purchases for the patient detail path.
- The same response model is also used for create/update/visit responses.

**Risk:** one patient-read permission currently corresponds to a wide payload containing multiple data classes. This increases minimum necessary/access-control complexity and makes accidental disclosure easier.

**Required action:** define purpose-specific response DTOs (e.g. demographic summary, dispensing safety context, insurance workflow) with explicit field allowlists. Do not return consultation notes, insurance identifiers, or purchase history unless the workflow requires them. Add schema contract tests that assert forbidden fields are absent from each endpoint response.

### F-03 — Patient lifecycle events carry direct identifiers

File: `src/pharmaviyum/services/patient.py`

- Before PR #385, `patient.created` included `patient_id`, `full_name`, `phone`, `country`, and `created_by`.
- PR #385 removes `full_name`, `phone`, and `country`; it retains `patient_id`, `pharmacy_id`, and `created_by` for correlation/routing.
- `patient.updated` continues to include patient ID and updated field names.
- The event bus is process-local and best-effort (`src/pharmaviyum/services/event_bus.py`); its current generic emit log records event type and handler count, not the event payload.
- The full subscriber graph and any external forwarding/logging behavior were not exhaustively traced.

**Risk:** direct identifiers enter a generic application event channel. Future subscribers, telemetry exporters, or integrations could propagate them into systems without PHI controls.

**Required action:** review whether the generic event needs a patient reference at all. A stable internal patient ID is linkable data, not an anonymous or cryptographically opaque identifier. If correlation is required, prefer a short-lived non-reversible event token with a separately authorized lookup path; use a dedicated permissioned clinical event contract for justified PHI-bearing workflows. Add tests that event payloads contain no name, phone, email, DOB, clinical notes, or prescription data. Audit subscribers before enabling external delivery.

### F-04 — Tenant-scoped mutation helpers perform an unscoped initial lookup

File: `src/pharmaviyum/repositories/patient.py`

- `soft_delete(id, pharmacy_id)` and `record_visit(id, pharmacy_id)` first load the patient by ID without a pharmacy predicate, then compare the loaded row's pharmacy ID when a scope was supplied.
- These methods currently return false/None for a mismatched tenant before applying the mutation, but the initial database read itself is unscoped.
- Other repository helpers such as `restore`, `update_loyalty`, `add_allergy`, and `add_condition` do not expose a pharmacy scope in their signatures; their caller authorization was not exhaustively mapped.

**Risk:** defense-in-depth and auditability are weaker than a single scoped query. Internal callers may accidentally bypass the intended tenant contract.

**Required action:** use scoped SELECT/UPDATE predicates in the database statement; require explicit trusted tenant context for patient mutations; enumerate all call sites and test cross-tenant denial at the repository and API layers.

### F-05 — Patient and order APIs preserve global superuser scope when pharmacy is omitted

Files: `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/api/v1/orders.py`

- `resolve_pharmacy_scope` returns the supplied pharmacy ID for superusers and returns `None` when a superuser omits it.
- Patient list/detail/search/statistics routes pass that result to the service/repository; `None` means no pharmacy predicate in the inspected repository methods.
- Order read and mutation handlers similarly allow the superuser to remain global when no pharmacy is supplied.

**Risk:** privileged access is not purpose-bound, time-limited, or read-audited in these inspected handlers. This is a privileged global access design, not evidence of an ordinary-user tenant escape.

**Required action:** implement a separate platform-support authorization decision (grant, reason, expiry, permitted action, patient/tenant scope) and mandatory audit for privileged patient-level access. Do not simply remove superuser support without reviewing operational workflows.

## Positive controls observed

- Ordinary users are resolved through active `PharmacyMembership` in `resolve_pharmacy_scope`; ambiguous multiple memberships require an explicit pharmacy ID.
- The MCP patient-history tool obtains pharmacy ID from trusted MCP context and includes it in the patient, prescription-count, and order-count queries.
- The AI API validates a supplied patient ID against the authorized pharmacy before invoking the harness.
- These controls do not replace dedicated PHI access auditing, and they do not compensate for repository methods that ignore an explicitly supplied pharmacy parameter.

## Required next implementation sequence

1. Map all call sites for F-01 and F-04, plus every Patient ORM response serialization path.
2. Add tenant predicates to repository methods and scoped mutation statements; add negative integration tests with two synthetic pharmacies.
3. Split broad PatientResponse into purpose-specific allowlisted DTOs and add response-contract tests.
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
