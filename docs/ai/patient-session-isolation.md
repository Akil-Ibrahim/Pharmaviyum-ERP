# Mortarium Patient-Scoped Conversation State

**Status:** Implemented in the pull request branch; not active in production until reviewed, merged and deployed.

## Scope

Mortarium conversation state is isolated by the tuple:

\`pharmacy_id + authenticated user_id + patient_id + client session_id\`

A missing patient is an explicit \`patient:none\` scope. It is not a wildcard and must never share state with a patient-specific conversation.

## Enforcement points

1. **API boundary** — both synchronous \`/api/v1/ai/query\` and streaming \`/api/v1/ai/query/stream\` derive the same versioned internal session scope after tenant authorization and patient membership validation.
2. **Redis dialogue memory** — memory keys are HMAC-derived from the API-scoped session identifier. Summary, short-term messages, archive and episodic facts therefore inherit the patient boundary.
3. **Agent checkpoint** — \`PharmacistAgent._thread_id()\` includes authenticated pharmacy, user, patient and session scope in its HMAC input.
4. **RAG checkpoint** — \`LangGraphRAG._thread_id()\` includes pharmacy, user, patient and session scope in its HMAC input. The persisted checkpoint thread ID is an opaque \`rag:v2:<sha256>\` digest.
5. **Prompt cache** — exact cache identity includes the full request context; semantic cache scope also includes patient and prescription IDs and remains opt-in for explicitly safe non-patient requests.

## Security invariants

- Reusing one client session ID for patient A and patient B MUST NOT reuse memory, Agent checkpoints, RAG checkpoints or cached responses.
- Patient A and a request without a patient MUST use distinct state namespaces.
- A patient ID is accepted only after the API confirms that the active patient belongs to the authenticated pharmacy tenant.
- Direct Agent/RAG checkpoint construction also validates patient ID shape and includes it in the checkpoint HMAC scope.
- Raw patient, user, tenant and session identifiers MUST NOT appear in the RAG checkpoint thread ID.
- The application \`SECRET_KEY\` must remain stable across instances and deployments. Rotation changes HMAC-derived checkpoint and memory namespaces and requires a planned migration/expiry strategy.
- Telemetry must not contain raw patient identifiers, prompts, completions or clinical content.

## Compatibility and retention

The API-scoped session format is versioned as \`mortarium-session:v3\`. Existing session namespaces are not automatically migrated or read as a fallback. This intentionally favors isolation over continuity: prior Redis memory may remain inaccessible to the new scope until its configured TTL expires.

RAG checkpoint IDs now use a versioned HMAC namespace. Existing plaintext RAG checkpoint records are not automatically rewritten or deleted. Before production rollout, define and execute an approved retention/deletion plan for legacy checkpoint rows and their backups. Do not perform broad checkpoint deletion without confirming ownership, retention requirements and rollback implications.

## Regression coverage

The test suite verifies:
- same client session + different patient yields different API session scopes;
- patient-specific and no-patient scopes differ;
- malformed patient/session identifiers are rejected;
- Agent checkpoint IDs differ by patient and reject malformed patient context;
- RAG checkpoint IDs differ by patient, tenant and secret; hide raw identifiers; and fail closed when a production secret is absent.

Before release, run the full AI unit suite, API tests, security tests, integration tests against PostgreSQL checkpoint storage and Redis memory, plus a staged end-to-end test that alternates patient A → patient B → no patient on one client session in both streaming and non-streaming modes.

## Operational boundary

This change modifies application code only. It does not migrate, delete or inspect production Redis/PostgreSQL checkpoint data, change production secrets, or deploy the application. It is not a clinical validation or regulatory certification.
