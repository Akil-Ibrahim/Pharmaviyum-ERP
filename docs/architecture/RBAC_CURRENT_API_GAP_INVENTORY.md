# Current API Authorization Gap Inventory

- **Status:** Read-only engineering findings for RBAC planning
- **Date:** 2026-11-26
- **Base reviewed:** `main` at `b5a0f51cc45e39b5afdfd21af99a5053823af5ce`
- **Related:** `PHARMACY_RBAC_PERMISSION_SPEC.md`, `SIDEBAR_AUTHORIZATION_INTEGRATION_PLAN.md`

This inventory records concrete authorization patterns found in the current source. It is not a complete endpoint audit and does not approve any role or permission grants. Verify router mounting and runtime exposure before treating any module as externally reachable.

## 1. High-priority findings

### 1.1 Prescription router currently has no authentication dependency

File: `src/pharmaviyum/api/v1/endpoints/prescriptions.py`

The placeholder router is included by the legacy `src/pharmaviyum/api/v1/router.py` aggregator. However, the runtime application imports `api_v1_router` from `src/pharmaviyum/api/v1/__init__.py` in `src/pharmaviyum/main.py`; that runtime aggregator does not include `prescriptions_router`. Therefore the separate placeholder handlers are not mounted by the reviewed runtime aggregator. Note: the runtime-mounted `pharmacy_entities.py` independently defines `/api/v1/prescriptions` GET/POST handlers protected by `CurrentSuperuser`; those are different handlers and are mounted. See section 3.2. Its current handlers:

- `GET /prescriptions/` has no user/authentication dependency and returns a placeholder empty list.
- `GET /prescriptions/{prescription_id}` has no user/authentication dependency and always returns 404.

There is no prescription data access in these placeholders today. However, the route is not protected by authentication. Before implementing real prescription reads or writes, add explicit authentication, pharmacy tenant resolution, action authorization, patient ownership checks, and PHI audit behavior. Do not expand these placeholders into real endpoints until the policy and data scope are defined.

### 1.2 Patient read and write operations use different coarse authorization models

File: `src/pharmaviyum/api/v1/endpoints/patients.py`

Observed patterns:

- Patient list, statistics, lookup, summary, and visit operations use `get_current_active_user` and `resolve_pharmacy_scope`.
- Patient create, update, and delete use `get_current_active_superuser`.
- AI-profile access has explicit pharmacist/membership-related checks and a required pharmacy context.

This is not yet a granular clinical permission model. Before replacing the current checks, inventory each patient operation separately and preserve pharmacy ownership enforcement. Do not infer that a pharmacy membership alone grants access to every patient record or every clinical action.

### 1.3 Tenant membership is not action authorization

Files: `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/models/pharmacy_membership.py`

`require_pharmacy_tenant` checks an active membership for ordinary users; superusers currently bypass that membership check. It returns a tenant context, not a role or action grant. The membership model has no role field.

Keep this boundary explicit: membership proves tenant affiliation, not permission to dispense, refund, approve procurement, change stock, view PHI, or administer users.

## 2. Additional coarse-grained authorization patterns

### 2.1 Product catalog

File: `src/pharmaviyum/api/v1/products.py`

Observed patterns:

- Product create, update, and delete require `CurrentSuperuser`.
- Product search, detail, and list require `CurrentUser`.

This is global user/superuser gating, not pharmacy-scoped catalog permissions. Review whether the catalog is global reference data or tenant-owned data before introducing pharmacy scoping.

### 2.2 Pharmacy entities and inventory

File: `src/pharmaviyum/api/v1/pharmacy_entities.py`

Observed patterns include:

- Pharmacy and supplier creation/listing are superuser-only in this module.
- Inventory list uses membership-derived pharmacy filtering for ordinary users.
- Inventory create, update, adjustments, and delete are superuser-only.
- Batch and prescription operations in this module are superuser-only.

Inventory mutations should be mapped to separate action permissions and audited. Do not replace the current superuser gate with a broad `inventory.write` grant without defining receive, adjust, transfer, reconcile, and delete semantics.

### 2.3 Orders

File: `src/pharmaviyum/api/v1/orders.py`

Observed patterns:

- Order create and status update require an active superuser.
- Order detail requires an active user and resolves pharmacy scope.
- Patient/order/purchase queries attempt to constrain data through patient pharmacy ownership.

The current endpoint-level gates are inconsistent in granularity. Preserve row-level tenant constraints while separating create, status-transition, and read permissions.

## 3. POS module requires router-mount verification

File: `src/pharmaviyum/api/v1/pos.py`

The module contains tenant membership checks for product search, lot lookup, checkout, cancellation, and sale reads. These checks establish tenant membership but do not distinguish cashier checkout from refunds/cancellations or other action-specific permissions.

The inspected `src/pharmaviyum/api/v1/router.py` does not directly include this POS router. Verify the actual application router composition before assuming these handlers are exposed in the deployed app or adding them to the Sidebar contract.

## 4. Suggested remediation order after policy approval

1. Complete the API route inventory, including the final mounted route graph.
2. Secure placeholder clinical endpoints before adding prescription data access.
3. Define a centralized authorization dependency/service that combines authenticated principal, active tenant context, action permission, and resource ownership.
4. Migrate patient/PHI endpoints with fail-closed ownership semantics and audit coverage.
5. Migrate inventory, procurement, and POS operations using action-specific permissions.
6. Migrate global catalog and administration endpoints only after deciding whether their data is global or pharmacy-scoped.
7. Add endpoint-level 401/403, cross-tenant, role-change, and audit tests.
8. Expose the effective permission context to the frontend and then filter Sidebar navigation.

## 5. Explicit non-actions

This review made no application code changes, route changes, schema changes, migration changes, permission grants, manual SQL, merge, or deployment. The findings must be reviewed against the complete router graph and runtime configuration before implementation.


### 3.2 Runtime router composition differs from the legacy router module

Files: `src/pharmaviyum/main.py`, `src/pharmaviyum/api/v1/__init__.py`, `src/pharmaviyum/api/v1/router.py`

Observed runtime composition:

- `main.py` imports and mounts `api_v1_router` from the `api.v1` package.
- The package-level `api_v1_router` is assembled in `api/v1/__init__.py`.
- That runtime aggregator includes AI, auth, catalog, dashboard, ingestion, monitoring, medical devices, orders, patients, patient purchases, POS, sync, pharmacy entities, products, and users.
- It does not include `prescriptions_router` or `feature_flags_router`.
- The separate `api/v1/router.py` defines another aggregator with a different set of routers, including prescriptions and feature flags, but code search found no import/use of its `api_router` symbol in the reviewed repository.
- The legacy aggregator adds an `/api/v1` prefix while the patients router already declares `/api/v1/patients`; mounting that aggregator as written would produce a duplicated path prefix for patients.

Implications:

- Do not report prescription placeholder endpoints as currently exposed in the deployed application based only on the legacy aggregator. Their source handlers are unauthenticated, but the runtime mount must be verified before treating them as reachable.
- Treat the existence of two divergent router aggregators as an API composition/maintenance risk. There must be one authoritative runtime router tree.
- Before RBAC implementation, generate or test the actual FastAPI route table from the same app factory/entrypoint used in deployment. Record method, path, router, authentication dependency, tenant dependency, and action permission for every mounted business route.
- Add a regression test asserting critical expected routes are mounted exactly once and retired/unmounted routes are absent.
- Resolve the duplicated-prefix issue only as a separately reviewed routing change; do not combine it with RBAC policy implementation without tests.



## 4. Runtime authorization findings by mounted domain

This section reviews the package-level router actually mounted by `src/pharmaviyum/main.py`. It is a source audit, not a substitute for an instantiated FastAPI route-table test.

### 4.1 POS

File: `src/pharmaviyum/api/v1/pos.py`

- The reviewed product search, lot lookup, goods receipt, and checkout handlers accept `CurrentUser` and call `require_pharmacy_tenant` using the requested or payload pharmacy ID.
- This establishes authentication and active membership for ordinary users, but it does not distinguish action permissions such as `pos.read`, `pos.checkout`, or `inventory.receive`.
- The same broad membership gate currently allows any active member to reach these operations unless a separate check exists in the handler/service path. No role/action check was found in the reviewed handlers.
- Tenant checks must remain server-side and must be paired with row-level pharmacy constraints for every resource read or mutated.

### 4.2 Products / Drug Catalog

File: `src/pharmaviyum/api/v1/products.py`

- Product search, list, and detail require an authenticated active user.
- Product create, update, and deactivate require `CurrentSuperuser`.
- These product queries are global catalog queries and do not resolve a selected pharmacy tenant.
- This may be appropriate for a shared reference catalog, but it is not sufficient for pharmacy-specific assortment, pricing, visibility, or catalog-review workflows. Those distinctions must be decided explicitly before mapping permissions.

### 4.3 Patients / PHI

File: `src/pharmaviyum/api/v1/endpoints/patients.py`

- List, statistics, phone lookup, patient detail, and visit recording require an active user and call `resolve_pharmacy_scope`.
- Patient create, update, and delete currently require `get_current_active_superuser`; they are not yet mapped to pharmacist/manager action permissions.
- AI profile access checks active membership and patient ownership in the selected pharmacy, rejects platform superusers through this endpoint, and records allow/deny PHI audit events with a controlled purpose.
- The current endpoint set therefore has a mix of tenant-scoped reads, superuser-only mutations, and a separately governed AI profile path. Do not flatten these into one generic `patients.*` permission.

### 4.4 Orders / legacy purchase workflow

File: `src/pharmaviyum/api/v1/orders.py`

- Order creation and status mutation require `CurrentSuperuser`.
- Order reads require an active user and resolve pharmacy scope, then constrain the order through its owning patient.
- The query helpers only add a pharmacy predicate when a scope is resolved. For ordinary users, `resolve_pharmacy_scope` requires a sole active membership or an explicit authorized pharmacy; this behavior must be preserved.
- This is a legacy order/patient-purchase workflow and should not be confused with the newer POS Sale/Payment domain when defining permission names.

### 4.5 Users

File: `src/pharmaviyum/api/v1/users.py`

- Self avatar read/update/delete require `CurrentUser`.
- Listing, creating, and reading other user accounts require `CurrentSuperuser`.
- There is no pharmacy-scoped membership/role administration API in this router. Do not infer that user creation grants pharmacy membership or a pharmacy role.

### 4.6 Pharmacy domain: inventory, suppliers, prescriptions and related resources

File: `src/pharmaviyum/api/v1/pharmacy_entities.py`

- This router exposes multiple pharmacy-domain resources under one router, including pharmacy, supplier, inventory, batch, prescription, and ERP integration operations.
- The reviewed inventory adjustment and inventory deletion handlers require `CurrentSuperuser`, and adjustment loads the inventory row by ID before applying the movement.
- Other handlers in this module must be audited individually for their exact dependency and whether the target row is constrained to the caller's authorized pharmacy. A router-level tag or the presence of a `pharmacy_id` field is not proof of tenant isolation.
- The permission map must be endpoint/action-specific and include object-level tenant checks; avoid assigning one broad permission to the entire router.

### 4.7 Current tenant helper limitation

File: `src/pharmaviyum/modules/auth/tenant.py`

- `require_pharmacy_tenant` treats `is_superuser` as a bypass for any requested pharmacy ID.
- `resolve_pharmacy_scope` allows a superuser to remain global when no pharmacy ID is supplied.
- This is a tenant-scope decision, not an action permission. Platform/support access must be designed separately from pharmacy business roles, with purpose-bound and audited access for PHI.

## 5. Router composition clarification

The package-level `api_v1_router` is the router mounted directly by `main.py`; it includes the patient router and several domain routers. It does not include `prescriptions_router` or `feature_flags_router` from the endpoints package. The separate `api/v1/router.py` aggregator is not the runtime router imported by `main.py`.

The top-level helper in `src/pharmaviyum/api/__init__.py` would add an additional `/api/v1` prefix, but `main.py` does not call that helper in the reviewed entrypoint. Therefore do not describe the legacy aggregator's possible duplicate-prefix behavior as a current runtime defect. The confirmed concern is divergent, unused router composition that can mislead route audits and future maintenance.

Before implementation, add a route-table test against the deployment app entrypoint and assert each expected method/path is registered exactly once, with an explicit expected set for intentionally unmounted routers.


## 6. Detailed mounted pharmacy-domain and POS authorization matrix

Source baseline: `main` at the time of this review. "Authenticated" means the dependency resolves an active authenticated account; "tenant" means an explicit pharmacy membership check or query-level membership constraint. No action-specific pharmacy role permission registry was found in these handlers.

| Method and path | Current dependency / scope | Current effective access | RBAC design target (provisional) |
|---|---|---|---|
| GET `/api/v1/pharmacies` | `CurrentUser`; membership join for non-superuser | Own active memberships; superuser sees all | `pharmacies.read`; platform-wide scope separately governed |
| POST `/api/v1/pharmacies` | `CurrentSuperuser` | Platform superuser only | Platform provisioning capability, not Pharmacy Admin by default |
| GET/POST `/api/v1/suppliers` | `CurrentSuperuser` | Global supplier list/create | Decide global supplier directory vs pharmacy-scoped suppliers; do not silently grant all members |
| GET `/api/v1/inventory` | `CurrentUser`; non-superuser query constrained to all active membership pharmacy IDs | Authenticated users can read inventory across all their active memberships; optional pharmacy filter narrows result | `inventory.read` plus selected/authorized pharmacy context; enforce object scope |
| POST `/api/v1/inventory` | `CurrentSuperuser` | Platform superuser only; creates zero-balance lot | Likely inventory/catalog administration action, subject to explicit role decision |
| PATCH `/api/v1/inventory/{id}` | `CurrentSuperuser`; row loaded by ID | Platform superuser only | `inventory.lot.update`; pharmacy ownership check in same query |
| POST `/api/v1/inventory/{id}/adjustments` | `CurrentSuperuser`; row loaded by ID | Platform superuser only | `inventory.adjust`; reason, idempotency, audit and tenant scope remain mandatory |
| DELETE `/api/v1/inventory/{id}` | `CurrentSuperuser`; row loaded by ID | Platform superuser only | `inventory.lot.delete`; zero balance/no movement safeguards remain |
| GET `/api/v1/batches` | `CurrentSuperuser`; global `ProductBatch` query | Platform superuser only; source comment says model has no pharmacy_id and fails closed | Keep denied to pharmacy roles until batch ownership/tenant model exists |
| GET/POST `/api/v1/prescriptions` | `CurrentSuperuser`; global query/create | Platform superuser only | Clinical permission + patient/pharmacy ownership + purpose-bound PHI audit; no global pharmacy-role access |
| GET/POST `/api/v1/erp/integrations` | `CurrentSuperuser` | Platform superuser only | Platform integration administration unless a pharmacy-scoped integration model is introduced |
| POST `/api/v1/erp/integrations/{id}/events` | `CurrentSuperuser`; integration loaded by ID | Platform superuser only | Integration-specific service identity / platform capability; audit and tenant binding |
| GET `/api/v1/sync-events`, GET `/api/v1/erp/integrations/{id}/events` | `CurrentSuperuser`; global event queries | Platform superuser only | Platform operations permission; tenant and sensitive-payload review |
| GET `/api/v1/pos/products/search` | `CurrentUser` + `require_pharmacy_tenant(pharmacy_id)` | Any active member of requested pharmacy | `pos.read` / catalog lookup permission |
| POST `/api/v1/pos/inventory/receive` | `CurrentUser` + tenant check for payload pharmacy | Any active member of requested pharmacy can invoke receipt | `inventory.receive` |
| GET `/api/v1/pos/products/{id}/lots` | `CurrentUser` + tenant check | Any active member of requested pharmacy | `inventory.read` |
| POST `/api/v1/pos/checkout` | `CurrentUser` + tenant check | Any active member of requested pharmacy can checkout | `pos.checkout`; discount/refund/cancel permissions separately |
| POST `/api/v1/pos/payments/webhook` | HMAC-SHA256 shared-secret signature; no user session | External signed payment adapter | Keep machine-to-machine auth; add provider identity, replay/idempotency and audit controls |
| POST `/api/v1/pos/sales/{id}/cancel` | `CurrentUser` + sale pharmacy tenant check | Any active member of sale pharmacy can cancel pending-payment sale | `pos.sale.cancel` distinct from checkout |
| GET `/api/v1/pos/sales/{id}` | `CurrentUser` + sale pharmacy tenant check | Any active member of sale pharmacy can read sale | `pos.sale.read` |

### 6.1 Confirmed design gaps / constraints

1. **Membership is not a role.** POS operations currently accept any active pharmacy member; there is no cashier/pharmacist/manager distinction at these handler boundaries.
2. **Inventory read is multi-membership scoped, not selected-context scoped.** The query restricts results to all active pharmacy memberships. Decide whether cross-membership aggregation is allowed; otherwise require selected pharmacy context.
3. **Inventory mutation handlers use global superuser dependencies.** They load rows by ID after authentication, without a pharmacy-role action check or explicit tenant predicate. Replacing superuser with a pharmacy role must add pharmacy ownership filtering in the query itself.
4. **Prescription endpoints do exist at runtime.** The mounted `pharmacy_entities.py` exposes GET/POST `/api/v1/prescriptions` behind `CurrentSuperuser`. The separate `endpoints/prescriptions.py` placeholder router is not included in the runtime aggregator. These must not be conflated.
5. **Prescription ownership is not established by the handler.** The create payload accepts `patient_id`, but the handler does not validate that patient belongs to an authorized pharmacy before creating the prescription. Superuser-only access limits callers but does not establish data integrity or pharmacy ownership.
6. **Supplier and ERP data are global in this model.** Do not map them to pharmacy roles until ownership semantics are defined.
7. **Webhook auth is not user RBAC.** HMAC signature validation is a separate machine identity boundary and should remain independent of interactive user roles.

### 6.2 Role mapping remains deliberately unapproved

The target permissions above are action candidates, not approved grants. Do not infer a final role matrix from endpoint names or existing superuser access. The four proposed pharmacy roles remain a proposal until the user explicitly approves the role and clinical-access decisions.


## 7. Drug Catalog, Patient Purchases, Dashboard, Medical Devices and AI

Source baseline: mounted runtime routers on `main`. All endpoints below are present in the package-level runtime aggregator reviewed for this audit.

| Method and path | Current dependency / scope | Current effective access | RBAC design target (provisional) |
|---|---|---|---|
| GET `/api/v1/drug-catalog/search` | `CurrentUser`; shared reference catalog query | Any active authenticated user; no pharmacy scope | `catalog.read`; shared reference-data access may be global by design |
| POST `/api/v1/drug-catalog/sources` | `CurrentSuperuser` | Platform superuser only | `catalog.source.create` or platform ingestion identity |
| GET `/api/v1/drug-catalog/sources` | `CurrentSuperuser` | Platform superuser only; global staged source records | `catalog.source.review.read` |
| GET `/api/v1/drug-catalog/sources/{id}/matches` | `CurrentSuperuser`; source row loaded by ID | Platform superuser only | `catalog.source.match` |
| PATCH `/api/v1/drug-catalog/sources/{id}/review` | `CurrentSuperuser`; row locked by ID | Platform superuser only; can approve/reject and create shared reference records | `catalog.source.review`; approval audit and separation of duties decision |
| GET `/api/v1/patient-purchases/` | `CurrentSuperuser`; purchase joined to patient and filtered by required pharmacy_id | Platform superuser only; requested pharmacy ID is not membership-authorized because caller is platform superuser | Separate platform support capability; purpose-bound PHI access and audit |
| GET `/api/v1/patient-purchases/{patient_id}/history` | `CurrentUser`; explicit active membership, active patient owned by pharmacy, required purpose; platform superuser explicitly denied | Any non-superuser active member of that pharmacy can read minimum-field purchase history; allowed/denied PHI audit rows are added to session | `patients.purchase_history.read` plus explicit clinical role and purpose policy |
| GET `/api/v1/dashboard/summary` | `CurrentUser` + `resolve_pharmacy_scope`; one active membership required unless explicit authorized pharmacy, superuser may remain global | Any active pharmacy member receives operational KPIs **and patient-level names, purchase aggregates and medication history**; no purpose parameter or PHI audit in this handler | Split operational dashboard permissions from patient-level dashboard/PHI permissions; default patient-level panels denied unless explicitly authorized |
| GET `/api/v1/medical-devices/search` | `CurrentUser`; shared reference catalog query | Any active authenticated user; no pharmacy scope | `medical_devices.reference.read`; shared reference-data access may be global by design |
| GET `/api/v1/ai/context` | `CurrentUser`; active pharmacy membership list (or all active pharmacies for superuser) | Any active user can enumerate their pharmacy IDs; non-superuser response substitutes names with `Pharmacy #id` | `ai.context.read`; return only authorized memberships and selected context |
| POST `/api/v1/ai/query` and POST `/api/v1/ai/query/stream` | `CurrentUser` + pharmacy tenant check; optional patient must be active and owned by same pharmacy; patient and purpose required together | Any active member of pharmacy can invoke AI; selected-patient context permits three controlled purpose strings. MCP context binds user, pharmacy, patient and purpose; session ID is HMAC-scoped to user/tenant/patient/purpose | Separate `ai.query` from `patients.phi.read`; enforce clinical role + purpose + patient ownership before MCP tool access |
| GET `/api/v1/ai/tools` | `CurrentUser`; tool list filtered by `current_user.role` | Role-filtered MCP tool discovery; current account role is not a pharmacy membership role, so it cannot distinguish cashier/pharmacist/manager | Tool discovery and execution must use effective pharmacy permissions, not legacy account-role labels |

### 7.1 Critical PHI finding: dashboard response is not minimal

The dashboard handler's query scoping is pharmacy-aware for non-superusers: `resolve_pharmacy_scope` selects an explicit authorized pharmacy or requires exactly one active membership. However, the response is not limited to aggregate metrics. It also returns:
- patient IDs and full names;
- each patient's purchase totals;
- patient medication rows, product names, dosage, form, quantity, prescription-required flag and expiry information;
- latest patient condition.

The endpoint accepts only `CurrentUser`, does not require a controlled access purpose, and does not write a PHI access audit record. Consequently, every active member of a pharmacy who can call the dashboard endpoint currently receives patient-level data, regardless of whether their job requires clinical access. This is a confirmed authorization/data-minimization gap, not merely a proposed design preference.

**Recommended boundary:** keep operational KPIs available under a dashboard permission, but remove patient-identifiable and patient-medication panels from the general summary response. Expose patient-level panels through a separate endpoint protected by a clinical permission, patient/pharmacy ownership, controlled purpose, and PHI audit.

### 7.2 Patient purchase history is better scoped, but role enforcement is incomplete

The dedicated patient history endpoint:
- rejects platform superusers and records a denied PHI audit event;
- requires active membership in the requested pharmacy;
- verifies the patient is active and belongs to that pharmacy;
- requires one of three declared purposes;
- limits date ranges to at most 365 days and returns a minimum set of purchase fields;
- adds an allowed PHI audit event after the read.

However, it does not check a granular pharmacy role or effective permission. Any non-superuser member can currently access the history route if they provide a permitted purpose string. A purpose supplied by the caller is not itself proof of professional authorization.

The legacy administrative list is separately superuser-only and filters purchases through the patient's pharmacy ID. It is not the same as the pharmacist history endpoint.

### 7.3 AI/MCP authorization boundary

The AI query routes correctly bind requests to an authorized pharmacy and, when a patient is selected, verify that patient is active and belongs to that pharmacy. The conversation namespace is HMAC-scoped to user, pharmacy, patient, purpose and supplied session ID. MCP context carries those same authorization dimensions.

The remaining RBAC limitation is upstream role resolution: `User.role` is a computed account-level property returning `admin` for every platform superuser and `pharmacist` for every other user. It is not a role assigned to a particular pharmacy membership. Consequently, every ordinary active account is presented to the AI tools endpoint and MCP registry as `pharmacist`; the registry's `required_roles=["pharmacist"]` check does not distinguish cashier, pharmacist, manager and pharmacy-admin grants. The patient-history tool itself does enforce exact selected-patient matching, a non-empty controlled purpose, same-pharmacy active-patient lookup, and metadata-only PHI audit with commit before returning data. These are meaningful controls, but because the upstream role is generic, they do not establish that the caller is a clinically authorized pharmacist. Patient-purpose validation and tenant binding are valuable controls, but they do not replace a pharmacy-specific clinical permission check.

### 7.4 Shared reference data vs tenant-owned data

Drug Catalog search and Medical Device search read shared reference records and do not expose patient records or pharmacy-specific stock in the reviewed handlers. Global access by authenticated users may be intentional. Keep these separate from tenant-owned sellable products, inventory, local assortment, pricing and catalog-review workflows.

### 7.5 Decisions still required

1. Should the general Dashboard return only non-identifiable operational metrics? Recommended default: yes.
2. Which pharmacy role may access patient purchase history and patient medication panels? Recommended default: deny all roles until explicitly granted; likely clinical roles only, subject to policy approval.
3. Should AI access to selected-patient context require a clinical permission in addition to membership and purpose? Recommended default: yes. The current MCP tool's pharmacist-role gate is ineffective as a pharmacy-role distinction because every non-superuser account resolves to `User.role == "pharmacist"`.
4. Which roles may review and approve imported drug reference records? Keep restricted to a designated catalog-governance capability; do not equate Pharmacy Admin with platform Superuser.
5. Are shared drug and medical-device reference searches available to every authenticated pharmacy member? This can remain a shared read capability if confirmed.



### 7.6 MCP patient-history tool: positive controls and remaining role flaw

A separate source review of `src/pharmaviyum/ai/mcp/tools/patient_history.py` confirms stronger controls inside the tool than the generic AI route alone suggests:
- the tool requires the trusted MCP context;
- model-supplied `patient_id` must exactly equal trusted `selected_patient_id`;
- a controlled purpose must be present;
- the patient must be active and belong to the trusted pharmacy;
- prescription and order counts are also constrained through the patient's pharmacy;
- allow/deny decisions are written to `PHIAccessAudit`, and the audit commit occurs before patient data is returned.

However, the tool declares `required_roles=["pharmacist"]`, while `User.role` is computed as `"admin" if is_superuser else "pharmacist"`. Therefore every non-superuser account passes the legacy pharmacist role filter. The tool's role check is not evidence that a user has been assigned the pharmacist role in the selected pharmacy. This is the precise distinction the new membership-role RBAC model must address.

Do not misclassify the MCP patient-history tool as lacking selected-patient binding or audit; those controls are present in the inspected source. The confirmed gap is the lack of pharmacy-specific role/permission resolution at the API-to-MCP boundary.

## 8. Reports, exports and background execution

Source baseline: `main` at `b5a0f51cc45e39b5afdfd21af99a5053823af5ce`. This is a targeted source search, not proof that no export feature can exist outside the searched repository paths.

### 8.1 Reports and exports

- The reviewed API tree and targeted searches did not identify a dedicated report/export endpoint or CSV/XLSX attachment implementation.
- `src/pharmaviyum/services/analytics_service.py` is empty in the reviewed revision.
- `GenerateDailyReportTask` is registered in the active custom worker, but its implementation returns `status: not_implemented`; it does not query or materialize report data.
- Therefore, do not describe report export as an implemented PHI read surface based on this source review. Treat report/export authorization as a required design gate before implementing it.
- The current `GET /api/v1/dashboard/summary` is an implemented analytics read surface and already exposes patient-identifiable and medication-level information to any active member with dashboard access; see section 7.1. This is the confirmed current risk, not a hypothetical export.

**Required controls before adding reports/exports:** explicit report-specific permission; pharmacy scope fixed server-side; minimum-field projection; purpose-bound PHI access where identifiable patient data is included; allowed/denied audit decisions; export creation/download audit; short-lived, actor-bound download grants; no public or guessable object URLs; and tests for cross-pharmacy denial, revocation, and audit-persistence failure. Background generation must carry the same authorization grant and must not broaden it.

### 8.2 Active background worker is Redis-backed, not the empty Celery scaffold

Reviewed files:
- `src/pharmaviyum/workers/dispatcher.py`
- `src/pharmaviyum/workers/worker.py`
- `src/pharmaviyum/workers/tasks/notifications.py`
- `src/pharmaviyum/workers/tasks/pos_sync.py`
- `src/pharmaviyum/workers/tasks/scheduled.py`

Findings:

1. The active worker consumes task payloads from Redis and dispatches by a hard-coded task registry. The dispatcher accepts a task name and arbitrary `task_args`; the payload has no required authenticated actor, permission/grant reference, purpose, or authorization-decision identifier.
2. The worker checks that a task name is registered and that its queue matches the task class. It does not independently validate the initiating actor's authorization or a signed, scoped job grant before execution.
3. `SendPatientNotificationTask` accepts `patient_id`, `pharmacy_id`, arbitrary `template_data`, channel and language. It correctly loads the patient using both patient ID and pharmacy ID, but it has no actor/permission provenance, no controlled-purpose field, no PHI audit event, and no template-specific allow-list for potentially sensitive values. It can send to patient phone/email destinations. This is a confirmed background PHI/communications governance gap; do not assume that tenant filtering alone proves the enqueueing actor was authorized.
4. `SyncProductsTask` scopes product reads/writes by `pharmacy_id`, which is a positive tenant predicate. The task payload still has no verified initiating actor or service-principal authorization in the worker. Other POS sync tasks are currently placeholders returning `not_implemented`.
5. `GenerateDailyReportTask` and `SyncAllPosTask` are placeholders; the former returns `not_implemented`, and the latter does not yet enumerate pharmacies or enqueue actual sync jobs.
6. `src/pharmaviyum/tasks/celery_app.py`, `src/pharmaviyum/tasks/worker.py`, `src/pharmaviyum/tasks/tasks/analytics_event.py`, `notify_new_order.py` and `sync_inventory.py` are empty in the reviewed revision. The existence of a `tasks` package and Celery-named files is not evidence of an active Celery task runtime. The worker actually inspected here is the Redis-backed implementation under `src/pharmaviyum/workers/`.

**Required controls:** define separate human-initiated and system-scheduled job principals; persist immutable actor, tenant, purpose, permission/grant ID, request/correlation ID and enqueue timestamp; validate a signed/opaque authorization grant at execution time; recheck resource ownership at execution; constrain and validate task schemas and template variables; audit patient-contact and PHI-bearing jobs; prevent sensitive payloads from appearing in logs, Redis status responses or dead-letter records; and test tenant isolation, revoked grants, retries, replay/idempotency and audit failure. A job must not inherit a caller's broad privileges merely because it runs asynchronously.

### 8.3 MCP tool inventory beyond patient history

Reviewed registered tool families:

| Tool | Current scope/control observed | RBAC / PHI conclusion |
|---|---|---|
| `search_pharmacy_products` | Trusted MCP context; inventory query constrained to `auth.pharmacy_id` | Tenant-scoped operational read; registry defaults to pharmacist/admin/system roles, but upstream legacy role mapping presents every non-superuser as pharmacist |
| `get_inventory_overview`, `get_expiring_inventory` | Trusted context; inventory rows constrained to `auth.pharmacy_id` | Tenant-scoped stock/expiry reads; same ineffective coarse role distinction |
| `get_sales_summary` | Trusted context; sales query constrained to `auth.pharmacy_id` | Tenant-scoped aggregate sales read; same role-resolution gap |
| `get_pharmacy_workflow_guide` | Static workflow guidance; no patient/tenant data query | No PHI read identified; registry role policy remains coarse |
| `get_patient_history` | Exact selected-patient match, controlled purpose, active patient/pharmacy check, PHIAccessAudit commit before response | Positive patient-level controls; role assignment remains ineffective because all ordinary accounts map to pharmacist; response fields remain broader than minimum necessary |
| `verify_prescription` | Prescription lookup joins Patient and constrains by trusted pharmacy; patient must be active | No selected-patient binding, controlled purpose, or PHIAccessAudit was found in the inspected function. Treat prescription lookup/verification as sensitive clinical access and add a clinical permission, purpose and audit before broadening access. |
| `check_drug_interactions` | Drug names supplied as input; static interaction data and RAG enrichment; no patient-record query in inspected function | No patient PHI read identified in this function. Keep patient-specific context out of generic tool arguments unless separately authorized. |
| `check_halal_compliance` | Drug/product and fiqh inputs; static compliance data in inspected function | No patient-record query identified. Avoid inferring a patient's religious affiliation from country defaults; this is a product-compliance lookup, not a patient authorization signal. |

The MCP registry defaults tools to roles `pharmacist`, `admin`, and `system` unless overridden. Tool discovery and invocation use the legacy account-level role, not a pharmacy membership role or effective permission set. The patient-history tool explicitly narrows to pharmacist, but because `User.role` maps every non-superuser to pharmacist, this does not distinguish actual pharmacy job functions. This remains a cross-cutting authorization design gap.

The prescription-verification tool is tenant-scoped, which is positive, but tenant scope alone does not establish clinical authorization. Its current implementation returns prescription validation results and performs prescription-status checks without the selected-patient/purpose/audit controls used by `get_patient_history`. The required policy should decide whether this tool is restricted to pharmacist-only and whether each lookup must be bound to the selected patient.

### 8.4 Implementation gates

1. Do not implement report/export access until the report data classification and permission/purpose model are approved.
2. Add a common job authorization envelope before enabling patient communications, PHI reports, or other sensitive asynchronous tasks.
3. Use a pharmacy membership's effective permission for MCP discovery and execution; do not use `User.role` as a proxy.
4. Add selected-patient/purpose/audit enforcement to prescription verification if it remains a patient-linked clinical operation.
5. Add integration tests for worker and MCP denial paths, including audit failure and cross-tenant payload substitution.
6. Keep all unapproved grants denied by default. These findings do not approve the proposed four pharmacy roles or any role-to-permission mapping.

## 9. Integrations, webhooks and application event flows

Source baseline: `main` at `b5a0f51cc45e39b5afdfd21af99a5053823af5ce`. This section distinguishes the legacy ERP integration API, POS payment callbacks, durable Edge synchronization, and the process-local application event bus.

### 9.1 Legacy ERP integration API is global and operator-only

Files: `src/pharmaviyum/api/v1/pharmacy_entities.py`, `src/pharmaviyum/models/erp_sync.py`.

- `ERPIntegration` has no `pharmacy_id`, owner tenant, credential reference, or service-principal identity. Its provider, endpoint and sync mode are global fields.
- `GET/POST /api/v1/erp/integrations`, `POST /api/v1/erp/integrations/{integration_id}/events`, `GET /api/v1/sync-events` and `GET /api/v1/erp/integrations/{integration_id}/events` use `CurrentSuperuser`. This is a platform-operator gate, not pharmacy-scoped integration authorization.
- The event-ingest route is not authenticated as an external provider. It requires an application superuser session; do not mistake it for a provider webhook contract.
- `ERPEventIn` accepts `event_id`, `entity_type`, optional `entity_id`, and a bounded free-form `direction`. It has no payload schema, signature, provider event timestamp, tenant binding or provider identity. The stored `ERPSyncEvent` is metadata-only in the reviewed model.
- Duplicate handling checks only whether the global `event_id` exists and returns `duplicate`; it does not compare the incoming integration/entity/direction with the stored event. Reuse of an ID with altered metadata is silently treated as duplicate rather than a protocol conflict.
- Event list endpoints are global superuser reads; no dedicated access audit was found in the inspected handlers.

**Conclusion:** this is a global administrative metadata API, not a production-ready multi-tenant connector framework. Keep it separate from Pharmacy Admin. Before external use, define integration ownership, machine identity, secret lifecycle, signed/versioned event schema, replay/idempotency semantics and operator audit.

### 9.2 POS payment webhook has HMAC authentication and state checks, but needs provider-bound replay controls

File: `src/pharmaviyum/api/v1/pos.py`, `payment_webhook`.

Positive controls:
- HMAC-SHA256 over the exact raw request body; constant-time `hmac.compare_digest`; fail-closed if `PAYMENT_WEBHOOK_SECRET` is absent.
- Only `succeeded` or `failed` states are accepted; payment must exist, be non-cash and pending; callback amount must equal the persisted amount.
- Sale/payment rows are locked before finalization; stock changes use the inventory movement service; the payment event is written to the transactional outbox in the same database transaction.
- Matching retries are idempotent; conflicting final states return 409.

Remaining controls:
- The handler's docstring explicitly delegates provider-specific signature verification to an adapter before the normalized event reaches this endpoint. This handler alone does not establish provider-specific verification, signed timestamp/nonce freshness, or credential-to-provider binding.
- `provider_name` and `provider_payment_id` are accepted from the signed body but are not compared with an expected provider identity/reference already bound to the pending payment.
- This is a machine-to-machine principal, not interactive user RBAC. Give each payment provider a distinct service identity/secret and explicit allowed operations.
- Add tests for wrong provider, stale signature, altered duplicate event, amount mismatch, concurrent callbacks and payment cross-link attempts.

This is not evidence that HMAC is absent; it identifies the boundary between the normalized shared-secret handler and provider-specific verification that must be proven in the adapter.

### 9.3 Pharmacy Edge Sync has meaningful tenant and payload controls

Files: `src/pharmaviyum/api/v1/sync.py`, `src/pharmaviyum/services/edge_identity.py`, `src/pharmaviyum/schemas/sync.py`, `src/pharmaviyum/services/outbox.py`, `src/pharmaviyum/services/outbox_dispatcher.py`.

Positive controls:
- Edge enrollment/revocation require `CurrentSuperuser`; enrollment validates an active pharmacy and returns a high-entropy credential once. Only a SHA-256 digest is stored; revoked/inactive credentials are rejected.
- Inbound pharmacy scope is derived from the authenticated Edge node registration, not the request body. The supplied `edge_node_id` must match that identity.
- Event v1 allowlists four POS lifecycle types with strict typed payload models, `extra="forbid"`, aggregate/version checks, monetary and quantity invariants, and a 256 KiB payload limit.
- Integration tests cover forged scope, cross-pharmacy Edge identity, revoked credentials, altered duplicate event content, unsupported event types and patient fields in payloads.
- Event IDs and aggregate versions are unique; identical retries are idempotently acknowledged, while altered content/conflicting versions are rejected.
- Edge outbox rows are written in the originating business transaction. Dispatcher uses HTTPS-only configuration, bounded retries, per-aggregate ordering, lease tokens/fencing and dead-letter quarantine.
- Dead-letter listing omits business payloads; replay is superuser-only and writes an `OutboxReplayAudit` with actor and reason.

Boundaries:
- POS event payloads contain product names/SKUs, lot numbers, quantities, prices and payment metadata. They exclude patient identity under the current allowlisted contract, but remain commercially sensitive.
- Central ingress stores `CentralInboxEvent` with `processing_status=accepted`; there is no Central domain consumer. `accepted` means durable receipt, not that Central applied sale/payment/inventory effects. ADR-0007 correctly blocks domain application pending product/lot mapping, actor provenance, stock semantics, ordering and reconciliation.
- Dead-letter listing is a global `CurrentSuperuser` view. Replay is audited, but support inspection/replay is not pharmacy-scoped and has no explicit time-bound support grant. Keep this a platform operations capability and consider reason-bound tenant access/read audit.
- Edge provisioning is platform-global superuser-only, not a Pharmacy Admin permission.

**Conclusion:** retain Edge identity and event-contract controls. Do not broaden v1 with patient identifiers or generic entity events. Do not implement the Central consumer until ADR-0007 prerequisites are met.

### 9.4 Generic patient lifecycle events still carry linkable identifiers

Files: `src/pharmaviyum/services/patient.py`, `src/pharmaviyum/services/event_bus.py`.

- `patient.created` was minimized to pharmacy-level metadata.
- `patient.updated` still emits `patient_id`, updated field names and optional `updated_by`; `patient.deleted` still emits `patient_id`, hard-delete flag and optional actor. Stable patient IDs are linkable personal data even without name/phone.
- The event bus is process-local and best-effort; handler exceptions are logged and swallowed. It is not durable integration delivery.
- The reviewed repository search found no in-repository `event_bus.on(...)` subscribers. That does not prove dynamic/runtime consumers cannot be registered and does not justify identifiers in a generic event contract.

**Required controls:** remove patient identifiers from generic lifecycle notifications. If a workflow needs a patient reference, define a dedicated event contract with explicit consumer identity, purpose and lookup authorization. Keep PHI out of generic telemetry and event payloads.

### 9.5 Integration/RBAC implementation gates

1. Decide which integrations are platform-global and which are pharmacy-owned; model tenant ownership explicitly.
2. Create distinct machine/service principals for each provider, Edge node and scheduled integration; keep them separate from human pharmacy roles.
3. Replace the legacy ERP metadata event contract before external use: authenticate provider, validate a versioned schema, derive tenant from credential, and reject event-ID reuse with different content.
4. Prove provider-specific signature validation, freshness/replay protection and binding to the expected payment/provider reference before production payment callbacks.
5. Preserve Edge Sync's strict allowlist, tenant derivation, idempotency, ordering and durable-receipt semantics. Keep Central domain application disabled until ADR-0007 prerequisites are met.
6. Minimize patient lifecycle events and audit privileged cross-pharmacy sync inspection/replay.
7. Test service-principal revocation, wrong-tenant credentials, altered duplicate IDs, stale/replayed callbacks, PHI payload rejection and audit failure.

These findings do not approve pharmacy role grants. Integration administration, Edge provisioning, payment callbacks and support replay are distinct machine/platform capabilities and must not be collapsed into `pharmacy_admin`.

## 10. Consolidated RBAC implementation blueprint — proposal only

This blueprint consolidates the API, Sidebar, PHI, MCP, worker and integration findings above. It is a delivery design, not authorization to implement or grant roles. The role matrix in `PHARMACY_RBAC_PERMISSION_SPEC.md` remains unapproved; unresolved policy means deny by default.

### 10.1 Target authorization decision

Every protected operation should resolve the following trusted context before accessing or mutating a resource:

1. **Principal:** authenticated human user or explicitly registered machine/service identity.
2. **Tenant:** one pharmacy resolved from a selected context and an active membership, or from a machine credential's registered pharmacy. Never derive tenant authority from a client-supplied ID alone.
3. **Action:** a stable permission identifier for the exact operation.
4. **Resource:** load the target row with tenant ownership in the SQL predicate; do not load globally and compare tenant ownership only after materialization.
5. **Additional policy:** patient ownership/care relationship, purpose of use, workflow state, approval threshold, and/or platform support grant as applicable.
6. **Audit:** persist required allow/deny decision metadata before releasing PHI or committing a privileged action. Audit failure must fail closed for governed PHI access.

Conceptual decision: `authenticated AND active_tenant AND action_permission AND resource_scope AND additional_policy`. A missing/unknown input is deny. This should be implemented as a small centralized authorization service/dependency plus resource-scoped query helpers, not as a broad general-purpose policy engine.

### 10.2 Separate human roles from machine/platform capabilities

| Principal class | Scope source | Intended responsibility | Must not inherit |
|---|---|---|---|
| Cashier / Pharmacist / Manager / Pharmacy Admin (proposed) | Active `PharmacyMembership` and approved membership role | Human pharmacy workflows | Platform-wide superuser or another pharmacy's permissions |
| Platform operator | Explicit platform capability and, for sensitive access, a time-bound support grant | Provisioning, support and operational review | Automatic clinical/PHI access |
| Payment provider | Provider-specific credential and verified signed callback | Narrow payment state callback | Interactive user permissions or arbitrary payment access |
| Pharmacy Edge node | Active enrolled `PharmacyEdgeNode` credential | Submit allowlisted events for its registered pharmacy | Other Edge nodes or direct Central domain writes |
| Background job | Persisted initiating actor or scheduled service identity plus scoped job grant | Execute one authorized task within one tenant | The caller's ambient/global privileges |
| MCP tool invocation | Trusted user, selected pharmacy, selected patient and purpose context plus effective permission | Execute one registered tool | Generic `User.role` as proof of clinical role |

### 10.3 Permission enforcement map

| Surface | Required enforcement boundary |
|---|---|
| POS checkout, cancel, refund, discount | Separate action permissions; sale and inventory rows constrained to the same pharmacy; payment provider callbacks use a separate machine identity |
| Inventory, Defectura, procurement, transfers | Action-specific permissions; selected pharmacy; object ownership in SQL; immutable movement ledger and reason/idempotency checks |
| Patients, purchases, prescriptions, clinical records | Clinical permission plus patient/pharmacy ownership, purpose-of-use policy, minimum response fields and PHI audit |
| General Dashboard | Operational aggregate permission only; remove patient-identifiable and medication-level panels from the general response |
| Clinical Dashboard panels | Separate clinical endpoint and permission; selected patient/tenant scope, purpose and PHI audit |
| Shared Drug Catalog / Medical Device reference | Explicitly approved shared-reference read capability; keep separate from pharmacy-owned assortment, stock and pricing |
| Catalog review, supplier and ERP administration | Designated governance/platform capability until ownership and separation-of-duties policy is approved |
| MCP discovery and execution | Effective pharmacy permission at both discovery and invocation; revalidate trusted context and resource scope inside the tool |
| Background jobs and notifications | Persist actor/service identity, tenant, purpose, permission/grant ID and correlation ID; revalidate scoped grant and ownership at execution |
| Reports and exports | Report-specific permission; server-derived tenant scope; minimum fields; audit export creation and download; short-lived actor-bound download authorization |
| ERP integration / payment webhook / Edge Sync | Distinct service principals and provider contracts; no mapping to human pharmacy roles |
| Support / dead-letter replay | Platform operations capability, reason-bound access and durable operator audit; no default PHI access |

### 10.4 Minimal technical architecture

- **Identity:** retain the global `User` identity; do not use `User.role` as a pharmacy role.
- **Membership:** after policy approval, add one constrained role assignment to each active pharmacy membership. A user may have different roles in different pharmacies.
- **Permission registry:** start with a versioned code-level registry mapping permission IDs to protected actions. Avoid a database-driven custom-role engine unless runtime-customizable roles become a concrete requirement.
- **Authorization dependency/service:** accept principal + selected tenant + permission; fail closed for missing membership, unknown permission, inactive membership or lookup failure.
- **Resource access:** use tenant-qualified SELECT/UPDATE/DELETE predicates and composite tenant/resource constraints where appropriate. Avoid fetching by global ID before checking ownership.
- **PHI governance:** use a shared metadata-only audit contract (actor/service, tenant, action, resource reference, purpose, request/correlation ID, timestamp, outcome); never copy clinical payloads, secrets or unnecessary patient fields into the audit record.
- **Authenticated context API:** extend `GET /api/v1/auth/me` only after API contract approval to expose selected pharmacy, memberships/roles and effective permissions. Do not return PHI or use the legacy role string as authority.
- **Frontend:** filter Sidebar destinations by implemented-route state and effective permissions for UX only. Backend remains authoritative; stale/unavailable permission context fails closed.
- **Non-HTTP execution:** use explicit job grants and service principals for workers, MCP, integrations and scheduled tasks; never rely on ambient process privileges.

### 10.5 Safe implementation sequence

| Phase | Deliverable | Gate |
|---|---|---|
| 0. Policy | Approve role set, permission IDs, role grants, PHI purposes, support access and global-vs-tenant integration ownership | Product + clinical + security approval |
| 1. Baseline tests | Runtime route-table inventory; endpoint × action × resource matrix; cross-tenant negative tests | All mounted routes identified; legacy routes distinguished |
| 2. Identity model | Membership role and safe existing-membership classification/backfill design | No automatic privileged role assignment; migration reviewed |
| 3. Authorization core | Central permission registry/dependency and tenant-qualified resource query helpers | Unit + PostgreSQL integration tests; 401/403 semantics |
| 4. PHI migration | Dashboard split, patient/prescription/purchase access, purpose and audit | Audit-before-release; ownership and failure-closed tests |
| 5. Operational domains | POS, inventory, Defectura, procurement, catalog and pharmacy administration | Per-action permissions; movement/idempotency invariants preserved |
| 6. Non-HTTP paths | MCP, notifications, workers, exports, reports and service integrations | Scoped grant validation, revocation, replay and tenant-isolation tests |
| 7. Frontend context | Authenticated context contract, selected pharmacy and Sidebar permission UX | UI tests; backend authorization independently verified |
| 8. Demo validation | Synthetic multi-pharmacy end-to-end validation and CI | No production DB changes; no migration guard bypass |
| 9. Controlled rollout | Staged enablement and rollback plan | Explicit release approval |

### 10.6 Non-negotiable acceptance criteria

- A user can hold different roles in different pharmacies; switching pharmacy changes the effective permission set.
- Client-supplied `pharmacy_id`, patient ID, sale ID, inventory ID or integration ID cannot widen scope.
- Every protected operation is checked at the backend action boundary; UI visibility never grants access.
- Unknown permission, missing membership, inactive membership, stale/revoked job grant, ambiguous patient ownership or failed authorization lookup denies access.
- PHI access is purpose-bound where required, minimum-necessary, and durably audited before data is returned.
- Platform operators and support tools are separately governed; Pharmacy Admin is never equivalent to platform superuser.
- Payment provider, Edge node, scheduled job and MCP tool identities are separate from human pharmacy roles.
- Retries, duplicate events, webhook replay, job replay and dead-letter replay cannot duplicate business effects or bypass authorization.
- All role × permission outcomes, cross-tenant attempts, revoked identities, audit failures and worker/MCP denial paths have automated tests.
- Migrations and deployments use approved workflows and environment guards; no manual production SQL or guard bypass.

**Current implementation status:** the application does not yet have this complete pharmacy-scoped RBAC model. The documents define gaps and a proposed sequence; they do not represent implemented authorization, approved role grants, or a production security certification.

## 11. Final mounted API route coverage and path corrections

Route coverage source baseline: `main` at `fb1e40fd47e1137bcff43369ececdb45953de473`.

This section supersedes any earlier shorthand path in this inventory where the live router prefix differs. It was derived from `src/pharmaviyum/main.py` and the package router actually imported there: `src/pharmaviyum/api/v1/__init__.py`. The separate `src/pharmaviyum/api/v1/router.py` is not mounted by `main.py`.

### 11.1 Live router composition

`main.py` includes `api_v1_router` at the application root, then separately includes `src/pharmaviyum/api/v1/endpoints/health.py` at the root. The actual mounted paths are therefore:

| Mounted surface | Live paths | Current access boundary | Candidate policy / gap |
|---|---|---|---|
| Legacy auth | `POST /api/v1/auth/register`, `POST /api/v1/auth/token` | Public | Registration creates an active non-superuser account but no pharmacy membership or invitation approval. Decide whether self-registration is allowed; account creation must not imply tenant access. |
| Authenticated identity | `GET /api/v1/auth/me` | CurrentUser | Returns legacy `User.role`; does not expose membership roles, selected pharmacy or effective permissions. |
| Modular auth | `POST /api/v1/auth/login/access-token`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `POST /api/v1/auth/password-recovery/{email}`, `POST /api/v1/auth/reset-password/` | Token/reset-token flows | Identity lifecycle controls; not pharmacy business permissions. Keep token revocation, one-time reset and account activation policy separate from RBAC. |
| AI | `GET /api/v1/ai/context`, `POST /api/v1/ai/query`, `POST /api/v1/ai/query/stream`, `GET /api/v1/ai/tools` | CurrentUser; query paths validate pharmacy tenant; optional patient requires patient + purpose together | Add effective pharmacy permission at both tool discovery and execution. Retain trusted MCP context and patient ownership checks. |
| Dashboard | `GET /api/v1/dashboard/summary` | CurrentUser + `resolve_pharmacy_scope` | Confirmed patient-identifiable/medication PHI exposure to all active members; split operational and clinical panels as in section 7.1. |
| Patients | `/api/v1/patients` collection, `/statistics`, `/phone/{phone}`, `/{patient_id}`, `/{patient_id}/ai-profile`, `/{patient_id}/visit`; `POST` collection, `PUT/DELETE` patient resource | CurrentUser + tenant scope; AI profile has explicit membership/patient checks and PHI audit; create/update/delete currently pass through service-level policy and tenant scope | Do not flatten to one permission. Separate patient search/read, clinical profile, create, update, archive/delete, and visit recording. Validate PHI audit coverage per operation. |
| Orders | `/orders/`, `/orders/{order_id}`, `/orders/{order_id}/status` | CurrentUser + `resolve_pharmacy_scope`; order is linked through patient | Distinguish legacy patient-linked order workflow from POS Sale/Payment. Separate read/create/status-transition permissions and enforce patient ownership in scoped queries. |
| POS | `/api/v1/pos/products/search`, `/inventory/receive`, `/products/{product_id}/lots`, `/checkout`, `/payments/webhook`, `/sales/{sale_id}/cancel`, `/sales/{sale_id}` | User endpoints use CurrentUser + tenant checks; payment callback uses HMAC service authentication | Separate POS read, inventory receive, checkout, sale read/cancel and provider callback. Current handlers lack pharmacy action-level role checks. |
| Pharmacy and inventory | `/api/v1/pharmacies`, `/api/v1/suppliers`, `/api/v1/inventory`, `/api/v1/inventory/{id}`, `/api/v1/inventory/{id}/adjustments`, `/api/v1/batches`, `/api/v1/prescriptions` | Pharmacies read: CurrentUser + memberships; create: CurrentSuperuser. Suppliers and inventory writes, batches, prescriptions: CurrentSuperuser. Inventory read: CurrentUser, membership pharmacy IDs, optional requested pharmacy filter | Inventory read is membership-scoped but not selected-context/action-permission scoped. Inventory writes and prescription APIs remain platform-superuser only. Batch model lacks pharmacy ownership; fail-closed restriction is appropriate. Prescription create must validate patient/pharmacy ownership when access is expanded. |
| Legacy ERP integration metadata | `/api/v1/erp/integrations`, `/api/v1/erp/integrations/{integration_id}/events`, `/api/v1/sync-events` | CurrentSuperuser | Global platform operations; not Pharmacy Admin. See section 9.1. |
| Drug reference search | `GET /drug-catalog/search` | CurrentUser | **Path correction:** the search router prefix is `/drug-catalog`, not `/api/v1/drug-catalog`. Shared reference read; confirm this root-level path is intentional and document one canonical API prefix. |
| Drug catalog review | `/api/v1/drug-catalog/sources`, `/api/v1/drug-catalog/sources/{id}/matches`, `/api/v1/drug-catalog/sources/{id}/review` and source creation | CurrentSuperuser | Global reference-data governance; separate from pharmacy stock/catalog read. |
| Medical-device reference | `GET /medical-devices/search` | CurrentUser | **Path correction:** live prefix is `/medical-devices`, not `/api/v1/medical-devices`. Shared reference read. |
| Pharmacy sellable Product master | `/api/v1/products/search`, `/api/v1/products/{product_id}`, `/api/v1/products/`, `POST/PUT/DELETE` | Read: CurrentUser; create/update/deactivate: CurrentSuperuser | Product model has no `pharmacy_id`; SKU is globally unique. It stores global `price` and legacy aggregate `stock` (the model/schema explicitly state per-pharmacy stock belongs to Inventory). Responses include both price and stock. Treat this as a shared/global product master, not tenant inventory. If prices differ by pharmacy, a pharmacy-scoped price/assortment model is required before exposing these fields as pharmacy-specific values. |
| Patient purchases | Legacy `/patient-purchases/` and canonical `/api/v1/patient-purchases/`; history at both `/{patient_id}/history` paths | Legacy list: CurrentSuperuser; history: CurrentUser + explicit active membership, patient ownership, purpose and PHI audit; platform superusers denied | The router is intentionally mounted twice. Maintain one documented canonical path and test both aliases until legacy removal is approved. History still lacks granular membership-role permission. |
| Pharmacy Edge Sync | `/api/v1/sync/edge-nodes`, `/edge-nodes/{node_id}`, `/outbox/dead-letter`, `/outbox/dead-letter/{entry_id}/replay`, inbound event endpoint | Provision/revoke/list/replay: CurrentSuperuser; inbound event: Edge credential authentication | Distinct platform and machine-principal policies; preserve tenant-derived Edge identity. See section 9.3. |
| User administration and self-service | `/users/me/avatar`, `/users/`, `/users/{user_id}` | Avatar operations: CurrentUser on self; list/create/read other users: CurrentSuperuser | User account administration is not pharmacy membership administration. No pharmacy-scoped membership/role assignment API is currently mounted. |
| Monitoring | Root `/health`, `/ready`, `/metrics`, `/mcp/health`, `/version`; root `/api-info` | Health/readiness/metrics/version/api-info: public; MCP health: CurrentSuperuser | Keep liveness/readiness public only as operationally required. Restrict metrics to trusted scrape network/identity. Review public version metadata (build, environment, debug flags, Python runtime). Detailed MCP health remains operator-only. |

The exact relative paths above are appended to each router's declared prefix. For collection routes shown without an HTTP method, the method follows the handler decorator in the source; the access boundary is the same for the listed handler family unless stated otherwise.

### 11.2 Router collisions and path inconsistencies

1. **Duplicate root health routes:** the mounted package aggregator includes `monitoring_router` first, registering `GET /health`, `GET /ready`, and `GET /metrics`. `main.py` then includes `endpoints.health.router`, which registers the same three method/path pairs. Both implementations are therefore registered. Starlette route matching is order-sensitive; the first matching route is the effective handler. Consolidate to one implementation and add route-table tests so readiness/metrics semantics cannot silently diverge.
2. **Mixed API prefixes:** `/api/v1` is used by several routers, but Orders, Drug Catalog search, Medical Devices, and Users use root-level prefixes. Do not assume the endpoint path from a module's directory or tag; use the mounted route table as source of truth. Choose and document a canonical versioning strategy before adding RBAC metadata or frontend clients.
3. **Patient purchases alias:** the same router is mounted at both `/patient-purchases` and `/api/v1/patient-purchases`. This is an explicit compatibility alias, not two different authorization implementations.
4. **Unused legacy router:** `src/pharmaviyum/api/v1/router.py` defines a separate `api_router` and `system_router`, including debug, feature flags and prescription placeholder routers. `main.py` does not import or mount it. Do not classify those endpoints as active production routes.
5. **Other unmounted modules:** `src/pharmaviyum/api/v1/erp.py` is not imported by the active aggregator; `endpoints/debug.py`, `endpoints/docs.py`, `endpoints/feature_flags.py` and `endpoints/prescriptions.py` are not included by the active package aggregator. `examples.py` contains examples, not live endpoints. Any future mounting requires a fresh authorization review.

### 11.3 Additional authorization and data-governance findings

**Public account registration**
- `POST /api/v1/auth/register` accepts an unauthenticated registration, creates an active non-superuser account and does not create a pharmacy membership.
- This does not itself grant access to tenant-scoped data, but there is no invite/approval or pharmacy onboarding decision in this route.
- Decide whether public self-registration is intended for the demo and for production separately. Production onboarding should use an invitation or controlled membership-assignment flow; never infer a pharmacy or role from an email domain.

**Global Product master**
- `Product` has no pharmacy foreign key and its SKU is globally unique. The API is therefore global product-master CRUD, not per-pharmacy inventory.
- `ProductResponse` exposes `price` and legacy `stock`; `ProductCreate/Update` allow those values. The model/schema say per-pharmacy stock is authoritative in `Inventory`.
- This is a semantic/data-model risk if clients interpret the returned price/stock as selected-pharmacy values. Before adding pharmacy roles, define whether product master price is global reference data or whether pharmacy-specific price/assortment must be modeled separately. Never use the global legacy `stock` field for pharmacy authorization or availability decisions.

**RAG ingestion Celery boundary**
- `POST /api/v1/ingest/documents/upload` and `/documents/url` require both `CurrentSuperuser` and `CurrentUser`, then call `require_pharmacy_tenant`. Ordinary non-superusers therefore need active membership; platform superusers use the existing bypass.
- The task config carries the authorized `pharmacy_id`; the Celery task requires a positive integer and stamps it onto each document before chunking. Uploaded object keys are validated against that pharmacy.
- The worker does not receive a persisted initiating actor, approved membership role, purpose, permission ID or signed job grant; its trust boundary is the Celery broker and caller-provided task config. The Redis progress record stores pharmacy metadata, while `GET /api/v1/ingest/jobs/{job_id}` and list jobs are global CurrentSuperuser-only views.
- Treat ingestion as a distinct high-privilege content-management action. Before allowing a pharmacy-level administrator role, add explicit ingestion permission, immutable actor/tenant provenance, a scoped worker grant validated at execution, and tenant-aware job status access. Review external URL fetch controls separately (SSRF/egress policy); URL scheme validation alone is not a complete destination policy.

**Public operational metadata**
- The root monitoring routes `/health`, `/ready`, `/metrics` are unauthenticated in the mounted implementation. The separate `/version` endpoint returns build/environment/debug/runtime metadata, also without an auth dependency.
- Public health/readiness may be operationally necessary, but metrics and detailed runtime identity should be restricted to trusted monitoring networks or a scrape identity. Avoid returning exception details or secrets from readiness; current monitoring readiness reports exception class names only.
- `/mcp/health` is protected by CurrentSuperuser, which is the correct separation for detailed dependency/tool diagnostics.

### 11.4 Route-level implementation gate

Before coding the permission registry, generate a runtime FastAPI route table from the actual app instance and snapshot method, path, endpoint function, dependencies, response model and router source. Assert no duplicate method/path registrations except explicitly approved aliases. The static source inventory above is a review baseline, not a substitute for that runtime snapshot or endpoint tests.

No new route or permission is approved by this inventory. Existing CurrentUser/CurrentSuperuser checks remain the current controls until a separate policy approval and implementation PR.
