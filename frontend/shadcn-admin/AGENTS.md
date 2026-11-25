# Frontend Agent Instructions — Pharmaviyum ERP

These instructions apply to `frontend/shadcn-admin/` and all files below it.

## Source of truth

- Read the repository-root `AGENTS.md` first. Its safety, privacy, Git, and production/demo rules remain mandatory.
- Frontend application: React 19 + TypeScript + Vite 8.
- Routing: TanStack Router with file-based routes. Do not introduce Next.js, Next.js App Router, React Server Components, or React Router conventions.
- Server state: TanStack Query. Tables: TanStack Table.
- UI: shadcn/ui, Tailwind CSS v4, Radix UI primitives, Lucide icons, CSS-variable theme tokens.
- Forms: React Hook Form + Zod.
- Client state: Zustand where cross-feature/shared state is justified; prefer local state for local interactions.
- Package manager: Bun. The committed lockfile is `bun.lock`; do not switch package managers.
- Browser tests: Vitest Browser + Playwright provider; E2E: Playwright Test.

Before relying on any version-specific API, inspect the installed package version and the local implementation. Do not assume current online documentation matches the lockfile.

For upstream specialist selection and Pharmaviyum-specific adaptation, follow [Frontend Project Skill Integration](../../docs/development/FRONTEND_PROJECT_SKILL_INTEGRATION.md). For architecture, accessibility, performance, observability, testing strategy, localization, and design-system governance, follow [Frontend Engineering Standards](../../docs/development/FRONTEND_ENGINEERING_STANDARDS.md) and assess progress against the [Frontend Engineering Maturity Model](../../docs/development/FRONTEND_ENGINEERING_MATURITY_MODEL.md). That document defines targets and adoption phases; do not claim a target is implemented until repository evidence exists.

Upstream specialist skills may supplement the project-owned frontend skill. The project-owned standard and this file always take precedence; inspect each upstream rule for compatibility before applying it. Do not run skill-provided install, CLI mutation, network-fetch, or audit-tool commands without explicit task approval.

## Architecture and generated files

- Inspect the nearest route, feature, component, hook, store, API service, and tests before editing.
- Keep feature-specific code close to its route/feature. Promote code to shared components only when there is a demonstrated reuse case.
- Reuse existing components from `src/components/`, feature modules under `src/features/`, and existing shadcn primitives under `src/components/ui/`.
- Treat `src/components/ui/` as the local shadcn primitive layer. Do not replace or broadly restyle primitives to solve a single screen requirement; compose them or add a feature-level wrapper.
- TanStack Router route-tree output is generated. Never edit `src/routeTree.gen.ts` manually; use the configured route-generation script.
- The generated API client under `src/client/` is owned by `scripts/generate-api-client.sh`. Never hand-edit generated output; update the backend contract and regenerate it.
- Keep API transport, query keys, query functions, mutations, and UI responsibilities separated consistently with adjacent code.
- Avoid adding dependencies when the existing stack already provides the capability.
- Record material, long-lived architecture decisions as ADRs under `docs/architecture/decisions/`; routine implementation details do not need an ADR.

## Design-system rules

- Preserve the established Pharmaviyum visual language and the existing shadcn `new-york` configuration. Do not migrate the component style, primitive library, icon library, or theme architecture without an explicit decision.
- Read `components.json`, `src/styles/index.css`, `src/styles/theme.css`, and the nearest screen before changing UI.
- Use semantic theme tokens and existing CSS variables for surfaces, text, borders, focus, and status. Do not introduce arbitrary hex/RGB/HSL colors or one-off dark-mode overrides when a semantic token exists.
- Follow the existing spacing, typography, radius, density, and responsive patterns. Avoid global CSS selectors that unintentionally affect unrelated features.
- Prefer composition of existing shadcn components over bespoke controls. Inspect the local component API before use; do not assume a component is installed just because it exists in upstream shadcn documentation.
- Keep dashboard metrics, tables, forms, navigation, dialogs, and empty/loading/error states visually consistent.
- Support light and dark themes and narrow viewports. Avoid horizontal overflow; dense data tables may use an intentional responsive overflow container.
- Use semantic HTML, accessible labels, keyboard-operable controls, visible focus states, and appropriate ARIA attributes.
- Do not use color alone to communicate medication, stock, expiry, or workflow status.
- Target WCAG 2.2 AA. Automated accessibility scans do not replace keyboard, focus, zoom/reflow, contrast, and appropriate assistive-technology checks.

## Pharmacy-domain correctness

Frontend behavior must preserve backend-enforced business rules; the UI is not a substitute for authorization or domain validation.

- Never infer or fabricate medicine identity, strength, dosage form, pack size, batch, expiry, stock quantity, price, prescription status, or dispensing eligibility.
- Preserve medicine identifiers and distinctions between generic name, brand, strength, dosage form, and pack presentation.
- Do not present stale cached inventory or batch availability as authoritative when a workflow requires a fresh server decision.
- For dispensing and POS, make quantity, price, discounts, batch/expiry, and confirmation states explicit. Do not bypass server validation or transactional workflows.
- Preserve FEFO and batch/expiry constraints as supplied by backend contracts. Do not implement a competing client-side source of truth.
- Keep patient, prescription, and tenant data isolated. Never place sensitive patient data in URLs, logs, analytics events, test snapshots, fixtures copied from production, or browser storage without an approved design.
- Treat every tenant-scoped identifier and API response as untrusted until the backend has enforced authorization. Never rely on hiding UI controls as access control.
- Show clear loading, empty, validation, success, and failure states. Do not silently swallow API errors.

## React, TypeScript, and data-fetching rules

- Keep TypeScript strict. Avoid `any`, unsafe casts, and duplicated API types.
- Prefer small, composable components and explicit prop types.
- Keep derived values derived; do not mirror props or query data into state without a concrete reason.
- Do not use effects for calculations or event-driven state transitions that can be expressed during render or in event handlers.
- Use TanStack Query for remote/server state. Define stable query keys, handle invalidation after mutations, and distinguish initial loading from background refetching.
- Handle cancellation/stale responses where relevant. Avoid duplicate requests and ad-hoc fetch logic inside presentational components.
- Validate untrusted form input with the existing Zod/form patterns. Server responses remain authoritative.
- Keep URL state for shareable/searchable/filterable table state when consistent with the adjacent route patterns.
- Use pagination, filtering, and sorting at the server when the dataset or backend contract requires it. Do not load unbounded pharmacy catalogs into the browser.

## Testing and validation

Run from `frontend/shadcn-admin/` using Bun and the committed lockfile:

- `bun run lint`
- `bun run format:check`
- `bun run test`
- `bun run build`
- `bun run test:e2e` when the change affects user journeys, routing, auth, responsive behavior, or critical pharmacy workflows.

Use focused tests first, then the broadest practical suite. E2E tests must use mocks or isolated test services, never production credentials or live production patient data. Do not claim checks passed unless they were executed and the result was observed.

Choose verification depth by risk, not diff size. Auth, tenant isolation, patient context, POS/dispensing, inventory, batch/expiry, FEFO, prescription, and API contract changes require negative/boundary tests and appropriate integration/E2E plus human domain/security review. Follow the test matrix in the Frontend Engineering Standards.

## Change discipline

1. State a concise plan for multi-file changes.
2. Keep the diff focused and preserve unrelated work.
3. Do not modify backend contracts, auth, tenant boundaries, dispensing, inventory, or generated files as a side effect of frontend styling work.
4. Add or update tests for changed behavior, including failure and boundary states.
5. Update docs and ADRs in the same PR when architecture, user-visible behavior, accessibility exceptions, performance budgets, or operational policy changes.
6. Report changed files, commands actually run, results, and remaining risks. Do not report proposed budgets or roadmap phases as implemented capabilities.
7. Follow the root Git workflow: feature branch, focused PR, no direct commits to `main`, no automatic merge or deployment.
