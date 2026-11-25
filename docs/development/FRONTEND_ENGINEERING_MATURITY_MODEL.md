# Frontend Engineering Maturity Model — Pharmaviyum ERP

**Status:** Project engineering capability model and evidence-based improvement roadmap  
**Scope:** `frontend/shadcn-admin/` and its agent/developer workflow  
**Audience:** Frontend engineers, reviewers, technical leads and coding agents  
**Relationship:** Extends [Frontend Engineering Standards](./FRONTEND_ENGINEERING_STANDARDS.md), [Frontend Implementation Audit](./FRONTEND_IMPLEMENTATION_AUDIT.md), and [Project Skill Integration](./FRONTEND_PROJECT_SKILL_INTEGRATION.md), with route-level findings in [Frontend Route Readiness Audit](./FRONTEND_ROUTE_READINESS_AUDIT.md).

This model defines what high-quality frontend engineering means for Pharmaviyum and how to prove it. It is not a claim that the current application already meets every level. Maturity is assessed from observable repository evidence, CI results, runtime measurements, and reviewed workflow outcomes.

## 1. Maturity levels

| Level | Name | Meaning | Evidence required |
|---|---|---|---|
| 0 | Unverified | No reliable evidence for the capability | Explicitly recorded unknown/gap |
| 1 | Foundational | Basic implementation and conventions exist | Source, local patterns and focused tests |
| 2 | Consistent | Reusable patterns are applied across relevant features | Shared contracts, repeatable checks and multiple route examples |
| 3 | Measured | Quality is measured against defined acceptance criteria | Reproducible metrics, CI or test evidence, tracked exceptions |
| 4 | Governed | Changes are controlled, risk-aware and continuously reviewed | ADRs, ownership, release gates, trend review and remediation SLAs |

A capability cannot be rated above the strongest available evidence. A document describing a target does not raise implementation maturity. A passing test suite proves only the behaviors it covers.

## 2. Pharmaviyum frontend competency model

| Competency | Level-4 expectation | Evidence to maintain |
|---|---|---|
| Architecture and boundaries | Explicit feature ownership, dependency direction, state ownership and ADR lifecycle | Architecture map, dependency checks, accepted ADRs, no unexplained circular dependencies |
| React and TypeScript | Predictable React 19 composition, strict types, controlled side effects and maintainable component APIs | Type-check, lint, focused component tests, reviewed patterns |
| Routing and navigation | TanStack Router conventions, route-level loading/error behavior, deep-link and access-flow verification | Route inventory, generated-tree checks, navigation E2E |
| Server state and API integration | TanStack Query cache ownership, stable keys, cancellation/invalidation and contract-safe mutations | Query-key conventions, generated API client, contract/integration tests |
| Design system and UX | Single governed token system, reusable accessible primitives and consistent responsive workflows | Component inventory, token governance, visual review, theme checks |
| Accessibility | WCAG 2.2 AA target verified across critical journeys, including manual checks | axe reports, keyboard and screen-reader evidence, contrast/reflow results, exception register |
| Performance | Route and interaction performance measured on representative hardware/data | Bundle budgets, Core Web Vitals, traces, large-catalog benchmarks and regression trends |
| Testing and release confidence | Risk-based coverage of unit, component, integration, contract and critical E2E paths | Test map, deterministic fixtures, CI results, critical-flow coverage |
| Security and privacy | Backend-enforced authorization supported by privacy-safe client state and observability | Cross-tenant negative tests, patient-context isolation tests, sanitization tests, security review |
| Pharmacy-domain correctness | Medication identity, POS, inventory, batch/expiry, FEFO and dispensing remain server-authoritative | Domain contracts, workflow traceability, invariant tests and pharmacist/domain review |
| Internationalization | Locale-safe presentation with clinically reviewed terminology and explicit fallback | Locale tests, translation ownership, terminology review, canonical value tests |
| Observability and operability | Actionable diagnostics without patient data or secrets | Approved event schema, correlation IDs, retention/access policy, telemetry tests |
| Engineering workflow and agents | Reproducible changes with scoped specialist guidance and human approval gates | AGENTS/skills, pinned provenance, PR checklist, exact-head CI and review evidence |

## 3. Evidence-based baseline

The initial source-inspection baseline is documented in [Frontend Implementation Audit](./FRONTEND_IMPLEMENTATION_AUDIT.md). It identifies these concrete observations:

- **Architecture foundation:** React 19, TypeScript, Vite 8, TanStack Router, shadcn/Radix, TanStack Query and the existing Bun-based toolchain are present in the inspected application.
- **Routing/build:** route generation and route-level code splitting are configured; generated route output must remain generator-owned.
- **Primary routes:** both the authenticated Dashboard and POS feature entry points return `null`; route registration is not proof of a usable page.
- **Route inventory:** 13 authenticated entity routes are explicitly disabled with `null` components while their entities remain in navigation; Sync Events, ERP Systems and Mortarium AI also have route components returning `null`. See the route-readiness audit for the exact inventory and recommended product decisions.
- **Dashboard data provenance:** dormant chart components contain `Math.random()` demo metrics. The current Dashboard entry point returns `null`, so these charts are not evidenced as mounted; replace demo data before exposing them as production KPIs.
- **POS:** the inspected `/pos` route is registered, but the inspected `Pos()` component returns `null`. This is a feature-critical implementation gap, not a stylistic issue.
- **Catalog:** the inspected Products page is a basic generic product list with a fixed `limit=50`, client-side filtering and USD formatting; it does not evidence a complete medication master or batch/expiry/FEFO workflow.
- **Accessibility:** useful primitives and form semantics exist, but the inspected Products search/table and asynchronous announcements have documented gaps. WCAG 2.2 AA conformance remains unverified.
- **Testing:** Vitest Browser and Playwright infrastructure exist; the inspected E2E suite is authentication-focused and does not evidence POS/inventory/dispensing journey coverage.
- **Performance:** route splitting exists, but measured Core Web Vitals, route budgets and realistic large-catalog benchmarks were not evidenced.
- **Privacy and tenant isolation:** frontend-only source inspection cannot prove backend authorization or end-to-end patient-context isolation.

These are bounded observations of the audited revision, not a complete certification of every frontend or backend module. Re-audit before treating a finding as current after implementation changes.

## 4. Engineering gates by change risk

### Low risk — presentation-only

Examples: copy, spacing, isolated icon, non-interactive visual adjustment.

Required:
- preserve existing design tokens and responsive behavior;
- semantic HTML and accessible names for changed controls;
- focused lint/format and relevant component test when behavior is affected;
- screenshots for material visual changes using synthetic/non-sensitive data.

### Medium risk — interactive feature

Examples: route, form, query, table, shared component, filter, navigation.

Required:
- explicit state ownership and API loading/error/empty/success behavior;
- unit/component tests and integration tests for data behavior;
- keyboard and responsive verification;
- production build and relevant route E2E;
- review of query keys, cache invalidation and stale-data behavior.

### High risk — pharmacy, identity or security workflow

Examples: authentication, tenant switching, patient context, POS, dispensing, prescriptions, inventory, batch/expiry, FEFO, payment, stock receiving or API contract.

Required:
- trace UI action through generated client/API contract to backend enforcement;
- negative and boundary cases, including unauthorized and stale-context paths;
- duplicate submission/replay behavior and idempotency contract review;
- integration and critical Playwright E2E using isolated synthetic data;
- privacy/security and pharmacy-domain human review;
- documented recovery/error semantics; no success indication before authoritative server confirmation.

Risk is determined by the workflow's potential impact, not the number of files or lines changed.

## 5. Reference architecture and ownership rules

| Concern | Preferred owner | Avoid |
|---|---|---|
| Remote data, freshness, retries, invalidation | TanStack Query + API service | Duplicating remote data in Zustand or component state |
| Ephemeral interaction state | Local React state | Global store for one component's open/closed state |
| Shareable navigation/filter state | TanStack Router search params | Hidden component-only state for shareable filters |
| Cross-route client-only state | Zustand, when justified | Using Zustand as a second server cache |
| Form input and validation | React Hook Form + Zod | Duplicated validation rules and ad-hoc form state |
| Domain and authorization rules | Backend contracts/services | Client-only enforcement or inferred clinical rules |
| Design primitives | Local shadcn/Radix layer | Competing component libraries and one-off primitives |
| Generated routes/API types | Declared generators | Manual edits to generated artifacts |
| Build and package management | Vite 8 + Bun | Next.js/Vercel assumptions or mixed lockfiles |

These are ownership defaults. A deviation requires a concrete problem statement, trade-off analysis and, for material long-lived changes, an ADR.

## 6. Priority improvement sequence

The sequence below is based on the inspected audit's risk, not on visual polish or popularity of tooling.

### P0 — Establish correct pharmacy workflows

1. Restore the authenticated Dashboard and POS entry points using approved data/workflow contracts; no route should silently render a blank page.
2. Define the frontend/backend POS workflow contract: cart, product identity, price/currency, stock/batch reservation, payment state, sale confirmation, receipt and failure recovery.
3. Implement the POS route only against approved backend contracts; do not fabricate missing endpoints or client-side transactional rules.
4. Define medication master and inventory display contracts, including active ingredient, brand/generic identity, strength, dosage form, route, pack size, manufacturer/barcode where available, stock location, batch/lot and expiry.
5. Establish FEFO and prescription/dispensing invariants at the backend boundary and test the UI's handling of authoritative results.
6. Add tenant and patient-context negative tests before expanding sensitive workflows.

**P0 exit:** documented contracts, working critical user journeys, backend enforcement evidence, failure-path tests and human domain/security approval. A rendered mockup alone is not completion.

### P1 — Make core workflows accessible and testable

1. Fix accessible names and semantics for Products search and table.
2. Add appropriate live-region behavior for asynchronous loading, results and errors.
3. Add keyboard and screen-reader verification to shared controls and critical workflows.
4. Build Playwright coverage for medication lookup, POS, stock receipt/adjustment, batch/expiry and role boundaries.
5. Add automated accessibility scans to representative stable routes, while retaining manual verification.

**P1 exit:** reproducible automated reports, keyboard walkthroughs, critical E2E coverage and a tracked exception register.

### P2 — Measure and optimize

1. Establish production-build bundle baselines and route-level JS transfer.
2. Benchmark dashboard, POS and catalog on representative device/network profiles and realistic synthetic catalog sizes.
3. Capture LCP, INP and CLS where field measurement is privacy-approved; otherwise maintain reproducible lab evidence.
4. Calibrate provisional budgets against measured baseline and user workflows before enforcing CI gates.
5. Optimize only measured bottlenecks and preserve before/after evidence.

**P2 exit:** reproducible baseline, calibrated budgets, regression checks and no sensitive data in performance telemetry.

### P3 — Operational maturity

1. Define privacy-reviewed frontend error/event schema and correlation ID propagation.
2. Verify cache clearing/partitioning on logout, session invalidation and tenant switch.
3. Establish translation ownership and locale-safe date, number, currency and medication terminology behavior.
4. Introduce visual regression selectively for stable, high-value routes.
5. Track frontend defects, accessibility exceptions, performance regressions and critical-flow test reliability.

**P3 exit:** owned operational signals, privacy tests, localization acceptance and maintained quality trends.

## 7. Architecture review checklist

For any proposed frontend architecture change, reviewers should ask:

1. What concrete user or engineering problem exists in the current architecture?
2. Which feature owns the behavior and data?
3. What is the authoritative source of truth: URL, local state, TanStack Query, backend, or another explicitly justified owner?
4. How are loading, stale data, retries, cancellation, concurrency and mutation failure handled?
5. What happens on logout, tenant switch, role change and patient-context change?
6. Does the change preserve medication identity, stock, batch/expiry, FEFO, price and dispensing invariants?
7. What accessibility and responsive behavior changes?
8. What measurements show a performance need or improvement?
9. Which tests prove success, failure, boundary and unauthorized behavior?
10. What is the migration, rollback and observability plan?
11. Does this introduce a dependency, runtime, framework or operational burden that the current stack does not need?
12. What documentation, ADR, agent instruction and generated artifacts must change together?

Reject architecture changes justified only by trend, tutorial defaults, benchmark claims without a matching workload, or an upstream Agent Skill recommendation.

## 8. Agent and reviewer operating contract

Coding agents are implementation assistants, not architecture authorities.

- Load repository and frontend instructions before editing; load only the specialist skill relevant to the task.
- Treat upstream skills as advisory and subordinate to Pharmaviyum-owned rules.
- Inspect installed versions, local component source, route conventions and API contracts before using version-sensitive guidance.
- Never execute downloaded scripts, install dependencies, mutate shadcn components, alter CI, or create remote design resources without explicit approval.
- Propose an ADR when a change alters long-lived architecture, security boundaries, state ownership, dependency policy or platform choice.
- Update the canonical documentation in the same PR when a durable rule, workflow contract or quality gate changes.
- Report exact files, commands actually run, check results, limitations and unresolved risks.
- Do not claim that accessibility, security, performance, clinical correctness or maturity targets are achieved without corresponding evidence.
- Never merge or deploy automatically.

## 9. Metrics and review cadence

Track a small set of actionable indicators rather than vanity metrics:

| Indicator | Definition | Review |
|---|---|---|
| Critical workflow coverage | Critical pharmacy journeys with deterministic E2E / journeys identified as release-critical | Each release |
| Accessibility debt | Open WCAG issues by severity, route and age | Each sprint/release |
| Frontend regression rate | Regressions attributable to frontend changes, classified by workflow impact | Monthly |
| Performance trend | LCP/INP/CLS and bundle-size trend for representative routes | Monthly and after performance work |
| Type/lint/build health | Exact-head required CI checks and recurring failure categories | Every PR |
| Flaky E2E rate | Reruns/failures attributable to test instability, separated from product defects | Monthly |
| Privacy/security findings | Open and remediated findings affecting patient/tenant data boundaries | Every high-risk change and release |
| Documentation drift | Material implementation changes missing corresponding docs/ADR updates | Each PR review |

Do not set numerical targets until a baseline, denominator and measurement method are agreed. A metric without an owner and a decision it informs should not become a release gate.

## 10. Definition of high engineering maturity

Pharmaviyum's frontend can be described as operating at a high engineering maturity level only when:

- the architecture is coherent, documented and consistently enforced;
- critical pharmacy workflows are complete against backend domain contracts;
- tenant and patient-context isolation are proven with negative tests;
- accessibility is validated across critical journeys, not inferred from component libraries;
- performance is measured on representative workflows and protected against regressions;
- tests cover important success, failure, boundary and authorization cases;
- observability is useful and demonstrably privacy-safe;
- changes are reviewed against risk and architecture decisions;
- coding agents follow project-owned instructions and cannot silently override architecture;
- quality evidence is current, reproducible and reviewed by accountable humans.

The objective is not to maximize process or documentation volume. It is to make the safest correct change the easiest change to implement, verify and maintain.

## References

- [Frontend Engineering Standards](./FRONTEND_ENGINEERING_STANDARDS.md)
- [Frontend Implementation Audit](./FRONTEND_IMPLEMENTATION_AUDIT.md)
- [Frontend Project Skill Integration](./FRONTEND_PROJECT_SKILL_INTEGRATION.md)
- [TanStack Router](https://tanstack.com/router/latest)
- [TanStack Query](https://tanstack.com/query/latest)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Web Vitals](https://web.dev/articles/vitals)
- [OpenTelemetry](https://opentelemetry.io/docs/)
