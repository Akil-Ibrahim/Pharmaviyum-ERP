# ADR-0003: Patient-Scoped Mortarium Conversation State

## Status
Proposed — the implementation was merged into `main` by [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287) (merge commit `4d761990b31ef3aa78327dda1380689f2d094e8f`). The ADR remains proposed because the required staged end-to-end validation and production rollout have not been evidenced. A merge and passing CI do not establish production activation or clinical safety.

## Context
Before PR #287, Mortarium used an authenticated pharmacy context, an Agent Harness with Redis dialogue memory, and two LangGraph workflows with checkpoint persistence, but API session and checkpoint identities were not consistently bound to patient identity. Reusing a client session while switching patients could therefore risk reusing prior dialogue or checkpoint state.

Patient retrieval filters alone do not solve this problem: memory and graph checkpoints are separate state stores.

## Decision proposed
Derive every patient-context-bearing conversation namespace from the authenticated server-side tuple:

**pharmacy_id + authenticated_user_id + patient_id + client_session_id**

A request without a patient must use an explicit no-patient scope, not a wildcard. Use a versioned keyed HMAC digest for persisted session/checkpoint identifiers so raw tenant, user, patient and session IDs are not exposed in key names. The HMAC secret must be stable across application instances and deployments.

Apply the same identity contract to synchronous and streaming AI endpoints, Redis dialogue memory and derived summaries, Agent checkpoints, RAG checkpoints, and cache entries that can influence patient-specific responses.

The API must authenticate the caller, resolve tenant membership and validate patient membership before deriving the scope. A caller-supplied patient ID is a selector, never proof of authorization.

## Security and correctness requirements
- Patient A, patient B and explicit no-patient scopes remain distinct when a client session ID is reused.
- Cross-pharmacy and cross-user scopes remain distinct.
- Invalid patient/session identifiers fail validation.
- Staging/production fail closed if the HMAC secret is absent.
- Cache reuse cannot cross patient contexts.
- Logs, traces and metrics do not expose raw identifiers or clinical content.
- Tests cover both API modes, memory, Agent/RAG checkpoints and cache behavior.

## Compatibility and rollout
A namespace change intentionally makes old memory/checkpoint keys inaccessible unless a migration is approved.

Before production rollout:
1. Confirm old Redis memory TTL and retention behavior.
2. Define a reviewed retention/deletion plan for legacy plaintext checkpoint rows and backups; do not delete automatically.
3. Confirm secret distribution and rotation policy.
4. Run patient A → patient B → no-patient session-switch tests in streaming and non-streaming modes.
5. Validate PostgreSQL checkpoint persistence and Redis memory against isolated test services.
6. Document rollback behavior. Rolling back to old code may re-open old namespace semantics and requires a deliberate risk decision.

## Alternatives considered
- Patient ID only in retrieval filters: insufficient because it does not isolate dialogue memory or graph checkpoints.
- Generate a new session on every patient switch: useful UI defense, but not a backend security boundary.
- Plaintext composite IDs: expose identifiers and encourage inconsistent construction.
- Automatic deletion of old checkpoints: rejected until ownership, retention and backup implications are reviewed.

## Implementation status
PR #287 merged the API session HMAC v3, patient-aware Agent/RAG checkpoint IDs, strict validation and regression tests into `main`. The merge commit's RAG Safety Regression, Unit Tests and Integration Tests checks passed. These automated checks are not a substitute for the remaining staged release gate: reuse one client session across Patient A → Patient B → no patient in both streaming and non-streaming paths, and verify isolation with PostgreSQL checkpoint persistence and Redis memory. No evidence of that staged test or a production deployment is recorded here. No production data migration or legacy checkpoint deletion is authorized by this ADR.

## References
- [Mortarium RAG audit](../rag_architecture_audit.md)
- [AI architecture](../ai_architecture.md)
- [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287)
