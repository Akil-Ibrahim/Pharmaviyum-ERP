# PHI Access Governance — Source-Level Architecture Audit

**Review date:** 2026-11-21  
**Baseline:** `main` at `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`  
**Scope:** read-only inspection of patient, purchase, tenant, audit-log and synchronization source files. No production database or runtime was accessed.

## Executive decision

**NO-GO for claiming complete patient-data access governance.** The repository has a generic `AuditLog` model and explicit pharmacy memberships, but the inspected patient-purchase read endpoint is globally scoped for superusers, the generic audit model does not encode the dimensions required for PHI access review, and the patient record's `pharmacy_id` is nullable.

This is a source-level finding, not evidence of an exploit or a confirmed production disclosure. The endpoint requires an active superuser. The issue is that privileged access is broader than a pharmacy-scoped workflow and has no demonstrated patient-level authorization or read-access audit in the inspected path.

## 1. Verified implementation facts

### 1.1 Patient purchase read API

File: `src/pharmaviyum/api/v1/patient_purchases.py`

- `GET /patient-purchases/` requires `CurrentSuperuser`.
- It selects `PatientPurchase` without joining `Patient` or filtering by `Patient.pharmacy_id`.
- It returns patient ID, product information, batch metadata, receipt number, quantity, prices, prescription-required flag and purchase timestamp.
- Pagination is bounded (`limit <= 200`), but pagination is not tenant isolation.
- No read-audit event is emitted in the inspected handler.

**Interpretation:** this is a privileged global read surface. A superuser-only dependency is an authorization check, but it is not a purpose-bound, pharmacy-scoped access policy. Do not describe this as a confirmed ordinary-user tenant escape.

### 1.2 Patient tenant ownership

File: `src/pharmaviyum/models/patients/patient.py`

- `Patient.pharmacy_id` is nullable.
- The patient model contains direct identifiers and sensitive fields (name, date of birth, phone, email, address, national/insurance identifiers, allergies and chronic-condition notes).
- The inspected model does not enforce non-null pharmacy ownership at the ORM declaration.

**Interpretation:** patient ownership cannot safely be assumed for legacy rows. Before making pharmacy scope mandatory, inventory null-owner records and define an explicit, reviewed ownership-resolution process. Never assign a pharmacy by guessing from phone, user session, purchase or current inventory.

### 1.3 Existing generic audit model

File: `src/pharmaviyum/models/audit_log.py`

The existing `AuditLog` stores actor ID/type, action, entity/entity ID, optional JSON changes, IP address, user agent and timestamp.

It does not explicitly model:
- pharmacy/tenant scope;
- patient subject reference distinct from the target entity;
- read/view/search/export/print access events;
- authorization outcome (allowed/denied);
- purpose-of-use or reason code;
- request/trace/correlation ID;
- source channel and authentication context;
- break-glass state and approval/review;
- policy/permission version.

The model's existence alone does not prove that sensitive reads are audited. The inspected patient-purchase handler does not write to it.

### 1.4 Tenant membership and superuser bypass

Files: `src/pharmaviyum/models/pharmacy_membership.py`, `src/pharmaviyum/modules/auth/tenant.py`

- `PharmacyMembership` binds a user to a pharmacy and has an active flag.
- `require_pharmacy_tenant` authorizes an active membership for ordinary users.
- The helper deliberately allows a superuser to resolve any requested pharmacy without a membership.
- `resolve_pharmacy_scope` allows superusers to remain global when no pharmacy is supplied.

**Interpretation:** this helper is useful for tenant-scoped operational APIs, but it is not a PHI policy by itself. Sensitive patient access needs an explicit pharmacy context, patient ownership validation, purpose/permission checks and an audit event. Global superuser access should be a separately governed administrative capability.

### 1.5 Central Inbox boundary

Files: `src/pharmaviyum/models/sync.py`, `src/pharmaviyum/api/v1/sync.py`, `docs/adr/ADR-0007-central-inbox-consumer.md`

- Edge ingress derives pharmacy scope from the authenticated enrolled Edge node, not from an untrusted request pharmacy field.
- Central Inbox persists a durable receipt and returns `accepted` after commit.
- The current implementation has no Central domain consumer. `accepted` is not proof of sale, payment or inventory application.
- The existing ADR explicitly blocks business side effects until product/lot/actor mapping, event coverage, idempotency, ordering and atomicity gates are satisfied.

**Security requirement:** general POS synchronization must not become a transport for patient records or clinical context. Keep patient/PHI events out of the POS event contract unless a separate, explicitly authorized clinical synchronization design is approved. Do not log raw Inbox payloads.

### 1.6 Other patient-facing surfaces sampled

A targeted source search found additional surfaces; these were sampled, not exhaustively audited:

- `src/pharmaviyum/api/v1/endpoints/patients.py`: list, detail, phone lookup, statistics and AI-profile handlers call `resolve_pharmacy_scope` and pass the resolved scope into the patient service. For ordinary users, the helper requires an active membership or a single unambiguous membership. For superusers, an omitted `pharmacy_id` intentionally remains global. Therefore the patient API is tenant-aware for ordinary users, but platform-wide superuser reads remain possible and need a separate governed support policy.
- `src/pharmaviyum/ai/mcp/tools/patient_history.py`: the patient lookup and prescription/order count queries explicitly filter by the trusted MCP context's `pharmacy_id`; tool input alone does not select the tenant. This is a positive control in the inspected path, but it is not a substitute for access auditing.
- `src/pharmaviyum/api/v1/orders.py`: order reads resolve a pharmacy scope and compare the joined patient's pharmacy. Superusers can remain global when no scope is supplied. Order creation and status mutation are superuser-only and should be included in the privileged-access review.
- `src/pharmaviyum/api/v1/ai.py`: AI requests require an authorized pharmacy context and validate an optional patient ID against that pharmacy before invoking the harness; session IDs are HMAC-scoped to pharmacy, user and patient. This is a positive authorization/session-isolation control, but the source does not demonstrate a dedicated PHI read audit event.

The repository also contains patient repositories and dashboard aggregates. Their complete call graph, query filters, response fields and role policy remain part of the required exhaustive inventory. Search results alone are not proof that every caller is safe.

## 2. Required target policy

### 2.1 Authorization decision

Every patient-data operation must resolve and enforce, server-side:

1. authenticated active principal;
2. active pharmacy membership and pharmacy-scoped role/permission;
3. patient ownership by that pharmacy (or a separately approved cross-pharmacy care relationship);
4. action permission (read, update, dispense, export, delete, etc.);
5. purpose-of-use / reason code where required by policy;
6. explicit denial when ownership or scope is missing or ambiguous.

A global `is_superuser` flag must not silently convert every patient endpoint into an unrestricted clinical-data endpoint. Platform support access should be separately granted, time-bounded, reason-coded, logged and reviewable.

### 2.2 Access audit event contract

Create a dedicated append-only PHI access audit contract rather than treating generic entity-change logs as sufficient. Minimum fields:

- immutable event ID and UTC timestamp;
- actor ID plus actor type (human, service, Edge/system);
- tenant/pharmacy ID;
- subject type and a stable patient reference (avoid copying patient identifiers);
- action: read, search, create, update, dispense, export, print, disclose, break-glass;
- resource type and resource reference;
- decision: allowed or denied, with bounded reason code;
- purpose-of-use / workflow context;
- request ID and trace ID;
- source channel (API, UI, MCP/tool, background job, Edge);
- authentication/session context sufficient for investigation, without storing credentials;
- break-glass approval/reviewer fields where applicable.

Do not store clinical payloads, full request/response bodies, prescriptions, notes, tokens, secrets or unnecessary direct identifiers in audit metadata. Use controlled reason-code vocabularies and bounded strings.

### 2.3 Audit integrity and operations

- Persist the access decision and its audit record reliably; define behavior when audit persistence fails. For PHI reads, fail closed if policy requires a durable audit and no safe fallback exists.
- Prevent application roles from UPDATE/DELETE of audit records; use database privileges and/or append-only triggers, and test them.
- Separate security audit retention from ordinary application logs; define retention, legal hold, export and access-review procedures by applicable jurisdiction.
- Restrict audit-log viewing to a dedicated permission; audit access to the audit log itself.
- Keep logs and traces free of PHI by default. Use opaque IDs, redaction, low-cardinality metrics and explicit allowlists.
- Alert on unusual bulk reads, repeated denied access, cross-pharmacy access attempts, exports and break-glass use.

## 3. Safe implementation sequence

1. **Inventory all patient read surfaces.** Enumerate API routes, dashboard queries, search, reports, exports, AI/MCP tools, background jobs and Edge contracts. Classify fields and required purpose.
2. **Define tenant ownership semantics.** Resolve nullable `Patient.pharmacy_id` rows through a reviewed migration plan. Define cross-pharmacy patient sharing explicitly; do not infer it.
3. **Define pharmacy-scoped roles and permissions.** A membership is a tenant boundary, not a role. Add explicit patient-data permissions and platform-support policy.
4. **Implement an authorization service.** Resolve the patient row and pharmacy ownership in the same query/transaction as the requested read; fail closed for missing or ambiguous ownership.
5. **Implement the PHI access audit event.** Add tests for allowed/denied reads, failed audit persistence, break-glass, export, and audit-log access.
6. **Narrow the global patient-purchase endpoint.** Prefer an explicit pharmacy-scoped route and server-enforced patient ownership. Keep any platform-wide support workflow separate, time-bounded and audited. Do not silently change the existing API until consumers and compatibility are reviewed.
7. **Add negative integration tests.** User A cannot read patient B in another pharmacy; superuser access requires the designated support policy; null-owner patients fail closed; denied attempts are audited; audit records cannot be mutated by the application role.
8. **Run synthetic-data staging validation.** Verify migrations, query plans, audit throughput, retention and alert delivery. No production rollout until backup/restore and rollback procedures are rehearsed.

## 4. Acceptance gates

- [ ] Every patient-data read surface has a documented owner, scope and permission.
- [ ] No patient read relies on global role alone.
- [ ] Null/ambiguous patient ownership fails closed.
- [ ] Allowed and denied sensitive access is auditable without recording PHI payloads.
- [ ] Audit records are append-only under the application database role.
- [ ] Break-glass is explicit, time-bounded, reason-coded and reviewed.
- [ ] Cross-pharmacy, export, MCP and background-job tests pass with synthetic fixtures.
- [ ] Logging/tracing redaction is verified by tests.
- [ ] Production access review and retention policy are approved.

## 5. Non-goals and safety

- This audit does not change application code, database schema, production data, secrets, permissions or deployment.
- It does not establish compliance with HIPAA, GDPR or any national health-data law. Applicability and legal requirements require jurisdiction-specific review.
- It does not authorize unrestricted superuser access or automatic reassignment of legacy patients.
- It does not enable patient data in Central POS Inbox events.

**Historical status at the 2026-11-21 source baseline:** implementation had not started. See the 2026-11-22 follow-up below for current partial remediation. PHI access governance remains a release blocker until all relevant patient-level routes satisfy the gates above.

## 6. Follow-up implementation status — 2026-11-22

A read-only review of `main` at `2616b4209fc037b1e4f1899b876478bf72258641` confirms partial implementation after this historical audit:

- Standard patient list/detail/phone routes now use `PatientSummaryResponse` rather than the broad legacy `PatientResponse`.
- `GET /api/v1/patients/{patient_id}/ai-profile` requires explicit pharmacy and purpose, active membership and patient ownership; it denies platform superusers and records metadata-only allowed/denied `PHIAccessAudit` decisions.
- `GET /api/v1/patient-purchases/{patient_id}/history` is a separate pharmacist-facing route with the same explicit pharmacy/purpose/membership/ownership controls. It denies superusers and null-owner patients, returns a minimum-field projection and records allowed/denied audit decisions.
- The legacy `GET /patient-purchases/` route remains superuser-only and requires an explicit pharmacy ID; its query now joins `Patient` and filters by `Patient.pharmacy_id`. It still returns a broader administrative projection and does not emit the new PHI audit event.
- The `PHIAccessAudit` table has database triggers rejecting UPDATE, DELETE and TRUNCATE; integration tests cover these protections and the retained-evidence downgrade guard.

Remaining gaps: general patient/order routes still permit global superuser scope; patient creation can still omit nullable pharmacy ownership; the legacy administrative purchase listing lacks the new read audit; support-access governance, database-backed MCP audit-failure tests, complete route coverage and telemetry redaction evidence remain incomplete. The MCP `get_patient_history` tool now carries trusted selected-patient/purpose context through registry dispatch, enforces exact patient matching and records metadata-only allowed/denied `PHIAccessAudit` decisions before returning data. Its response remains broader than the minimum-necessary target, and current MCP audit tests use a test double rather than a database-backed authorization fixture. Ansible Compose still reuses the PostgreSQL bootstrap `POSTGRES_USER` credential for application runtime connections; the repository does not provision a separate non-superuser runtime role, so trigger-only append-only enforcement is not proven against the application credential. These are source-level changes, not evidence of current Production deployment or regulatory acceptance.

This follow-up does not establish legal/regulatory compliance or certify a live Production deployment.
