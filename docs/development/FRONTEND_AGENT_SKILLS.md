# Frontend Agent Skills — Pharmaviyum ERP

## Purpose

This document defines the recommended agent-skill setup for the active frontend at `frontend/shadcn-admin/`. It is aligned with the repository's actual stack and deployment model, not generic React/Next.js or Vercel-hosted templates.

## Repository findings

The active frontend currently uses:

- React 19 and TypeScript.
- Vite 8.
- TanStack Router for file-based routing.
- TanStack Query and TanStack Table.
- Tailwind CSS v4.
- shadcn/ui with the `new-york` style and `rsc: false`.
- Radix UI packages and Lucide icons.
- React Hook Form and Zod.
- Zustand.
- Bun and the committed `bun.lock`.
- Vitest Browser and Playwright Test.

The frontend is part of the FastAPI application and is served with the backend from the same application/domain. The demo deployment target is **FastAPI Cloud**. Vercel skills are considered only as framework-independent React/frontend guidance; no Vercel hosting, edge runtime, deployment, or platform configuration is implied.

The repository already has a root `AGENTS.md` and a Library Skills management guide under `.agents/skills/library-skills/`. This PR adds a frontend-specific `AGENTS.md` and a Pharmaviyum frontend engineering skill.

## Recommended skills

Install selectively. The project-owned skill remains authoritative for Pharmaviyum architecture, pharmacy workflows, security, deployment, and quality gates. Upstream skills provide focused specialist guidance.

| Priority | Skill | Source | Role and adoption |
|---|---|---|---|
| P0 | `pharmaviyum-frontend-engineering` | This repository | Project architecture, FastAPI Cloud deployment boundary, pharmacy workflows, privacy, and quality gates. |
| P0 | `shadcn` | [Official shadcn skill](https://github.com/shadcn-ui/ui/tree/main/skills/shadcn) | Official component discovery, CLI, composition, theming, and project-aware shadcn guidance. |
| P0 | `react-best-practices` | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) | React rendering, performance, async, and bundle practices. Apply framework-independent guidance only; ignore Vercel deployment/runtime assumptions. |
| P1 | `frontend-ui-engineering` | [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills/tree/main/skills/frontend-ui-engineering) | Production UI composition, design-system adherence, responsive behavior, interaction states, and accessibility. |
| P1 | `performance-optimization` | [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills/tree/main/skills/performance-optimization) | Measurement-first performance investigation across browser, frontend, API, and database boundaries. Use when profiling or performance work is requested. |
| P1 | `accessibility-engineering` | [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills/tree/main/skills/accessibility-engineering) | Structured accessibility audits and remediation. Complements, rather than replaces, automated and manual testing. |
| P1 | `composition-patterns` | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns) | Compound components and maintainable component APIs. |
| P1 | `web-design-guidelines` | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | Accessibility and web-interface quality review. Avoid duplicating the Addy accessibility skill in every task; select the more relevant reviewer. |
| P1 | `react-vite-dashboard` | [Google Stitch Skills](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-build/skills/react-vite-dashboard) | Dashboard layout and design-to-React workflow, TanStack Query patterns, and design-token mapping. Adapt React Router examples to TanStack Router; remove Web3-specific material. Stitch MCP is optional and not required for normal development. |
| P1 | `shadcn-ui` | [Google Stitch Skills](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-build/skills/shadcn-ui) | Additional shadcn component discovery, composition, forms, tables, and accessibility guidance. Prefer the official shadcn skill as the primary source; use this as a supplementary reference after adapting outdated Next.js/Tailwind v3 assumptions. |
| P2 | `react-components` | [Google Stitch Skills](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-build/skills/react-components) | Optional conversion of Stitch screens into React component systems when the team adopts Stitch as a design workflow. |
| P1 | `playwright` | Existing project tooling and E2E docs | Browser-level verification of critical user journeys using the project's existing Playwright setup. |
| P2 | `visual-regression` | Project-owned future extension | Screenshot comparison for stable, high-value screens. |

### Compatibility notes

The upstream skills are useful references, not drop-in project specifications:

- Google Stitch `react-vite-dashboard` describes React 18 and React Router. Pharmaviyum uses React 19 and TanStack Router. Its Web3 examples are irrelevant to this pharmacy ERP.
- Google Stitch `shadcn-ui` includes Next.js-oriented examples and Tailwind CSS v3-era configuration. Pharmaviyum uses Vite and Tailwind CSS v4.
- Addy Osmani's frontend UI skill is broadly applicable, but its examples and breakpoints must be reconciled with existing local components, theme tokens, and project test tooling.
- Addy's performance skill is measurement-first. Do not add instrumentation or dependencies just because a skill example mentions them.
- Vercel skills are not deployment instructions. FastAPI Cloud remains the target hosting platform; frontend build/serving stays integrated with FastAPI.

### Suggested installation commands

Run from the repository root only after reviewing the current skill source and its license. Install only the skills needed for the task; do not install every skill pack globally by default.

```bash
# Official shadcn skill
npx skills add shadcn/ui

# Vercel React performance and component composition
npx skills add vercel-labs/agent-skills --skill react-best-practices
npx skills add vercel-labs/agent-skills --skill composition-patterns
npx skills add vercel-labs/agent-skills --skill web-design-guidelines

# Addy Osmani — production UI, performance, and accessibility
npx skills add addyosmani/agent-skills --skill frontend-ui-engineering
npx skills add addyosmani/agent-skills --skill performance-optimization
npx skills add addyosmani/agent-skills --skill accessibility-engineering

# Google Stitch — Vite dashboard and shadcn supplementary guidance
npx skills add google-labs-code/stitch-skills --skill react-vite-dashboard
npx skills add google-labs-code/stitch-skills --skill shadcn-ui
```

For environments using Bun, use the equivalent `bunx skills add ...` invocation supported by the installed Skills CLI. Follow the CLI's interactive review and target selection; do not use an install-all option by default. Some Stitch workflows additionally require Stitch MCP; ordinary frontend development does not.

## What should remain project-owned

The following rules are specific to Pharmaviyum and must not be delegated to generic upstream skills:

- Vite + TanStack Router architecture; no Next.js, React Server Components, or React Router assumptions.
- FastAPI Cloud as the demo deployment target; no Vercel deployment/runtime assumptions.
- Existing shadcn configuration, local component implementations, theme tokens, and Bun lockfile.
- Pharmacy-specific medicine identity and medication catalog semantics.
- POS and dispensing safeguards, batch/expiry handling, FEFO, and transactional backend authority.
- Patient-data privacy, tenant isolation, and authorization boundaries.
- API client generation and OpenAPI contract consistency.
- The repository's lint, format, test, build, and Playwright commands.

These constraints live in `frontend/shadcn-admin/AGENTS.md` and `.agents/skills/pharmaviyum-frontend-engineering/SKILL.md`.

## Installation and maintenance policy

1. Keep the custom Pharmaviyum skill in source control.
2. Prefer official upstream skills for generic React and shadcn guidance.
3. Use Addy Osmani's skills for focused UI engineering, measured optimization, and accessibility reviews; avoid loading all three when the task does not need them.
4. Use Google Stitch skills selectively for dashboard/design-to-code and supplementary shadcn guidance; do not let their framework assumptions override the repository.
5. Do not copy upstream skill files into this repository unless there is a clear offline/reproducibility requirement and its license, attribution, and update process are documented.
6. Do not install overlapping skills that prescribe conflicting frameworks, component libraries, state managers, styling systems, or package managers.
7. Review upstream changes before updating installed skills.
8. Keep generated route trees, generated API clients, and managed skill symlinks under their respective generators/managers.
9. Validate skill installation with the Skills CLI or the existing Library Skills workflow; do not hand-edit managed symlinks.

## Audit references

- [Official shadcn Skills documentation](https://ui.shadcn.com/docs/skills)
- [Official shadcn skill source](https://github.com/shadcn-ui/ui/tree/main/skills/shadcn)
- [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills)
- [Vercel React Best Practices](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices)
- [Vercel Composition Patterns](https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns)
- [Vercel Web Design Guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines)
- [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills)
- [Addy Frontend UI Engineering](https://github.com/addyosmani/agent-skills/tree/main/skills/frontend-ui-engineering)
- [Addy Performance Optimization](https://github.com/addyosmani/agent-skills/tree/main/skills/performance-optimization)
- [Addy Accessibility Engineering](https://github.com/addyosmani/agent-skills/tree/main/skills/accessibility-engineering)
- [Google Stitch Skills](https://github.com/google-labs-code/stitch-skills)
- [Google Stitch React + Vite Dashboard](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-build/skills/react-vite-dashboard)
- [Google Stitch shadcn/ui](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-build/skills/shadcn-ui)
- [Anthropic Skills](https://github.com/anthropics/skills)
- [Repository frontend E2E guide](./frontend-e2e.md)
