# ADR-0003: Patient-Scoped Mortarium Conversation State

## Status
Proposed — implementation is under review in [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287). This ADR does not claim the change is merged or active in production.

## Context
Mortarium uses an authenticated pharmacy context, an Agent Harness with Redis dialogue memory, and two LangGraph workflows with checkpoint persistence. The current main implementation scopes the API session by pharmacy, user and client session, but not by patient. Agent and RAG checkpoint identities do not consistently bind patient identity. Reusing a session while switching patients can therefore risk reusing prior dialogue or checkpoint state.

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
PR #287 proposes API session HMAC v3, patient-aware Agent/RAG checkpoint IDs, strict validation and regression tests. Required CI and code review must pass before this ADR can be reconsidered. No production deployment, data migration or legacy checkpoint deletion is authorized by this proposal.

## References
- [Mortarium RAG audit](../rag_architecture_audit.md)
- [AI architecture](../ai_architecture.md)
- [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287)
