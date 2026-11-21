# Pi project guidance — Pharmaviyum

You are working in the Pharmaviyum ERP/CRM repository. Read the root `AGENTS.md` before making changes and follow it.

## Default workflow
- Start by checking `git status --short --branch`; preserve any user changes.
- Inspect relevant implementation, tests, migrations, API schemas, and recent history before editing.
- For multi-file work, give a concise plan and implement in small, reviewable steps.
- Prefer focused tests first, then the relevant broader checks. Report commands and results accurately.
- Keep changes on the current feature branch. Never commit directly to `main`, merge a PR, or deploy unless the user explicitly requests that specific action.
- Before finishing, summarize changed files, tests actually run, failures, and remaining risks.

## Domain-specific invariants
- Treat pharmacy inventory, batch/expiry, FEFO, receiving, dispensing, POS, prescriptions, procurement, and transfers as transactional business workflows. Preserve stock consistency and auditability.
- Do not infer medication availability, price, stock, or sellability from reference-drug data alone. Follow the existing local-product, price, stock, and batch rules.
- For Mortarium AI/RAG, enforce tenant isolation and authorization at retrieval and tool boundaries. Keep grounded outputs, citations, schema validation, and guardrails. Never leak patient or tenant data across contexts.
- Do not use real patient data in tests or logs; use synthetic fixtures.
- Never put API keys, OAuth tokens, database URLs, secrets, or production data in repository files or tool output.

## Quality and safety
- Do not weaken tests, security checks, type checks, or CI configuration merely to obtain a green build.
- Do not run write tests, migrations, load tests, or destructive commands against production.
- Do not change deployment configuration or initiate deployment as an incidental part of a code task.
- Generated API client files should be regenerated from the backend OpenAPI contract using the repository's script rather than hand-edited, unless the task explicitly requires otherwise.
