# Pharmaviyum Frontend — Upstream Skill Integration Contract

## Status

Project-specific integration policy for the nine selected upstream skills. This document defines how agents must apply those skills to the existing frontend; it does not claim that third-party skill packages have been installed or that their tooling has been executed.

## Authoritative project stack

The following stack is authoritative and must not be replaced by an upstream skill:

- React 19 + TypeScript + Vite 8 (client-rendered frontend).
- TanStack Router (file-based routing), TanStack Query (server state), TanStack Table.
- Tailwind CSS v4; shadcn/ui `new-york`, `rsc: false`; existing Radix UI and Lucide.
- React Hook Form + Zod; Zustand only for justified shared client state.
- Bun and the committed `bun.lock`.
- Vitest Browser and Playwright Test.
- Frontend is served by the FastAPI application on the same domain. FastAPI Cloud is the Demo hosting target; it is not a Vercel application.

Read the installed package versions, `components.json`, local component source, route conventions, styles, and adjacent tests before applying version-sensitive advice.

## Skill-to-project routing

| Upstream skill | Use it for in Pharmaviyum | Project-specific constraints |
|---|---|---|
| Anthropic `frontend-design` | Visual hierarchy, typography, layout, interaction design | Preserve approved Pharmaviyum design tokens, density, brand, dark/light themes, and existing dashboard language. Do not invent a new visual identity per screen. |
| Vercel `react-best-practices` | React rendering, async work, state, bundle and client performance | React 19 + Vite only. Exclude Next.js, RSC, Server Actions, Next APIs, hydration/server-component rules. Map SWR examples to TanStack Query; map `next/dynamic` to Vite dynamic imports/lazy routes. |
| Vercel `composition-patterns` | Component API design, composition, compound components | Use selectively; do not add abstraction or replace local primitives without a demonstrated need. React 19 patterns must match installed APIs. |
| Vercel `web-design-guidelines` | Interface quality review, semantics, responsive behavior, accessibility heuristics | Keep the skill's bundled reference snapshot intact. Verify findings against actual UI and WCAG test evidence. |
| Official shadcn `shadcn` | Component discovery, local composition, theming, registries and CLI guidance | Existing `components.json` and local components are authoritative. Inspection is distinct from mutation; adding/overwriting/migrating components requires explicit approval and diff review. |
| Addy `frontend-ui-engineering` | Production UI composition, responsive behavior, design-system consistency | Reuse existing feature and shared components; do not introduce a competing component library or token system. |
| Addy `accessibility-engineering` | Accessibility review and remediation planning | Target WCAG 2.2 AA. Inspect scripts before execution; no automatic downloads/tool installs. Combine automated checks with keyboard, focus, zoom/reflow, contrast, and assistive-technology review as appropriate. |
| Addy `performance-optimization` | Measurement, profiling, bottleneck analysis and optimization | Measure before changing code. No automatic `web-vitals`, RUM, telemetry, dependencies, or performance budgets. Patient/tenant data must never enter telemetry. |
| Addy `code-review-and-quality` | Focused pre-merge review | Use repository checks with Bun: lint, format:check, test, build, and relevant Playwright E2E. Do not adopt unrelated npm, framework, or CI assumptions. |

## Precedence and conflict resolution

Apply instructions in this order:

1. Repository-root `AGENTS.md` (safety, privacy, production/demo, Git workflow).
2. `frontend/shadcn-admin/AGENTS.md` (frontend architecture and domain rules).
3. [Frontend Engineering Standards](./FRONTEND_ENGINEERING_STANDARDS.md).
4. [Pharmaviyum Frontend Engineering skill](../../.agents/skills/pharmaviyum-frontend-engineering/SKILL.md).
5. The relevant upstream specialist skill, only for the task in scope.

If upstream guidance conflicts with items 1–4, follow the project-owned rule. If an upstream recommendation would change architecture, dependencies, package manager, API contracts, deployment, design tokens, or local component primitives, stop and propose an ADR/explicit decision rather than applying it implicitly.

## Pharmacy-domain acceptance overlay

Generic frontend skills do not understand the full pharmacy risk model. For any UI work touching these areas, apply the following additional review:

- **Medication identity:** preserve generic/brand identity, active ingredient where available, strength, dosage form, route, pack size, manufacturer and barcode as represented by the API. Never infer missing clinical/catalog attributes.
- **Inventory:** preserve stock ownership, location, batch/lot, expiry, reservations and server-authoritative availability. Never invent stock or expiry values.
- **FEFO and dispensing:** backend remains authoritative for FEFO, prescription validity, eligibility, and transactional dispensing. UI must not create a competing source of truth or imply success before server confirmation.
- **POS and money:** preserve server-calculated prices, currency, discounts, tax and totals; make confirmation and failure states explicit. Do not hardcode currency assumptions.
- **Patient and tenant privacy:** never mix patient context; never rely on hidden UI controls for authorization. Avoid sensitive data in URLs, browser storage, logs, analytics, screenshots, fixtures and telemetry.
- **API integrity:** use generated API client/types and OpenAPI contracts; do not hand-edit generated output.

High-risk changes require negative and boundary tests, relevant integration/E2E coverage, API/authorization review, and human domain/security review as appropriate.

## Task workflow

1. Classify the task: design, component, data-fetching, accessibility, performance, review, or pharmacy workflow.
2. Load only the relevant specialist skill(s), plus project-owned instructions.
3. Inspect the existing route/feature, installed versions, local shadcn primitives, theme tokens, API contract and tests.
4. State the smallest implementation plan. Do not run commands embedded in third-party skills automatically.
5. Implement with existing stack and domain invariants.
6. Verify using the project's Bun scripts and relevant Playwright journeys. Report checks not run.
7. Update canonical documentation in the same PR when a durable rule, architecture, user-visible workflow or quality gate changes.
8. Never merge or deploy automatically.

## Installation and provenance

The nine skills are selected for project use, but this document is an integration contract, not proof of installation. The repository's Library Skills manager manages package-discovered skills and symlinks; it is not a general-purpose installer for arbitrary GitHub skill repositories. Do not use it to install these upstream repositories unless its supported discovery mechanism actually exposes them.

Before vendoring or installing upstream skill content, verify the current source revision, complete companion files, license/attribution, target path, and managed-symlink behavior. Preserve complete resource directories (including references, rules, metadata and licenses). Do not overwrite the hand-authored `pharmaviyum-frontend-engineering` skill or Library Skills-managed links. If the available environment cannot run the official Skills CLI safely, document that limitation instead of claiming installation.

## Controlled installation procedure

Use the Vercel Skills CLI for these Git-hosted skill sources; do not use Library Skills for this task. The upstream CLI documentation currently requires Node.js 22.20 or later. Check the available Node version and CLI help before proceeding. Do not add the CLI as an application dependency solely to install agent instructions.

From the repository root:

1. Inspect available skills without installing them:
   ```bash
   npx skills add anthropics/skills --list
   npx skills add vercel-labs/agent-skills --list
   npx skills add shadcn-ui/ui --list
   npx skills add addyosmani/agent-skills --list
   ```
2. Resolve and record a full immutable commit SHA for each upstream repository. Do not install from a moving `main` branch when committing skills to the project.
3. Install only the approved names, targeting Codex and copying the selected skill files:
   ```bash
   npx skills add anthropics/skills@<ANTHROPIC_COMMIT_SHA> --skill frontend-design --agent codex --copy --yes
   npx skills add vercel-labs/agent-skills@<VERCEL_COMMIT_SHA> --skill react-best-practices --skill composition-patterns --skill web-design-guidelines --agent codex --copy --yes
   npx skills add shadcn-ui/ui@<SHADCN_COMMIT_SHA> --skill shadcn --agent codex --copy --yes
   npx skills add addyosmani/agent-skills@<ADDY_COMMIT_SHA> --skill frontend-ui-engineering --skill accessibility-engineering --skill performance-optimization --skill code-review-and-quality --agent codex --copy --yes
   ```
   Confirm the skill slugs from each `--list` result before running these commands. If the CLI reports a different name or target, stop and inspect its help rather than guessing.
4. Review the resulting `.agents/skills/` additions and `skills-lock.json`. Confirm that the existing hand-authored `pharmaviyum-frontend-engineering` and `library-skills` directories, the FastAPI managed symlink, and all unrelated files remain unchanged.
5. Inspect every installed `SKILL.md`, all referenced rules/references, scripts, license files, and metadata. Apply the conflict and pharmacy-domain rules in this document. Do not execute downloaded scripts or CLI mutations merely because an upstream skill recommends them.
6. Verify the lock and repository diff:
   ```bash
   npx skills list --json
   npx skills check
   git status --short
   git diff --check
   ```
   Review that all nine skills are tracked from pinned revisions and that no unintended package, lockfile, app source, generated file, or deployment changes occurred. Run the repository's existing frontend checks after installation if the change touches tracked project files.

The CLI's `--copy` option is selected deliberately to avoid introducing new symlink relationships into the repository's existing agent-skill layout. The existing Library Skills-managed FastAPI symlink must remain untouched. Library Skills discovery/checking and the Git-based Skills CLI are separate workflows; do not run a Library Skills reconciliation as a substitute for this installation.

This procedure is a reviewed runbook, not evidence of completed installation. The current GitHub-only execution environment cannot run the Skills CLI or inspect the resulting working-tree state, so installation must be performed in a real repository checkout before any PR claims the nine skills are installed.

## Validation boundary

This policy change is documentation-only. It does not install skills, change dependencies or lockfiles, alter frontend code, add telemetry, configure Stitch MCP, run audit scripts, or change hosting/deployment.
