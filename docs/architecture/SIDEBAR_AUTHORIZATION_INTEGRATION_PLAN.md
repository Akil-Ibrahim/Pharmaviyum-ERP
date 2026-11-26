# Sidebar Authorization Integration Plan

- **Status:** Architecture proposal — not approved for implementation
- **Date:** 2026-11-26
- **Related proposal:** [Pharmacy-Scoped RBAC Permission Specification](PHARMACY_RBAC_PERMISSION_SPEC.md)
- **Related UI:** `frontend/shadcn-admin/src/components/layout/data/sidebar-data.ts`
- **Related API:** `GET /api/v1/auth/me`

## 1. Current implementation findings

The current main branch has a presentation-only navigation model:

- `AppSidebar` renders the static `sidebarData.navGroups` array.
- Navigation items have `disabled` and `disabledReason`, but no permission metadata.
- The current `_authenticated` route guard checks only whether an access token exists.
- The frontend auth store holds a legacy `role: string[]` field.
- `GET /api/v1/auth/me` currently returns `accountNo`, `email`, `role`, and `exp`; it does not return pharmacy memberships, active pharmacy context, or action permissions.
- Backend `User.role` is currently derived from `is_superuser` (`admin` or `pharmacist`); it is not a pharmacy-scoped role.
- `PharmacyMembership` currently establishes active tenant membership only. It has no persisted role.
- `require_pharmacy_tenant` verifies membership for ordinary users, but it does not authorize a resource action.

These are observations of the current code, not a statement that RBAC is implemented.

## 2. Target responsibility boundaries

Keep three separate responsibilities:

1. **Navigation availability:** whether a destination is implemented and may be shown as an active link.
2. **User interface visibility:** whether the authenticated user has a permission to see or enter a navigation destination in the selected pharmacy context.
3. **Backend authorization:** whether the authenticated principal may perform a specific action on a specific resource in the requested tenant.

The backend remains authoritative. Hiding a navigation item, disabling a button, or guarding a client route is not an access-control boundary.

## 3. Proposed navigation metadata

After the permission vocabulary and role matrix are approved, add optional permission metadata to navigation item types. Use explicit permission identifiers, for example:

| Navigation destination | Candidate visibility permission |
|---|---|
| Dashboard | A dashboard-specific read permission, or an explicitly documented authenticated-member baseline |
| POS | `pos.read` |
| Clinical Care / Patients | `patients.read` |
| Clinical Care / Prescriptions | `prescriptions.read` |
| Inventory / Drug Catalog | `catalog.read` |
| Inventory / Stock Management | `inventory.read` |
| Inventory / Transfers | `inventory.read` plus a future transfer-specific read permission if needed |
| Inventory / Defectura | `defectura.read` |
| Procurement / Suppliers | `suppliers.read` |
| Procurement / Purchase Orders | `procurement.read` |
| Procurement / Receiving | `procurement.read` |
| Pharmacies | A separately approved pharmacy-administration/read permission |
| Administration / Users | A separately approved user/member administration permission |
| Settings | A documented account-settings baseline or a pharmacy-settings permission, depending on the actual page scope |
| System / Background Tasks | A separately approved operational/system permission |

This table is an integration mapping proposal, not approval to grant any permission. Do not infer that a read permission grants create, update, approve, dispense, refund, export, or administrative actions.

Items that are not implemented remain disabled regardless of permission. Permission metadata must not turn an unavailable route into an active route.

## 4. Proposed authenticated context contract

The current `GET /api/v1/auth/me` response is insufficient for permission-aware navigation. Before frontend integration, define a backward-compatible authenticated-context contract that can represent:

- canonical user identity;
- active pharmacy context, if selected;
- the user's active pharmacy memberships and their assigned roles, without exposing unrelated tenant data;
- effective action permissions for the selected pharmacy context;
- platform-level capabilities only when separately governed;
- a context/version marker if permissions or the selected pharmacy can change during a session.

The exact response shape, pharmacy-selection flow, and refresh/invalidation behavior require API design review. Do not treat the legacy `role: ["admin"]` or `role: ["pharmacist"]` values as authoritative pharmacy roles.

Do not place PHI, patient identifiers, or broad patient lists in the navigation context.

## 5. Proposed frontend behavior

Once the API contract is approved:

1. Load authenticated context after login and when the selected pharmacy changes.
2. Derive visible navigation from the static IA plus implemented-route state plus effective permissions.
3. Keep the approved group and item order unchanged.
4. Keep unavailable destinations disabled; do not show them as enabled merely because a permission is present.
5. Do not show a parent group if all of its children are unavailable or unauthorized, unless product explicitly wants a visible disabled group.
6. Refresh or invalidate the context after membership/role changes and on an authorization failure that indicates stale context.
7. Do not persist permissions as trusted client-side authority. A browser store is presentation state only.
8. Do not silently fall back to a broader role or show all navigation if the context request fails. Fail closed for permission-dependent destinations while preserving safe account/session recovery UI.

## 6. Backend enforcement requirements

- Enforce tenant membership and the specific action permission on every protected API operation.
- Resolve tenant scope from trusted authenticated context; never trust a client-supplied pharmacy identifier before authorization.
- Apply resource ownership checks after tenant authorization, especially for patients, prescriptions and other PHI.
- Return consistent 401 for unauthenticated requests and 403 for authenticated requests lacking authorization.
- Apply the same policy to API routes, background jobs, exports, reports, MCP tools and integrations.
- Treat permission lookup failures, unknown permissions, missing roles and ambiguous tenant ownership as deny.
- Keep platform support/superuser access separate from pharmacy roles and governed by an explicit audited policy.

## 7. Test plan

Frontend:
- Navigation remains in the approved IA order for each permission set.
- Unauthorized destinations are not rendered as active links.
- Unimplemented destinations remain disabled for every role.
- Empty, stale, malformed and unavailable permission context fails closed.
- Parent groups behave correctly when no child destination is visible.
- Existing Dashboard and POS navigation regressions remain covered.

Backend:
- Every protected endpoint checks the exact action permission.
- Cross-pharmacy identifiers are denied.
- UI visibility does not change API authorization outcomes.
- Role changes and membership deactivation invalidate or refresh effective context.
- PHI ownership and audit requirements are tested independently of navigation.
- Background and non-HTTP execution paths preserve tenant and permission context.

## 8. Delivery sequence and gates

1. Approve the role set, permission vocabulary and unresolved decisions in the RBAC specification.
2. Complete the API/resource-to-permission inventory.
3. Approve the authenticated-context API contract and pharmacy-selection behavior.
4. Agree on safe legacy membership classification and migration/backfill behavior.
5. Implement centralized backend authorization with unit and cross-tenant integration tests.
6. Expose the approved effective permission context to the frontend.
7. Connect Sidebar visibility and route UX to that context.
8. Validate with synthetic Demo data and the existing CI suite before any deployment.

This document authorizes no code changes, schema changes, migrations, manual SQL, permission grants, merge, or deployment. Keep the existing Sidebar behavior until the required policy and API decisions are approved.
