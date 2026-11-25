# Frontend Engineering Standards — Staff-Level Practice

**Status:** Engineering standard and adoption roadmap  
**Scope:** `frontend/shadcn-admin/`  
**Audience:** Engineers and coding agents working on the Pharmaviyum frontend

This document extends the repository's frontend agent instructions. It defines decision-making, quality attributes, measurable acceptance criteria, and governance. It does not claim that every capability is already implemented. Existing architecture, manifests, tests, and backend contracts remain authoritative.

## 1. Engineering principles

1. **Domain correctness before presentation.** Medication identity, prescription context, inventory, batch/expiry, FEFO, pricing, dispensing eligibility, and tenant boundaries are backend-authoritative.
2. **Explicit architecture over convention by accident.** Significant structural decisions are recorded and reviewed.
3. **Measure before optimizing.** Performance budgets begin with reproducible baselines; no optimization is accepted solely on intuition.
4. **Accessibility is a release criterion.** Keyboard, screen-reader, contrast, focus, and zoom behavior are part of feature acceptance.
5. **Test observable behavior.** Prefer user-visible outcomes and API contracts over implementation-detail assertions.
6. **Privacy by design.** Patient and tenant data must not leak through UI state, caches, URLs, telemetry, logs, screenshots, or fixtures.
7. **Progressive governance.** Apply controls proportional to risk; do not turn a small isolated UI change into heavyweight process.

## 2. Architecture decision records (ADRs)

Create an ADR when a change materially affects one or more of:
- routing, feature boundaries, state ownership, or data-fetching architecture;
- design-system primitives, tokens, component API conventions, or theming;
- API/client generation, caching, persistence, or offline behavior;
- authentication, authorization, tenant isolation, or patient-data handling;
- performance budgets, observability, testing infrastructure, or build/deployment boundaries;
- a dependency or platform choice that is expensive to reverse.

Do not create an ADR for routine component implementation, local styling, or a reversible refactor that follows an established pattern.

### ADR format

Store accepted decisions under `docs/architecture/decisions/` using a monotonically increasing identifier and descriptive filename, for example `0001-frontend-state-ownership.md`.

Each ADR contains:
- **Status:** Proposed, Accepted, Superseded, or Deprecated.
- **Date and owners:** decision date and accountable roles.
- **Context:** problem, constraints, affected users/workflows, and alternatives.
- **Decision:** selected approach and explicit non-goals.
- **Consequences:** benefits, trade-offs, migration and operational impact.
- **Security/privacy/accessibility:** relevant impact, or an explicit reason none applies.
- **Validation:** evidence, measurements, tests, and rollback/exit strategy.
- **Supersedes / Superseded by:** links where applicable.

Proposed ADRs are reviewed before implementation when the decision is high-impact. Accepted ADRs are amended by a new ADR, not silently rewritten. Link relevant ADRs from feature documentation and PR descriptions.

## 3. Frontend architecture governance

### 3.1 Current architecture boundary

The supported application architecture remains:
- React 19 + TypeScript + Vite 8;
- TanStack Router (file-based) and TanStack Query;
- TanStack Table where complex tabular behavior is needed;
- Tailwind CSS v4 and the repository's shadcn/ui configuration;
- React Hook Form + Zod, Zustand only for justified shared client state;
- Bun and the committed `bun.lock`;
- Vitest Browser and Playwright Test;
- React frontend built/served as part of the FastAPI application.

Do not introduce Next.js, React Server Components, React Router, another package manager, a second UI framework, or Vercel hosting/runtime assumptions without an explicitly reviewed architecture decision. FastAPI Cloud is the Demo hosting target; Production release controls remain separate and operator-controlled.

### 3.2 Feature boundaries and dependency direction

- Organize code around business capabilities and route/feature ownership, not arbitrary technical buckets alone.
- Feature modules may depend on shared UI primitives and approved platform services; shared primitives must not import feature-specific business logic.
- Keep API transport and generated types separate from presentation components.
- Keep server state in TanStack Query, local interaction state in components, URL state for shareable navigation/filter state, and Zustand only for genuinely cross-route client state.
- Preserve HTTP status and safe server error details in a typed transport error. Query retry policy must recognize the error type emitted by the active transport, never retry authorization/validation failures, and bound retries for transient failures. Do not automatically retry non-idempotent mutations; see [Frontend API Error Contract](./FRONTEND_API_ERROR_CONTRACT.md).
- Avoid duplicated sources of truth. Derived state should be computed, not synchronized through effects without a demonstrated need.
- Prevent circular dependencies and deep imports across feature internals. Promote a public feature API only when cross-feature reuse is real.
- Keep route definitions, generated route trees, generated API clients, and other generated artifacts under their generators.

### 3.3 Change-risk classification

| Risk | Examples | Minimum engineering response |
|---|---|---|
| Low | Copy, isolated styling, presentational component | Focused review; lint/format; relevant component test if behavior changed |
| Medium | Route behavior, forms, query/mutation, shared component, table state | Unit/component tests; API/error-state review; keyboard and responsive checks; build |
| High | Auth, tenant scope, patient context, POS/dispensing, stock, batch/expiry, FEFO, prescription, generated API contract | Trace UI-to-backend flow; negative/boundary tests; integration and critical E2E; privacy/security review; explicit human review |

Risk is determined by the highest affected workflow, not by the number of changed lines.

## 4. Design-system governance

- The installed local shadcn components and `components.json` are the implementation source of truth; upstream examples are references only.
- Prefer semantic design tokens for color, surfaces, borders, typography, spacing, radius, focus, and status. Avoid one-off hard-coded values when a token exists.
- Shared primitives stay generic and accessible. Pharmacy-specific behavior belongs in feature-level components.
- New shared components require at least two credible use cases or a documented platform capability gap; do not abstract speculative future reuse.
- Component APIs should expose semantic intent, controlled/uncontrolled behavior where appropriate, composition slots, and predictable loading/disabled/error states.
- Document non-obvious component contracts, keyboard behavior, variants, and responsive constraints alongside the component or in the design-system documentation.
- Breaking shared component API changes require a migration plan and updates to all consumers in the same PR.
- Avoid introducing a parallel component library, icon set, CSS-in-JS system, or theme mechanism without an ADR.

### Design-system contribution checklist

- [ ] Existing primitive and token checked before adding a new one.
- [ ] Semantic tokens used; light and dark themes verified.
- [ ] Keyboard interaction and visible focus verified.
- [ ] Responsive and dense-data behavior verified.
- [ ] Loading, empty, error, disabled, and success states considered.
- [ ] Component API and usage examples documented where shared.
- [ ] No pharmacy domain rules embedded in generic primitives.

## 5. Accessibility standard — WCAG 2.2 AA

Target **WCAG 2.2 Level AA** for application UI. Automated scans are useful but do not establish conformance by themselves.

### Required acceptance criteria

- All functionality is operable by keyboard; no keyboard traps.
- Focus order is logical, focus is visible, and sticky headers/dialogs do not obscure focused controls.
- Interactive targets meet WCAG 2.2 target-size requirements or a documented exception/spacing alternative.
- Text contrast meets 4.5:1 for normal text and 3:1 for large text; meaningful non-text UI components and states meet applicable 3:1 contrast requirements.
- Information is not conveyed by color alone; status includes text, iconography, or another perceivable cue.
- Inputs have programmatic labels, instructions, required-state communication, and associated validation errors.
- Dynamic updates (search results, mutation status, validation, async loading) are announced appropriately without excessive live-region noise.
- Dialogs and popovers manage focus, expose names/roles/states, and return focus to the invoking control.
- Tables have meaningful headers and accessible names; sorting and pagination state is programmatically available.
- Layout remains usable at 200% zoom and reflow widths without loss of information or two-dimensional scrolling except where the content genuinely requires it (for example, a complex data table).
- Motion respects reduced-motion preferences; no flashing content is introduced.
- Authentication and session flows remain accessible, including timeout and error recovery.

### Verification

For each changed interactive flow:
1. Run automated accessibility checks in the existing browser test environment where supported.
2. Test keyboard-only operation, including focus entry/exit, dialogs, menus, comboboxes, and tables.
3. Inspect at least one screen-reader flow for high-risk or shared components.
4. Check contrast and zoom/reflow at representative viewport sizes.
5. Record known exceptions with rationale, affected users, compensating behavior, and a follow-up owner.

Do not claim WCAG conformance from an automated score alone. Accessibility review is required for shared primitives and high-risk workflows.

## 6. Performance engineering and budgets

Performance work is evidence-led. Capture a baseline before changing code and compare the same route, device profile, network profile, data volume, and build mode after the change.

### Initial target budgets

These are proposed engineering targets, not measured claims about the current application. Establish the baseline and tune targets against real route complexity and supported devices before enforcing them as CI gates.

| Dimension | Initial target | Measurement |
|---|---:|---|
| LCP | ≤ 2.5 s at the 75th percentile | Field data where available; repeatable lab profile otherwise |
| INP | ≤ 200 ms at the 75th percentile | Field interaction data; representative interaction profiling |
| CLS | ≤ 0.1 at the 75th percentile | Field data and route-level lab runs |
| Initial JS transfer | ≤ 250 KiB compressed, provisional | Production build output and browser network panel |
| Route-specific JS | ≤ 150 KiB compressed incremental, provisional | Bundle analyzer / build manifest |
| Long tasks | Avoid tasks > 50 ms on critical interactions | Browser Performance trace |
| API-driven critical UI | Show meaningful pending state immediately; define route-specific response SLO with backend | Browser traces correlated with API timing |

The JavaScript budgets are provisional guardrails. They must be validated against the current bundle and dependency graph before enforcement. Do not remove essential security, accessibility, or domain behavior to satisfy a byte target.

### Optimization workflow

1. Identify the affected user journey and performance symptom.
2. Capture a reproducible baseline and save the trace/build report as a PR artifact when practical.
3. Attribute cost to network, JavaScript download/parse/execute, React rendering, layout/paint, or API/backend latency.
4. Choose the smallest intervention: route-level code splitting, reduced over-fetching, stable query/cache policy, virtualization for large tables, image/font optimization, or rendering simplification.
5. Re-measure under the same conditions and report before/after values and trade-offs.
6. Add a regression test or budget only when the metric is stable and actionable.

Do not add memoization, virtualization, caching, or dependencies without evidence that they address the measured bottleneck. Avoid unbounded client-side medication catalogs; use backend pagination/search according to API contracts.

## 7. Frontend observability and error handling

Observability must help diagnose user-visible failures without collecting patient data or secrets.

### Required event dimensions

Where approved telemetry exists, use low-cardinality, non-sensitive dimensions such as:
- application version/build identifier and environment (Demo vs approved Production context);
- route template or feature name, not raw URL/query string;
- operation name, outcome category, duration, and retry count;
- sanitized error category and correlation/trace identifier;
- browser/runtime family where privacy policy permits.

### Prohibited telemetry

Never emit:
- patient names, contact details, prescription contents, medication history, or free-text clinical notes;
- access tokens, session identifiers, passwords, API keys, or authorization headers;
- raw request/response bodies containing tenant or patient data;
- tenant identifiers unless explicitly approved, necessary, access-controlled, and appropriately pseudonymized.

### Error-handling requirements

- Distinguish validation, authentication/authorization, conflict, rate-limit, network, server, and unexpected client errors.
- Give users a safe, actionable message and preserve entered non-sensitive form data where appropriate.
- Show success only after authoritative server confirmation.
- Do not automatically retry non-idempotent POS, dispensing, receiving, stock, or payment operations unless the API provides an idempotency contract.
- Use correlation IDs to connect frontend failures to backend traces without exposing sensitive payloads.
- Error boundaries should isolate recoverable feature failures and provide a safe recovery path; they must not silently conceal data-integrity failures.

Use the project's approved telemetry and OpenTelemetry conventions if/when configured. This standard does not authorize adding a vendor SDK, analytics service, or new dependency. Instrumentation and retention require privacy/security review.

## 8. Testing strategy

Use a risk-based testing pyramid. The goal is fast feedback at lower layers and confidence in user-visible critical journeys.

| Layer | Primary purpose | Required use |
|---|---|---|
| Static checks | Types, lint, formatting, build-time constraints | Every PR through existing CI |
| Unit | Pure logic, formatting, selectors, validation helpers | Complex or domain-sensitive logic |
| Component/browser | Accessible interactions, loading/error/empty states | Interactive components and forms |
| Integration | UI + query/API boundary, mutation and invalidation behavior | Data-driven features and workflows |
| Contract | Generated client/OpenAPI compatibility and schema assumptions | API contract changes |
| E2E | End-to-end user outcomes across critical journeys | Auth, POS, dispensing, inventory, prescription and other high-risk flows |
| Visual regression | Layout/theme regression on stable high-value screens | Introduce selectively after deterministic baseline setup |

### Test design rules

- Test user-observable behavior, business invariants, and failure paths; avoid brittle assertions on internal component structure.
- Use synthetic, deterministic fixtures only. Never copy Production patient, prescription, or tenant data.
- Include negative and boundary cases: unauthorized tenant, stale stock, unavailable/expired batch, invalid quantity, conflicting mutation, API timeout, and duplicate submission where relevant.
- Test loading, empty, validation, success, partial failure, retry, and recovery states.
- E2E tests must use isolated test services or intercepted APIs and must not call public Production endpoints.
- Use stable selectors such as accessible roles/names; avoid brittle CSS selectors and arbitrary sleeps.
- Visual tests require pinned viewport/browser/font conditions and controlled data; mask only genuinely nondeterministic regions, never hide meaningful UI regressions.
- Keep test data isolated across tenants and test workers. Reset through supported fixtures/API, not destructive shared-environment cleanup.
- A passing test suite is evidence for the covered cases only, not proof of total correctness.

### Minimum verification by risk

- Low risk: lint/format plus focused test when behavior changes.
- Medium risk: lint, format, unit/component tests, production build, responsive and keyboard review.
- High risk: all relevant lower layers plus integration and critical E2E, negative/boundary tests, contract review, and human security/domain review.

Run the actual repository commands from `frontend/shadcn-admin/`: `bun run lint`, `bun run format:check`, `bun run test`, `bun run build`, and `bun run test:e2e` when required by the change. Report skipped checks explicitly.

## 9. Internationalization and localization

The base interface language remains English unless the product owner approves a different default. Design for localization without inventing country-specific medication or regulatory behavior.

- Keep user-facing strings out of business logic and centralize them using the project's chosen i18n approach once adopted.
- Do not introduce an i18n dependency until the library, locale strategy, bundle impact, translation ownership, and fallback behavior are reviewed.
- Avoid concatenating sentence fragments; use parameterized messages that translators can reorder.
- Format dates, times, numbers, currency, and units with locale-aware APIs and explicit domain units.
- Store and exchange canonical values (for example, ISO timestamps and backend-defined currency/unit representations); localize presentation only.
- Preserve medication identifiers, strengths, dosage forms, pack sizes, and quantities exactly as supplied by the domain/API. Never translate identifiers or alter numeric meaning.
- Plan for English and Russian retrieval/display requirements where product scope requires them; language selection must not weaken tenant isolation or clinical grounding.
- Support text expansion, right-to-left layout if later required, accessible language metadata, and locale-aware sorting/search.
- Translation fallback must be explicit and observable; do not silently show mixed-language critical instructions.
- Clinical and medication terminology requires domain review, not machine translation alone.

## 10. Security, privacy, and pharmacy-domain assurance

- Backend authorization is authoritative; frontend route guards and hidden controls are UX only.
- Tenant scope must be represented and enforced by the API contract. Query keys, caches, persisted state, and browser tabs must not permit cross-tenant data reuse.
- Clear or partition sensitive client state on logout, tenant switch, and session invalidation according to the approved auth design.
- Do not store patient/prescription data in local storage, session storage, URLs, analytics, console output, or screenshots without explicit security approval.
- Avoid rendering untrusted content as HTML. Validate and encode data at the correct trust boundary.
- Treat medication name, brand, strength, dosage form, pack size, batch, expiry, quantity, price, prescription state, and dispensing eligibility as distinct fields; do not infer missing values.
- POS and dispensing mutations must use backend transactional guarantees and idempotency semantics. The UI must prevent accidental duplicate submission but must not substitute client-side checks for server enforcement.
- FEFO and expiry decisions are displayed from authoritative backend results; client-side sorting is not a competing decision engine.
- Security-sensitive changes require threat-focused review and tests for unauthorized access, stale context, replay/duplicate action, and error leakage.

## 11. Pull request and release quality gates

Every frontend PR should state:
- user/problem outcome and affected routes/features;
- risk level and domain workflows touched;
- architecture/design-system impact and ADR link if applicable;
- accessibility checks performed and known exceptions;
- performance baseline/measurement when performance is a stated goal;
- tests and commands actually run, with pass/fail/skipped status;
- privacy/security considerations and synthetic-data confirmation;
- screenshots or short recordings for material visual changes, with no real patient data.

Before merge:
- required CI checks pass for the exact PR head;
- generated artifacts are regenerated through the owning tool;
- high-risk changes receive human review from an appropriate domain/security owner;
- documentation and ADRs are updated in the same change when behavior or architecture changes;
- no secrets, patient data, private Production implementation, or unrelated files are included.

Merge and deployment remain human/operator-controlled. Demo and Production release processes must not be conflated.

## 12. Adoption roadmap

Adopt standards incrementally; do not imply that future tooling already exists.

| Phase | Deliverable | Exit evidence |
|---|---|---|
| 1. Governance | ADR template and risk classification | First material architecture decision recorded; PR template/checklist aligned |
| 2. Accessibility | WCAG 2.2 AA checklist and automated browser checks | Shared primitives and critical workflows keyboard-tested; known exceptions tracked |
| 3. Performance | Route baselines and validated budgets | Reproducible baseline for dashboard, POS, and inventory; targets calibrated before CI enforcement |
| 4. Observability | Privacy-reviewed error and performance instrumentation | Sanitization tests, correlation IDs, retention/access policy, no sensitive payload capture |
| 5. Testing | Risk-based test map and stable E2E/visual strategy | Critical journeys covered with deterministic synthetic fixtures |
| 6. Localization | Locale architecture and terminology workflow | Approved language scope, translation ownership, canonical data formatting |

A phase is complete only when its exit evidence exists in the repository or approved operational tooling. A checklist or roadmap entry alone is not proof of implementation.

## 13. References

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Web Vitals](https://web.dev/articles/vitals)
- [Core Web Vitals thresholds](https://web.dev/articles/vitals#core_web_vitals)
- [Architecture Decision Records](https://adr.github.io/)
- [OpenTelemetry](https://opentelemetry.io/docs/)
- [Playwright accessibility testing](https://playwright.dev/docs/accessibility-testing)
- [TanStack Router](https://tanstack.com/router/latest)
- [TanStack Query](https://tanstack.com/query/latest)
- [shadcn/ui](https://ui.shadcn.com/docs)
