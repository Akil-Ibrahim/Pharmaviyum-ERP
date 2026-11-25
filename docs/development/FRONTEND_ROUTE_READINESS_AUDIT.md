# Frontend Route and Workflow Readiness Audit

**Audit date:** 2026-11-25  
**Audited application revision:** `main` at `7a03b7da1508d1ef92f63346880d9b331d55eba8`  
**Scope:** Authenticated route inventory, page-component renderability, pharmacy workflow entry points, and dashboard data provenance  
**Method:** Read-only GitHub source inspection; no local execution or runtime validation  
**Status vocabulary:** Implemented · Partially implemented · Missing · Intentionally disabled · Not verified

## 1. Executive summary

The frontend has a working routing and component foundation, but the authenticated route inventory currently overstates the set of usable workflows. Several routes resolve to components that intentionally render nothing; the POS and Dashboard feature entry points also return `null`. This is a route/readiness issue: a URL can exist in the route tree without delivering a user workflow.

The audit distinguishes three different cases:

1. **Critical entry points with empty feature components:** Dashboard and POS.
2. **Explicitly disabled route placeholders:** pharmacy and business entities whose source comments say the standalone UI was intentionally removed while the entity remains in navigation.
3. **Other route components returning null:** Sync Events, ERP Systems, and Mortarium AI.

The Products page is not empty, but it is a limited generic product/stock list. It must not be treated as a clinically complete medication master or inventory workflow.

This document is an implementation-readiness audit, not a product-scope decision. A disabled page may be an intentional product decision, but a visible navigation entry that leads to a blank page is still a broken user experience unless it is hidden, disabled with explanation, redirected, or replaced by a meaningful placeholder.

## 2. Critical entry-point findings

### R-01 — Dashboard route resolves to an empty component

- **Status:** Missing
- **Severity:** Critical — primary authenticated landing page
- **Evidence:** `src/routes/_authenticated/index.tsx` registers the authenticated index route with `Dashboard`; `src/features/dashboard/index.tsx` implements `Dashboard()` as `return null`.
- **Impact:** The primary authenticated route renders no dashboard content. The presence of dashboard chart/card component files does not change this because the route-level Dashboard component does not render them.
- **Acceptance evidence:** The route renders a real dashboard with clearly defined data contracts, loading/error/empty states, accessible metrics and links to supported workflows. Metrics must be sourced from authoritative APIs and scoped to the authenticated tenant/pharmacy.

### R-02 — POS route resolves to an empty component

- **Status:** Missing
- **Severity:** Critical — core pharmacy workflow
- **Evidence:** `src/routes/_authenticated/pos.tsx` registers `/pos` with `Pos`; `src/features/pos/index.tsx` implements `Pos()` as `return null`.
- **Impact:** The route renders no POS workflow. It does not evidence basket lifecycle, product/medication validation, stock/batch allocation, authoritative price calculation, payment state, sale confirmation, receipt, audit trail, or failure recovery.
- **Acceptance evidence:** Approved backend/domain contracts plus end-to-end sale tests covering normal, rejected, duplicate, stale-stock and failed-payment paths. Prescription-controlled dispensing must follow the approved pharmacy contract.

## 3. Explicitly disabled authenticated route placeholders

The following route files contain comments stating that the entity remains in the sidebar while its standalone UI has intentionally been removed, and the route component returns `null`:

| Route | Source file | Readiness |
|---|---|---|
| `/orders` | `src/routes/_authenticated/orders.tsx` | Intentionally disabled; blank route |
| `/batches` | `src/routes/_authenticated/batches.tsx` | Intentionally disabled; blank route |
| `/patients` | `src/routes/_authenticated/patients.tsx` | Intentionally disabled; blank route |
| `/suppliers` | `src/routes/_authenticated/suppliers.tsx` | Intentionally disabled; blank route |
| `/inventory` | `src/routes/_authenticated/inventory.tsx` | Intentionally disabled; blank route |
| `/transfers` | `src/routes/_authenticated/transfers.tsx` | Intentionally disabled; blank route |
| `/pharmacies` | `src/routes/_authenticated/pharmacies.tsx` | Intentionally disabled; blank route |
| `/procurement` | `src/routes/_authenticated/procurement.tsx` | Intentionally disabled; blank route |
| `/prescriptions` | `src/routes/_authenticated/prescriptions.tsx` | Intentionally disabled; blank route |
| `/drug-reference` | `src/routes/_authenticated/drug-reference.tsx` | Intentionally disabled; blank route |
| `/expiry-control` | `src/routes/_authenticated/expiry-control.tsx` | Intentionally disabled; blank route |
| `/patient-purchases` | `src/routes/_authenticated/patient-purchases.tsx` | Intentionally disabled; blank route |
| `/drug-catalog-review` | `src/routes/_authenticated/drug-catalog-review.tsx` | Intentionally disabled; blank route |

**Navigation confirmation:** `src/components/layout/data/sidebar-data.ts` still exposes these route destinations in the Operations navigation. `src/components/layout/data/sidebar-data.test.ts` asserts the Inventory and Procurement child labels and the Operations group order, but does not assert that each destination renders a usable page or an intentional disabled state.

**Finding:** These routes should not be counted as implemented merely because TanStack Router registers them. The source comments indicate deliberate removal, so this audit does not classify them as accidental regressions. However, retaining visible navigation affordances to blank routes is inconsistent with a production-ready workflow. The current navigation test protects labels/order, not route readiness.

**Required product/engineering decision for each route:**
- restore a supported workflow;
- remove or hide its navigation item until it is supported;
- show an explicit, accessible not-yet-available state with an owner/next step; or
- redirect to a supported parent workflow when that is semantically correct.

Do not restore these pages by inventing API endpoints or domain behavior.

## 4. Other empty route components

| Route | Source file | Finding |
|---|---|---|
| `/sync-events` | `src/routes/_authenticated/sync-events.tsx` | `SyncPage()` returns `null` |
| `/erp-systems` | `src/routes/_authenticated/erp-systems.tsx` | `ERPPage()` returns `null` |
| `/mortarium-ai` | `src/routes/_authenticated/mortarium-ai.tsx` | `MortariumAI()` returns `null` |

- **Status:** Missing
- **Severity:** High where the corresponding navigation entries are visible; otherwise medium pending product-scope confirmation.
- **Acceptance evidence:** Every reachable route must render a meaningful page, redirect, or explicit empty/disabled state. A route returning an empty React tree is not an acceptable user-facing state.

## 5. Products page: generic catalog, not pharmacy-grade medication workflow

- **Status:** Partially implemented
- **Severity:** High
- **Evidence:** `src/features/pharmaviyum/products.tsx` requests `/api/v1/products/?limit=50`, stores the first response in local component state, and filters that in-memory array. The local TypeScript model is `id`, `name`, `sku`, `description`, `price`, `stock`, and `is_active`.
- **Additional evidence:** The page calculates a catalog stock value and formats it as USD using a hard-coded `en-US` locale and `currency: 'USD'`.
- **Impact:**
  - No server-side search, sorting, or pagination is evidenced.
  - The model does not evidence active ingredient, brand/generic relationship, strength, dosage form, route, pack size, manufacturer, barcode, or medication identifier.
  - No batch/lot, expiry, FEFO, stock-location, stock movement, or reservation workflow is evidenced by this page.
  - Client-side stock value calculation and hard-coded USD presentation are not a trusted financial/inventory source of truth.
  - The search control has a placeholder but no explicit programmatic label; the table has no caption; async loading/error/empty messages lack explicit live-region semantics in this component.
- **Acceptance evidence:** A versioned API contract with tenant/pharmacy scope, server-side query semantics, canonical medication identity, currency sourced from trusted pharmacy context, stock/batch/expiry workflow contracts, and tests for ambiguous identity and inventory invariants.

## 6. Dashboard chart components contain generated demo values

- **Status:** Present in dormant components; not currently rendered by the Dashboard entry point
- **Severity:** High if mounted in a production dashboard without replacement
- **Evidence:** `src/features/dashboard/components/overview.tsx` generates monthly totals with `Math.random()`; `src/features/dashboard/components/analytics-chart.tsx` generates chart values with `Math.random()`. The route's current `Dashboard()` component returns `null`, so this audit does not claim these charts are currently visible to users.
- **Impact:** Randomly generated metrics are non-deterministic demo data and must never be presented as actual sales, stock, patient, or pharmacy KPIs.
- **Acceptance evidence:** Replace demo values with typed API responses; define metric semantics, date range, timezone, currency, tenant/pharmacy scope, aggregation and empty/error states. Tests should use deterministic fixtures. Clearly label any intentionally retained demo mode.

## 7. Dead or incomplete feature component

- **Status:** Missing implementation in inspected component; route usage not established
- **Severity:** Low/medium pending reference analysis
- **Evidence:** `src/features/users/index.tsx` exports `Users()` returning `null`. The inspected `/users` route currently renders a generic `EntityPage`, so this component was not proven to be the active route implementation.
- **Action:** Confirm references and remove, implement, or document the unused component. Do not infer route behavior from an unused export.

## 8. Readiness and remediation backlog

| Priority | Work item | Exit criteria |
|---|---|---|
| P0 | Restore Dashboard and POS entry points | Real API-backed page behavior, domain contracts, loading/error/empty states, critical E2E and human domain review |
| P0 | Decide navigation behavior for intentionally disabled pharmacy routes | No visible navigation item leads to a blank page; decisions documented per route |
| P1 | Resolve Sync Events, ERP Systems and Mortarium AI empty routes | Implement, explicitly defer with accessible state, redirect or remove navigation |
| P1 | Upgrade Products from generic catalog to pharmacy-grade catalog | Canonical medication identity, server-side query/pagination, trusted currency, batch/expiry/FEFO contract |
| P1 | Replace dashboard demo metrics before mounting charts | Typed authoritative API contract, deterministic tests, explicit metric definitions |
| P1 | Add route readiness checks | Automated inventory/test that detects user-facing route components returning an empty tree or routes lacking a meaningful state |
| P2 | Remove or resolve dead empty feature exports | Reference analysis, ownership decision, no misleading unused implementation |
| P2 | Add route-level accessibility and responsive validation | Automated scan plus keyboard/manual verification for each critical route |

## 9. Route readiness engineering standard

A route is considered **implemented** only when all applicable conditions hold:

1. It renders a meaningful page, an intentional redirect, or a designed empty/disabled state.
2. It has an explicit loading, error, empty and success state where remote data is involved.
3. Its navigation visibility matches authorization and product availability.
4. Its data comes from a documented, typed and authorized contract.
5. Critical domain invariants are enforced by the backend and reflected accurately in UI state.
6. Interactive controls have accessible names, semantics, keyboard behavior and status announcements.
7. Tests cover success, failure, boundary and unauthorized behavior proportionate to risk.
8. Navigation tests verify both information architecture and the renderability/readiness of every visible destination.
9. The page does not expose demo/random data as production facts.

A registered route, a component file, a screenshot, or a passing TypeScript build is not sufficient evidence by itself.

## 10. Limitations

- The inspection is bounded to named route and feature files at the audited `main` revision.
- The sidebar source and its unit test were inspected; navigation destinations are present in source, but visibility/permissions were not runtime-tested in a browser.
- No local build, tests, browser session, screen-reader, axe scan, API/backend audit, tenant-isolation test, or performance measurement was performed.
- The route list is based on source search and individual inspection of identified matches; it is not a formal AST-wide static analysis.
- No application source, backend, dependencies, lockfiles, API contracts or deployment settings were changed.

## References

- [Frontend Implementation Audit](./FRONTEND_IMPLEMENTATION_AUDIT.md)
- [Frontend Engineering Standards](./FRONTEND_ENGINEERING_STANDARDS.md)
- [Frontend Engineering Maturity Model](./FRONTEND_ENGINEERING_MATURITY_MODEL.md)
- [TanStack Router](https://tanstack.com/router/latest)
