# Pi Coding Agent Instructions — Pharmaviyum ERP/CRM

## Project context
- Pharmacy ERP/CRM with a FastAPI backend and React/TypeScript admin frontend.
- Backend source: `src/pharmaviyum/`; tests: `tests/`.
- Frontend: `frontend/shadcn-admin/`.
- Python dependencies and tooling are managed with `uv` and `pyproject.toml`; do not introduce or update a separate `requirements.txt`.
- Python constraint in `pyproject.toml`: `>=3.14.7,<3.15`.
- API client generation script: `scripts/generate-api-client.sh`. It expects a local backend at `http://localhost:8000` and writes generated code under `frontend/shadcn-admin/src/client/`.

## Non-negotiable safety rules
- Never commit directly to `main`; work on a descriptive feature/fix branch and open a PR.
- Never deploy, trigger production actions, change Render/FastAPI Cloud settings, or run destructive database operations unless the user explicitly requests that exact action.
- Treat production data, credentials, patient data, prescriptions, and tenant-specific data as sensitive. Never print secrets or place credentials in source files, logs, tests, prompts, or commits.
- Do not run write-load tests against production or public endpoints. Prefer local/test databases and explicit test fixtures.
- Before changing migrations, auth, permissions, tenant isolation, dispensing, inventory, batch/expiry, or stock movements, inspect adjacent code and tests and explain data-integrity implications.
- Do not bypass failing CI checks, weaken tests, or change quality gates just to make a workflow pass.
- Do not claim a command, test, deployment, or health check passed unless you actually ran it and saw the result.

## Engineering approach
1. Inspect relevant code, tests, API schemas, and recent changes before editing. Keep changes minimal and consistent with existing patterns.
2. State a short plan for multi-file or risky work. Prefer incremental changes with focused tests.
3. Preserve auditability and transactional integrity for POS, dispensing, FEFO, inventory, receiving, procurement, transfers, prescriptions, and expiry handling.
4. For Mortarium AI/RAG, preserve tenant isolation, access control, grounding/citations, structured-output validation, guardrails, and evaluation coverage. Never expose one tenant's context to another.
5. Keep API contracts and frontend types aligned. Do not hand-edit generated client output when it can be regenerated from OpenAPI.
6. Avoid broad refactors, unrelated formatting, speculative dependencies, and country-specific assumptions unless requested.
7. Report files changed, commands actually run, test outcomes, and unresolved risks/blockers.

## Backend checks
Run from repository root as appropriate:
- `uv run ruff check src/ tests/`
- `uv run black --check src/ tests/`
- `uv run isort --check-only --diff --profile black src/ tests/`
- `uv run mypy --explicit-package-bases src/pharmaviyum/`
- `uv run pytest` (prefer focused tests first; run the full suite when practical)

Do not auto-format unrelated files. Use the repository's pinned tooling from `pyproject.toml`.

## Frontend checks
Run from `frontend/shadcn-admin/` using the repository's existing package manager and lockfile:
- `bun run lint`
- `bun run format:check`
- `bun run test`
- `bun run build`

Check the lockfile and CI workflow before installing dependencies or switching package managers. Do not update dependencies merely to resolve an unrelated failure.

## High-risk workflows to verify
- Authentication and authorization, including tenant boundaries.
- POS/dispensing and stock/batch updates in a transaction.
- FEFO selection and expiry/batch constraints.
- Receiving, procurement, transfers, and audit trail.
- OpenAPI/frontend API-client contract consistency.
- Mortarium AI/RAG retrieval quality, citations, validation, access control, and tenant isolation.

## Git workflow
- Check `git status` before editing and before committing; preserve user changes.
- Do not reset, clean, force-push, amend unrelated commits, or discard user work.
- Keep the PR focused and include validation results and known limitations.
- Wait for required checks and review before merge. Do not merge or deploy automatically.
