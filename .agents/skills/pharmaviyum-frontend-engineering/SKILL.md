---
name: pharmaviyum-frontend-engineering
description: Build, review, refactor, and test the Pharmaviyum ERP frontend. Use for React, TypeScript, Vite, TanStack Router/Query, Tailwind CSS v4, shadcn/ui, dashboard, POS, inventory, pharmacy workflows, forms, tables, accessibility, and frontend API integration.
---

# Pharmaviyum Frontend Engineering

## Mission

Deliver production-grade frontend changes for Pharmaviyum ERP. Preserve the existing application architecture, visual system, API contracts, pharmacy-domain correctness, privacy boundaries, and test strategy. Do not turn a focused UI task into an unrelated rewrite.

## Mandatory context loading

Before implementation, read:

1. Repository-root `AGENTS.md`.
2. `frontend/shadcn-admin/AGENTS.md`.
3. `frontend/shadcn-admin/package.json` and `components.json`.
4. The nearest route/feature implementation and its tests.
5. Relevant API types/services and the backend contract when data or workflow behavior changes.
6. `src/styles/index.css` and `src/styles/theme.css` when styling or theming changes.

Treat repository files and the committed lockfile as the source of truth. Do not assume a different framework or upgrade versions implicitly.

## Stack contract

- React 19, TypeScript, Vite 8.
- TanStack Router (file-based routing) and TanStack Query.
- TanStack Table for complex tabular data.
- Tailwind CSS v4 and shadcn/ui configured in `components.json`.
- Existing Radix UI primitives and Lucide icons.
- React Hook Form + Zod for forms.
- Zustand for justified shared client state.
- Bun with `bun.lock`.
- Vitest Browser for component/unit tests and Playwright Test for E2E.

Next.js, React Server Components, Next.js routing, and React Router patterns are out of scope unless the project architecture is explicitly changed.

## Workflow

### 1. Understand before changing

- Identify the route, feature owner, current component composition, data source, and state ownership.
- Search for reusable components, hooks, query patterns, schemas, and tests before creating new abstractions.
- Inspect the actual local shadcn component source and `components.json`; upstream APIs may not match the installed version or primitive base.
- For workflow changes, trace the full path from UI action through API client, query/mutation, backend endpoint, and response/error handling.
- For visual changes, inspect existing theme tokens and the closest implemented screens.

### 2. Design and implement

- Preserve the Pharmaviyum design system. Use semantic CSS variables and Tailwind theme tokens.
- Compose existing primitives; create feature-level wrappers when a real capability gap exists.
- Keep components focused and colocate feature-specific code.
- Use explicit TypeScript types. Avoid `any`, duplicate API contracts, and unsafe assumptions.
- Keep server state in TanStack Query, transient UI state local, and shared client state in Zustand only when justified.
- Use stable query keys, mutation invalidation, and explicit loading/error/empty/success states.
- Validate forms with the existing React Hook Form + Zod conventions.
- Make responsive behavior intentional, including dense table and POS interaction states.
- Keep all controls keyboard accessible and provide visible focus indicators and meaningful labels.

### 3. Protect pharmacy workflows

- Medicine selection must preserve identity, brand/generic distinction, strength, dosage form, and pack size.
- Never invent or infer medicine details, stock, batch, expiry, pricing, prescription validity, or dispensing eligibility.
- Backend authorization and validation remain authoritative. UI visibility is never a security boundary.
- Preserve tenant isolation and patient-context boundaries across requests, caches, URLs, browser storage, logs, and tests.
- POS, dispensing, receiving, inventory, batch/expiry, FEFO, procurement, and transfers must follow backend contracts and transactional guarantees.
- Do not silently retry non-idempotent actions or show success before the server confirms success.
- Use synthetic fixtures only; never copy production patient or prescription data into tests or screenshots.

### 4. Verify

Run the relevant checks from `frontend/shadcn-admin/`:

```bash
bun run lint
bun run format:check
bun run test
bun run build
```

Run `bun run test:e2e` for affected critical journeys, auth, route behavior, responsive UI, or pharmacy workflows. E2E must use isolated test data and intercepted/mock APIs where appropriate.

Do not install dependencies, change lockfiles, or alter CI quality gates to hide unrelated failures. Report checks not run.

## Skill routing and upstream references

Use specialized upstream skills when available; this skill defines Pharmaviyum-specific constraints and does not replace their detailed guidance. Load only the specialist relevant to the task.

- Official shadcn skill: `npx skills add shadcn/ui` — primary source for component discovery, composition, CLI, registries, and theming.
- Vercel React Best Practices: `npx skills add vercel-labs/agent-skills --skill react-best-practices` — React rendering, async, and bundle performance. Apply React guidance only; this does not make Vercel a hosting target.
- Vercel Composition Patterns: `npx skills add vercel-labs/agent-skills --skill composition-patterns` — scalable component APIs and composition.
- Vercel Web Design Guidelines: `npx skills add vercel-labs/agent-skills --skill web-design-guidelines` — interface quality and accessibility review.
- Addy Osmani Frontend UI Engineering: `npx skills add addyosmani/agent-skills --skill frontend-ui-engineering` — production UI composition, responsive behavior, and design-system adherence.
- Addy Osmani Performance Optimization: `npx skills add addyosmani/agent-skills --skill performance-optimization` — measurement-first profiling and optimization; use when performance is in scope.
- Addy Osmani Accessibility Engineering: `npx skills add addyosmani/agent-skills --skill accessibility-engineering` — focused accessibility audits and remediation.
- Addy Osmani Code Review and Quality: `npx skills add addyosmani/agent-skills --skill code-review-and-quality` — pre-merge review across correctness, readability, architecture, security, and performance. Review the exact PR head and use Pharmaviyum's Bun-based checks; do not apply unrelated npm/tooling assumptions blindly.
- Google Stitch React + Vite Dashboard: `npx skills add google-labs-code/stitch-skills --skill react-vite-dashboard` — dashboard and design-to-code guidance. Adapt React Router examples to TanStack Router, ignore Web3 examples, and do not require Stitch MCP for ordinary development.
- Google Stitch shadcn UI: `npx skills add google-labs-code/stitch-skills --skill shadcn-ui` — supplementary component guidance only; prefer official shadcn guidance and adapt Next.js/Tailwind v3 assumptions to Vite/Tailwind v4.

The demo deployment target is FastAPI Cloud. The React/Vite frontend is served as part of the FastAPI application; do not add Vercel hosting, edge-runtime, or deployment assumptions. Use the project's Bun runner when installing from the terminal if that is the environment's supported invocation. Review source and license before vendoring third-party files. Keep upstream skills updateable and this skill focused on Pharmaviyum-specific rules.

## Definition of done

- The change follows root and frontend agent instructions.
- Existing components and patterns were reused where appropriate.
- No Next.js-only assumptions or unintended dependency changes were introduced.
- Pharmacy data, tenant boundaries, and backend business rules remain intact.
- Relevant tests and checks were run, with results reported accurately.
- The diff is focused and ready for human review; no merge or deployment is performed automatically.
