# Git History and Branch Governance

## Purpose

Keep the repository history reviewable, attributable, reproducible, and safe for a public engineering showcase. This policy governs future work; it does not require rewriting already-merged history.

## Commit messages

Use Conventional Commit syntax:

```text
<type>(<scope>): <imperative summary>
```

Examples:

- `feat(pos): enforce idempotent checkout allocation`
- `fix(auth): reject cross-tenant patient lookup`
- `test(inventory): verify FEFO allocation under contention`
- `docs(architecture): record dispensing workflow decision`
- `security(phi): audit purpose-bound patient reads`

Rules:

- Use a meaningful type and a narrow domain scope where practical.
- Keep the subject imperative, specific, and at most 72 characters.
- Describe the outcome, not the activity ("fix checkout replay" rather than "work on checkout").
- One commit should represent one coherent, reviewable change.
- Explain non-obvious rationale, constraints, and compatibility implications in the body.
- Include issue/PR references when they exist.
- Do not use repeated generic subjects such as "updates", "fixes", or "changes".
- Formatting-only commits should be avoided inside focused feature work. If a repository-wide formatting pass is necessary, isolate it and explain why.

## Commit body for non-trivial changes

Use the body to capture the information that cannot fit in the subject:

- **Why:** requirement, defect, or risk being addressed.
- **What:** behavior or contract changed.
- **Validation:** exact tests or checks run; do not claim checks that were not run.
- **Risk:** migration, data-retention, compatibility, security, or rollout implications.

For security, tenant isolation, PHI, dispensing, inventory, and database changes, make the relevant invariant explicit.

## Branches and pull requests

- Never commit directly to `main`.
- Use descriptive branch names with a stable prefix: `feat/`, `fix/`, `security/`, `test/`, `docs/`, or `chore/`.
- Keep each PR focused on one independently reviewable objective.
- Prefer a small, coherent commit series over repeated formatting or wording-only commits.
- A stacked PR must target its actual parent feature branch. Do not retarget it to `main` until the parent has merged and the resulting diff has been rechecked.
- Rebase or amend only a private feature branch before merge, after checking whether collaborators depend on it. If a rewrite is necessary, use lease-protected force push; never rewrite `main` or a shared/merged history.
- Wait for required CI checks on the exact PR head SHA.
- Use squash merge for a PR whose internal commits are exploratory, repetitive, or mostly mechanical. Preserve a multi-commit series when each commit is independently meaningful and reviewable.
- Delete a merged feature branch only after confirming it is not needed by another open PR, release, or recovery procedure.

## Author identity and provenance

- Preserve truthful author and committer attribution.
- Do not fabricate authorship, dates, signatures, test results, or historical intent.
- GitHub merge commits may have GitHub as committer while preserving the PR author; this is expected.
- Signed commits are encouraged where the contributor's signing setup supports them, but a missing signature must not be misrepresented as a verified signature.

## NDA, privacy, and secret hygiene

- Treat public Git history, PR diffs, comments, artifacts, and deleted-file history as externally reviewable.
- Never commit credentials, tokens, private keys, PHI, real patient records, or confidential commercial metrics.
- Use synthetic data in tests and demos.
- Run secret scanning and review changed files before opening a PR.
- If a secret is exposed, revoke/rotate it immediately; removing it from the latest tree is not sufficient. History cleanup is a separate incident-response action and must be coordinated with repository collaborators.
- Do not publish proprietary implementation or internal business information unless publication rights have been confirmed.

## Review and release evidence

For every non-trivial PR, record:

1. Requirement or issue being addressed.
2. Scope and files changed.
3. Tests and CI evidence tied to the exact head SHA.
4. Known limitations and rollback/data-retention implications.
5. Confirmation that no production deployment, production data, or secrets were changed unless explicitly approved.

This policy is an engineering workflow standard, not legal advice or proof of NDA compliance.
