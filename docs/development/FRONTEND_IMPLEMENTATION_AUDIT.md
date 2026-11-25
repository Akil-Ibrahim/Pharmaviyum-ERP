# Frontend Implementation Audit — Baseline

**Audit date:** 2026-11-25  
**Audited application revision:** `main` at `7a03b7da1508d1ef92f63346880d9b331d55eba8`  
**Application area:** `frontend/shadcn-admin/`  
**Audit type:** Read-only source inspection; no runtime or manual assistive-technology validation  
**Status vocabulary:** Implemented · Partially implemented · Missing · Not verified

## 1. Executive summary

The repository contains a substantial React/Vite admin foundation: file-based TanStack Router, route generation during build, reusable shadcn/Radix primitives, React Hook Form + Zod, Vitest Browser tests, and Playwright browser tests. This is a credible application foundation, but the inspected evidence does not establish WCAG 2.2 AA conformance, production-grade pharmacy workflows, measured performance, or end-to-end privacy/tenant isolation.

The highest-priority finding in the inspected pharmacy surface is that the POS route is registered but its page component currently returns `null`. The Products page is a functional initial catalog view, but it is a generic product/stock list rather than a complete medication and inventory workflow.

This is a bounded baseline, not a full repository certification. Findings apply to the named files and inspected surfaces; absence from those files is not proof that no implementation exists elsewhere.

## 2. Findings

### F-01 — POS route has no rendered workflow

- **Status:** Missing
- **Severity:** Critical for the POS feature
- **Evidence:** `src/routes/_authenticated/pos.tsx` registers the authenticated `/pos` route and renders `Pos`; `src/features/pos/index.tsx` implements `Pos()` as `return null`.
- **Impact:** The route can resolve without rendering a point-of-sale workflow. No sale lifecycle, basket, payment, dispensing, stock decrement, or receipt behavior is present in this component.
- **Acceptance evidence required:** A pharmacist can complete a controlled end-to-end sale with validated product identity, stock/batch selection, pricing, payment state, audit trail, and failure/rollback behavior. Prescription-controlled dispensing must follow the pharmacy domain contract.
- **Boundary:** This finding is about the inspected frontend route/component; backend POS capabilities were not assessed here.

### F-02 — Products view is an initial generic catalog, not a medication master/inventory workflow

- **Status:** Partially implemented
- **Severity:** High
- **Evidence:** `src/features/pharmaviyum/products.tsx` requests `/api/v1/products/?limit=50`, keeps the result in local component state, and filters the loaded array in the browser. The displayed model contains only `id`, `name`, `sku`, `description`, `price`, `stock`, and `is_active`.
- **Impact:** This page does not demonstrate medication identity fields such as active ingredient, strength, dosage form, route, pack size, manufacturer, or barcode, nor lot/batch, expiry, FEFO, or stock-movement handling. A fixed first-page limit and client-only filtering do not establish complete catalog search or scalable pagination.
- **Additional concern:** Monetary values are formatted as USD in this component. The inspected code does not show a tenant/pharmacy currency contract or currency sourced from the API.
- **Acceptance evidence required:** Explicit medication/product identity schema; server-side query, sorting and pagination; tenant-scoped currency; batch/expiry and FEFO workflows; tests for duplicate/ambiguous medication identities and stock invariants.
- **Boundary:** These fields and workflows may exist in other backend or frontend modules; they are not evidenced by this page.

### F-03 — Products table and search need stronger accessible semantics

- **Status:** Partially implemented
- **Severity:** High
- **Evidence:** The Products page renders a native `table` with header cells but no `caption`; its search `Input` has only a placeholder and no explicit label or `aria-label`. The search icon is decorative but is not marked `aria-hidden`.
- **Impact:** The table's purpose and the search control's accessible name are not explicitly exposed. Placeholder text is not a robust substitute for a persistent programmatic label.
- **Acceptance evidence required:** Accessible name for search; table caption or equivalent labelled relationship; explicit header associations where appropriate; keyboard and screen-reader verification at representative viewport sizes.

### F-04 — Products loading, error and empty states exist, but dynamic announcements are not evidenced

- **Status:** Partially implemented
- **Severity:** Medium
- **Evidence:** The Products page renders loading, error, and no-results messages. The inspected messages are ordinary paragraphs; no live-region or alert semantics are present in this component.
- **Impact:** Asynchronous status changes may not be announced reliably to assistive technology.
- **Acceptance evidence required:** Appropriate `role=status` / `aria-live` for non-urgent loading/results and `role=alert` for actionable errors, avoiding duplicate announcements; test with keyboard and screen reader.

### F-05 — Authentication form has a reusable validation foundation and focused E2E coverage

- **Status:** Partially implemented
- **Severity:** Medium
- **Evidence:** `src/features/auth/sign-in/components/user-auth-form.tsx` uses React Hook Form, Zod, FormLabel, FormControl, and FormMessage; `e2e/auth.spec.ts` covers sign-in rendering, required-field validation, an API error, and forgot-password validation. The shared form primitive sets `aria-invalid` and `aria-describedby`.
- **Gap:** The inspected FormMessage implementation does not add an explicit live announcement role. The E2E file covers authentication only, not the critical pharmacy journeys.
- **Acceptance evidence required:** Keyboard-only form completion, announced validation/error changes, focus management, password-manager behavior, and end-to-end tests for core pharmacy tasks.

### F-06 — Automated test infrastructure exists, but the evidence is not broad enough for pharmacy acceptance

- **Status:** Partially implemented
- **Severity:** High
- **Evidence:** The frontend package defines Vitest Browser tests and Playwright E2E tests. The source tree contains 24 `*.test.*` files and one Playwright spec file (`e2e/auth.spec.ts`). Vitest is configured to run in Chromium; Playwright defines desktop Chromium and mobile Chromium projects.
- **Gap:** The inspected E2E suite is authentication-focused. No axe-core or equivalent accessibility scanner, visual-regression suite, or dedicated POS/catalog/inventory/dispensing E2E coverage was found in the inspected frontend tree.
- **Acceptance evidence required:** Risk-based test matrix spanning unit, component, API contract, integration, E2E, accessibility automation, and visual regression; critical pharmacy flows must be release-gated.

### F-07 — Route code splitting and generated route-tree lifecycle are configured

- **Status:** Implemented
- **Severity:** Positive control
- **Evidence:** `vite.config.ts` enables TanStack Router `autoCodeSplitting`; `package.json` build script runs `generate-routes` before `vite build` and `tsc -b`; generated `src/routeTree.gen.ts` is present.
- **Guardrail:** Treat `routeTree.gen.ts` as generated output. Change route source files and regenerate through the declared build workflow; do not hand-edit the generated tree.

### F-08 — Performance budgets and measured runtime baselines are not verified

- **Status:** Not verified
- **Severity:** Medium
- **Evidence:** The inspected Vite configuration enables route-level code splitting, but no measured Core Web Vitals report, bundle-size budget, route performance budget, or large-catalog benchmark was provided by the inspected files.
- **Acceptance evidence required:** Capture reproducible production-build bundle metrics and field/lab Core Web Vitals; define budgets only after a baseline; benchmark realistic medication catalog/table sizes and slow-network behavior.

### F-09 — Patient-data privacy and tenant isolation are not verified by this frontend audit

- **Status:** Not verified
- **Severity:** Critical assurance gap
- **Evidence:** The inspected files do not establish backend authorization, tenant-scoped data access, patient-context isolation, or privacy-safe telemetry end to end.
- **Acceptance evidence required:** Backend-enforced authorization and tenant isolation; negative cross-tenant tests; patient-context separation tests; safe logging/telemetry review. Frontend route guards must not be treated as the security boundary.

## 3. Accessibility conclusion

**WCAG 2.2 AA conformance: Not verified.**

The code includes useful accessibility foundations: Radix primitives, focus-visible styling in the shared Input, labelled authentication fields, an explicit sidebar-toggle label, and a skip-link component. These are positive implementation signals, not conformance evidence.

The skip-link component points to `#content`; the target must be verified in the rendered authenticated route tree. Static inspection alone cannot establish focus order, focus visibility in all themes, contrast, reflow/zoom, target size, screen-reader announcements, or correct dialog/menu keyboard behavior.

Required next validation:
1. Automated axe scan on representative routes and states.
2. Keyboard-only walkthrough of navigation, dialogs, tables, forms, and POS.
3. Manual screen-reader checks for status, errors, table navigation, and dynamic updates.
4. Contrast and 200%/400% zoom/reflow checks.
5. WCAG 2.2 AA issue log with route, criterion, reproduction, severity, and retest evidence.

## 4. Prioritized remediation backlog

| Priority | Work item | Exit evidence |
|---|---|---|
| P0 | Implement the POS route workflow | End-to-end sale/dispensing tests, stock and audit invariants, failure recovery |
| P0 | Establish medication identity and inventory contracts | API/domain contract plus FEFO, batch/expiry, and tenant-scoped acceptance tests |
| P1 | Complete Products search and pagination | Server-side search/filter/sort/page contract; currency from trusted pharmacy context |
| P1 | Fix table/search semantics and async announcements | axe + manual keyboard/screen-reader checks |
| P1 | Add pharmacy-critical Playwright flows | POS, product lookup, stock receipt/adjustment, batch/expiry and role-boundary coverage |
| P1 | Verify tenant and patient-context isolation | Negative authorization and isolation tests across backend/API/UI |
| P2 | Establish measured performance baselines | Bundle report, Core Web Vitals, large-catalog benchmark and calibrated budgets |
| P2 | Add visual regression where it protects high-value workflows | Stable route/state screenshots with reviewed baselines |

## 5. Validation and limitations

- Source inspected at `main` commit `7a03b7da1508d1ef92f63346880d9b331d55eba8`.
- Inspected package scripts/dependencies, shadcn configuration, Vite/Vitest configuration, Playwright configuration, route wiring, POS and Products pages, shared form/dialog/input primitives, table toolbar/pagination, auth form, E2E auth spec, ESLint config, and global styles.
- This pass used GitHub source inspection only. No local install, build, test execution, browser session, axe scan, screen-reader test, contrast measurement, performance profile, API/backend audit, or deployment verification was performed.
- The 24 test-file count is a source-tree inventory, not a coverage percentage or proof that every test passes.
- Existing PR #425 CI success applies to its documentation branch head and is not evidence that this audit's source-level recommendations are implemented. PR #426 had no check runs at the time of this snapshot.
- Do not interpret this report as a security certification, clinical validation, WCAG conformance statement, or production-readiness approval.

## 6. Next audit slice

Continue with route-by-route inspection of the authenticated workspace, medication/catalog API client contracts, inventory and batch/expiry flows, and the root layout's skip-link target. Then convert confirmed gaps into a sequenced implementation plan before making application-code changes.
