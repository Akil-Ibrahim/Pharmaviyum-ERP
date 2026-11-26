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
