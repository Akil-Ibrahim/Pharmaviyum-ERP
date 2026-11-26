# Current API Authorization Gap Inventory

- **Status:** Read-only engineering findings for RBAC planning
- **Date:** 2026-11-26
- **Base reviewed:** `main` at `b5a0f51cc45e39b5afdfd21af99a5053823af5ce`
- **Related:** `PHARMACY_RBAC_PERMISSION_SPEC.md`, `SIDEBAR_AUTHORIZATION_INTEGRATION_PLAN.md`

This inventory records concrete authorization patterns found in the current source. It is not a complete endpoint audit and does not approve any role or permission grants. Verify router mounting and runtime exposure before treating any module as externally reachable.

## 1. High-priority findings

### 1.1 Prescription router currently has no authentication dependency

File: `src/pharmaviyum/api/v1/endpoints/prescriptions.py`

The placeholder router is included by the legacy `src/pharmaviyum/api/v1/router.py` aggregator. However, the runtime application imports `api_v1_router` from `src/pharmaviyum/api/v1/__init__.py` in `src/pharmaviyum/main.py`; that runtime aggregator does not include `prescriptions_router`. Therefore these handlers are present in source but are not mounted by the reviewed runtime aggregator. See section 3.2. Its current handlers:

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
