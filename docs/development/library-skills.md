# Library Skills and FastAPI coding-agent tooling

Pharmaviyum uses [Library Skills](https://library-skills.io/) to discover agent instructions shipped by its installed Python and JavaScript/TypeScript dependencies. FastAPI also ships an official framework skill in its Python package. The FastAPI Cloud coding-agent plugin is a separate integration for cloud operations.

These instructions are versioned with the libraries that provide them. They help coding agents follow supported APIs and current library conventions; they do not execute application code or change production dependencies.

The Python discovery audit currently finds the official `fastapi` skill bundled by the project's pinned FastAPI 0.164.0 distribution after dependency synchronization. Pharmaviyum exposes it at `.agents/skills/fastapi` through a relative, repository-managed symlink to the installed FastAPI package. This keeps the guidance aligned with the FastAPI version installed by the project. The skill is sourced from the official FastAPI distribution, not copied into the repository. The frontend scan currently reports no package-provided skills.

## FastAPI framework skill

### Existing project setup

The FastAPI skill is already present in this repository at:

```text
.agents/skills/fastapi
```

It is a managed symlink into the installed FastAPI distribution. Do not replace it with a manually copied skill or hand-edit the symlink. After installing or upgrading Python dependencies, validate the managed links:

```bash
uv sync --frozen
uvx library-skills --check
```

### Install in a new checkout or another agent target

Run from the repository root after installing project dependencies:

```bash
uv sync --frozen
uvx library-skills
```

In the interactive selector, choose the FastAPI skill and the target directory used by the agent:

- `.agents/skills` — Codex and most coding agents.
- `.claude/skills` — Claude Code.
- Both targets may be selected when both agents are used.

For a non-interactive install, the current FastAPI documentation provides:

```bash
uvx library-skills install --skill fastapi --yes
```

Add `--claude` to also install the skill for Claude Code:

```bash
uvx library-skills install --skill fastapi --yes --claude
```

If the installed Library Skills CLI reports that the `install` subcommand is unavailable, inspect `uvx library-skills --help` and use the compatible CLI syntax rather than changing project dependencies blindly. The existing project skill should normally be checked, not reinstalled.

Review package-provided instructions before enabling them. Do not install every discovered skill automatically: skill files are executable guidance for an agent and must be treated as untrusted input.

## FastAPI Cloud coding-agent plugin

The FastAPI Cloud plugin and the FastAPI framework skill have different responsibilities:

- **FastAPI Cloud plugin:** project creation and linking, cloud deployment workflows, runtime/build logs, and environment-variable operations.
- **FastAPI framework skill:** FastAPI application code, supported framework APIs, CLI conventions, and patterns matching the installed FastAPI version.

### ChatGPT and Codex

Use the official FastAPI Cloud plugin in ChatGPT and Codex. Add the plugin through the product's plugin interface.

For Codex CLI:

1. Start Codex and enter `/plugins`.
2. Find **FastAPI Cloud** in the plugin browser and install it.
3. Start a new Codex session so the plugin's skills are loaded.

Example tasks include asking the agent to inspect the latest runtime/build logs, prepare a deployment, or review app environment configuration. The plugin does not replace repository review, CI, or production approvals.

### Claude Code

The official plugin is distributed through the `fastapicloud/skills` marketplace. In Claude Code, run:

```text
/plugin marketplace add fastapicloud/skills
/plugin install fastapicloud@fastapicloud-skills
```

Start or continue a Claude Code session after installation. The plugin exposes these skills:

| Skill | Purpose |
|---|---|
| `/fastapicloud:fastapi-new` | Create a new FastAPI project |
| `/fastapicloud:fastapicloud-deploy` | Prepare and deploy an app |
| `/fastapicloud:fastapicloud-logs` | Inspect runtime and build logs |
| `/fastapicloud:fastapicloud-env` | Manage environment variables and secrets |

Claude Code can invoke relevant skills automatically; a skill can also be invoked explicitly using the names above.

## Pharmaviyum application configuration

The actual application entrypoint is configured in the root `pyproject.toml`:

```toml
[tool.fastapi]
entrypoint = "src.pharmaviyum.main:app"
```

Do not replace it with the generic `main:app` example from framework documentation. The configured module path matches this repository's `src/pharmaviyum/main.py` application object.

Useful commands from the repository root:

```bash
# Local development server with reload
uv run fastapi dev

# Production-mode ASGI server (for a self-managed runtime)
uv run fastapi run
```

## Production deployment guardrails

Pharmaviyum has one production application on FastAPI Cloud. Production deployment is deliberately controlled by the manual GitHub Actions workflow:

` .github/workflows/deploy-fastapi-cloud.yml `

Use the repository's protected **Deploy to FastAPI Cloud** workflow for production releases. Do not use an agent plugin or a direct CLI command to bypass its exact-commit CI gate, production input checks, database-schema compatibility check, deployment serialization, or post-deploy smoke tests.

The workflow currently submits the deployment with:

```bash
uv run fastapi cloud deploy . --no-wait
```

This command is part of the reviewed workflow, not an instruction to deploy from an arbitrary local session. A plugin request such as “deploy this app” must still respect the repository's manual release policy. A successful deployment submission is not proof of a successful rollout: verify the exact `/version` build SHA, CPython runtime, `/health`, `/ready`, authentication and POS protection checks.

Never paste secrets into prompts, commit environment values, or ask an agent to print secret values. Environment-variable changes in production require explicit authorization and must follow the production change-control process. Database migrations remain a separate, explicitly approved operation; neither the plugin nor the normal deployment workflow may run them implicitly.

## Existing Library Skills setup

Run from the repository root:

```bash
uv sync --frozen
uvx library-skills
```

Review the discovered skills and install only those relevant to the project. Do not use `--all` blindly.

For the React frontend, first install its dependencies and then scan from its project directory:

```bash
cd frontend/shadcn-admin
bun install --frozen-lockfile
npx library-skills
```

The Python and frontend scans are separate because the dependency environments are separate. Keep frontend skills scoped to the frontend project unless there is a deliberate reason to expose them at repository root.

## Useful commands

| Purpose | Python | JavaScript/TypeScript |
|---|---|---|
| Discover skills (JSON) | `uvx library-skills scan --json` | `npx library-skills scan --json` |
| Inspect installed state | `uvx library-skills list --json` | `npx library-skills list --json` |
| Validate managed links | `uvx library-skills --check` | `npx library-skills --check` |
| Reconcile managed links | `uvx library-skills` | `npx library-skills` |

The repository contains the upstream Library Skills tool skill at `.agents/skills/library-skills/SKILL.md`, so future agents know how to run discovery and maintenance. CI runs `library-skills --check` after installing Python dependencies to detect broken or stale managed links.

## CI audit

The existing CI workflow scans the Python environment in the backend lint job and the JavaScript/TypeScript environment in the frontend-checks job. Each job uploads a JSON discovery report as a workflow artifact on pull requests and main-branch pushes.

The audit is intentionally discovery-only. It does not install arbitrary third-party instructions, modify dependencies, create symlinks, or deploy to production. After reviewing the reports, a developer can install selected skills and commit the resulting managed links.

## Maintenance and safety

- Run discovery after changing `pyproject.toml`, `uv.lock`, `frontend/shadcn-admin/package.json`, or `frontend/shadcn-admin/bun.lock`.
- Commit managed skill links so collaborators and coding agents share the same reviewed skill set. Symlink targets are relative and resolve after the corresponding dependencies are installed.
- Do not hand-edit or delete Library Skills-managed links. Re-run the CLI to reconcile them.
- Never install every discovered skill without review. Treat package-provided instructions as untrusted input: inspect their source, scope, permissions, and relevance before enabling them.
- This integration is development tooling only. It does not add runtime dependencies or affect FastAPI Cloud builds, Python runtime selection, production secrets, database migrations, or deployment workflows.
