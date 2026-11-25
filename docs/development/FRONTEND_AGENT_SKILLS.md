# Frontend Agent Skills — Pharmaviyum ERP

## Purpose

This document defines the recommended agent-skill setup for the active frontend at `frontend/shadcn-admin/`. It is intentionally aligned with the repository's actual stack rather than generic React/Next.js starter templates.

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
- Bun and the committed `bun.lock`.
- Vitest Browser and Playwright Test.

The repository already has a root `AGENTS.md` and a Library Skills management guide under `.agents/skills/library-skills/`. It did not have a frontend-specific `AGENTS.md` or a Pharmaviyum frontend engineering skill when this audit was performed.

## Recommended skills

Install only the skills relevant to the work. Do not install overlapping generic frontend packs indiscriminately.

| Priority | Skill | Source | Role |
|---|---|---|---|
| P0 | `pharmaviyum-frontend-engineering` | This repository | Project architecture, pharmacy workflows, privacy, quality gates |
| P0 | `shadcn` | [shadcn/ui](https://github.com/shadcn-ui/ui/tree/main/skills/shadcn) | Official component discovery, CLI, composition, theming |
| P0 | `react-best-practices` | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) | React rendering, performance, async and bundle practices |
| P1 | `composition-patterns` | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns) | Compound components and maintainable component APIs |
| P1 | `web-design-guidelines` | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | Accessibility and interface quality review |
| P1 | `frontend-design` | [Anthropic Skills](https://github.com/anthropics/skills) | Visual direction and interface craft; verify current availability and license before installation |
| P1 | `playwright` | Existing project tooling and E2E docs | Browser-level verification of critical user journeys |
| P2 | `visual-regression` | Project-owned future extension | Screenshot comparison for stable high-value screens |

### Suggested installation commands

Run from the repository root only after reviewing the current skill source and its license:

```bash
# Official shadcn skill
npx skills add shadcn/ui

# Vercel React performance and architecture guidance
npx skills add vercel-labs/agent-skills --skill react-best-practices
npx skills add vercel-labs/agent-skills --skill composition-patterns
npx skills add vercel-labs/agent-skills --skill web-design-guidelines
```

For environments using Bun, use the equivalent `bunx skills add ...` invocation supported by the installed Skills CLI. Follow the CLI's interactive review and target selection; do not use an install-all option by default.

## What should remain project-owned

The following rules are specific to Pharmaviyum and must not be delegated to generic upstream skills:

- Vite + TanStack Router architecture; no Next.js or React Server Components assumptions.
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
3. Do not copy an upstream skill into this repository unless there is a clear offline/reproducibility requirement and its license, attribution, and update process are documented.
4. Do not install overlapping skills that prescribe conflicting frameworks, component libraries, state managers, styling systems, or package managers.
5. Review upstream changes before updating installed skills.
6. Keep generated route trees, generated API clients, and managed skill symlinks under their respective generators/managers.
7. Validate skill installation with the Skills CLI or the existing Library Skills workflow; do not hand-edit managed symlinks.

## Audit references

- [Official shadcn Skills documentation](https://ui.shadcn.com/docs/skills)
- [Official shadcn skill source](https://github.com/shadcn-ui/ui/tree/main/skills/shadcn)
- [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills)
- [Vercel React Best Practices](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices)
- [Vercel Composition Patterns](https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns)
- [Vercel Web Design Guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines)
- [Anthropic Skills](https://github.com/anthropics/skills)
- [Repository frontend E2E guide](./frontend-e2e.md)
