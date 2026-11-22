# PHI Read-Surface Inventory — Follow-up Source Review

**Review date:** 2026-11-22  
**Source baseline:** `main` at `2616b4209fc037b1e4f1899b876478bf72258641`  
**Baseline:** `main` at `2616b4209fc037b1e4f1899b876478bf72258641`  
**Scope:** targeted read-only review of patient API, patient service/repository, response schemas, MCP patient-history tool, order API, and in-process event bus. No database, runtime, production data, or secrets were accessed.

## Executive summary

This review expands the initial PHI governance audit. It identifies additional source-level risks that should be addressed before claiming complete tenant isolation or PHI access governance.

**Additional critical findings:** the MCP patient-history tool is not bound to the selected patient/purpose, and the Ansible Compose profile reuses the PostgreSQL bootstrap user as the runtime application credential. These gaps limit the security value of the route-level PHI audit controls.

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
- Before this remediation, standard patient endpoints used a broad Patient response or returned a broad related object.
- The repository detail query eagerly loads clinical/insurance/consultation relations and purchase lines by default.
- The dedicated AI profile schema and repository result were inconsistent: the schema required `patient_id` and `phone`, while the repository returned `id` and unrelated demographic/purchase aggregates. This could cause response validation failure.

**Risk:** one general patient-read contract exposed several unrelated data classes, violating minimum-necessary design and increasing accidental disclosure and serialization cost.

**Remediation in this PR:** introduce `PatientSummaryResponse` as the standard contract for list/create/update/get/get-by-phone/visit. Standard patient endpoints no longer serialize clinical, insurance, consultation, or purchase relations. Create/update/summary repository reads explicitly disable relationship eager loading. The AI profile is narrowed to a purpose-bound clinical safety context containing only patient_id, allergies, and conditions; its repository query excludes insurance, consultation, and purchase relations. Regression tests assert the response allowlist and AI-profile schema contract.

**Remediation in follow-up PR:** `GET /patients/{patient_id}/ai-profile` now requires an explicit purpose code and pharmacy ID, denies platform superusers, requires active `PharmacyMembership`, verifies active patient ownership in SQL, and writes metadata-only allowed/denied `PHIAccessAudit` decisions. Request IDs are bounded to 128 characters. Integration tests cover allowed access, missing membership, cross-pharmacy denial, and superuser denial. The broad `PatientResponse` remains legacy-only and must stay out of route contracts. This closes the AI-profile-specific gap, not all patient PHI read surfaces.

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

### F-05 — Patient and order APIs retain global superuser scope; the new pharmacist history route has narrower controls

Files: `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/api/v1/orders.py`, `src/pharmaviyum/api/v1/patient_purchases.py`

- `resolve_pharmacy_scope` returns the supplied pharmacy ID for superusers and returns `None` when a superuser omits it.
- Patient list/detail/search/statistics routes and order read/mutation handlers pass that result to service/repository code; `None` means no pharmacy predicate in the inspected query paths.
- The newer `GET /patient-purchases/{patient_id}/history` route is different: it requires a pharmacy ID and one of three purpose codes, denies superuser principals, checks active `PharmacyMembership`, verifies the patient belongs to that pharmacy, and writes metadata-only allowed/denied audit records.
- The legacy `GET /patient-purchases/` route remains superuser-only and requires a pharmacy ID, but does not use the new PHI audit record in the inspected implementation.

**Risk:** the dedicated purchase-history route has a purpose and membership gate, but general patient endpoints and order handlers still permit global superuser scope without a purpose-bound grant or read audit. This is a privileged global-access design, not evidence of an ordinary-user tenant escape.

**Required action:** implement a separate platform-support authorization decision (grant, reason, expiry, permitted action, patient/tenant scope) and mandatory audit for privileged patient-level access across all read surfaces. Extend the new audit contract to standard patient reads and any other PHI-bearing paths. Do not simply remove superuser support without reviewing operational workflows.

### F-06 — Order and purchase tenant predicates are enforced in SQL

File: `src/pharmaviyum/api/v1/orders.py`

- The order create path originally loaded Patient by ID only, then compared `patient.pharmacy_id` in Python.
- Order detail and status-update paths joined Patient but filtered only by `Order.id`; tenant ownership was checked after materializing the Order/Patient result.
- Order completion reloaded Patient by ID without a pharmacy predicate.
- The duplicate-receipt lookup filtered by receipt number without joining the owning Patient tenant.
- These post-fetch checks denied mismatched non-null scopes before the guarded write, but did not enforce tenant isolation at the database query boundary.

**Risk:** cross-tenant rows could be materialized in the application process before authorization rejection. The receipt lookup also relied on globally unique receipt naming rather than an explicit tenant predicate. This review does not establish a production disclosure or cross-tenant mutation.

**Remediation in PR #387:** shared query builders add `Patient.pharmacy_id == scope` to patient, order, and purchase lookups whenever a tenant scope is resolved. The existing global-superuser behavior when scope is `None` is preserved. PostgreSQL SQL-compilation regression tests and the full CI suite passed. Database-backed two-tenant integration coverage remains required.

### F-07 — MCP patient-history tool is pharmacy-scoped but not patient-context/purpose-bound or PHI-audited

Files: `src/pharmaviyum/ai/mcp/context.py`, `src/pharmaviyum/api/v1/ai.py`, `src/pharmaviyum/ai/mcp/schemas.py`, `src/pharmaviyum/ai/mcp/tools/patient_history.py`

- `MCPAuthorizationContext` carries only `user_id`, `pharmacy_id` and `user_role`. The AI API injects those fields; the selected request `patient_id` used for the HMAC session namespace is not included in MCP authorization context.
- `PatientHistoryRequest` accepts a model-supplied `patient_id` and has no purpose-of-use field.
- The tool query enforces `Patient.id`, trusted `pharmacy_id` and active status. This prevents a cross-pharmacy lookup, but it does not prove that the requested patient matches the patient selected for the current AI session.
- The tool returns full name, age, gender, blood type, allergies, conditions, active-prescription count, recent-order count, loyalty tier and preferred language.
- The tool does not write `PHIAccessAudit`. Its current log records only counts and latency, which avoids logging the patient ID or clinical payload.

**Risk:** an AI session bound to Patient A can potentially request Patient B within the same pharmacy because the trusted MCP context does not carry/verify the selected patient and purpose. This is a source-level authorization gap, not evidence of a Production disclosure.

**Required action:** bind MCP context to the selected patient and purpose; require the tool patient ID to match that context or require a separately authorized patient-selection transition; record allowed/denied `PHIAccessAudit` decisions; minimize the output schema; add mismatch, missing-purpose, denied-access and audit-failure integration tests.

### F-08 — Runtime database credential is the PostgreSQL bootstrap superuser; audit triggers are not a complete immutability boundary

Files: `ansible/roles/app-backend/files/docker-compose-backend.yml`, `ansible/group_vars/all.yml`, `ansible/roles/postgresql/tasks/main.yml`, `alembic/versions/2026_11_21_000001_phi_access_audit.py`

- The pharmacy-server Compose profile initializes PostgreSQL with `POSTGRES_USER` (default `app_user`) and passes the same username/password to `DATABASE_URL` for backend, Celery worker and Celery beat.
- On initial data-volume creation, the standard PostgreSQL container entrypoint creates `POSTGRES_USER` as the bootstrap superuser. The repository does not show a later role split, a `NOSUPERUSER` runtime role, or grants that prevent the application credential from changing audit schema objects.
- The Ansible `postgresql` role currently creates/checks the data directory and reports container status; it does not provision separate runtime, owner, migration and audit roles or verify database privileges.
- The PHI audit migration adds triggers rejecting UPDATE/DELETE/TRUNCATE, but a database superuser or table owner can disable/drop triggers or alter the table. The runtime application credential must not have those privileges.
- The production Alembic guard requires `MIGRATION_DATABASE_URL`, but the public Ansible migration environment does not inject it; a separate migration credential and least-privilege path are not yet wired.

**Risk:** the append-only trigger is useful defense in depth, but the current repository configuration does not prove that the application cannot bypass it. This is a configuration/code-path risk, not evidence that a live Production role has been abused.

**Required action:** provision a bootstrap-only superuser, a narrowly scoped runtime role, a controlled migration role and (if needed) a dedicated audit writer/owner. Ensure the runtime role is not superuser and cannot ALTER/DROP/TRUNCATE audit storage or disable triggers. Add PostgreSQL tests for `pg_roles.rolsuper`, `has_table_privilege`, trigger protection and attempted schema/trigger tampering. Keep migration credentials out of the application runtime environment.

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
