# Library Skills integration

Pharmaviyum uses [Library Skills](https://library-skills.io/) to discover agent instructions shipped by its installed Python and JavaScript/TypeScript dependencies.

These instructions are versioned with the libraries that provide them. They help coding agents follow supported APIs and current library conventions; they do not execute application code or change production dependencies.

## Local setup

Run from the repository root:

```bash
uv sync --frozen
uvx library-skills
```

Review the discovered skills and install only those relevant to the project. Do not use `--all` blindly: a package-provided skill is still third-party instruction content and must be reviewed before adoption.

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

The repository contains the upstream Library Skills tool skill at `.agents/skills/library-skills/SKILL.md`, so future agents know how to run discovery and maintenance.

## CI audit

The `Library Skills Audit` GitHub Actions workflow scans both environments when manually dispatched or when dependency manifests/lockfiles or agent skills change in a pull request. It uploads JSON reports as a workflow artifact.

The audit is intentionally discovery-only. It does not install arbitrary third-party instructions, modify dependencies, create symlinks, or deploy to production. After reviewing the reports, a developer can install selected skills and commit the resulting managed links.

## Maintenance and safety

- Run discovery after changing `pyproject.toml`, `uv.lock`, `frontend/shadcn-admin/package.json`, or `frontend/shadcn-admin/bun.lock`.
- Commit managed skill links so collaborators and coding agents share the same reviewed skill set. Symlink targets are relative and resolve after the corresponding dependencies are installed.
- Do not hand-edit or delete Library Skills-managed links. Re-run the CLI to reconcile them.
- Never install every discovered skill without review. Treat package-provided instructions as untrusted input: inspect their source, scope, permissions, and relevance before enabling them.
- This integration is development tooling only. It does not add runtime dependencies or affect FastAPI Cloud builds, Python runtime selection, production secrets, database migrations, or deployment workflows.
