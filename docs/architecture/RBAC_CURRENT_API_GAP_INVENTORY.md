# Current API Authorization Gap Inventory

- **Status:** Read-only engineering findings for RBAC planning
- **Date:** 2026-11-26
- **Base reviewed:** `main` at `b5a0f51cc45e39b5afdfd21af99a5053823af5ce`
- **Related:** `PHARMACY_RBAC_PERMISSION_SPEC.md`, `SIDEBAR_AUTHORIZATION_INTEGRATION_PLAN.md`

This inventory records concrete authorization patterns found in the current source. It is not a complete endpoint audit and does not approve any role or permission grants. Verify router mounting and runtime exposure before treating any module as externally reachable.

## 1. High-priority findings

### 1.1 Prescription router currently has no authentication dependency

File: `src/pharmaviyum/api/v1/endpoints/prescriptions.py`

The placeholder router is included by the legacy `src/pharmaviyum/api/v1/router.py` aggregator. However, the runtime application imports `api_v1_router` from `src/pharmaviyum/api/v1/__init__.py` in `src/pharmaviyum/main.py`; that runtime aggregator does not include `prescriptions_router`. Therefore the separate placeholder handlers are not mounted by the reviewed runtime aggregator. Note: the runtime-mounted `pharmacy_entities.py` independently defines `/api/v1/prescriptions` GET/POST handlers protected by `CurrentSuperuser`; those are different handlers and are mounted. See section 3.2. Its current handlers:

- `GET /prescriptions/` has no user/authentication dependency and returns a placeholder empty list.
- `GET /prescriptions/{prescription_id}` has no user/authentication dependency and always returns 404.

There is no prescription data access in these placeholders today. However, the route is not protected by authentication. Before implementing real prescription reads or writes, add explicit authentication, pharmacy tenant resolution, action authorization, patient ownership checks, and PHI audit behavior. Do not expand these placeholders into real endpoints until the policy and data scope are defined.

### 1.2 Patient read and write operations use different coarse authorization models

File: `src/pharmaviyum/api/v1/endpoints/patients.py`

Observed patterns:

- Patient list, statistics, lookup, summary, and visit operations use `get_current_active_user` and `resolve_pharmacy_scope`.
- Patient create, update, and delete use `get_current_active_superuser`.
- AI-profile access has explicit pharmacist/membership-related checks and a required pharmacy context.

This is not yet a granular clinical permission model. Before replacing the current checks, inventory each patient operation separately and preserve pharmacy ownership enforcement. Do not infer that a pharmacy membership alone grants access to every patient record or every clinical action.

### 1.3 Tenant membership is not action authorization

Files: `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/models/pharmacy_membership.py`

`require_pharmacy_tenant` checks an active membership for ordinary users; superusers currently bypass that membership check. It returns a tenant context, not a role or action grant. The membership model has no role field.

Keep this boundary explicit: membership proves tenant affiliation, not permission to dispense, refund, approve procurement, change stock, view PHI, or administer users.

## 2. Additional coarse-grained authorization patterns

### 2.1 Product catalog

File: `src/pharmaviyum/api/v1/products.py`

Observed patterns:

- Product create, update, and delete require `CurrentSuperuser`.
- Product search, detail, and list require `CurrentUser`.

This is global user/superuser gating, not pharmacy-scoped catalog permissions. Review whether the catalog is global reference data or tenant-owned data before introducing pharmacy scoping.

### 2.2 Pharmacy entities and inventory

File: `src/pharmaviyum/api/v1/pharmacy_entities.py`

Observed patterns include:

- Pharmacy and supplier creation/listing are superuser-only in this module.
- Inventory list uses membership-derived pharmacy filtering for ordinary users.
- Inventory create, update, adjustments, and delete are superuser-only.
- Batch and prescription operations in this module are superuser-only.

Inventory mutations should be mapped to separate action permissions and audited. Do not replace the current superuser gate with a broad `inventory.write` grant without defining receive, adjust, transfer, reconcile, and delete semantics.

### 2.3 Orders

File: `src/pharmaviyum/api/v1/orders.py`

Observed patterns:

- Order create and status update require an active superuser.
- Order detail requires an active user and resolves pharmacy scope.
- Patient/order/purchase queries attempt to constrain data through patient pharmacy ownership.

The current endpoint-level gates are inconsistent in granularity. Preserve row-level tenant constraints while separating create, status-transition, and read permissions.

## 3. POS module requires router-mount verification

File: `src/pharmaviyum/api/v1/pos.py`

The module contains tenant membership checks for product search, lot lookup, checkout, cancellation, and sale reads. These checks establish tenant membership but do not distinguish cashier checkout from refunds/cancellations or other action-specific permissions.

The inspected `src/pharmaviyum/api/v1/router.py` does not directly include this POS router. Verify the actual application router composition before assuming these handlers are exposed in the deployed app or adding them to the Sidebar contract.

## 4. Suggested remediation order after policy approval

1. Complete the API route inventory, including the final mounted route graph.
2. Secure placeholder clinical endpoints before adding prescription data access.
3. Define a centralized authorization dependency/service that combines authenticated principal, active tenant context, action permission, and resource ownership.
4. Migrate patient/PHI endpoints with fail-closed ownership semantics and audit coverage.
5. Migrate inventory, procurement, and POS operations using action-specific permissions.
6. Migrate global catalog and administration endpoints only after deciding whether their data is global or pharmacy-scoped.
7. Add endpoint-level 401/403, cross-tenant, role-change, and audit tests.
8. Expose the effective permission context to the frontend and then filter Sidebar navigation.


### 4.7 AI API and MCP tool authorization use the legacy account role

Files: `src/pharmaviyum/models/user.py`, `src/pharmaviyum/api/v1/ai.py`, `src/pharmaviyum/ai/mcp/context.py`, `src/pharmaviyum/ai/mcp/registry.py`, `src/pharmaviyum/ai/mcp/tool_management.py`, `src/pharmaviyum/ai/mcp/tools/patient_history.py`

Verified source behavior on the reviewed `main` commit:

- `User.role` is a computed property: `admin` when `is_superuser` is true, otherwise `pharmacist`. It is not stored on `PharmacyMembership` and cannot represent different roles for one user in different pharmacies.
- Both AI query endpoints validate the requested pharmacy through `require_pharmacy_tenant`, then `_set_mcp_context` copies `current_user.role` into trusted `MCPAuthorizationContext`. Tenant scope is therefore checked, but the role in that context remains account-global.
- `GET /api/v1/ai/tools` has only `CurrentUser`; it does not resolve a pharmacy context. It filters tool discovery using the same global `current_user.role`.
- MCP registry execution checks `ToolMetadata.required_roles` against the supplied trusted-context role. `check_rbac` grants every registered tool to `admin` and `system` regardless of each tool's `required_roles`.
- The `get_patient_history` tool declares `required_roles=["pharmacist"]` and independently requires `auth_context.user_role == "pharmacist"`, exact selected-patient equality, a non-empty purpose, and active patient ownership in the trusted pharmacy. It writes metadata-only PHI audit decisions and fails closed if the audit commit fails.

Security and consistency implications:

1. Every ordinary non-superuser account is currently represented as `pharmacist` in AI/MCP, regardless of whether that account should be a cashier, manager, or pharmacy admin in the selected pharmacy. The MCP role filter therefore does not establish clinical authorization.
2. A platform superuser is represented as `admin`; generic registry filtering exposes all tools to that role, but the patient-history function itself rejects `admin`. Tool discovery and tool execution can therefore disagree for this tool.
3. AI tool discovery is not pharmacy-context-aware. It must not be treated as a reliable UI permission contract for a multi-pharmacy user.
4. Patient-history selected-patient binding, tenant ownership, purpose classification, and PHI audit are meaningful additional safeguards, but they do not repair the incorrect upstream role resolution.
5. The generic MCP role list (`patient`, `pharmacist`, `admin`, `system`) is not the proposed pharmacy-role vocabulary and does not model action-level permissions.

Required future controls (not implemented by this audit):

- Resolve one active pharmacy membership for every pharmacy-scoped AI request and derive effective permissions from that membership on the server.
- Authorize patient-history access with an explicit clinical permission (for example, `patients.phi.read`) plus patient ownership and purpose policy; do not rely on a string role label.
- Make tool discovery use the same trusted pharmacy permission context as execution, while treating discovery only as presentation and rechecking authorization at dispatch.
- Keep platform-operator privileges separate from pharmacy roles; do not let a generic `admin` bypass silently imply unrestricted clinical access.
- Add tests for cashier/pharmacist/manager/admin membership roles across two pharmacies, role revocation, missing/ambiguous tenant context, tool discovery versus execution parity, and cross-patient/cross-pharmacy denial.



### 4.8 MCP request context propagation, server exposure, and asynchronous ingestion boundary

Files: `src/pharmaviyum/api/v1/ai.py`, `src/pharmaviyum/ai/mcp/context.py`, `src/pharmaviyum/ai/mcp/client.py`, `src/pharmaviyum/ai/mcp/registry.py`, `src/pharmaviyum/ai/mcp/server.py`, `src/pharmaviyum/api/v1/ingestion.py`, `src/pharmaviyum/ai/mortarium_rag/ingestion/tasks.py`.

Verified behavior:

- AI `/query` installs an `MCPAuthorizationContext` around `harness.run` and resets the ContextVar token in `finally`. Streaming installs the context inside the async event generator and resets it in the generator's `finally`. This is the correct request-lifetime pattern for async ContextVar use in these handlers.
- MCP Client refuses tool calls without trusted context and rejects supplied user/tenant/role values that differ from that context. Agent tool calls pass identity and tenant from graph state, but the client compares them against the trusted ContextVar before execution.
- MCP Registry independently requires trusted context and checks identity, pharmacy and role equality before dispatch. It re-establishes a child context for the tool function and resets that token in `finally`.
- MCP JSON-RPC `initialize` is intentionally public; all data capabilities (`tools/list`, `tools/call`, resources and prompts) require trusted context. Repository search found no FastAPI route or other production transport caller for `mcp_server.handle_request`; it is currently an internal server object exercised directly by tests, not evidence of an exposed unauthenticated MCP network endpoint.
- The AI `/tools` REST endpoint is different: it uses the global account role and does not resolve pharmacy context (see 4.7).

Async ingestion boundary:

- Both ingestion submission endpoints require `CurrentSuperuser`, then separately call `require_pharmacy_tenant` for the requested pharmacy before placing `pharmacy_id` in the Celery task config. The worker requires a positive integer pharmacy ID and stamps it onto document metadata before chunking/vector persistence.
- The Celery task does not receive or independently verify the submitting actor, membership, or role. The worker therefore relies on the API dispatch boundary and trusted task broker/config integrity; do not expose direct task dispatch to untrusted callers.
- `GET /ingest/jobs/{job_id}` and `GET /ingest/jobs` require only `CurrentSuperuser`; the job-status lookup does not visibly bind the job to a pharmacy or submitting actor. The jobs list is global for platform superusers. This is a platform-admin operation today, not pharmacy-admin functionality, and should remain platform-scoped unless a tenant-aware job ownership model is deliberately introduced.
- The upload route is additionally gated by global `CurrentSuperuser`, so a future pharmacy_admin membership role alone would not authorize ingestion. The current endpoint policy and product intent need an explicit decision before RBAC migration.

Security assessment:

- No ContextVar leakage or missing reset was identified in the reviewed AI query, stream, client, registry, and MCP server paths. This is a source-level assessment, not a concurrency stress-test result.
- The main remaining authorization defects are upstream role provenance (4.7), non-pharmacy-aware tool discovery, global-superuser-only ingestion administration, and lack of actor-bound job ownership. Do not claim ContextVar alone provides authentication; the trusted context must continue to be created only after the API authentication and tenant checks.
- Required tests: overlapping concurrent AI requests with different user/pharmacy/patient contexts; stream cancellation and exception cleanup; nested registry context restoration; attempts to call MCP server/client without context; and ingestion job cross-tenant access denial if tenant-visible job status is later introduced.



### 4.9 RAG retrieval, patient scope, LangGraph checkpoints, and cache isolation

Files reviewed on `main`: `src/pharmaviyum/ai/mortarium_rag/vector_store.py`, `pipeline.py`, `graph.py`, `schemas.py`, `src/pharmaviyum/ai/harness/cache.py`, `agent_harness.py`, `src/pharmaviyum/ai/harness/memory.py`, `src/pharmaviyum/ai/mortarium_rag/embeddings.py`, `src/pharmaviyum/api/v1/ai.py`.

Verified positive controls:

- `PgVectorStore.vector_search`, `bm25_search`, and `hybrid_search` require a positive integer `pharmacy_id` and an explicit `access_level` in `public|pharmacy|patient`. Patient-level retrieval additionally requires an exact positive `patient_id`; patient_id on non-patient access levels is rejected. No missing-filter fallback exists.
- LangGraph RAG builds three distinct retrieval scopes: public, pharmacy, and (only when selected) exact patient. Every filter set includes the authenticated pharmacy ID. Unknown country/category filters are omitted rather than compared to SQL NULL.
- Vector and BM25 retrieval receive the same metadata filters; hybrid search fuses those results. The current implementation does not implement parent expansion or source-record fetch as a second retrieval path; architecture documents correctly describe parent-child retrieval as target capability, not shipped behavior.
- `CanonicalMetadata` requires pharmacy_id and requires patient_id for patient-level chunks; it rejects patient_id for public/pharmacy chunks. `PgVectorStore.upsert` validates every chunk before persistence and serializes canonical metadata so extension fields cannot override canonical fields.
- Prompt exact-cache operations require both authenticated user and positive pharmacy ID. The exact cache key includes the prompt and full supplied context; the scoped context includes pharmacy, user, patient, prescription, jurisdiction/language and relevant policy/data versions.
- Semantic response-cache reuse is opt-in and rejects patient- or prescription-specific contexts, force-fresh requests and cache-disabled requests. Its Redis sorted-set namespace is scoped by pharmacy and user (and additional context dimensions).
- API session namespace is currently `mortarium-session:v4` and includes pharmacy, authenticated user, patient, controlled purpose and client session ID. Agent and RAG checkpoint IDs HMAC pseudonymize their input and include pharmacy/user/patient plus the API-scoped session ID. Thus purpose is included transitively through the v4 session ID, although it is not a separate field in the checkpoint HMAC payload.
- The reviewed memory module states that API supplies the scoped session identifier; the checkpoint and cache controls do not depend on model-supplied tenant IDs.

Remaining gaps / qualifications:

1. `CachedEmbeddings` uses a global Redis namespace keyed by provider class, cache namespace and SHA-256 of input text; it is not partitioned by pharmacy/user/patient. It stores embedding vectors for 30 days, not raw prompt text. This is not a direct cross-tenant retrieval path, because vectors are only reused for identical input text and are not returned as RAG evidence, but it is a shared cache of derived representations of potentially sensitive queries. Confirm whether query embeddings can contain PHI in actual call paths; consider disabling query-embedding caching for patient-specific/PHI-bearing text or using a documented privacy-reviewed policy.
2. The semantic prompt cache is correctly disabled for patient_id/prescription_id contexts by its helper, but its safety depends on `semantic_cache_safe` being set only by trusted server-side code. Do not accept that flag from client request payloads. Confirm the full call path and tests before enabling semantic reuse.
3. `RAGPipeline._build_filter_sets` (legacy compatibility path) includes `country: None` when country is absent, unlike the LangGraph path which omits unknown country. SQL JSON text equality to a NULL bind will match no rows, causing a fail-closed false-negative rather than a cross-tenant leak. Align the compatibility path to omit absent optional filters.
4. Checkpoint HMAC identifiers are pseudonymized, not encrypted; checkpoint payloads may still contain prompts and clinical evidence. Redis memory payloads and checkpoint payloads require separate transport, access-control, at-rest encryption, retention, backup-expiry and deletion controls.
5. Existing session-isolation docs are inconsistent: `patient-session-isolation.md` describes v4 in its enforcement section but retains v3 in its compatibility paragraph; `docs/ai_architecture.md` and `docs/rag_architecture_audit.md` still describe v3. Runtime `api/v1/ai.py` currently uses v4. Documentation must be reconciled before treating it as the authoritative rollout/retention contract.
6. Existing regression coverage is stronger than a source-only review: `tests/integration/test_ai_patient_session_isolation.py` contains (a) sync + streaming route scope binding using a recording harness, (b) real Redis memory-tier separation and per-scope clearing, (c) rejection of a patient belonging to another pharmacy before the harness is called, and (d) real PostgreSQL LangGraph checkpoint persistence/separation using unique HMAC thread IDs. The PostgreSQL test compiles a minimal synthetic StateGraph against the production checkpointer class; it does not run the complete Mortarium retrieval/agent graph end to end.
7. Prompt-cache tests in `tests/security/test_prompt_cache_isolation.py` cover missing user/pharmacy, tenant/user cache-key separation, semantic opt-in, patient/prescription exclusion and versioned context. RAG unit tests cover filter construction and patient A/B/no-patient filter separation for both LangGraphRAG and legacy RAGPipeline. These tests establish contracts, not the absence of every possible bypass in all runtime call paths.
8. No test execution was performed during this audit. The existence of integration tests is not evidence that they pass against the current branch or deployed environment. Staged end-to-end validation and production activation remain unverified.

Required regression/evidence:
- Run the existing `tests/security/test_rag_tenant_isolation.py`, patient isolation and prompt-cache isolation suites against current HEAD.
- Add/verify regression for legacy `RAGPipeline` missing-country behavior, semantic_cache_safe trust provenance, and embedding cache treatment of PHI-bearing query text.
- Perform staged E2E with one reused client session across patient A, patient B, and no-patient requests in both sync and streaming modes, backed by real Redis memory and PostgreSQL checkpoint persistence.
- Verify Redis ACL/TLS/at-rest policy, checkpoint table access grants, backups and retention separately from application-level HMAC namespacing.


### 4.10 MCP patient-history PHI audit coverage and minimum-necessary response

Files reviewed on `main`: `src/pharmaviyum/ai/mcp/tools/patient_history.py`, `src/pharmaviyum/ai/mcp/context.py`, `src/pharmaviyum/ai/mcp/registry.py`, `src/pharmaviyum/ai/mcp/tool_management.py`, `src/pharmaviyum/api/v1/ai.py`, `src/pharmaviyum/models/user.py`, `tests/security/test_mcp_patient_history_scope.py`.

Verified positive controls:

- `MCPAuthorizationContext` validates positive user/pharmacy identifiers, selected-patient ID shape, the controlled-purpose vocabulary, and recognized legacy role values. A purpose cannot exist without a selected patient.
- Both AI query handlers validate the selected active patient against the pharmacy tenant before invoking the harness. The model-supplied `PatientHistoryRequest.patient_id` must then exactly equal the trusted selected patient; the tool independently queries an active patient with the trusted pharmacy ID.
- `get_patient_history` records metadata-only allowed/denied `PHIAccessAudit` decisions. The allowed audit commit occurs before the response is returned; a commit exception prevents release of the patient history. The audit payload does not copy clinical fields.
- The tool's prescription and order count queries also constrain through the patient's trusted pharmacy ownership.
- `tests/security/test_mcp_patient_history_scope.py` contains unit-level cases for selected-patient success, model-selected patient mismatch, missing purpose, direct tool-boundary role denial, audit-commit failure, registry context propagation, AI patient/purpose pairing and invalid context construction.

Remaining gaps / qualifications:

1. **The effective clinical role is not pharmacy-scoped.** `User.role` still resolves to `admin` for platform superusers and `pharmacist` for every other account. `PharmacyMembership` has no persisted role/permission. Thus an ordinary member who should be a cashier or another non-clinical role is represented as pharmacist in the trusted MCP context. Membership proves tenant affiliation only; it does not prove clinical authorization.
2. **Registry denial is not PHI-audited.** `MCPToolRegistry.call_tool` performs generic `check_rbac` before invoking the patient-history function. A role rejected at this pre-dispatch check never reaches the function's `record_decision` path, so no `PHIAccessAudit` row is written for that denied MCP invocation. The direct function role-denial unit test does not exercise this registry-level denial path.
3. **Tool discovery and execution are inconsistent for platform admins.** `check_rbac` grants `admin` and `system` access to every registered tool, and role-filtered discovery therefore exposes patient history to `admin`; the patient-history function itself requires exactly `pharmacist` and rejects `admin`. Discovery is not authorization, but the mismatch is misleading and needs a regression test.
4. **The MCP role vocabulary cannot represent the proposed pharmacy roles.** The context and registry currently accept only `patient|pharmacist|admin|system`; future `cashier`, `manager` and `pharmacy_admin` membership roles cannot be represented without changing the authorization contract. Do not map these roles to the legacy global `pharmacist` string.
5. **The response is not minimum-necessary.** The tool returns full name, age, gender, blood type, allergies, conditions, prescription and order counts, loyalty tier and preferred language. The caller currently has no permission-specific field projection or narrower purpose-to-field policy. Review whether every field is required for each supported purpose; default to the smallest clinical projection.
6. **Database-backed enforcement remains unverified.** The security tests replace the session factory with a fake session and assert calls to `commit()`; they do not prove PostgreSQL persistence, transaction rollback behavior, database constraints/triggers, or audit durability under a real database failure. No database-backed MCP audit fixture was identified in the reviewed test.
7. **Some denials occur before the MCP tool.** Invalid tenant membership or selected-patient ownership is rejected by the AI API before the harness and MCP tool execute. These API-level rejections are not written by the tool's `PHIAccessAudit` function. Define whether the governance requirement is to audit all PHI-access attempts end-to-end, then implement a single consistent audit boundary without double-counting.
8. No tests were executed during this source audit. Test presence is not evidence that these tests pass on current HEAD or that the behavior is active in a deployed environment.

Required regression/evidence:

- Derive the effective role/permissions from the authenticated user's active pharmacy membership and resolve an explicit clinical permission at tool execution; retain tenant and patient ownership checks as independent predicates.
- Add registry-dispatch tests proving denied MCP patient-history calls are audited, allowed calls are audited before data release, and audit persistence failure blocks release. Include PostgreSQL-backed integration tests for allowed, denied, rollback and commit-failure paths.
- Make tool discovery pharmacy-context-aware for presentation, but re-evaluate the same effective permission at dispatch. Add parity tests for discovery versus execution, including platform admin denial absent a separately approved support grant.
- Add tests for cashier, pharmacist, manager and pharmacy-admin memberships across two pharmacies, role revocation, cross-patient and cross-pharmacy access, missing/invalid purpose, and concurrent request context isolation.
- Define and test a purpose-specific minimum-necessary response schema; verify PHI audit records and logs contain no clinical payload.
- Keep support/operator access separate from pharmacy clinical permissions. A platform superuser or generic MCP `admin` role must not imply patient-history access.

### 4.11 MCP registry inventory, prescription PHI scope, and verification-result integrity

Files reviewed on `main`: `src/pharmaviyum/ai/mcp/tools/__init__.py`, `registry.py`, `tool_management.py`, `context.py`, `schemas.py`, `tools/patient_history.py`, `tools/prescription_verification.py`, `tools/drug_interactions.py`, `tools/halal_compliance.py`, `tools/pharmacy_operations.py`, `server.py`, `tests/security/test_mcp_rbac.py`, `tests/security/test_mcp_patient_history_scope.py`, `tests/unit/ai/test_pharmacy_operations_mcp.py`.

Registered tool inventory on the reviewed source:

| Tool | Declared role policy | Scope / data boundary observed |
|---|---|---|
| `get_patient_history` | Explicit `pharmacist` | Patient PHI; exact selected-patient + purpose + same-pharmacy ownership + function-level PHI audit |
| `verify_prescription` | Registry default: `pharmacist`, `admin`, `system` | Prescription lookup by caller-supplied number; same-pharmacy active patient filter, but no selected-patient/purpose binding or PHI audit |
| `check_drug_interactions` | Registry default | Drug names supplied as input; inspected implementation uses static interaction data and does not query patient records. Its optional `patient_id` input is not used by the function |
| `check_halal_compliance` | Registry default | Product/compliance lookup; no patient-record query identified |
| `search_pharmacy_products` | Registry default | Active product catalogue and stock; inventory join is constrained by trusted pharmacy ID |
| `get_inventory_overview` | Registry default | Inventory lots constrained by trusted pharmacy ID |
| `get_expiring_inventory` | Registry default | Expiring/expired inventory constrained by trusted pharmacy ID |
| `get_sales_summary` | Registry default | Aggregate sale totals/status counts constrained by trusted pharmacy ID |
| `get_pharmacy_workflow_guide` | Registry default | Static workflow guidance; no patient or pharmacy record query |

All nine registered tools declare `execution_class="read"`. The five pharmacy-operations tools have unit coverage for registration, schemas and read-only classification. Those tests do not constitute database-backed cross-pharmacy isolation evidence. The registry requires a trusted MCP context and compares the supplied user, pharmacy and role with it before dispatch; the MCP server's data methods also require that context. The reviewed repository still has no production HTTP/network route invoking `mcp_server.handle_request`; do not describe the internal server object as an exposed public MCP transport.

Confirmed authorization and data-boundary findings:

1. **Prescription verification is a separate patient-linked PHI read path.** `verify_prescription` accepts a prescription number, loads the matching prescription joined to an active patient in the trusted pharmacy, and returns the patient's name with prescription verification details. It does not compare that patient's ID with `MCPAuthorizationContext.selected_patient_id`, require a controlled `purpose`, or write `PHIAccessAudit`. A pharmacy-scoped caller who knows another active patient's prescription number can therefore query that prescription through this tool even when another patient is selected in the AI context. This is a source-level same-pharmacy patient-scope gap; cross-pharmacy lookup remains constrained by the pharmacy predicate.
2. **The prescription tool's caller-supplied `pharmacist_id` is not an authorization check.** It is part of `PrescriptionVerifyRequest`, but the inspected function does not use it to establish actor identity or permission. Any future use must derive actor identity from trusted context, never trust this input as proof of the pharmacist.
3. **The verification result can report a false positive when checks are omitted.** `PrescriptionVerifyRequest.checks` is a list without a minimum-length constraint. The function computes `is_valid = all(c.passed for c in checks)`; when the caller supplies an empty list, Python's `all([])` is true and the result can be `is_valid=True` with no checks performed. The request schema also allows `drug_availability` and `interactions`, but the inspected function does not implement those branches. The default path creates an empty prescription-item list pending a normalized prescription-line model, so quantity-limit checks currently iterate over no items. The pharmacy jurisdiction is hard-coded to unknown and expiry/quantity checks fail closed when requested, but caller-selectable checks can still produce an incomplete or misleading validity result. This tool must remain advisory and must never authorize dispensing.
4. **Default role policy is broad and implicit.** Every tool that omits `required_roles` inherits `[pharmacist, admin, system]`. Combined with global `User.role` resolution, every ordinary account reaches the legacy pharmacist category, while platform admin/system are generic bypass roles. There is no pharmacy-specific permission check for inventory, sales summary, prescription verification or product search. Tenant filtering protects the data partition but does not provide action-level authorization.
5. **Operational tools have positive tenant predicates but no action-level permission model.** The four DB-backed operational queries reviewed derive pharmacy scope from trusted context and do not accept caller-supplied user/pharmacy/role fields. They expose product/stock/lot/expiry and aggregate sales information. This is a positive tenant boundary, not proof that every pharmacy member should see all lot, expiry, stock or revenue details.
6. **Drug interaction patient selector is misleading.** `DrugInteractionCheck.patient_id` is optional but unused by the implementation; no patient-record lookup was identified. Do not treat passing that ID as patient-specific checking or as an authorization check. Either remove it from the generic tool contract or bind any future patient-specific workflow to trusted selected-patient/purpose and explicit PHI controls.
7. **Tests do not close these gaps.** `tests/security/test_mcp_rbac.py` verifies role-filtered discovery and a generic unauthorized-role denial, not the complete registered-tool permission matrix or pharmacy membership roles. `tests/unit/ai/test_pharmacy_operations_mcp.py` checks tool registration/schema/read-only metadata and rejects caller-supplied identity fields for four operational schemas, but its own module description and assertions do not establish cross-pharmacy DB isolation. No dedicated prescription-verification test was found by the targeted repository search. Existing broad `tests/test_mcp.py` cases exercise legacy schema/function imports and direct function calls; they do not prove the current patient/purpose/audit contract for prescription verification. No tests were run during this audit.

Required regression/evidence:

- Treat `verify_prescription` as a PHI access operation: require the trusted selected patient to equal the prescription's patient, require an allowed purpose, enforce an explicit clinical permission at execution, and commit metadata-only PHI audit before returning patient-linked data. Audit denials and fail closed if audit persistence fails.
- Do not allow the model to select a prescription outside the trusted selected patient. Prefer a server-resolved prescription identifier constrained by both patient and pharmacy, or require a compound query predicate containing the trusted patient ID.
- Make verification checks server-defined and mandatory for the intended workflow. Reject an empty check list; do not let the caller omit mandatory checks. Distinguish `not_verified`, `invalid`, and `verified` rather than interpreting an empty set of checks as valid. Do not return a positive dispensing signal while jurisdiction, product lines, quantity limits, drug availability or duplicate-dispensing evidence is incomplete.
- Add prescription tool tests for another patient in the same pharmacy, another pharmacy, no selected patient, missing purpose, missing clinical permission, audit commit failure, empty checks, partial checks, missing jurisdiction and incomplete prescription lines. Include PostgreSQL-backed tests for PHI audit persistence.
- Replace default broad roles with explicit least-privilege policy for every tool. Resolve effective pharmacy permissions from the active membership; keep platform support/operator access separate from pharmacy roles. Apply action permissions to stock/lot/revenue reads as well as writes.
- Add database-backed cross-pharmacy decoy-record tests for each operational tool. Keep the existing schema tests as contract tests only.
- Remove or clearly deprecate unused patient identity fields in generic tools; any patient-specific extension must inherit the same trusted patient, purpose, permission and audit boundary.

### 4.12 MCP Client, Agent Harness, prompt-injection boundary, and execution budget

Files reviewed on `main`: `src/pharmaviyum/ai/mcp/client.py`, `registry.py`, `server.py`, `context.py`, `src/pharmaviyum/ai/agents/pharmacist_agent.py`, `src/pharmaviyum/ai/agents/state.py`, `src/pharmaviyum/ai/harness/agent_harness.py`, `src/pharmaviyum/ai/harness/guardrails.py`, `src/pharmaviyum/ai/harness/tool_calling.py`, `src/pharmaviyum/ai/mcp/resources.py`, `src/pharmaviyum/ai/mcp/prompts.py`, `tests/security/test_mcp_rbac.py`, `tests/unit/test_contextual_compression_security.py`, `tests/unit/test_tool_calling_privacy.py`, `tests/test_harness.py`.

Verified positive controls:

- `MCPClient.call_tool` requires the request-scoped `MCPAuthorizationContext`; caller-supplied user, pharmacy or role values are only consistency assertions and are rejected when they differ from the trusted context. The effective identity/tenant/role passed to the registry is copied from that context.
- `MCPToolRegistry.call_tool` independently requires the same context and checks user, pharmacy and role equality, registered tool existence, role policy, dependency health and Pydantic input validation before function execution. Validation errors are replaced with a generic message to avoid echoing clinical input values.
- Tool discovery through `MCPClient.to_openai_tools` and `MCPServer tools/list` is role-filtered. The planner receives the list derived from the active request context; this is a discoverability control, not the authorization boundary.
- The LangGraph executor calls `MCPClient.call_tool` for each model-generated call. The model-generated tool arguments do not set trusted user or pharmacy identity. Registry authorization is repeated at dispatch, so a tool omitted from discovery is still denied if directly requested by the model.
- The registry fails closed for `execution_class="write"`: a write requires a configured trusted approval verifier and pharmacist confirmation; otherwise it is denied. All nine currently registered tools are read-class.
- MCP JSON-RPC initialization is public, but the server requires trusted context for tool/resource/prompt data capabilities. The repository search found no production HTTP/network route calling `mcp_server.handle_request`; treat this server as an internal implementation until a real transport adapter is identified.
- The RAG contextual-compression tests verify escaping of retrieved content and delimiters. The main planner prompt explicitly says retrieved/tool content is untrusted and must not be followed as instructions. The user-input guardrail has heuristic prompt-injection detection tests.

Remaining gaps / qualifications:

1. **Authorization still resolves to legacy global role.** The Client and Registry correctly trust the context, but that context currently carries the global `User.role` value, not a pharmacy-membership role/permission. Therefore the strong context-binding mechanism does not fix the previously documented cashier-versus-pharmacist clinical authorization gap.
2. **Prompt injection detection is not a security boundary.** `MedicalGuardrails.pre_process` uses regular-expression heuristics on the user query only. It cannot reliably detect indirect injection in stored product descriptions, external data, RAG chunks or tool results. Those data are labelled untrusted in the planner system prompt, but the model is still the enforcement mechanism for that instruction. The existing retrieved-RAG escaping tests do not test malicious MCP tool output flowing through `ToolMessage`.
3. **Tool output is passed to the planner as raw JSON text.** `executor_node` serializes successful tool data into a `ToolMessage`; database fields can themselves contain attacker-controlled text. The system prompt says to treat tool content as untrusted, but there is no deterministic output envelope/taint marker or sanitization boundary for model consumption. This is a residual indirect prompt-injection risk, not a demonstrated authorization bypass.
4. **The medical reviewer receives interpolated untrusted content without an explicit trust boundary.** `reviewer_node` concatenates the user question, draft, tool results and RAG sources into a plain-text `review_prompt`. Its system message only says it is a strict reviewer; unlike the planner prompt, it does not explicitly classify each interpolated section as untrusted data or instruct it to ignore embedded instructions. A malicious tool/RAG payload could attempt to influence the reviewer decision. Add structured, separately delimited fields and explicit untrusted-data instructions, then test indirect injection at the reviewer boundary.
5. **Tool-call execution budget is not a single strict request budget.** `PharmacistAgent.MAX_ITERATIONS=5` limits planner iterations, while `executor_node` processes up to 10 calls per iteration. This permits up to 50 tool dispatches in one graph run (before considering MCP Client retries); calls beyond the first 10 in a batch are silently ignored. Each read tool may also be attempted up to four times by the MCP Client after timeouts/transient errors (`max_retries=3`). There is no explicit shared per-request tool-call/retry/time/token budget or rate limit in the reviewed path. This is primarily cost/availability and audit-volume exposure; it does not itself bypass RBAC.
6. **Timeout retries need idempotency/cancellation evidence.** The MCP Client retries read-class calls after timeout and generic exceptions. This is safer than replaying writes, which are not retried, but no reviewed test proves cancellation of a timed-out database operation before the next attempt. A slow/non-cancellation-safe read could overlap retries and amplify load.
7. **The separate `ToolCallingLayer` is not the live Agent path reviewed.** `PharmacistAgent.executor_node` calls `MCPClient` directly; the targeted repository search found tests instantiating `ToolCallingLayer`, but no production construction/use in this agent path. Its fallback/retry/schema-validation claims must not be mistaken for controls active in the LangGraph executor. Its default fallback chains are empty in any case.
8. **MCP prompt/resource registries are not equivalent to tool authorization.** Their methods require a trusted context at the JSON-RPC server boundary, but prompt/resource reads have no per-item pharmacy permission or patient-purpose policy. The current resources are static country-regulation and halal-standard data; prompts accept caller-provided drug/patient attributes and interpolate them into prompt text. No patient database lookup was found in these handlers. The generic resource template matcher only substitutes `{id}`, while current templates use `{country}` and `{body}`; the server also calls `read_resource(uri)` without extracted template kwargs, so those dynamic resource reads appear nonfunctional as implemented. No production transport caller was identified.
9. **Error handling has both positive and negative details.** The MCP Client generally returns generic errors and the server suppresses exception details. However, `executor_node` places `result.error` into a ToolMessage for the model, and tool-result records retain the error. Current MCP Client errors are mostly generic, but future exception text must never contain PHI, SQL or credentials. The agent's top-level exception result includes `str(exc)`; the outer AgentHarness currently converts agent failure to a generic harness failure before the API response, but this should remain covered by privacy regression tests.
10. **Test coverage is partial.** `tests/security/test_mcp_rbac.py` checks missing context and a generic role denial. `tests/test_harness.py` tests regex-based user prompt injection. `tests/unit/test_contextual_compression_security.py` tests RAG delimiter escaping. `tests/unit/test_tool_calling_privacy.py` tests redaction of an exception in the separate ToolCallingLayer. No reviewed test exercises an adversarial MCP tool result through planner and reviewer, aggregate per-request call limits, retries after cancellation, or concurrent request context isolation across actual LangGraph tool dispatch. No tests were run during this audit.

Required regression/evidence:

- Keep trusted identity and tenant scope exclusively in request context; add tests that forged identity fields in tool arguments and forged optional Client arguments cannot alter the authenticated actor or pharmacy.
- Enforce pharmacy-specific permissions at Registry dispatch, independently for each tool; tool discovery must remain presentation-only and cannot grant permission.
- Treat all tool/RAG/resource outputs as untrusted data. Use a typed, bounded envelope with explicit provenance and escaped/delimited content for both planner and reviewer; add indirect prompt-injection tests using malicious product names/descriptions, prescription fields, RAG chunks and tool errors.
- Give the safety reviewer an explicit system-level untrusted-data policy and structured fields; test that instructions embedded in question, draft, tool output and retrieved evidence cannot change its review criteria or override safety rejection.
- Introduce a strict shared per-request execution budget: maximum total tool calls, maximum calls per tool, maximum retries, wall-clock budget and concurrency limit. Reject or explicitly report truncated tool-call batches; do not silently discard model calls.
- Add cancellation-aware timeout tests and ensure a timed-out read is stopped before retry; apply bounded backoff and per-user/per-pharmacy rate limits.
- Add end-to-end tests proving unauthorized direct tool requests are denied even when omitted from model discovery; include context spoofing, patient A/B, pharmacy A/B, role revocation, indirect prompt injection and audit behavior.
- Either integrate `ToolCallingLayer` intentionally with the production agent or mark/remove its unused orchestration path; tests for an unused layer are not evidence of live-path behavior.
- Keep MCP prompt/resource access limited to approved static knowledge unless a separate explicit permission model is added. Fix URI-template parameter extraction before treating dynamic resource support as implemented.
- Preserve generic client-facing errors and ensure no PHI-bearing exception, input or tool output is written to logs, spans, analytics or error responses.

### 4.13 RAG-to-Agent end-to-end scope, Redis memory, checkpoints, cache, and PHI audit

Files reviewed on `main`: `src/pharmaviyum/api/v1/ai.py`, `src/pharmaviyum/ai/agents/pharmacist_agent.py`, `src/pharmaviyum/ai/agents/checkpointer.py`, `src/pharmaviyum/ai/mortarium_rag/graph.py`, `src/pharmaviyum/ai/mortarium_rag/vector_store.py`, `src/pharmaviyum/ai/mortarium_rag/schemas.py`, `src/pharmaviyum/ai/harness/agent_harness.py`, `src/pharmaviyum/ai/harness/cache.py`, `src/pharmaviyum/ai/harness/memory.py`, `tests/security/test_rag_tenant_isolation.py`, `tests/security/test_prompt_cache_isolation.py`, `tests/integration/test_ai_patient_session_isolation.py`, `docs/ai/patient-session-isolation.md`.

Verified positive controls:

- Both AI API modes validate the pharmacy tenant and selected active patient before invoking the Harness. Patient ID and controlled purpose must be supplied together; the patient is checked against the authenticated pharmacy.
- The API session namespace is HMAC-derived from pharmacy, authenticated user, patient (including explicit no-patient scope), purpose and client session ID. Sync and streaming use the same derivation. The purpose is therefore transitively included in the downstream Agent/RAG checkpoint namespace when the production call passes this scoped session ID as `thread_id`.
- `PharmacistAgent.knowledge_retrieval_node` builds `QueryContext` from the authenticated request context, including pharmacy and selected patient. RAG filter sets include public and pharmacy scopes under the current pharmacy and add patient scope only for the exact selected patient.
- `PgVectorStore` rejects retrieval without a positive pharmacy ID and explicit `public|pharmacy|patient` access level. Patient retrieval requires a positive exact patient ID; a patient ID with a non-patient access level is rejected. Vector and BM25 search use the same validated filter set in hybrid retrieval.
- `LangGraphRAG` requires an explicit checkpointer, validates a positive bounded thread identifier, derives a versioned HMAC thread key from pharmacy/user/patient/session scope and fails closed in staging/production when `SECRET_KEY` is absent.
- `PharmacistAgent._thread_id` similarly binds pharmacy, authenticated user, patient and session to an opaque HMAC checkpoint key. The agent and RAG use distinct namespace prefixes.
- `DialogueMemory` derives Redis key prefixes from the API-scoped session ID using HMAC. Short-term messages, summary, archive and episodic facts share that session prefix and configured seven-day TTL. Stored memory is explicitly labelled as untrusted historical/user-provided context; summarization prompts also label prior summary and turns as untrusted.
- `PromptCache` requires authenticated user and positive pharmacy ID. Exact cache identity includes the full allowlisted request context; the Harness also adds the scoped session ID and a memory fingerprint. Semantic cache reuse is explicitly opt-in and rejects patient- or prescription-specific context.
- Existing tests cover retrieval tenant filters and exact patient filter construction; cache key separation by user/pharmacy and formulary version; semantic-cache exclusions; API sync/stream scope separation across patient A, patient B, different purpose and no-patient; Redis memory-tier separation using a real Redis fixture; and PostgreSQL checkpoint persistence/separation using synthetic LangGraph state.
- `AgentCheckpointer` verifies the expected PostgreSQL checkpoint tables, schema version and indexes at initialization. It does not create/migrate the schema at runtime.

Remaining gaps / qualifications:

1. **RAG has no explicit purpose field in its QueryContext.** The API validates purpose and binds it into the opaque session ID, so the current API-to-Agent-to-RAG checkpoint namespace is purpose-separated. However, `PharmacistAgent.knowledge_retrieval_node` does not pass purpose into `QueryContext`, and `LangGraphRAG._build_filters` has no purpose-specific authorization. The RAG retrieval operation therefore cannot independently enforce or audit why patient-specific evidence is being accessed. Preserve purpose as trusted server context through retrieval and enforce an explicit allowed-purpose policy for patient-level retrieval.
2. **RAG patient retrieval has no demonstrated PHI access audit.** The inspected retrieval graph records operational metrics/stage telemetry, but no `PHIAccessAudit` allowed/denied event is written for patient-level RAG reads. The dedicated MCP patient-history audit path does not automatically cover pgvector/BM25 patient-chunk retrieval. Add metadata-only, durable audit records before patient evidence is returned, including denied decisions and fail-closed behavior if audit persistence fails.
3. **Exact cache can return previously authorized tool/RAG results without re-running the agent.** `AgentHarness.run` and streaming cache lookup occur before model routing and Agent/Registry dispatch. Current API tenant membership checks still run, and current role model is global/legacy; however, when pharmacy-specific permissions and role revocation are introduced, a cache hit could bypass the current tool-level permission check unless the cache key includes a server-derived policy/permission version and the request revalidates authorization before returning cached results. `role` and `permissions_version` are allowlisted by cache code, but the current API context does not populate them. This is a future RBAC integration gap, not evidence of a current cross-user cache collision.
4. **Cache stores potentially sensitive response payloads.** Exact cache responses include answer, tool results and RAG sources, with a default one-hour TTL. Patient-specific exact caching is not disabled; it is instead scoped to the user, pharmacy, patient/purpose-derived session and memory fingerprint. This prevents the obvious cross-session key collision but means PHI may persist in Redis. The source review cannot establish Redis TLS, ACLs, encryption at rest, backup protection or operational retention. These controls and a documented PHI cache policy are required before production use. Semantic cache is conservatively disabled for patient/prescription context; through the current Harness allowlist, `semantic_cache_safe` is not forwarded, so semantic opt-in is not currently reachable through this path.
5. **Cache freshness is not bound to live source versions in the API context.** The cache supports `formulary_version`, `inventory_version`, `catalog_version` and `permissions_version`, but the reviewed API context only supplies user, pharmacy, patient, purpose, country, language, halal flag and force-fresh. Thus these version dimensions are not populated by the current API route. Exact entries can remain for one hour even when underlying inventory/catalog/permission data changes, unless the caller sets `force_fresh` or cache is disabled. Define server-owned version/freshness invalidation for volatile inventory, prescription and permission-sensitive answers.
6. **Redis HMAC namespaces pseudonymize keys; they do not encrypt payloads.** Memory stores raw user and assistant messages; summary/archive/episodic tiers may also contain clinical details. The HMAC-derived key prevents raw identifiers appearing in Redis key names but does not protect values from Redis operators, backups, compromised credentials or unauthorized Redis clients. Seven-day TTL is a code default, not proof that all deployment Redis keys/backups are purged on schedule.
7. **Checkpoint HMAC scope is application-level isolation, not database row-level authorization.** The shared PostgreSQL checkpointer stores opaque thread IDs and checkpoint payloads in the LangGraph checkpoint tables. The inspected checkpointer verifies schema/tables/indexes, but no checkpoint-table RLS policy or per-tenant database-role enforcement was established in this review. Anyone with broad database read access could potentially inspect checkpoint payloads across tenants even without knowing their raw IDs. Verify actual DB grants, RLS, backup access and runtime-vs-migration roles; do not treat HMAC thread IDs as encryption or DB-level tenant isolation.
8. **Purpose separation for direct RAG callers is weaker than the API path.** `LangGraphRAG._thread_id` itself binds pharmacy, user, patient and the supplied raw thread ID, but does not accept purpose. Production Agent calls pass the purpose-bound API session ID as that raw thread ID, which preserves purpose separation transitively. Direct callers that reuse one thread ID across different purposes could collide unless they derive the same trusted API namespace or RAG receives and binds purpose itself. Keep direct construction restricted or make purpose part of the explicit RAG scope.
9. **Checkpoint integration coverage is narrower than full application E2E.** The integration test uses real PostgreSQL checkpointer storage and synthetic LangGraph `MessagesState` to demonstrate different HMAC-derived RAG thread IDs do not share state. It does not execute the complete production `PharmacistAgent` + `LangGraphRAG` graph with MCP calls, patient evidence, role changes, cancellation or multiple app instances. The Redis integration test covers memory tiers, and API tests use a deterministic recording Harness; they do not establish full live graph isolation. These tests were not run during this audit.
10. **Streaming and synchronous cache paths are not identical in response payloads.** Synchronous cache hits return cached tool results and RAG sources; streaming cache hits return answer/warnings/RAG sources and a tool-result count, but not the cached tool-result payloads. This is not a demonstrated isolation flaw, but it can make source/tool provenance differ between sync and stream for the same scoped request. Define one response contract and test parity.
11. **Memory and checkpoints have independent retention/rotation lifecycles.** Changing `SECRET_KEY` changes HMAC-derived namespaces and makes prior state inaccessible through the new keys; it does not delete old Redis entries or PostgreSQL checkpoint rows. Existing session-isolation documentation acknowledges legacy namespace/checkpoint retention. Define coordinated retention, backup deletion, key rotation and old-namespace cleanup before production rollout; no deletion or migration was performed during this audit.
12. **Audit and telemetry are not a unified PHI access trail.** RAG telemetry records counts, timing and error types, and Agent spans record source/tool counts. These are operational observability, not proof of who accessed which patient evidence for what purpose. Do not add prompts, patient IDs or clinical payloads to telemetry; use a separate metadata-only access audit with request/trace correlation.

Required regression/evidence:

- Carry server-derived patient purpose and permission decision into RAG retrieval; independently deny patient-level retrieval if selected patient, purpose, pharmacy membership or clinical permission is missing or mismatched.
- Add durable allowed/denied PHI audit events for patient-level RAG retrieval and MCP reads; verify transaction commit before returning evidence and fail closed on audit persistence failure.
- Add cache-hit authorization tests: revoke a pharmacy-specific permission while retaining membership and prove a cached prior tool/RAG response is not returned. Include role/permission version, data freshness version and policy version in server-owned cache scope or revalidate the cached result against current policy.
- Add real Redis tests proving cache payloads are isolated across user, pharmacy, patient, purpose and permission-version changes; test exact-cache expiration, invalidation and force-fresh behavior.
- Add PostgreSQL checkpoint access tests under the actual runtime DB role; inspect and document grants/RLS/backup access. Prove one tenant cannot read another tenant's checkpoint payload even when thread IDs are enumerated.
- Exercise the actual Agent and RAG graphs with synthetic patient A → patient B → no-patient → different-purpose requests using the same client session in sync and streaming modes; assert retrieved chunk IDs, tool outputs, memory, checkpoint snapshots and cache results never cross scopes.
- Add cancellation/disconnect tests that verify ContextVar reset, no partial PHI cache write, no cross-request state reuse and bounded cleanup after a cancelled stream.
- Add multi-instance tests using a shared Redis/PostgreSQL backend and a stable HMAC secret, then verify deliberate secret rotation behavior without destructive production operations.
- Define PHI classification, encryption-at-rest/TLS/ACL, TTL, backup retention, deletion and incident-response controls for Redis cache, dialogue memory and PostgreSQL checkpoints. HMAC pseudonymization alone is insufficient.
- Establish one consistent sync/stream response provenance contract and verify cached responses preserve the same source and warning semantics.
- Keep the staged E2E gate open until these tests run against isolated synthetic infrastructure; no production DB, Redis, secret or deployment changes are authorized by this audit.

### 4.14 RAG ingestion provenance, canonical metadata stamping, and database enforcement

Files reviewed on `main`: `src/pharmaviyum/api/v1/ingestion.py`, `src/pharmaviyum/ai/mortarium_rag/ingestion/tasks.py`, `src/pharmaviyum/ai/mortarium_rag/ingestion/orchestrator.py`, `src/pharmaviyum/ai/mortarium_rag/schemas.py`, `src/pharmaviyum/ai/mortarium_rag/chunking.py`, `src/pharmaviyum/ai/mortarium_rag/vector_store.py`, `src/pharmaviyum/ai/mortarium_rag/ingestion/versioning.py`, `src/pharmaviyum/ai/dependencies.py`, `alembic/versions/2026_11_21_000002_pgvector_schema.py`, `tests/unit/ai/test_mortarium_rag_security_contracts.py`.

Verified positive controls:

- The active FastAPI ingestion endpoints require `CurrentSuperuser` and independently call `require_pharmacy_tenant` for the requested pharmacy before dispatching a Celery task. The worker receives the server-resolved pharmacy ID, not a raw model-generated tenant ID.
- Object-storage upload keys are generated with the authorized pharmacy ID; the worker validates the object key against the same pharmacy before downloading the document.
- The active Celery task requires a positive integer pharmacy ID and rejects `access_level="patient"` because that worker path has no patient-level ingestion authorization contract.
- Before chunking, the active task calls `_stamp_tenant_metadata`. The server-derived pharmacy ID, source, version/effective window, access level, country, language and document type override any same-named source-document metadata fields. This is the correct direction for preventing uploaded document metadata from choosing its own tenant.
- `PgVectorStore.upsert` validates every chunk using `CanonicalMetadata` before persistence. Canonical metadata requires a positive strict pharmacy ID and source; patient chunks require a patient ID, and non-patient chunks reject patient IDs. SQL search filters use bound values; metadata filter keys are constrained to safe SQL identifiers.
- The Alembic pgvector migration owns creation of `public.document_chunks`, pgvector indexes and full-text indexes. Runtime `PgVectorStore.initialize` performs schema verification and does not issue DDL.
- Existing unit/security tests cover required pharmacy metadata, patient metadata shape, invalid/missing tenant filters, exact patient filter construction, safe SQL filter identifiers and canonical identifier types.

Remaining gaps / qualifications:

1. **Database tenant isolation is enforced in application SQL, not shown as PostgreSQL RLS.** The reviewed `document_chunks` migration creates a shared table with tenant identity embedded in JSONB metadata and indexes it, but does not enable row-level security or define tenant policies. `PgVectorStore` fails closed when a query omits tenant/access filters, which is positive application enforcement; however, a future direct SQL path or a compromised runtime credential can bypass that helper. No separate RLS migration/policy was found in the inspected migration/search results. Verify actual database policies and grants; do not claim DB-enforced tenant isolation.
2. **The initialized IngestionOrchestrator is a second, materially different ingestion path.** `AIComponents.initialize` constructs `IngestionOrchestrator`, but repository search found no production call site invoking its `ingest_file` or `ingest_batch` methods. Unlike the active Celery task, the orchestrator checks that `config.pharmacy_id` is positive but does not stamp that server-derived value into each loaded document before chunking. It relies on document metadata already containing canonical tenant metadata for `PgVectorStore.upsert` to succeed. Missing metadata fails closed at upsert; if loaded metadata already contains a valid but wrong pharmacy ID, the upsert validation alone does not compare it with `config.pharmacy_id`. Treat this path as unused/untrusted until it is unified with the active stamping boundary or removed.
3. **The worker trusts the authenticated API dispatch and broker boundary.** The Celery worker independently checks the pharmacy ID shape and object-storage tenant key, but it does not independently query the initiating actor's active pharmacy membership or role. This can be an acceptable service-to-service trust model only if the broker is private, task producers are restricted, and task payload integrity is protected. No actor ID, authorization decision ID or immutable initiator record is passed into the worker for later audit.
4. **Patient-level ingestion is intentionally unavailable in the active task.** This is fail-closed and preferable to accepting a patient ID from a file or prompt. A future patient-record ingestion workflow must have a separate server-authorized patient lookup, controlled purpose, explicit clinical permission, source provenance and PHI audit; do not simply enable `access_level="patient"` in the generic worker.
5. **Source metadata is not proof of source trust or clinical validity.** Canonical stamping establishes tenant/access metadata, but it does not validate document issuer, authenticity, jurisdictional authority, effective date correctness, content integrity or clinical review status. Those need separate source registry/approval/version controls before clinical use.
6. **Deduplication and versioning require cross-tenant regression evidence.** The active orchestrator's `DocumentVersionManager` receives pharmacy ID for version operations, but this audit did not establish persisted two-pharmacy isolation for deduplication, archival, rollback or reactivation. The generic worker task does not show the same dedup/version orchestration in the reviewed path. Do not assume the two ingestion implementations have identical lifecycle guarantees.
7. **Ingestion job visibility is platform-superuser scoped, not pharmacy-admin scoped.** `GET /jobs` and `GET /jobs/{job_id}` require `CurrentSuperuser` and do not take a pharmacy filter. This is a platform-operator capability, not a pharmacy membership read. Keep it restricted to platform operations and avoid exposing it as a pharmacy-level admin feature without tenant-scoped job ownership.
8. **Metadata-only test coverage does not establish the entire worker trust chain.** The reviewed unit tests exercise schema/filter contracts; they do not prove that a malicious uploaded document cannot override tenant fields through every loader/preprocessor/chunker combination, or that a task forged outside the API cannot ingest into another pharmacy. No tests were run during this audit.

Required regression/evidence:

- Add integration tests with a malicious document containing forged `pharmacy_id`, `patient_id`, `access_level`, `source`, country and version metadata; prove active Celery stamping overwrites server-controlled fields and patient-level ingestion is rejected.
- Add tests proving invalid, missing and mismatched pharmacy IDs are rejected before object access and before persistence; include forged task payloads from an unauthorized producer in a controlled broker test.
- Unify `IngestionOrchestrator` and Celery worker on one canonical server-side metadata stamping service, or remove/disable the unused orchestrator entry point. Never accept tenant ownership from loaded document metadata.
- Add actual PostgreSQL two-tenant tests under the production-like runtime DB role; inspect `pg_class.relrowsecurity`, `pg_policies`, table grants and direct SELECT behavior. Implement RLS/least-privilege grants if the chosen deployment architecture requires database-enforced isolation.
- Verify every deduplication/version/archive query includes pharmacy scope and cannot update or suppress another tenant's source/document.
- Add source provenance and approval states for clinical documents; unreviewed or jurisdiction-unknown content must not be represented as authoritative clinical evidence.
- Keep patient-level ingestion disabled until patient ownership, purpose, permission, source validation and durable PHI audit are implemented.
- Keep platform-wide ingestion job APIs restricted to platform operators; if pharmacy admins need job visibility, add pharmacy-owned job records and pharmacy-scoped lookup.
- Do not modify database schema, execute migrations or change worker/broker infrastructure as part of this documentation audit.

## 5. Explicit non-actions

This review made no application code changes, route changes, schema changes, migration changes, permission grants, manual SQL, merge, or deployment. The findings must be reviewed against the complete router graph and runtime configuration before implementation.


### 3.2 Runtime router composition differs from the legacy router module

Files: `src/pharmaviyum/main.py`, `src/pharmaviyum/api/v1/__init__.py`, `src/pharmaviyum/api/v1/router.py`

Observed runtime composition:

- `main.py` imports and mounts `api_v1_router` from the `api.v1` package.
- The package-level `api_v1_router` is assembled in `api/v1/__init__.py`.
- That runtime aggregator includes AI, auth, catalog, dashboard, ingestion, monitoring, medical devices, orders, patients, patient purchases, POS, sync, pharmacy entities, products, and users.
- It does not include `prescriptions_router` or `feature_flags_router`.
- The separate `api/v1/router.py` defines another aggregator with a different set of routers, including prescriptions and feature flags, but code search found no import/use of its `api_router` symbol in the reviewed repository.
- The legacy aggregator adds an `/api/v1` prefix while the patients router already declares `/api/v1/patients`; mounting that aggregator as written would produce a duplicated path prefix for patients.

Implications:

- Do not report prescription placeholder endpoints as currently exposed in the deployed application based only on the legacy aggregator. Their source handlers are unauthenticated, but the runtime mount must be verified before treating them as reachable.
- Treat the existence of two divergent router aggregators as an API composition/maintenance risk. There must be one authoritative runtime router tree.
- Before RBAC implementation, generate or test the actual FastAPI route table from the same app factory/entrypoint used in deployment. Record method, path, router, authentication dependency, tenant dependency, and action permission for every mounted business route.
- Add a regression test asserting critical expected routes are mounted exactly once and retired/unmounted routes are absent.
- Resolve the duplicated-prefix issue only as a separately reviewed routing change; do not combine it with RBAC policy implementation without tests.



## 4. Runtime authorization findings by mounted domain

This section reviews the package-level router actually mounted by `src/pharmaviyum/main.py`. It is a source audit, not a substitute for an instantiated FastAPI route-table test.

### 4.1 POS

File: `src/pharmaviyum/api/v1/pos.py`

- The reviewed product search, lot lookup, goods receipt, and checkout handlers accept `CurrentUser` and call `require_pharmacy_tenant` using the requested or payload pharmacy ID.
- This establishes authentication and active membership for ordinary users, but it does not distinguish action permissions such as `pos.read`, `pos.checkout`, or `inventory.receive`.
- The same broad membership gate currently allows any active member to reach these operations unless a separate check exists in the handler/service path. No role/action check was found in the reviewed handlers.
- Tenant checks must remain server-side and must be paired with row-level pharmacy constraints for every resource read or mutated.

### 4.2 Products / Drug Catalog

File: `src/pharmaviyum/api/v1/products.py`

- Product search, list, and detail require an authenticated active user.
- Product create, update, and deactivate require `CurrentSuperuser`.
- These product queries are global catalog queries and do not resolve a selected pharmacy tenant.
- This may be appropriate for a shared reference catalog, but it is not sufficient for pharmacy-specific assortment, pricing, visibility, or catalog-review workflows. Those distinctions must be decided explicitly before mapping permissions.

### 4.3 Patients / PHI

File: `src/pharmaviyum/api/v1/endpoints/patients.py`

- List, statistics, phone lookup, patient detail, and visit recording require an active user and call `resolve_pharmacy_scope`.
- Patient create, update, and delete currently require `get_current_active_superuser`; they are not yet mapped to pharmacist/manager action permissions.
- AI profile access checks active membership and patient ownership in the selected pharmacy, rejects platform superusers through this endpoint, and records allow/deny PHI audit events with a controlled purpose.
- The current endpoint set therefore has a mix of tenant-scoped reads, superuser-only mutations, and a separately governed AI profile path. Do not flatten these into one generic `patients.*` permission.

### 4.4 Orders / legacy purchase workflow

File: `src/pharmaviyum/api/v1/orders.py`

- Order creation and status mutation require `CurrentSuperuser`.
- Order reads require an active user and resolve pharmacy scope, then constrain the order through its owning patient.
- The query helpers only add a pharmacy predicate when a scope is resolved. For ordinary users, `resolve_pharmacy_scope` requires a sole active membership or an explicit authorized pharmacy; this behavior must be preserved.
- This is a legacy order/patient-purchase workflow and should not be confused with the newer POS Sale/Payment domain when defining permission names.

### 4.5 Users

File: `src/pharmaviyum/api/v1/users.py`

- Self avatar read/update/delete require `CurrentUser`.
- Listing, creating, and reading other user accounts require `CurrentSuperuser`.
- There is no pharmacy-scoped membership/role administration API in this router. Do not infer that user creation grants pharmacy membership or a pharmacy role.

### 4.6 Pharmacy domain: inventory, suppliers, prescriptions and related resources

File: `src/pharmaviyum/api/v1/pharmacy_entities.py`

- This router exposes multiple pharmacy-domain resources under one router, including pharmacy, supplier, inventory, batch, prescription, and ERP integration operations.
- The reviewed inventory adjustment and inventory deletion handlers require `CurrentSuperuser`, and adjustment loads the inventory row by ID before applying the movement.
- Other handlers in this module must be audited individually for their exact dependency and whether the target row is constrained to the caller's authorized pharmacy. A router-level tag or the presence of a `pharmacy_id` field is not proof of tenant isolation.
- The permission map must be endpoint/action-specific and include object-level tenant checks; avoid assigning one broad permission to the entire router.

### 4.7 Current tenant helper limitation

File: `src/pharmaviyum/modules/auth/tenant.py`

- `require_pharmacy_tenant` treats `is_superuser` as a bypass for any requested pharmacy ID.
- `resolve_pharmacy_scope` allows a superuser to remain global when no pharmacy ID is supplied.
- This is a tenant-scope decision, not an action permission. Platform/support access must be designed separately from pharmacy business roles, with purpose-bound and audited access for PHI.

## 5. Router composition clarification

The package-level `api_v1_router` is the router mounted directly by `main.py`; it includes the patient router and several domain routers. It does not include `prescriptions_router` or `feature_flags_router` from the endpoints package. The separate `api/v1/router.py` aggregator is not the runtime router imported by `main.py`.

The top-level helper in `src/pharmaviyum/api/__init__.py` would add an additional `/api/v1` prefix, but `main.py` does not call that helper in the reviewed entrypoint. Therefore do not describe the legacy aggregator's possible duplicate-prefix behavior as a current runtime defect. The confirmed concern is divergent, unused router composition that can mislead route audits and future maintenance.

Before implementation, add a route-table test against the deployment app entrypoint and assert each expected method/path is registered exactly once, with an explicit expected set for intentionally unmounted routers.


## 6. Detailed mounted pharmacy-domain and POS authorization matrix

Source baseline: `main` at the time of this review. "Authenticated" means the dependency resolves an active authenticated account; "tenant" means an explicit pharmacy membership check or query-level membership constraint. No action-specific pharmacy role permission registry was found in these handlers.

| Method and path | Current dependency / scope | Current effective access | RBAC design target (provisional) |
|---|---|---|---|
| GET `/api/v1/pharmacies` | `CurrentUser`; membership join for non-superuser | Own active memberships; superuser sees all | `pharmacies.read`; platform-wide scope separately governed |
| POST `/api/v1/pharmacies` | `CurrentSuperuser` | Platform superuser only | Platform provisioning capability, not Pharmacy Admin by default |
| GET/POST `/api/v1/suppliers` | `CurrentSuperuser` | Global supplier list/create | Decide global supplier directory vs pharmacy-scoped suppliers; do not silently grant all members |
| GET `/api/v1/inventory` | `CurrentUser`; non-superuser query constrained to all active membership pharmacy IDs | Authenticated users can read inventory across all their active memberships; optional pharmacy filter narrows result | `inventory.read` plus selected/authorized pharmacy context; enforce object scope |
| POST `/api/v1/inventory` | `CurrentSuperuser` | Platform superuser only; creates zero-balance lot | Likely inventory/catalog administration action, subject to explicit role decision |
| PATCH `/api/v1/inventory/{id}` | `CurrentSuperuser`; row loaded by ID | Platform superuser only | `inventory.lot.update`; pharmacy ownership check in same query |
| POST `/api/v1/inventory/{id}/adjustments` | `CurrentSuperuser`; row loaded by ID | Platform superuser only | `inventory.adjust`; reason, idempotency, audit and tenant scope remain mandatory |
| DELETE `/api/v1/inventory/{id}` | `CurrentSuperuser`; row loaded by ID | Platform superuser only | `inventory.lot.delete`; zero balance/no movement safeguards remain |
| GET `/api/v1/batches` | `CurrentSuperuser`; global `ProductBatch` query | Platform superuser only; source comment says model has no pharmacy_id and fails closed | Keep denied to pharmacy roles until batch ownership/tenant model exists |
| GET/POST `/api/v1/prescriptions` | `CurrentSuperuser`; global query/create | Platform superuser only | Clinical permission + patient/pharmacy ownership + purpose-bound PHI audit; no global pharmacy-role access |
| GET/POST `/api/v1/erp/integrations` | `CurrentSuperuser` | Platform superuser only | Platform integration administration unless a pharmacy-scoped integration model is introduced |
| POST `/api/v1/erp/integrations/{id}/events` | `CurrentSuperuser`; integration loaded by ID | Platform superuser only | Integration-specific service identity / platform capability; audit and tenant binding |
| GET `/api/v1/sync-events`, GET `/api/v1/erp/integrations/{id}/events` | `CurrentSuperuser`; global event queries | Platform superuser only | Platform operations permission; tenant and sensitive-payload review |
| GET `/api/v1/pos/products/search` | `CurrentUser` + `require_pharmacy_tenant(pharmacy_id)` | Any active member of requested pharmacy | `pos.read` / catalog lookup permission |
| POST `/api/v1/pos/inventory/receive` | `CurrentUser` + tenant check for payload pharmacy | Any active member of requested pharmacy can invoke receipt | `inventory.receive` |
| GET `/api/v1/pos/products/{id}/lots` | `CurrentUser` + tenant check | Any active member of requested pharmacy | `inventory.read` |
| POST `/api/v1/pos/checkout` | `CurrentUser` + tenant check | Any active member of requested pharmacy can checkout | `pos.checkout`; discount/refund/cancel permissions separately |
| POST `/api/v1/pos/payments/webhook` | HMAC-SHA256 shared-secret signature; no user session | External signed payment adapter | Keep machine-to-machine auth; add provider identity, replay/idempotency and audit controls |
| POST `/api/v1/pos/sales/{id}/cancel` | `CurrentUser` + sale pharmacy tenant check | Any active member of sale pharmacy can cancel pending-payment sale | `pos.sale.cancel` distinct from checkout |
| GET `/api/v1/pos/sales/{id}` | `CurrentUser` + sale pharmacy tenant check | Any active member of sale pharmacy can read sale | `pos.sale.read` |

### 6.1 Confirmed design gaps / constraints

1. **Membership is not a role.** POS operations currently accept any active pharmacy member; there is no cashier/pharmacist/manager distinction at these handler boundaries.
2. **Inventory read is multi-membership scoped, not selected-context scoped.** The query restricts results to all active pharmacy memberships. Decide whether cross-membership aggregation is allowed; otherwise require selected pharmacy context.
3. **Inventory mutation handlers use global superuser dependencies.** They load rows by ID after authentication, without a pharmacy-role action check or explicit tenant predicate. Replacing superuser with a pharmacy role must add pharmacy ownership filtering in the query itself.
4. **Prescription endpoints do exist at runtime.** The mounted `pharmacy_entities.py` exposes GET/POST `/api/v1/prescriptions` behind `CurrentSuperuser`. The separate `endpoints/prescriptions.py` placeholder router is not included in the runtime aggregator. These must not be conflated.
5. **Prescription ownership is not established by the handler.** The create payload accepts `patient_id`, but the handler does not validate that patient belongs to an authorized pharmacy before creating the prescription. Superuser-only access limits callers but does not establish data integrity or pharmacy ownership.
6. **Supplier and ERP data are global in this model.** Do not map them to pharmacy roles until ownership semantics are defined.
7. **Webhook auth is not user RBAC.** HMAC signature validation is a separate machine identity boundary and should remain independent of interactive user roles.

### 6.2 Role mapping remains deliberately unapproved

The target permissions above are action candidates, not approved grants. Do not infer a final role matrix from endpoint names or existing superuser access. The four proposed pharmacy roles remain a proposal until the user explicitly approves the role and clinical-access decisions.


## 7. Drug Catalog, Patient Purchases, Dashboard, Medical Devices and AI

Source baseline: mounted runtime routers on `main`. All endpoints below are present in the package-level runtime aggregator reviewed for this audit.

| Method and path | Current dependency / scope | Current effective access | RBAC design target (provisional) |
|---|---|---|---|
| GET `/api/v1/drug-catalog/search` | `CurrentUser`; shared reference catalog query | Any active authenticated user; no pharmacy scope | `catalog.read`; shared reference-data access may be global by design |
| POST `/api/v1/drug-catalog/sources` | `CurrentSuperuser` | Platform superuser only | `catalog.source.create` or platform ingestion identity |
| GET `/api/v1/drug-catalog/sources` | `CurrentSuperuser` | Platform superuser only; global staged source records | `catalog.source.review.read` |
| GET `/api/v1/drug-catalog/sources/{id}/matches` | `CurrentSuperuser`; source row loaded by ID | Platform superuser only | `catalog.source.match` |
| PATCH `/api/v1/drug-catalog/sources/{id}/review` | `CurrentSuperuser`; row locked by ID | Platform superuser only; can approve/reject and create shared reference records | `catalog.source.review`; approval audit and separation of duties decision |
| GET `/api/v1/patient-purchases/` | `CurrentSuperuser`; purchase joined to patient and filtered by required pharmacy_id | Platform superuser only; requested pharmacy ID is not membership-authorized because caller is platform superuser | Separate platform support capability; purpose-bound PHI access and audit |
| GET `/api/v1/patient-purchases/{patient_id}/history` | `CurrentUser`; explicit active membership, active patient owned by pharmacy, required purpose; platform superuser explicitly denied | Any non-superuser active member of that pharmacy can read minimum-field purchase history; allowed/denied PHI audit rows are added to session | `patients.purchase_history.read` plus explicit clinical role and purpose policy |
| GET `/api/v1/dashboard/summary` | `CurrentUser` + `resolve_pharmacy_scope`; one active membership required unless explicit authorized pharmacy, superuser may remain global | Any active pharmacy member receives operational KPIs **and patient-level names, purchase aggregates and medication history**; no purpose parameter or PHI audit in this handler | Split operational dashboard permissions from patient-level dashboard/PHI permissions; default patient-level panels denied unless explicitly authorized |
| GET `/api/v1/medical-devices/search` | `CurrentUser`; shared reference catalog query | Any active authenticated user; no pharmacy scope | `medical_devices.reference.read`; shared reference-data access may be global by design |
| GET `/api/v1/ai/context` | `CurrentUser`; active pharmacy membership list (or all active pharmacies for superuser) | Any active user can enumerate their pharmacy IDs; non-superuser response substitutes names with `Pharmacy #id` | `ai.context.read`; return only authorized memberships and selected context |
| POST `/api/v1/ai/query` and POST `/api/v1/ai/query/stream` | `CurrentUser` + pharmacy tenant check; optional patient must be active and owned by same pharmacy; patient and purpose required together | Any active member of pharmacy can invoke AI; selected-patient context permits three controlled purpose strings. MCP context binds user, pharmacy, patient and purpose; session ID is HMAC-scoped to user/tenant/patient/purpose | Separate `ai.query` from `patients.phi.read`; enforce clinical role + purpose + patient ownership before MCP tool access |
| GET `/api/v1/ai/tools` | `CurrentUser`; tool list filtered by `current_user.role` | Role-filtered MCP tool discovery; current account role is not a pharmacy membership role, so it cannot distinguish cashier/pharmacist/manager | Tool discovery and execution must use effective pharmacy permissions, not legacy account-role labels |

### 7.1 Critical PHI finding: dashboard response is not minimal

The dashboard handler's query scoping is pharmacy-aware for non-superusers: `resolve_pharmacy_scope` selects an explicit authorized pharmacy or requires exactly one active membership. However, the response is not limited to aggregate metrics. It also returns:
- patient IDs and full names;
- each patient's purchase totals;
- patient medication rows, product names, dosage, form, quantity, prescription-required flag and expiry information;
- latest patient condition.

The endpoint accepts only `CurrentUser`, does not require a controlled access purpose, and does not write a PHI access audit record. Consequently, every active member of a pharmacy who can call the dashboard endpoint currently receives patient-level data, regardless of whether their job requires clinical access. This is a confirmed authorization/data-minimization gap, not merely a proposed design preference.

**Recommended boundary:** keep operational KPIs available under a dashboard permission, but remove patient-identifiable and patient-medication panels from the general summary response. Expose patient-level panels through a separate endpoint protected by a clinical permission, patient/pharmacy ownership, controlled purpose, and PHI audit.

### 7.2 Patient purchase history is better scoped, but role enforcement is incomplete

The dedicated patient history endpoint:
- rejects platform superusers and records a denied PHI audit event;
- requires active membership in the requested pharmacy;
- verifies the patient is active and belongs to that pharmacy;
- requires one of three declared purposes;
- limits date ranges to at most 365 days and returns a minimum set of purchase fields;
- adds an allowed PHI audit event after the read.

However, it does not check a granular pharmacy role or effective permission. Any non-superuser member can currently access the history route if they provide a permitted purpose string. A purpose supplied by the caller is not itself proof of professional authorization.

The legacy administrative list is separately superuser-only and filters purchases through the patient's pharmacy ID. It is not the same as the pharmacist history endpoint.

### 7.3 AI/MCP authorization boundary

The AI query routes correctly bind requests to an authorized pharmacy and, when a patient is selected, verify that patient is active and belongs to that pharmacy. The conversation namespace is HMAC-scoped to user, pharmacy, patient, purpose and supplied session ID. MCP context carries those same authorization dimensions.

The remaining RBAC limitation is upstream role resolution: `User.role` is a computed account-level property returning `admin` for every platform superuser and `pharmacist` for every other user. It is not a role assigned to a particular pharmacy membership. Consequently, every ordinary active account is presented to the AI tools endpoint and MCP registry as `pharmacist`; the registry's `required_roles=["pharmacist"]` check does not distinguish cashier, pharmacist, manager and pharmacy-admin grants. The patient-history tool itself does enforce exact selected-patient matching, a non-empty controlled purpose, same-pharmacy active-patient lookup, and metadata-only PHI audit with commit before returning data. These are meaningful controls, but because the upstream role is generic, they do not establish that the caller is a clinically authorized pharmacist. Patient-purpose validation and tenant binding are valuable controls, but they do not replace a pharmacy-specific clinical permission check.

### 7.4 Shared reference data vs tenant-owned data

Drug Catalog search and Medical Device search read shared reference records and do not expose patient records or pharmacy-specific stock in the reviewed handlers. Global access by authenticated users may be intentional. Keep these separate from tenant-owned sellable products, inventory, local assortment, pricing and catalog-review workflows.

### 7.5 Decisions still required

1. Should the general Dashboard return only non-identifiable operational metrics? Recommended default: yes.
2. Which pharmacy role may access patient purchase history and patient medication panels? Recommended default: deny all roles until explicitly granted; likely clinical roles only, subject to policy approval.
3. Should AI access to selected-patient context require a clinical permission in addition to membership and purpose? Recommended default: yes. The current MCP tool's pharmacist-role gate is ineffective as a pharmacy-role distinction because every non-superuser account resolves to `User.role == "pharmacist"`.
4. Which roles may review and approve imported drug reference records? Keep restricted to a designated catalog-governance capability; do not equate Pharmacy Admin with platform Superuser.
5. Are shared drug and medical-device reference searches available to every authenticated pharmacy member? This can remain a shared read capability if confirmed.



### 7.6 MCP patient-history tool: positive controls and remaining role flaw

A separate source review of `src/pharmaviyum/ai/mcp/tools/patient_history.py` confirms stronger controls inside the tool than the generic AI route alone suggests:
- the tool requires the trusted MCP context;
- model-supplied `patient_id` must exactly equal trusted `selected_patient_id`;
- a controlled purpose must be present;
- the patient must be active and belong to the trusted pharmacy;
- prescription and order counts are also constrained through the patient's pharmacy;
- allow/deny decisions are written to `PHIAccessAudit`, and the audit commit occurs before patient data is returned.

However, the tool declares `required_roles=["pharmacist"]`, while `User.role` is computed as `"admin" if is_superuser else "pharmacist"`. Therefore every non-superuser account passes the legacy pharmacist role filter. The tool's role check is not evidence that a user has been assigned the pharmacist role in the selected pharmacy. This is the precise distinction the new membership-role RBAC model must address.

Do not misclassify the MCP patient-history tool as lacking selected-patient binding or audit; those controls are present in the inspected source. The confirmed gap is the lack of pharmacy-specific role/permission resolution at the API-to-MCP boundary.

## 8. Reports, exports and background execution

Source baseline: `main` at `b5a0f51cc45e39b5afdfd21af99a5053823af5ce`. This is a targeted source search, not proof that no export feature can exist outside the searched repository paths.

### 8.1 Reports and exports

- The reviewed API tree and targeted searches did not identify a dedicated report/export endpoint or CSV/XLSX attachment implementation.
- `src/pharmaviyum/services/analytics_service.py` is empty in the reviewed revision.
- `GenerateDailyReportTask` is registered in the active custom worker, but its implementation returns `status: not_implemented`; it does not query or materialize report data.
- Therefore, do not describe report export as an implemented PHI read surface based on this source review. Treat report/export authorization as a required design gate before implementing it.
- The current `GET /api/v1/dashboard/summary` is an implemented analytics read surface and already exposes patient-identifiable and medication-level information to any active member with dashboard access; see section 7.1. This is the confirmed current risk, not a hypothetical export.

**Required controls before adding reports/exports:** explicit report-specific permission; pharmacy scope fixed server-side; minimum-field projection; purpose-bound PHI access where identifiable patient data is included; allowed/denied audit decisions; export creation/download audit; short-lived, actor-bound download grants; no public or guessable object URLs; and tests for cross-pharmacy denial, revocation, and audit-persistence failure. Background generation must carry the same authorization grant and must not broaden it.

### 8.2 Active background worker is Redis-backed, not the empty Celery scaffold

Reviewed files:
- `src/pharmaviyum/workers/dispatcher.py`
- `src/pharmaviyum/workers/worker.py`
- `src/pharmaviyum/workers/tasks/notifications.py`
- `src/pharmaviyum/workers/tasks/pos_sync.py`
- `src/pharmaviyum/workers/tasks/scheduled.py`

Findings:

1. The active worker consumes task payloads from Redis and dispatches by a hard-coded task registry. The dispatcher accepts a task name and arbitrary `task_args`; the payload has no required authenticated actor, permission/grant reference, purpose, or authorization-decision identifier.
2. The worker checks that a task name is registered and that its queue matches the task class. It does not independently validate the initiating actor's authorization or a signed, scoped job grant before execution.
3. `SendPatientNotificationTask` accepts `patient_id`, `pharmacy_id`, arbitrary `template_data`, channel and language. It correctly loads the patient using both patient ID and pharmacy ID, but it has no actor/permission provenance, no controlled-purpose field, no PHI audit event, and no template-specific allow-list for potentially sensitive values. It can send to patient phone/email destinations. This is a confirmed background PHI/communications governance gap; do not assume that tenant filtering alone proves the enqueueing actor was authorized.
4. `SyncProductsTask` scopes product reads/writes by `pharmacy_id`, which is a positive tenant predicate. The task payload still has no verified initiating actor or service-principal authorization in the worker. Other POS sync tasks are currently placeholders returning `not_implemented`.
5. `GenerateDailyReportTask` and `SyncAllPosTask` are placeholders; the former returns `not_implemented`, and the latter does not yet enumerate pharmacies or enqueue actual sync jobs.
6. `src/pharmaviyum/tasks/celery_app.py`, `src/pharmaviyum/tasks/worker.py`, `src/pharmaviyum/tasks/tasks/analytics_event.py`, `notify_new_order.py` and `sync_inventory.py` are empty in the reviewed revision. The existence of a `tasks` package and Celery-named files is not evidence of an active Celery task runtime. The worker actually inspected here is the Redis-backed implementation under `src/pharmaviyum/workers/`.

**Required controls:** define separate human-initiated and system-scheduled job principals; persist immutable actor, tenant, purpose, permission/grant ID, request/correlation ID and enqueue timestamp; validate a signed/opaque authorization grant at execution time; recheck resource ownership at execution; constrain and validate task schemas and template variables; audit patient-contact and PHI-bearing jobs; prevent sensitive payloads from appearing in logs, Redis status responses or dead-letter records; and test tenant isolation, revoked grants, retries, replay/idempotency and audit failure. A job must not inherit a caller's broad privileges merely because it runs asynchronously.

### 8.3 MCP tool inventory beyond patient history

Reviewed registered tool families:

| Tool | Current scope/control observed | RBAC / PHI conclusion |
|---|---|---|
| `search_pharmacy_products` | Trusted MCP context; inventory query constrained to `auth.pharmacy_id` | Tenant-scoped operational read; registry defaults to pharmacist/admin/system roles, but upstream legacy role mapping presents every non-superuser as pharmacist |
| `get_inventory_overview`, `get_expiring_inventory` | Trusted context; inventory rows constrained to `auth.pharmacy_id` | Tenant-scoped stock/expiry reads; same ineffective coarse role distinction |
| `get_sales_summary` | Trusted context; sales query constrained to `auth.pharmacy_id` | Tenant-scoped aggregate sales read; same role-resolution gap |
| `get_pharmacy_workflow_guide` | Static workflow guidance; no patient/tenant data query | No PHI read identified; registry role policy remains coarse |
| `get_patient_history` | Exact selected-patient match, controlled purpose, active patient/pharmacy check, PHIAccessAudit commit before response | Positive patient-level controls; role assignment remains ineffective because all ordinary accounts map to pharmacist; response fields remain broader than minimum necessary |
| `verify_prescription` | Prescription lookup joins Patient and constrains by trusted pharmacy; patient must be active | No selected-patient binding, controlled purpose, or PHIAccessAudit was found in the inspected function. Treat prescription lookup/verification as sensitive clinical access and add a clinical permission, purpose and audit before broadening access. |
| `check_drug_interactions` | Drug names supplied as input; static interaction data and RAG enrichment; no patient-record query in inspected function | No patient PHI read identified in this function. Keep patient-specific context out of generic tool arguments unless separately authorized. |
| `check_halal_compliance` | Drug/product and fiqh inputs; static compliance data in inspected function | No patient-record query identified. Avoid inferring a patient's religious affiliation from country defaults; this is a product-compliance lookup, not a patient authorization signal. |

The MCP registry defaults tools to roles `pharmacist`, `admin`, and `system` unless overridden. Tool discovery and invocation use the legacy account-level role, not a pharmacy membership role or effective permission set. The patient-history tool explicitly narrows to pharmacist, but because `User.role` maps every non-superuser to pharmacist, this does not distinguish actual pharmacy job functions. This remains a cross-cutting authorization design gap.

The prescription-verification tool is tenant-scoped, which is positive, but tenant scope alone does not establish clinical authorization. Its current implementation returns prescription validation results and performs prescription-status checks without the selected-patient/purpose/audit controls used by `get_patient_history`. The required policy should decide whether this tool is restricted to pharmacist-only and whether each lookup must be bound to the selected patient.

### 8.4 Implementation gates

1. Do not implement report/export access until the report data classification and permission/purpose model are approved.
2. Add a common job authorization envelope before enabling patient communications, PHI reports, or other sensitive asynchronous tasks.
3. Use a pharmacy membership's effective permission for MCP discovery and execution; do not use `User.role` as a proxy.
4. Add selected-patient/purpose/audit enforcement to prescription verification if it remains a patient-linked clinical operation.
5. Add integration tests for worker and MCP denial paths, including audit failure and cross-tenant payload substitution.
6. Keep all unapproved grants denied by default. These findings do not approve the proposed four pharmacy roles or any role-to-permission mapping.



### 8.5 POS action authorization is membership-only

## 8.6 Pharmacy membership is not yet a role-bearing authorization principal

**Verified against `main` source models and dependencies:**

- `PharmacyMembership` stores only `id`, `user_id`, `pharmacy_id`, `is_active` and `created_at`. It has no role, permission set, assignment actor, assignment timestamp or revocation metadata.
- `User.role` is a computed property: every non-superuser is `pharmacist` and every superuser is `admin`. There is no persisted pharmacy-scoped role on `User` either. This legacy property must not be used as pharmacy RBAC authority.
- `require_pharmacy_tenant` checks active membership only. It returns a tenant context with user and pharmacy IDs, but no role or effective permissions. The superuser branch bypasses membership lookup.
- `GET /api/v1/auth/me` returns account name, email, the legacy global role and token expiry. It does not return memberships, selected pharmacy context, membership roles or effective permissions.
- The inspected `POST /api/v1/auth/register` creates a user account but does not create a pharmacy or membership. The inspected pharmacy API exposes pharmacy listing/creation, but no pharmacy-membership list/create/update/deactivate or role-assignment workflow was identified.
- The membership model's uniqueness constraint prevents duplicate user/pharmacy pairs, but does not implement role lifecycle, approval, audit or effective-permission resolution.

**Authorization consequences:** a pharmacy membership currently proves tenant membership only. It cannot distinguish Cashier, Pharmacist, Manager or Pharmacy Admin. The frontend's legacy role value is not sufficient to render pharmacy-specific permissions, and the backend has no effective-permission dependency to enforce them. Do not backfill all existing members as Pharmacists or grant roles by inference.

**Additional tenant-lifecycle check:** `require_pharmacy_tenant` checks `PharmacyMembership.is_active` but the inspected function does not check `Pharmacy.is_active`. Define and test whether inactive pharmacies must be denied for all operational actions, including for platform superusers, before finalizing tenant-context semantics.

**Required implementation gates (not authorized by this audit):** approve a role-bearing membership schema and least-privilege backfill policy; define controlled membership/role administration with append-only audit; implement a centralized permission/tenant-context dependency; define `/auth/me` or a dedicated context endpoint for selected pharmacy and effective permissions; add cross-pharmacy, inactive-membership, inactive-pharmacy, role-change and default-deny tests. Keep unknown roles, missing context and permission-resolution failures denied.

**Test-coverage observation:** the inspected patient-history and AI-profile integration suites cover allowed access, missing membership, cross-pharmacy denial and superuser denial. They do not include an inactive-membership case or inactive-pharmacy case in the reviewed tests. These tests validate selected PHI routes, not a universal RBAC policy. No membership role-assignment or role-change authorization tests were identified in the reviewed test surface.


**POS authorization finding (verified against mounted `src/pharmaviyum/api/v1/pos.py`):** `require_pharmacy_tenant` proves active membership only; it does not evaluate pharmacy role or action permission. Consequently, checkout, lot lookup, goods receipt and pending-sale cancellation are membership-authorized today. Checkout accepts caller-supplied `discount_total` and only checks that discount is below subtotal and final total remains positive; no discount permission, ceiling, reason or approval is enforced. Lot lookup returns lot identifiers, expiry and quantity/reservation details. These are implementation gaps, not grants. Do not interpret the draft role matrix as active controls. Prioritize server-side action authorization and discount policy before enabling pharmacy roles.


## 9. Integrations, webhooks and application event flows

Source baseline: `main` at `b5a0f51cc45e39b5afdfd21af99a5053823af5ce`. This section distinguishes the legacy ERP integration API, POS payment callbacks, durable Edge synchronization, and the process-local application event bus.

### 9.1 Legacy ERP integration API is global and operator-only

Files: `src/pharmaviyum/api/v1/pharmacy_entities.py`, `src/pharmaviyum/models/erp_sync.py`.

- `ERPIntegration` has no `pharmacy_id`, owner tenant, credential reference, or service-principal identity. Its provider, endpoint and sync mode are global fields.
- `GET/POST /api/v1/erp/integrations`, `POST /api/v1/erp/integrations/{integration_id}/events`, `GET /api/v1/sync-events` and `GET /api/v1/erp/integrations/{integration_id}/events` use `CurrentSuperuser`. This is a platform-operator gate, not pharmacy-scoped integration authorization.
- The event-ingest route is not authenticated as an external provider. It requires an application superuser session; do not mistake it for a provider webhook contract.
- `ERPEventIn` accepts `event_id`, `entity_type`, optional `entity_id`, and a bounded free-form `direction`. It has no payload schema, signature, provider event timestamp, tenant binding or provider identity. The stored `ERPSyncEvent` is metadata-only in the reviewed model.
- Duplicate handling checks only whether the global `event_id` exists and returns `duplicate`; it does not compare the incoming integration/entity/direction with the stored event. Reuse of an ID with altered metadata is silently treated as duplicate rather than a protocol conflict.
- Event list endpoints are global superuser reads; no dedicated access audit was found in the inspected handlers.

**Conclusion:** this is a global administrative metadata API, not a production-ready multi-tenant connector framework. Keep it separate from Pharmacy Admin. Before external use, define integration ownership, machine identity, secret lifecycle, signed/versioned event schema, replay/idempotency semantics and operator audit.

### 9.2 POS payment webhook has HMAC authentication and state checks, but needs provider-bound replay controls

File: `src/pharmaviyum/api/v1/pos.py`, `payment_webhook`.

Positive controls:
- HMAC-SHA256 over the exact raw request body; constant-time `hmac.compare_digest`; fail-closed if `PAYMENT_WEBHOOK_SECRET` is absent.
- Only `succeeded` or `failed` states are accepted; payment must exist, be non-cash and pending; callback amount must equal the persisted amount.
- Sale/payment rows are locked before finalization; stock changes use the inventory movement service; the payment event is written to the transactional outbox in the same database transaction.
- Matching retries are idempotent; conflicting final states return 409.

Remaining controls:
- The handler's docstring explicitly delegates provider-specific signature verification to an adapter before the normalized event reaches this endpoint. This handler alone does not establish provider-specific verification, signed timestamp/nonce freshness, or credential-to-provider binding.
- `provider_name` and `provider_payment_id` are accepted from the signed body but are not compared with an expected provider identity/reference already bound to the pending payment.
- This is a machine-to-machine principal, not interactive user RBAC. Give each payment provider a distinct service identity/secret and explicit allowed operations.
- Add tests for wrong provider, stale signature, altered duplicate event, amount mismatch, concurrent callbacks and payment cross-link attempts.

This is not evidence that HMAC is absent; it identifies the boundary between the normalized shared-secret handler and provider-specific verification that must be proven in the adapter.

### 9.3 Pharmacy Edge Sync has meaningful tenant and payload controls

Files: `src/pharmaviyum/api/v1/sync.py`, `src/pharmaviyum/services/edge_identity.py`, `src/pharmaviyum/schemas/sync.py`, `src/pharmaviyum/services/outbox.py`, `src/pharmaviyum/services/outbox_dispatcher.py`.

Positive controls:
- Edge enrollment/revocation require `CurrentSuperuser`; enrollment validates an active pharmacy and returns a high-entropy credential once. Only a SHA-256 digest is stored; revoked/inactive credentials are rejected.
- Inbound pharmacy scope is derived from the authenticated Edge node registration, not the request body. The supplied `edge_node_id` must match that identity.
- Event v1 allowlists four POS lifecycle types with strict typed payload models, `extra="forbid"`, aggregate/version checks, monetary and quantity invariants, and a 256 KiB payload limit.
- Integration tests cover forged scope, cross-pharmacy Edge identity, revoked credentials, altered duplicate event content, unsupported event types and patient fields in payloads.
- Event IDs and aggregate versions are unique; identical retries are idempotently acknowledged, while altered content/conflicting versions are rejected.
- Edge outbox rows are written in the originating business transaction. Dispatcher uses HTTPS-only configuration, bounded retries, per-aggregate ordering, lease tokens/fencing and dead-letter quarantine.
- Dead-letter listing omits business payloads; replay is superuser-only and writes an `OutboxReplayAudit` with actor and reason.

Boundaries:
- POS event payloads contain product names/SKUs, lot numbers, quantities, prices and payment metadata. They exclude patient identity under the current allowlisted contract, but remain commercially sensitive.
- Central ingress stores `CentralInboxEvent` with `processing_status=accepted`; there is no Central domain consumer. `accepted` means durable receipt, not that Central applied sale/payment/inventory effects. ADR-0007 correctly blocks domain application pending product/lot mapping, actor provenance, stock semantics, ordering and reconciliation.
- Dead-letter listing is a global `CurrentSuperuser` view. Replay is audited, but support inspection/replay is not pharmacy-scoped and has no explicit time-bound support grant. Keep this a platform operations capability and consider reason-bound tenant access/read audit.
- Edge provisioning is platform-global superuser-only, not a Pharmacy Admin permission.

**Conclusion:** retain Edge identity and event-contract controls. Do not broaden v1 with patient identifiers or generic entity events. Do not implement the Central consumer until ADR-0007 prerequisites are met.

### 9.4 Generic patient lifecycle events still carry linkable identifiers

Files: `src/pharmaviyum/services/patient.py`, `src/pharmaviyum/services/event_bus.py`.

- `patient.created` was minimized to pharmacy-level metadata.
- `patient.updated` still emits `patient_id`, updated field names and optional `updated_by`; `patient.deleted` still emits `patient_id`, hard-delete flag and optional actor. Stable patient IDs are linkable personal data even without name/phone.
- The event bus is process-local and best-effort; handler exceptions are logged and swallowed. It is not durable integration delivery.
- The reviewed repository search found no in-repository `event_bus.on(...)` subscribers. That does not prove dynamic/runtime consumers cannot be registered and does not justify identifiers in a generic event contract.

**Required controls:** remove patient identifiers from generic lifecycle notifications. If a workflow needs a patient reference, define a dedicated event contract with explicit consumer identity, purpose and lookup authorization. Keep PHI out of generic telemetry and event payloads.

### 9.5 Integration/RBAC implementation gates

1. Decide which integrations are platform-global and which are pharmacy-owned; model tenant ownership explicitly.
2. Create distinct machine/service principals for each provider, Edge node and scheduled integration; keep them separate from human pharmacy roles.
3. Replace the legacy ERP metadata event contract before external use: authenticate provider, validate a versioned schema, derive tenant from credential, and reject event-ID reuse with different content.
4. Prove provider-specific signature validation, freshness/replay protection and binding to the expected payment/provider reference before production payment callbacks.
5. Preserve Edge Sync's strict allowlist, tenant derivation, idempotency, ordering and durable-receipt semantics. Keep Central domain application disabled until ADR-0007 prerequisites are met.
6. Minimize patient lifecycle events and audit privileged cross-pharmacy sync inspection/replay.
7. Test service-principal revocation, wrong-tenant credentials, altered duplicate IDs, stale/replayed callbacks, PHI payload rejection and audit failure.

These findings do not approve pharmacy role grants. Integration administration, Edge provisioning, payment callbacks and support replay are distinct machine/platform capabilities and must not be collapsed into `pharmacy_admin`.

## 10. Consolidated RBAC implementation blueprint — proposal only

This blueprint consolidates the API, Sidebar, PHI, MCP, worker and integration findings above. It is a delivery design, not authorization to implement or grant roles. The role matrix in `PHARMACY_RBAC_PERMISSION_SPEC.md` remains unapproved; unresolved policy means deny by default.

### 10.1 Target authorization decision

Every protected operation should resolve the following trusted context before accessing or mutating a resource:

1. **Principal:** authenticated human user or explicitly registered machine/service identity.
2. **Tenant:** one pharmacy resolved from a selected context and an active membership, or from a machine credential's registered pharmacy. Never derive tenant authority from a client-supplied ID alone.
3. **Action:** a stable permission identifier for the exact operation.
4. **Resource:** load the target row with tenant ownership in the SQL predicate; do not load globally and compare tenant ownership only after materialization.
5. **Additional policy:** patient ownership/care relationship, purpose of use, workflow state, approval threshold, and/or platform support grant as applicable.
6. **Audit:** persist required allow/deny decision metadata before releasing PHI or committing a privileged action. Audit failure must fail closed for governed PHI access.

Conceptual decision: `authenticated AND active_tenant AND action_permission AND resource_scope AND additional_policy`. A missing/unknown input is deny. This should be implemented as a small centralized authorization service/dependency plus resource-scoped query helpers, not as a broad general-purpose policy engine.

### 10.2 Separate human roles from machine/platform capabilities

| Principal class | Scope source | Intended responsibility | Must not inherit |
|---|---|---|---|
| Cashier / Pharmacist / Manager / Pharmacy Admin (proposed) | Active `PharmacyMembership` and approved membership role | Human pharmacy workflows | Platform-wide superuser or another pharmacy's permissions |
| Platform operator | Explicit platform capability and, for sensitive access, a time-bound support grant | Provisioning, support and operational review | Automatic clinical/PHI access |
| Payment provider | Provider-specific credential and verified signed callback | Narrow payment state callback | Interactive user permissions or arbitrary payment access |
| Pharmacy Edge node | Active enrolled `PharmacyEdgeNode` credential | Submit allowlisted events for its registered pharmacy | Other Edge nodes or direct Central domain writes |
| Background job | Persisted initiating actor or scheduled service identity plus scoped job grant | Execute one authorized task within one tenant | The caller's ambient/global privileges |
| MCP tool invocation | Trusted user, selected pharmacy, selected patient and purpose context plus effective permission | Execute one registered tool | Generic `User.role` as proof of clinical role |

### 10.3 Permission enforcement map

| Surface | Required enforcement boundary |
|---|---|
| POS checkout, cancel, refund, discount | Separate action permissions; sale and inventory rows constrained to the same pharmacy; payment provider callbacks use a separate machine identity |
| Inventory, Defectura, procurement, transfers | Action-specific permissions; selected pharmacy; object ownership in SQL; immutable movement ledger and reason/idempotency checks |
| Patients, purchases, prescriptions, clinical records | Clinical permission plus patient/pharmacy ownership, purpose-of-use policy, minimum response fields and PHI audit |
| General Dashboard | Operational aggregate permission only; remove patient-identifiable and medication-level panels from the general response |
| Clinical Dashboard panels | Separate clinical endpoint and permission; selected patient/tenant scope, purpose and PHI audit |
| Shared Drug Catalog / Medical Device reference | Explicitly approved shared-reference read capability; keep separate from pharmacy-owned assortment, stock and pricing |
| Catalog review, supplier and ERP administration | Designated governance/platform capability until ownership and separation-of-duties policy is approved |
| MCP discovery and execution | Effective pharmacy permission at both discovery and invocation; revalidate trusted context and resource scope inside the tool |
| Background jobs and notifications | Persist actor/service identity, tenant, purpose, permission/grant ID and correlation ID; revalidate scoped grant and ownership at execution |
| Reports and exports | Report-specific permission; server-derived tenant scope; minimum fields; audit export creation and download; short-lived actor-bound download authorization |
| ERP integration / payment webhook / Edge Sync | Distinct service principals and provider contracts; no mapping to human pharmacy roles |
| Support / dead-letter replay | Platform operations capability, reason-bound access and durable operator audit; no default PHI access |

### 10.4 Minimal technical architecture

- **Identity:** retain the global `User` identity; do not use `User.role` as a pharmacy role.
- **Membership:** after policy approval, add one constrained role assignment to each active pharmacy membership. A user may have different roles in different pharmacies.
- **Permission registry:** start with a versioned code-level registry mapping permission IDs to protected actions. Avoid a database-driven custom-role engine unless runtime-customizable roles become a concrete requirement.
- **Authorization dependency/service:** accept principal + selected tenant + permission; fail closed for missing membership, unknown permission, inactive membership or lookup failure.
- **Resource access:** use tenant-qualified SELECT/UPDATE/DELETE predicates and composite tenant/resource constraints where appropriate. Avoid fetching by global ID before checking ownership.
- **PHI governance:** use a shared metadata-only audit contract (actor/service, tenant, action, resource reference, purpose, request/correlation ID, timestamp, outcome); never copy clinical payloads, secrets or unnecessary patient fields into the audit record.
- **Authenticated context API:** extend `GET /api/v1/auth/me` only after API contract approval to expose selected pharmacy, memberships/roles and effective permissions. Do not return PHI or use the legacy role string as authority.
- **Frontend:** filter Sidebar destinations by implemented-route state and effective permissions for UX only. Backend remains authoritative; stale/unavailable permission context fails closed.
- **Non-HTTP execution:** use explicit job grants and service principals for workers, MCP, integrations and scheduled tasks; never rely on ambient process privileges.

### 10.5 Safe implementation sequence

| Phase | Deliverable | Gate |
|---|---|---|
| 0. Policy | Approve role set, permission IDs, role grants, PHI purposes, support access and global-vs-tenant integration ownership | Product + clinical + security approval |
| 1. Baseline tests | Runtime route-table inventory; endpoint × action × resource matrix; cross-tenant negative tests | All mounted routes identified; legacy routes distinguished |
| 2. Identity model | Membership role and safe existing-membership classification/backfill design | No automatic privileged role assignment; migration reviewed |
| 3. Authorization core | Central permission registry/dependency and tenant-qualified resource query helpers | Unit + PostgreSQL integration tests; 401/403 semantics |
| 4. PHI migration | Dashboard split, patient/prescription/purchase access, purpose and audit | Audit-before-release; ownership and failure-closed tests |
| 5. Operational domains | POS, inventory, Defectura, procurement, catalog and pharmacy administration | Per-action permissions; movement/idempotency invariants preserved |
| 6. Non-HTTP paths | MCP, notifications, workers, exports, reports and service integrations | Scoped grant validation, revocation, replay and tenant-isolation tests |
| 7. Frontend context | Authenticated context contract, selected pharmacy and Sidebar permission UX | UI tests; backend authorization independently verified |
| 8. Demo validation | Synthetic multi-pharmacy end-to-end validation and CI | No production DB changes; no migration guard bypass |
| 9. Controlled rollout | Staged enablement and rollback plan | Explicit release approval |

### 10.6 Non-negotiable acceptance criteria

- A user can hold different roles in different pharmacies; switching pharmacy changes the effective permission set.
- Client-supplied `pharmacy_id`, patient ID, sale ID, inventory ID or integration ID cannot widen scope.
- Every protected operation is checked at the backend action boundary; UI visibility never grants access.
- Unknown permission, missing membership, inactive membership, stale/revoked job grant, ambiguous patient ownership or failed authorization lookup denies access.
- PHI access is purpose-bound where required, minimum-necessary, and durably audited before data is returned.
- Platform operators and support tools are separately governed; Pharmacy Admin is never equivalent to platform superuser.
- Payment provider, Edge node, scheduled job and MCP tool identities are separate from human pharmacy roles.
- Retries, duplicate events, webhook replay, job replay and dead-letter replay cannot duplicate business effects or bypass authorization.
- All role × permission outcomes, cross-tenant attempts, revoked identities, audit failures and worker/MCP denial paths have automated tests.
- Migrations and deployments use approved workflows and environment guards; no manual production SQL or guard bypass.

**Current implementation status:** the application does not yet have this complete pharmacy-scoped RBAC model. The documents define gaps and a proposed sequence; they do not represent implemented authorization, approved role grants, or a production security certification.

## 11. Final mounted API route coverage and path corrections

Route coverage source baseline: `main` at `fb1e40fd47e1137bcff43369ececdb45953de473`.

This section supersedes any earlier shorthand path in this inventory where the live router prefix differs. It was derived from `src/pharmaviyum/main.py` and the package router actually imported there: `src/pharmaviyum/api/v1/__init__.py`. The separate `src/pharmaviyum/api/v1/router.py` is not mounted by `main.py`.

### 11.1 Live router composition

`main.py` includes `api_v1_router` at the application root, then separately includes `src/pharmaviyum/api/v1/endpoints/health.py` at the root. The actual mounted paths are therefore:

| Mounted surface | Live paths | Current access boundary | Candidate policy / gap |
|---|---|---|---|
| Legacy auth | `POST /api/v1/auth/register`, `POST /api/v1/auth/token` | Public | Registration creates an active non-superuser account but no pharmacy membership or invitation approval. Decide whether self-registration is allowed; account creation must not imply tenant access. |
| Authenticated identity | `GET /api/v1/auth/me` | CurrentUser | Returns legacy `User.role`; does not expose membership roles, selected pharmacy or effective permissions. |
| Modular auth | `POST /api/v1/auth/login/access-token`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `POST /api/v1/auth/password-recovery/{email}`, `POST /api/v1/auth/reset-password/` | Token/reset-token flows | Identity lifecycle controls; not pharmacy business permissions. Keep token revocation, one-time reset and account activation policy separate from RBAC. |
| AI | `GET /api/v1/ai/context`, `POST /api/v1/ai/query`, `POST /api/v1/ai/query/stream`, `GET /api/v1/ai/tools` | CurrentUser; query paths validate pharmacy tenant; optional patient requires patient + purpose together | Add effective pharmacy permission at both tool discovery and execution. Retain trusted MCP context and patient ownership checks. |
| Dashboard | `GET /api/v1/dashboard/summary` | CurrentUser + `resolve_pharmacy_scope` | Confirmed patient-identifiable/medication PHI exposure to all active members; split operational and clinical panels as in section 7.1. |
| Patients | `/api/v1/patients` collection, `/statistics`, `/phone/{phone}`, `/{patient_id}`, `/{patient_id}/ai-profile`, `/{patient_id}/visit`; `POST` collection, `PUT/DELETE` patient resource | CurrentUser + tenant scope; AI profile has explicit membership/patient checks and PHI audit; create/update/delete currently pass through service-level policy and tenant scope | Do not flatten to one permission. Separate patient search/read, clinical profile, create, update, archive/delete, and visit recording. Validate PHI audit coverage per operation. |
| Orders | `/orders/`, `/orders/{order_id}`, `/orders/{order_id}/status` | CurrentUser + `resolve_pharmacy_scope`; order is linked through patient | Distinguish legacy patient-linked order workflow from POS Sale/Payment. Separate read/create/status-transition permissions and enforce patient ownership in scoped queries. |
| POS | `/api/v1/pos/products/search`, `/inventory/receive`, `/products/{product_id}/lots`, `/checkout`, `/payments/webhook`, `/sales/{sale_id}/cancel`, `/sales/{sale_id}` | User endpoints use CurrentUser + tenant checks; payment callback uses HMAC service authentication | Separate POS read, inventory receive, checkout, sale read/cancel and provider callback. Current handlers lack pharmacy action-level role checks. |
| Pharmacy and inventory | `/api/v1/pharmacies`, `/api/v1/suppliers`, `/api/v1/inventory`, `/api/v1/inventory/{id}`, `/api/v1/inventory/{id}/adjustments`, `/api/v1/batches`, `/api/v1/prescriptions` | Pharmacies read: CurrentUser + memberships; create: CurrentSuperuser. Suppliers and inventory writes, batches, prescriptions: CurrentSuperuser. Inventory read: CurrentUser, membership pharmacy IDs, optional requested pharmacy filter | Inventory read is membership-scoped but not selected-context/action-permission scoped. Inventory writes and prescription APIs remain platform-superuser only. Batch model lacks pharmacy ownership; fail-closed restriction is appropriate. Prescription create must validate patient/pharmacy ownership when access is expanded. |
| Legacy ERP integration metadata | `/api/v1/erp/integrations`, `/api/v1/erp/integrations/{integration_id}/events`, `/api/v1/sync-events` | CurrentSuperuser | Global platform operations; not Pharmacy Admin. See section 9.1. |
| Drug reference search | `GET /drug-catalog/search` | CurrentUser | **Path correction:** the search router prefix is `/drug-catalog`, not `/api/v1/drug-catalog`. Shared reference read; confirm this root-level path is intentional and document one canonical API prefix. |
| Drug catalog review | `/api/v1/drug-catalog/sources`, `/api/v1/drug-catalog/sources/{id}/matches`, `/api/v1/drug-catalog/sources/{id}/review` and source creation | CurrentSuperuser | Global reference-data governance; separate from pharmacy stock/catalog read. |
| Medical-device reference | `GET /medical-devices/search` | CurrentUser | **Path correction:** live prefix is `/medical-devices`, not `/api/v1/medical-devices`. Shared reference read. |
| Pharmacy sellable Product master | `/api/v1/products/search`, `/api/v1/products/{product_id}`, `/api/v1/products/`, `POST/PUT/DELETE` | Read: CurrentUser; create/update/deactivate: CurrentSuperuser | Product model has no `pharmacy_id`; SKU is globally unique. It stores global `price` and legacy aggregate `stock` (the model/schema explicitly state per-pharmacy stock belongs to Inventory). Responses include both price and stock. Treat this as a shared/global product master, not tenant inventory. If prices differ by pharmacy, a pharmacy-scoped price/assortment model is required before exposing these fields as pharmacy-specific values. |
| Patient purchases | Legacy `/patient-purchases/` and canonical `/api/v1/patient-purchases/`; history at both `/{patient_id}/history` paths | Legacy list: CurrentSuperuser; history: CurrentUser + explicit active membership, patient ownership, purpose and PHI audit; platform superusers denied | The router is intentionally mounted twice. Maintain one documented canonical path and test both aliases until legacy removal is approved. History still lacks granular membership-role permission. |
| Pharmacy Edge Sync | `/api/v1/sync/edge-nodes`, `/edge-nodes/{node_id}`, `/outbox/dead-letter`, `/outbox/dead-letter/{entry_id}/replay`, inbound event endpoint | Provision/revoke/list/replay: CurrentSuperuser; inbound event: Edge credential authentication | Distinct platform and machine-principal policies; preserve tenant-derived Edge identity. See section 9.3. |
| RAG document ingestion | `POST /api/v1/ingest/documents/upload`, `POST /api/v1/ingest/documents/url`, `GET /api/v1/ingest/jobs`, `GET /api/v1/ingest/jobs/{job_id}` | Upload and URL ingestion require both `CurrentSuperuser` and `CurrentUser`; job list/status require `CurrentSuperuser` | These routes are platform-superuser-only today, not ordinary pharmacy-admin/member endpoints. Keep content ingestion as a distinct platform capability until a scoped pharmacy permission and worker grant are designed. URL ingestion additionally needs SSRF/egress controls. |
| User administration and self-service | `/users/me/avatar`, `/users/`, `/users/{user_id}` | Avatar operations: CurrentUser on self; list/create/read other users: CurrentSuperuser | User account administration is not pharmacy membership administration. No pharmacy-scoped membership/role assignment API is currently mounted. |
| Monitoring | Root `/health`, `/ready`, `/metrics`, `/mcp/health`, `/version`; root `/api-info` | Health/readiness/metrics/version/api-info: public; MCP health: CurrentSuperuser | Keep liveness/readiness public only as operationally required. Restrict metrics to trusted scrape network/identity. Review public version metadata (build, environment, debug flags, Python runtime). Detailed MCP health remains operator-only. |

The exact relative paths above are appended to each router's declared prefix. For collection routes shown without an HTTP method, the method follows the handler decorator in the source; the access boundary is the same for the listed handler family unless stated otherwise.

### 11.2 Router collisions and path inconsistencies

1. **Duplicate root health routes:** the mounted package aggregator includes `monitoring_router` first, registering `GET /health`, `GET /ready`, and `GET /metrics`. `main.py` then includes `endpoints.health.router`, which registers the same three method/path pairs. Both implementations are therefore registered. Starlette route matching is order-sensitive; the first matching route is the effective handler. Consolidate to one implementation and add route-table tests so readiness/metrics semantics cannot silently diverge.
2. **Mixed API prefixes:** `/api/v1` is used by several routers, but Orders, Drug Catalog search, Medical Devices, and Users use root-level prefixes. Do not assume the endpoint path from a module's directory or tag; use the mounted route table as source of truth. Choose and document a canonical versioning strategy before adding RBAC metadata or frontend clients.
3. **Patient purchases alias:** the same router is mounted at both `/patient-purchases` and `/api/v1/patient-purchases`. This is an explicit compatibility alias, not two different authorization implementations.
4. **Unused legacy router:** `src/pharmaviyum/api/v1/router.py` defines a separate `api_router` and `system_router`, including debug, feature flags and prescription placeholder routers. `main.py` does not import or mount it. Do not classify those endpoints as active production routes.
5. **Other unmounted modules:** `src/pharmaviyum/api/v1/erp.py` is not imported by the active aggregator; `endpoints/debug.py`, `endpoints/docs.py`, `endpoints/feature_flags.py` and `endpoints/prescriptions.py` are not included by the active package aggregator. `examples.py` contains examples, not live endpoints. Any future mounting requires a fresh authorization review.

### 11.3 Additional authorization and data-governance findings

**Public account registration**
- `POST /api/v1/auth/register` accepts an unauthenticated registration, creates an active non-superuser account and does not create a pharmacy membership.
- This does not itself grant access to tenant-scoped data, but there is no invite/approval or pharmacy onboarding decision in this route.
- Decide whether public self-registration is intended for the demo and for production separately. Production onboarding should use an invitation or controlled membership-assignment flow; never infer a pharmacy or role from an email domain.

**Global Product master**
- `Product` has no pharmacy foreign key and its SKU is globally unique. The API is therefore global product-master CRUD, not per-pharmacy inventory.
- `ProductResponse` exposes `price` and legacy `stock`; `ProductCreate/Update` allow those values. The model/schema say per-pharmacy stock is authoritative in `Inventory`.
- This is a semantic/data-model risk if clients interpret the returned price/stock as selected-pharmacy values. Before adding pharmacy roles, define whether product master price is global reference data or whether pharmacy-specific price/assortment must be modeled separately. Never use the global legacy `stock` field for pharmacy authorization or availability decisions.

**RAG ingestion Celery boundary**
- `POST /api/v1/ingest/documents/upload` and `/documents/url` declare both `CurrentSuperuser` and `CurrentUser` dependencies, so the effective human caller must be a platform superuser; the second dependency does not broaden access to ordinary active pharmacy members. The handler then calls `require_pharmacy_tenant` for the supplied pharmacy ID. A platform superuser currently passes through the existing superuser tenant bypass.
- The task config carries the pharmacy ID accepted by the handler; the Celery task requires a positive integer and stamps it onto each document before chunking. Uploaded object keys are validated against that pharmacy.
- The worker does not receive a persisted initiating actor, approved membership role, purpose, permission ID or signed job grant; its trust boundary is the Celery broker and caller-provided task config. The Redis progress record stores pharmacy metadata, while `GET /api/v1/ingest/jobs/{job_id}` and `GET /api/v1/ingest/jobs` are platform-superuser-only views.
- Treat ingestion as a distinct high-privilege content-management action. Do not map it to Pharmacy Admin by implication. If future policy permits pharmacy-level ingestion, add an explicit permission, immutable actor/tenant provenance, a scoped worker grant validated at execution, and tenant-aware job status access. Review external URL fetch controls separately (SSRF/egress policy); URL scheme validation alone is not a complete destination policy.

**Public operational metadata**
- The root monitoring routes `/health`, `/ready`, `/metrics` are unauthenticated in the mounted implementation. The separate `/version` endpoint returns build/environment/debug/runtime metadata, also without an auth dependency.
- Public health/readiness may be operationally necessary, but metrics and detailed runtime identity should be restricted to trusted monitoring networks or a scrape identity. Avoid returning exception details or secrets from readiness; current monitoring readiness reports exception class names only.
- `/mcp/health` is protected by CurrentSuperuser, which is the correct separation for detailed dependency/tool diagnostics.

### 11.4 Route-level implementation gate

Before coding the permission registry, generate a runtime FastAPI route table from the actual app instance and snapshot method, path, endpoint function, dependencies, response model and router source. Assert no duplicate method/path registrations except explicitly approved aliases. The static source inventory above is a review baseline, not a substitute for that runtime snapshot or endpoint tests.

No new route or permission is approved by this inventory. Existing CurrentUser/CurrentSuperuser checks remain the current controls until a separate policy approval and implementation PR.

## 12. Endpoint-to-permission mapping and vocabulary gaps

This matrix translates the observed mounted route families into action-level candidate permissions. Identifiers already present in section 3 of the Pharmacy RBAC Permission Specification are marked **existing candidate**. Any other identifier below is a **proposed vocabulary addition**, not an approved grant. Where the current endpoint is platform-superuser-only or machine-authenticated, the permission is a future target boundary only; it must not be interpreted as permission to widen access.

| API operation | Existing enforcement | Candidate permission / principal boundary | Additional condition |
|---|---|---|---|
| POS product search and sale read | CurrentUser + pharmacy tenant | `pos.read` (existing candidate) | Selected pharmacy context; product and sale tenant predicates |
| POS lot lookup | `GET /api/v1/pos/products/{product_id}/lots`; CurrentUser + requested pharmacy membership | `inventory.read` (existing candidate; earlier mapping) | Returns lot number, expiry date, on-hand quantity, reserved quantity and available quantity. No narrower POS-only permission or minimum-field response policy; decide whether Cashier needs lot-level visibility or only availability needed for checkout |
| POS discount application | `POST /api/v1/pos/checkout`; CurrentUser + pharmacy membership; client supplies `discount_total` | `pos.discount.apply` (candidate) | No role/permission check, discount threshold, reason code, approval reference or server-side pricing policy identified. Any member can submit a discount below subtotal; matrix proposal of Manager-only must not be mistaken for enforced behavior |
| POS sale cancellation | `POST /api/v1/pos/sales/{sale_id}/cancel`; CurrentUser + sale pharmacy membership; pending-payment state only | `pos.sale.cancel` (existing candidate) | No actor-role/action permission, ownership/shift restriction, mandatory cancellation reason or manager approval identified. Any pharmacy member can cancel an unpaid sale and release its stock reservations |
| POS checkout | `POST /api/v1/pos/checkout`; CurrentUser + pharmacy membership; FEFO allocation, reservation, idempotency and payment-state handling | `pos.checkout` (existing candidate) | No role/action permission or cashier-session/register ownership check identified. Tenant membership alone authorizes checkout today |
| POS goods receipt | `POST /api/v1/pos/inventory/receive`; CurrentUser + pharmacy membership; actor-attributed movement and idempotency | `inventory.receive` (existing candidate) | No role/action permission, PO/supplier linkage, receiver/count separation or approval identified. Any pharmacy member can add stock through this route today |
| POS checkout | CurrentUser + pharmacy tenant | `pos.checkout` (existing candidate) | Cashier session, stock reservation, idempotency and payment state |
| POS sale cancel | CurrentUser + pharmacy tenant | `pos.sale.cancel` (existing candidate) | Allowed sale/payment state; cancellation reason and inventory invariants |
| POS inventory receipt | CurrentUser + pharmacy tenant | `inventory.receive` (existing candidate) | Supplier/lot ownership, receiving workflow, idempotency |
| POS payment callback | `POST /api/v1/pos/payments/webhook`; HMAC-SHA256 over raw body using `PAYMENT_WEBHOOK_SECRET`, constant-time signature comparison; validates payment ID, non-cash method, pending state and exact amount; retries of finalized matching status/provider payment ID are idempotent | Payment-provider service principal; not a human role permission | Current endpoint does not itself validate a signed timestamp/nonce or provider-specific identity/credential binding; document/verify provider adapter contract, replay window and payment reference binding before production provider integration |
| Inventory read | CurrentUser + membership pharmacy IDs | `inventory.read` (existing candidate) | Selected tenant scope and object-level pharmacy predicate |
| Low-stock inventory query | `GET /api/v1/inventory?low_stock=...` through pharmacy domain router; CurrentUser; ordinary users are filtered to all active membership pharmacy IDs, optional `pharmacy_id` is an additional filter | `inventory.read` (existing candidate) | Membership-scoped but not selected-pharmacy-context or action-permission scoped. Low-stock is a query over `quantity - reserved_quantity <= reorder_level`; it is not a replenishment proposal or Defectura workflow |
| Inventory lot creation | `POST /api/v1/inventory`; CurrentSuperuser; validates active product/pharmacy and permits zero-balance lots only | `inventory.create` (proposed vocabulary addition) | Platform-only today; non-zero opening stock is rejected and must use a movement workflow |
| Inventory lot metadata update | `PATCH /api/v1/inventory/{inventory_id}`; CurrentSuperuser; reorder level, lot number and expiry metadata only | `inventory.update` (proposed vocabulary addition) | Platform-only today. Lot number/expiry become immutable after movement history exists. The reviewed handler loads by ID and has no pharmacy-role/object-scope authorization |
| Physical stock adjustment | `POST /api/v1/inventory/{inventory_id}/adjustments`; CurrentSuperuser; reason, non-zero delta and idempotency key; shared movement service | `inventory.adjust` (existing candidate) | Platform-only today; actor-attributed and movement-ledger-backed. A future pharmacy grant requires tenant-qualified object lookup and approval/audit policy |
| Inventory lot deletion / archival | `DELETE /api/v1/inventory/{inventory_id}`; CurrentSuperuser; zero balance and no movement history required; no archive endpoint identified | `inventory.archive` (proposed vocabulary addition), but current operation is hard delete | Keep platform-only. Do not describe the current delete route as archival; lots with history must be retained |
| Batch master read | `GET /api/v1/batches`; CurrentSuperuser; ProductBatch has product_id but no pharmacy_id | `inventory.batch.read` (proposed vocabulary addition) | Global batch records are not pharmacy-owned; no pharmacy-role access until ownership and tenant predicates are modeled. Operational stock lots are represented separately by Inventory |
| Stock transfer lifecycle | No mounted pharmacy-scoped transfer request/create/approve/dispatch/receive/cancel API identified | `inventory.transfer` (existing candidate) | Movement enum includes transfer_in/transfer_out, but that does not implement a paired, atomic, tenant-aware transfer lifecycle. Keep role grants pending explicit decision and implementation |
| Write-off / expiry disposal | Movement service and ledger define write_off / expiry_disposal movement semantics; no dedicated mounted pharmacy workflow endpoint identified | Future inventory write-off / expiry-disposal action permission required; no role grant | Do not treat ledger support as an executable workflow. Require reason, actor, lot status/expiry validation, idempotency and audit |
| Defectura request / replenishment proposal | No mounted Defectura request, calculation, review or approval API identified; current Inventory supports low-stock visibility and reorder levels only | Future `defectura.read`, `defectura.create`, `defectura.approve` candidates; no role grants | Defectura is one Inventory workflow/entity. Manual entry and automatic calculation are proposal-generation mechanisms, not separate navigation domains; automatic calculation must not approve or order stock |
| Purchase-order lifecycle | No purchase-order model or mounted purchase-order create/read/approve API identified in the inspected model/API surface | Future `procurement.read`, `procurement.create_order`, `procurement.approve_order` candidates; no role grants | Do not map legacy patient-linked Orders or supplier master records to purchase orders |
| PO-linked goods receiving | No PO-matching receiving API identified; standalone `POST /api/v1/pos/inventory/receive` creates a lot and goods-receipt movement without supplier/PO/invoice/delivery-note/discrepancy linkage | Future `procurement.receive` candidate; no role grant. Existing standalone endpoint remains `inventory.receive` candidate | Keep POS lot receipt distinct from procurement receiving; require PO line matching, partial receipt, discrepancy handling and audit before treating this as a procurement workflow |
| Inventory create/update/adjust/delete | CurrentSuperuser | `inventory.create`, `inventory.update`, `inventory.archive` (proposed vocabulary additions); `inventory.adjust` (existing candidate) | Keep platform-only until product/security approves pharmacy role matrix and object scope |
| Batch read | CurrentSuperuser | `inventory.batch.read` (proposed vocabulary addition) | ProductBatch currently lacks pharmacy ownership; do not widen access until tenant ownership exists |
| Patient list/search/detail | CurrentUser + pharmacy scope | `patients.read` (existing candidate) | Active membership, selected tenant, patient ownership; PHI purpose/audit where applicable |
| Patient create/update/delete | CurrentSuperuser for create/update/delete; archive is not a separately exposed operation in the reviewed route set | `patients.create`, `patients.archive` (proposed vocabulary additions); `patients.update` (existing candidate) | Do not widen the current platform-only mutation boundary until role policy, service checks, ownership and PHI audit are approved |
| Patient visit recording | CurrentUser + pharmacy scope | `patients.visit.record` (proposed vocabulary addition) | Patient ownership; record purpose and audit policy |
| Patient AI profile | CurrentUser + explicit membership/patient checks and PHI audit | `clinical_records.read` (existing candidate) | Patient ownership, allowed purpose, audit commit before release |
| Patient purchase history | CurrentUser + explicit membership, ownership, purpose and PHI audit | `patients.purchase_history.read` (proposed vocabulary addition) | Deny platform support principal absent separately approved support grant |
| Legacy patient purchase list | CurrentSuperuser | Platform data-operations capability; not `patients.read` | Keep global admin path separate from pharmacy clinical access |
| Dashboard operational summary | CurrentUser + pharmacy scope | `dashboard.read` (proposed vocabulary addition) | Response must exclude identifiable patient and medication-level fields |
| Dashboard clinical panels | CurrentUser + pharmacy scope (current gap) | `clinical_dashboard.read` (proposed vocabulary addition) | Split endpoint, patient/tenant scope, purpose and PHI audit |
| Legacy patient-linked order read/create/status | CurrentUser + pharmacy scope | `orders.read`, `orders.create`, `orders.status.update` (proposed vocabulary additions) | Preserve distinction from POS Sale/Payment |
| Shared drug catalog search | CurrentUser | `catalog.read` (existing candidate) | Shared reference-data semantics |
| Drug catalog source ingestion/review | CurrentSuperuser | `catalog.manage` (existing candidate) plus platform governance boundary | Shared catalog governance; separate approval and audit |
| Medical-device reference search | CurrentUser | `catalog.read` (existing candidate) or a future `medical_devices.read` if independent policy is required | Shared reference data, no pharmacy stock scope |
| Global Product master read | CurrentUser | `catalog.read` (existing candidate) | Global product master; do not imply tenant-specific price/stock |
| Global Product master create/update/deactivate | CurrentSuperuser | `catalog.manage` (existing candidate) plus platform governance boundary | SKU globally unique; no pharmacy_id on Product |
| Suppliers read/manage | CurrentSuperuser | `suppliers.read`, `suppliers.manage` (existing candidates) | Current model/API are global; define ownership before pharmacy role exposure |
| Pharmacy membership administration | No mounted pharmacy-scoped membership/role API | `members.read`, `members.invite`, `members.role.assign` (existing candidates) | Requires invitation/approval workflow, audit and anti-self-escalation |
| Pharmacy settings | No complete mounted action API identified | `pharmacy.settings.read`, `pharmacy.settings.update` (existing candidates) | Define resource ownership and settings contract |
| RAG ingestion upload/URL | CurrentSuperuser + CurrentUser; effective platform superuser only | Platform content-management capability; future `rag.ingestion.create` (proposed vocabulary addition) | Worker grant must bind actor, pharmacy, source, purpose, permission and correlation ID |
| RAG job list/status | CurrentSuperuser | Platform operations capability; future `rag.ingestion.job.read` (proposed vocabulary addition) | Tenant-aware access if exposed to pharmacy users |
| Edge node provision/revoke and dead-letter replay | CurrentSuperuser | Platform Edge operations principal; not Pharmacy Admin | Replay reason, operator audit, scoped tenant support grant if later required |
| Edge inbound sync event | Edge credential | Edge service principal | Derive pharmacy from enrolled node; validate event schema, version and idempotency |
| ERP integration metadata/events | CurrentSuperuser | Platform integration-operations capability | Tenant binding and provider/service identity not yet modeled |
| User self-avatar | CurrentUser on self | Account self-service; no pharmacy role permission | User may only mutate own avatar |
| User account administration | CurrentSuperuser | Platform identity-administration capability | Separate from pharmacy member administration |
| Health/readiness | Public | Operational probe endpoint | Return minimum status only; no PHI or secrets |
| Metrics | Public | Monitoring scrape principal / network boundary (proposed) | Restrict access at infrastructure or application boundary |
| Version/build metadata | Public | Operational metadata endpoint | Minimize environment/debug/runtime disclosure |
| MCP patient history | Trusted MCP context, patient binding, purpose, ownership and PHI audit; registry role filter uses legacy role | `clinical_records.read` (existing candidate) plus MCP invocation principal | Resolve effective pharmacy permission at execution; retain PHI audit |
| MCP prescription verification | Trusted pharmacy context and patient scope; no selected-patient binding/purpose/PHI audit in reviewed function | Future `prescriptions.verify` (proposed vocabulary addition) | Add patient binding, purpose and PHI audit before exposing clinical result |
| Background patient notifications | Worker task, pharmacy-qualified patient lookup | Future `patients.notify` (proposed vocabulary addition) plus scoped job grant | Actor/service, template allowlist, purpose, tenant and audit at enqueue and execution |
| Report/export generation | No dedicated implementation identified | Future `reports.generate`, `exports.create`, `exports.download` | Server-derived tenant scope, minimum fields, actor-bound short-lived download authorization and audit |

### 12.1 Permission vocabulary reconciliation

The current specification is a starting vocabulary, not yet a complete route-level contract. Before implementation, reconcile at least these items:

1. Add explicit permissions for patient creation, patient visit recording, purchase-history access, operational versus clinical dashboard access, legacy orders, RAG ingestion/jobs, MCP prescription verification, notifications, reports and exports.
2. POS sale cancellation is consistently named `pos.sale.cancel` in the specification and endpoint mapping. Preserve this identifier; do not introduce a `pos.cancel` alias.
3. Decide whether inventory writes should remain separate actions (`inventory.receive`, `inventory.adjust`, `inventory.transfer`) and whether create/update/archive need separate identifiers.
4. Keep shared reference catalog permissions distinct from pharmacy-owned assortment, pricing and inventory permissions.
5. Do not use a broad `patients.read` permission as a substitute for purpose-bound clinical record, purchase-history or AI-profile access.
6. Keep platform operations, Edge nodes, payment providers, workers and MCP invocations as distinct principal classes. A permission string does not convert a machine principal into a human pharmacy role.

No proposed vocabulary addition in this section is approved for assignment or enforcement. Product, clinical and security owners must resolve the policy decisions before implementation.


## 9. RAG document lifecycle and data integrity

Source baseline: targeted source review of `main`, including the Celery ingestion task, the separate `IngestionOrchestrator`, `PgVectorStore`, the deduplication/versioning managers, the pgvector migration and the available RAG contract tests. This is a static source review; no database, worker, or integration test was executed.

### 9.1 Ingestion paths are not lifecycle-equivalent

The repository contains two distinct ingestion implementations:

- The active API ingestion path dispatches `src/pharmaviyum/ai/mortarium_rag/ingestion/tasks.py::ingest_document`. It loads, preprocesses, stamps tenant/source metadata, chunks, embeds and persists through `PgVectorStore.upsert()`.
- `IngestionOrchestrator.ingest_file()` additionally invokes `DocumentDeduplicator` and `DocumentVersionManager`.

The active Celery task does not invoke either lifecycle manager. Its metadata stamping reads a supplied `version` value but does not assign a managed `version_number` or `version_status`; it also does not run duplicate filtering. Therefore the existence of deduplication/versioning classes does not establish those guarantees for the API's active ingestion path.

**Required decision:** designate one production ingestion implementation and make every supported entry point use the same tenant authorization, provenance, idempotency, deduplication, version activation, failure recovery and deletion contract. Until then, treat lifecycle guarantees in the Celery path as absent.

### 9.2 Deduplication: tenant predicate exists, but fuzzy mode is not fuzzy

Positive control:
- `DocumentDeduplicator._strict_dedup()` compares exact `content_hash` values and includes `pharmacy_id` in the SQL predicate. A matching hash in another pharmacy is not considered a duplicate by this query.
- `DocumentPreprocessor` calculates a SHA-256 content hash from preprocessed/redacted content.

Gaps:
1. `DedupStrategy="fuzzy"` currently delegates to `_strict_dedup()`; it performs no embedding-similarity or other near-duplicate comparison.
2. Deduplication is read-then-filter, not protected by a database uniqueness constraint or transaction-level serialization. Concurrent ingestion requests can both observe no existing hash and both insert.
3. The deduplication query is not part of the active Celery task.
4. The deduplication helper's `get_duplicate_stats()` is global and does not accept a pharmacy scope. Do not expose its output to pharmacy users or use it as tenant-scoped reporting without an explicit authorization boundary.
5. The current chunk table has a unique constraint on `(document_id, chunk_index)`, but no uniqueness constraint on tenant plus document content hash.

**Required controls:** define the intended scope (same pharmacy only versus explicitly shared public reference documents), use a canonical source/document identity, make duplicate decisions concurrency-safe, and test both same-tenant deduplication and cross-tenant non-interference. Do not silently deduplicate across pharmacies.

### 9.3 Versioning and activation are incomplete

The separate `DocumentVersionManager` scopes `get_next_version()`, `archive_old_versions()`, `rollback_to_version()` and `get_version_history()` by both `source` and `pharmacy_id`. This is a useful tenant predicate.

However:
1. `get_next_version()` performs `MAX(version_number) + 1` without an evident row lock, advisory lock or unique version constraint. Concurrent ingestions for the same pharmacy/source can select the same version.
2. `IngestionOrchestrator` archives old versions before chunking, embedding and persistence of the new version have completed. Because `archive_old_versions()` commits independently, a later failure can leave the previous version archived without a successfully stored replacement.
3. `rollback_to_version()` archives currently active chunks before checking whether the target version exists. A nonexistent target can therefore leave the source with no active chunks; the method does not fail closed on a zero-row restore.
4. The version manager updates chunk metadata directly; there is no separate document-level lifecycle record or transaction coordinating version creation, chunk replacement and activation.
5. The active Celery ingestion path does not call the version manager.

**Required controls:** stage a new version without deactivating the current one; validate completeness and provenance; atomically activate the new version and archive the previous version; serialize version allocation; and make rollback validate the target before changing active state. A failed ingest must leave the last known-good version searchable.

### 9.4 Retrieval does not enforce active-version status by default

`PgVectorStore` builds retrieval predicates from the supplied metadata filters and validates the pharmacy/access-level boundary. It does not independently add `version_status = active` or exclude archived/deleted chunks. The version manager writes `version_status`, but that metadata is not, by itself, a retrieval control.

Consequently, archived or deleted-status chunks can remain eligible for retrieval unless every caller supplies a correct status filter. The current code does not establish a single mandatory active-document predicate shared by vector and BM25 search.

**Required controls:** enforce active status centrally in the vector store/query contract, apply the same predicate to vector, BM25 and hybrid retrieval, and test that archived/deleted versions cannot appear even when a caller omits the status filter. Define explicit behavior for documents with missing legacy status metadata before migration/backfill.

### 9.5 Upsert does not reconcile a document's complete chunk set

`PgVectorStore.upsert()` inserts or updates rows using `ON CONFLICT (document_id, chunk_index)`. It updates matching chunk content/metadata/embedding/token count but does not remove rows whose chunk indexes are no longer present in a replacement document.

If a previously indexed document becomes shorter or its chunking strategy changes, trailing chunks from the old content can remain in the table. Those stale chunks may still be retrieved and cited as if they belong to the current document version.

**Required controls:** replace a document's complete chunk set atomically (or use immutable version-specific document IDs and activate the new version only after all chunks are stored). Add regression tests for shorter replacements, changed chunk boundaries, partial batch failure and retry/idempotency.

### 9.6 Delete, purge and reindex contracts are not established

The reviewed `PgVectorStore` exposes upsert and retrieval operations but no tenant-checked document deletion/replacement API. The migration downgrade intentionally retains `document_chunks`, which is appropriate for a non-destructive schema rollback but does not implement a governed document deletion workflow.

The inspected code does not establish:
- a pharmacy-scoped soft-delete operation that immediately excludes a document from retrieval;
- a separately authorized hard-purge workflow with audit and retention checks;
- cascade handling for every chunk belonging to a document/version;
- safe reindexing that cannot expose a partial new index or erase the last good version;
- idempotent retry behavior for deletion and reindex jobs.

**Required controls:** separate logical retirement from irreversible purge; require an authorized tenant and immutable actor/job provenance; apply exact pharmacy + document identity predicates to every mutation; audit the decision; and test that deleting/reindexing one pharmacy's document cannot alter another pharmacy's chunks.

### 9.7 Source provenance and ingestion trust

The active worker stamps `pharmacy_id`, source, version, access level, country, language and document type from its configuration/document context before persistence. This protects those canonical fields from being accepted solely from arbitrary source metadata at that step. However, metadata stamping does not prove that the source is authentic, current, approved for the jurisdiction, or clinically valid. The current chunk schema also lacks a first-class document registry with source publisher, source URL/identifier, content digest, approval state, effective interval, ingestion actor, review actor and supersession relationship.

The Celery worker validates a positive pharmacy ID and tenant-scoped object-storage key, but it relies on the dispatch/broker boundary for the assertion that the supplied pharmacy was authorized. This review does not establish an independently verifiable actor authorization grant inside the worker.

**Required controls:** persist source provenance and approval state separately from untrusted document metadata; distinguish uploaded, quarantined, reviewed, approved, superseded and withdrawn states; retain source digest and jurisdiction/effective dates; and pass a verifiable tenant-scoped job authorization envelope to background execution.

### 9.8 Test coverage and release gates

The inspected RAG contract/security tests cover important metadata and retrieval-filter validation, but the targeted search did not identify dedicated tests proving the full lifecycle behavior above: concurrent deduplication/version allocation, cross-pharmacy dedup isolation, stale trailing-chunk removal, active-only retrieval, failed replacement rollback, missing-target rollback, tenant-scoped deletion, hard-purge authorization, and Celery-path lifecycle parity.

Before treating document lifecycle as production-safe, add database-backed tests for:
1. Two pharmacies ingesting identical content without cross-tenant suppression or mutation.
2. Concurrent ingestion of the same source within one pharmacy.
3. Shorter-document replacement and chunker-version changes without stale chunks.
4. Active-only retrieval across vector, BM25 and hybrid paths.
5. Failed embedding/storage leaving the previous version active.
6. Rollback to an existing and a nonexistent version.
7. Soft delete, authorized purge, retries and idempotency.
8. Forged or mismatched tenant/job authorization at the worker boundary.
9. Reindex and deletion isolation across two pharmacies.

No application source changes, database operations, migrations, CI runs or deployments were performed as part of this review.


## 10. RAG retrieval security and clinical source governance

Source baseline: targeted static review of `main`, including `LangGraphRAG`, the compatibility `RAGPipeline`, `PgVectorStore`, canonical schemas, active Celery ingestion, PDF/HTML loaders, chunk metadata propagation and targeted security/citation tests. No clinical validation, live retrieval, database query or application test run was performed.

### 10.1 Positive retrieval controls

The active LangGraph retrieval path has meaningful baseline controls:
- It constructs pharmacy-scoped filters from the immutable `QueryContext`.
- It searches public, pharmacy and (only when selected) exact-patient access-level filter sets.
- It includes a country equality filter when `QueryContext.country` is present.
- Vector and BM25 queries use the same metadata filter clause; hybrid search fuses those scoped result sets.
- The SQL filter builder validates metadata key identifiers and binds filter values as parameters.
- Retrieval failures are surfaced as a partial-retrieval warning; no unscoped retry path was identified in the inspected node.

These controls reduce tenant and query-scope risks. They do not establish that a retrieved document is clinically authoritative, current, approved or legally applicable.

### 10.2 Missing country must fail closed for jurisdiction-sensitive questions

`LangGraphRAG._build_filters()` adds `country` only when `QueryContext.country` is truthy. When country is absent, retrieval continues with pharmacy/access-level filters but without a jurisdiction predicate. The compatibility `RAGPipeline` always places the optional country value into its filter dictionary; a null value becomes SQL equality against NULL and ordinarily returns no matching rows, which is safer than silently omitting the filter but is not a consistent contract between the two pipelines.

The active Celery worker's `_stamp_tenant_metadata()` sets canonical `country` from worker config. If the config omits country, the stamped value is null even though the PDF and HTML loaders currently default their Document country to `VN`; the worker's explicit metadata update overrides that loader default. Therefore loader defaults do not guarantee a jurisdiction for active ingestion.

**Risk:** a country-unspecified request can retrieve documents from multiple jurisdictions within the same tenant. This is especially material for prescribing information, controlled medicines, contraindications, market authorizations and regulatory guidance.

**Required controls:** require a trusted pharmacy jurisdiction or explicit user-selected jurisdiction for jurisdiction-sensitive retrieval; do not infer it from language, user IP or model output. If jurisdiction is unknown, block jurisdiction-dependent conclusions or return a clarification/no-answer response. Define a reviewed exception policy for genuinely jurisdiction-neutral sources. Add tests for missing, mismatched and cross-jurisdiction country values in both LangGraph and compatibility pipelines.

### 10.3 Effective dates are schema fields, not retrieval enforcement

`CanonicalMetadata` defines `effective_from` and `effective_to` and validates that the end is not earlier than the start. The active worker stamps those values from ingestion config. However, the reviewed LangGraph filter builder does not include an effective-date predicate, and `PgVectorStore` applies only the filters it receives. No mandatory current-validity condition was identified in vector, BM25 or hybrid retrieval.

A document may therefore be retrieved after its stated end date, or before its effective start date, unless another caller supplies date filters. The schema also permits both dates to be absent. There is no reviewed policy defining whether undated sources are allowed for clinical use.

**Required controls:** define the business meaning of effective dates (including timezone and inclusive/exclusive boundaries); require dates where source type/regulation requires them; filter to the request's trusted effective date; and separate historical lookup from current clinical guidance. Test start boundary, end boundary, expired, future and undated documents. Historical documents must remain available only through an explicit historical-use path and be visibly labelled as historical.

### 10.4 No source approval or authority gate before generation

The relevance grader in `LangGraphRAG._grade_one()` asks an LLM whether a chunk is relevant to the question and returns YES/NO. It does not evaluate publisher authority, source approval, evidence quality, jurisdiction, supersession, publication date or clinical review status.

The canonical metadata schema contains source, version, effective dates, access level, country, language, category and document type, but no required `approval_status`, `reviewed_by`, `reviewed_at`, `publisher`, `evidence_grade` or `superseded_by` contract. The active worker stamps source and tenant context but does not establish source authenticity or clinical approval.

**Risk:** a syntactically valid, tenant-scoped and relevant document can still be an unreviewed upload, outdated webpage, unofficial summary or source from the wrong regulatory authority. Retrieval relevance is not evidence quality.

**Required controls:** introduce a controlled source-governance registry and lifecycle (for example: submitted, quarantined, under_review, approved, superseded, withdrawn, rejected). Define source-type-specific authority rules and clinical review ownership. Only approved and currently effective material should be eligible for clinical-answer retrieval by default. Quarantined/unreviewed sources may be searchable only in a separately labelled administrative review workflow, never silently mixed into pharmacist answers. Approval and withdrawal actions require actor, timestamp, rationale and audit trail.

### 10.5 Citation ID validation is not claim-to-evidence validation

Positive control: the LangGraph pipeline validates that cited `[src-UUID]` identifiers belong to the retrieved source set. If there are no sources or the answer has missing/fabricated citation IDs, the inspected validation path returns a fail-closed response and warning. The `RAGResponse` schema also constructs citation objects tied to chunk/document UUIDs.

Limitations:
1. `_validate_answer_citations()` accepts the answer when at least one citation is present and every detected citation ID is in the allowed set. It does not establish that every factual/clinical claim has a citation.
2. It does not verify that a cited chunk entails or supports the specific adjacent claim, dosage, strength, contraindication or regulatory statement.
3. `SourceCitation` standardizes source name, document/chunk IDs, optional version and retrieval score, but not a required resolvable source URL, publisher, page/section locator, jurisdiction or effective date. Some loaders preserve page/URL in arbitrary metadata, but there is no mandatory typed citation locator contract.
4. Citation validation confirms membership in retrieved results, not source approval, freshness or clinical correctness.
5. The compatibility `RAGPipeline` builds prompt citations but does not call the LangGraph `_validate_answer_citations()` method in its inspected query/query_stream path. Its optional guardrail behavior is not equivalent to the LangGraph citation gate.

**Required controls:** use structured claim/evidence associations; require every clinical claim to map to one or more exact evidence spans; verify source authority and current validity before citation acceptance; expose a resolvable source/version/page/section locator; and ensure sync, streaming, compatibility and agent-harness paths share one citation-validation contract. Citation validation failure must not stream an unvalidated clinical answer to the user.

### 10.6 Retrieval confidence is not clinical confidence

The compatibility pipeline computes confidence as the arithmetic mean of retrieval scores. The LangGraph pipeline returns a state confidence value, but the inspected retrieval/relevance path does not establish a calibrated clinical confidence model. Similarity, BM25 and relevance-grader outputs indicate retrieval relevance, not truth, source quality or patient-specific safety.

**Required controls:** do not label retrieval similarity as clinical confidence. Keep retrieval score, source-quality assessment, evidence sufficiency and answer-validation status as separate fields. Calibrate any user-facing confidence only against reviewed clinical evaluation datasets and use conservative abstention rules.

### 10.7 Source provenance and page anchors

PDF loading captures page number and document metadata; HTML loading captures URL and title; the chunker copies document metadata into chunk metadata. This is a useful start. However, those fields remain loosely typed arbitrary metadata, and the standard `SourceCitation` does not require a stable locator. A local file path or mutable web URL alone does not prove immutable source identity or exact version.

**Required controls:** retain immutable source identity and content digest, publisher/issuing authority, canonical URL or repository identifier, retrieved-at timestamp, published/revised date, jurisdiction, language, effective interval, document version and page/section/span locator. Store the original source snapshot or a controlled immutable reference where licensing permits. A citation must resolve to the exact source revision used for generation, not merely the current page at the same URL.

### 10.8 Public access label does not mean globally shared source

The retrieval filter sets include `access_level="public"`, but still carry the authenticated `pharmacy_id`; canonical metadata requires a positive pharmacy ID for all access levels. Thus the current implementation does not establish a globally shared public corpus. The word `public` describes an access class within the current tenant-keyed storage contract, not proof of cross-tenant public visibility.

**Required decision:** either document this as tenant-local public material, or design a separate explicitly global reference-source scope with its own provenance, authorization and storage constraints. Do not remove pharmacy filters or treat public metadata as a bypass. Add tests that prove the chosen semantics.

### 10.9 Required clinical source-governance tests

Before enabling clinical-answer use of imported or uploaded reference material, add deterministic tests for:
1. Missing jurisdiction on a jurisdiction-sensitive query fails closed or requests clarification.
2. A UA request cannot retrieve VN-only or other jurisdiction-specific guidance unless an approved cross-jurisdiction rule explicitly permits it.
3. Future-effective and expired documents are excluded from current guidance; historical lookup is separately labelled.
4. Unreviewed, quarantined, rejected, withdrawn and superseded documents cannot enter the default clinical evidence set.
5. An approved source is traceable to publisher, exact version/digest, jurisdiction, effective dates and review decision.
6. Each clinical claim is linked to evidence that supports that claim; a single valid citation cannot legitimize unrelated uncited claims.
7. Fabricated IDs, wrong-source IDs, stale-source IDs and unresolved locators fail closed.
8. PDF page and HTML URL citations resolve to the exact ingested snapshot/revision.
9. LangGraph, compatibility pipeline, streaming and agent harness enforce equivalent citation and source-eligibility rules.
10. Retrieval score is not presented as calibrated clinical confidence.

No application source changes, database operations, migrations, CI runs or deployments were performed as part of this review.


## 11. RAG evaluation implementation and clinical quality assurance

Source baseline: static review of `RagasEvaluationAdapter`, `clinical_metrics.py`, their unit tests, the golden-dataset tests, `pyproject.toml` and the `rag-evaluation` CI job. No test suite, Ragas judge model, benchmark, retrieval workload or clinical validation run was executed during this review.

### 11.1 Positive controls

- Ragas 0.4.3 is isolated in the optional `eval` dependency group and loaded lazily by the adapter; it is not required by the production request path.
- The adapter exposes Faithfulness and AnswerRelevancy, and conditionally ContextPrecisionWithReference and ContextRecall when a reference answer is supplied.
- Missing contexts and missing reference answers are represented as unavailable scores rather than silently converted to zero.
- AnswerRelevancy accepts its documented negative cosine-similarity range; normalized metrics are range-checked.
- Project-specific evaluators exist for citation support, medication name/strength/form F1, negation polarity, clinical hallucination rate, patient-context isolation and Russian/English gold-source recall.
- The CI workflow contains a dedicated RAG evaluation job, installs the `eval` group, checks the Ragas Collections imports and invokes the evaluator unit tests and golden-dataset schema tests.

### 11.2 P1 — Patient-isolation evaluator exempts tenant-local public sources from pharmacy matching

`patient_context_isolation()` immediately skips every source whose `access_level` is `public`, before checking its `pharmacy_id`. The documented storage/retrieval contract says that the current `public` class remains pharmacy-keyed (tenant-local), not globally shared.

A source marked `public` with another pharmacy's ID can therefore pass this evaluator without a scope violation. This creates a false negative in a security regression metric.

**Required correction:** enforce the expected pharmacy scope for every source under the current tenant-keyed contract, regardless of `access_level`. If a future global reference corpus is introduced, represent it with an explicit global scope/type and a separately tested authorization rule; do not overload tenant-local `public`. Add tests for same-tenant public, cross-tenant public, pharmacy-private and exact-patient sources.

### 11.3 P1 — Clinical metric functions are not wired into an evaluation runner

The targeted repository search found the pharmaceutical metric functions referenced by their definitions and unit tests, but did not identify a benchmark/evaluation runner that invokes them for a dataset of generated LangGraph RAG responses. Likewise, the Ragas adapter is exercised by isolated unit tests; the existing golden-dataset tests validate dataset structure and the legacy benchmark tests use mocked harness/evaluator responses.

The CI job therefore provides dependency/API and deterministic contract coverage, not evidence that the active RAG pipeline has been evaluated end to end with Ragas or the clinical metrics.

**Required correction:** implement a separate offline evaluation command/runner that:
1. loads a versioned synthetic or de-identified dataset;
2. invokes the same retrieval and answer-generation path used by the target application, under a controlled evaluation configuration;
3. preserves retrieved source IDs, metadata, language and jurisdiction;
4. supplies independent pharmacist-reviewed reference labels and a separately configured judge;
5. runs Ragas and all applicable domain metrics;
6. emits per-case results plus aggregate metrics, dataset/model/prompt/embedding/index versions and reproducible artifacts;
7. fails the run on missing required metrics or security-critical violations rather than treating missing values as passes.

Do not send live patient data or PHI to external judge models.

### 11.4 P1 — Citation correctness is sentence-split, not atomic claim-to-evidence evaluation

The current evaluator splits text on sentence-ending punctuation and treats each resulting non-empty sentence as a factual claim. It then accepts the sentence if at least one citation ID resolves to a supplied source and at least one cited source passes the entailment judge.

This does not reliably isolate atomic claims. A sentence containing multiple clinical propositions can pass when the source supports only one proposition. A sentence with multiple citations can also pass when only one cited source supports the claim, leaving other attached citations unchecked. Sentence splitting is not robust to abbreviations, structured lists or other answer formatting.

**Required correction:** evaluate atomic factual/clinical claims, preserve each claim's exact citation associations, validate every citation reference, and record claim-level entailment outcomes. Add adversarial tests for two claims in one sentence, one citation supporting only one claim, unsupported extra citations, fabricated IDs, bullet lists, abbreviations and uncited clinical clauses. Keep the judge unavailable state explicit.

### 11.5 P2 — Negation and medication metrics depend on externally prepared predictions

The negation evaluator compares two booleans supplied in `NegationExpectation`; it does not extract proposition polarity from the generated answer. Medication accuracy compares pre-structured `MedicationEntity` triples; it does not extract medication entities from the generated answer. This is valid as a scoring primitive, but the inspected unit tests do not establish the upstream annotation/extraction pipeline or its independence from the answer under evaluation.

The medication tuple currently covers exact name, strength and dosage form only. It does not independently score active ingredient, concentration, dose, route, frequency or duration.

**Required correction:** define and test an independent, reproducible annotation/extraction stage with pharmacist-reviewed gold labels, explicit normalization/equivalence rules and adjudication. Report name, strength, dosage form and other clinically material fields separately; a correct name must not compensate for an incorrect strength, dose or route.

### 11.6 P2 — Russian/English metric measures only gold-source recall

`multilingual_retrieval()` calculates recall over supplied expected and retrieved source IDs, with the language passed as an argument. It does not verify the language of the query, retrieved document, answer or reference, and it does not measure language-specific context precision, answer relevancy, faithfulness or medication terminology quality.

The unit tests demonstrate arithmetic for labels `ru` and `en`, not that production ingestion and retrieval support Russian content end to end.

**Required correction:** build balanced pharmacist-reviewed RU/EN datasets; validate language labels and cross-language cases; report retrieval Recall@K/MRR/nDCG and context precision/recall per language; evaluate answer faithfulness, citation support, medication terminology and safe abstention per language. Keep ingestion/retrieval language support as a separately verified capability.

### 11.7 P2 — Current tests prove contracts, not clinical quality thresholds

The Ragas adapter test replaces all Ragas metric classes with a fake metric returning a fixed score. The CI import check validates that the pinned Ragas API is importable, but does not execute a real evaluator LLM/embedding pair. Golden-dataset tests check that cases exist and required fields are present; they do not establish expert-reviewed coverage, dataset balance, statistical confidence or clinically justified release thresholds.

**Required correction:** retain fast mocked unit tests, and add a separately scheduled/manual judge-backed evaluation against a versioned pharmacist-reviewed dataset. Record raw per-case outcomes, sample size, confidence intervals where appropriate, judge/model versions and reproducibility metadata. Clinical thresholds must be set by qualified reviewers; do not invent universal pass percentages. Patient isolation, wrong medication strength/form, negation loss and unsupported high-risk claims must remain non-compensatory release blockers.

### 11.8 Evaluation status

- Ragas dependency isolation: **implemented in configuration; CI execution not re-run in this audit**.
- Ragas adapter: **implemented; unit tests mock the metric classes**.
- Pharmaceutical metric primitives: **implemented; end-to-end runner integration not established**.
- Golden dataset: **present and structurally tested; pharmacist review and clinical representativeness not established**.
- Real judge-backed Ragas/clinical benchmark: **not measured in this audit**.
- Russian production retrieval quality: **not established by source-ID arithmetic tests**.
- Patient isolation evaluator: **contains the tenant-local public-source false-negative described above**.
- Clinical release thresholds: **not established by measured, expert-reviewed evidence**.

No application source changes, database operations, migrations, CI runs or deployments were performed as part of this review.


## 12. Russian/English multilingual RAG end-to-end audit

Source baseline: static inspection of `RAGSettings`, the active Celery ingestion task, loader configuration, tenant metadata stamping, embedding providers/router, `LangGraphRAG`, `PgVectorStore` BM25/hybrid retrieval and targeted search results. No document ingestion, embedding API call, database retrieval, OCR run or language benchmark was executed.

### 12.1 Positive controls

- `RAGSettings.default_languages` includes `ru` and `en`.
- `QueryContext.language` is propagated into LangGraph query transformation and answer-language instructions.
- LangGraph adds `_search_language` to retrieval filters; the vector store removes this control key before SQL metadata filtering and passes it to BM25.
- PostgreSQL BM25 uses `english` text search configuration for English and `simple` for other languages. The `simple` configuration avoids applying English stemming to Russian, but does not provide Russian morphology/lemmatization.
- The repository contains a language-aware embedding router abstraction and a separate retrieval benchmark script. Their presence does not establish that the active ingestion and request paths use them.

### 12.2 P1 — Active ingestion defaults omit Russian from loader languages

The Celery worker constructs `LoaderConfig.languages` with a default of `["vi", "en", "ar", "th", "id"]`. The central `RAGSettings.default_languages` includes Russian, but the active worker does not derive its loader language list from that setting.

When callers omit an explicit `languages` value, the active ingestion loader therefore receives no Russian language entry. This can affect OCR or language-aware document extraction for Russian documents, depending on loader behavior.

**Required correction:** establish one canonical supported-language configuration and use it in the active worker. Add Russian to the default only after verifying each loader/OCR backend's actual language-code contract. Add PDF/DOCX/HTML ingestion tests for Russian Cyrillic, English, mixed RU/EN documents and OCR fallback; verify extracted text and language metadata rather than merely checking configuration values.

### 12.3 P1 — Worker metadata stamping defaults every unspecified document to English

`_stamp_tenant_metadata()` uses `config.get("language", "en")` and explicitly overwrites both document language and canonical metadata language. The loader's detected or source-provided language is therefore not preserved when the ingestion request omits `config.language`.

A Russian document ingested without an explicit language can be stamped as English. This can corrupt language-aware filtering, evaluation segmentation and downstream analytics even if the text itself remains in Cyrillic.

**Required correction:** define trusted language provenance and precedence. Prefer a validated explicit ingestion language when supplied; otherwise use a reliable loader-level detection result or mark language as unknown/mixed. Do not silently default unknown documents to English. Add tests proving Russian loader output is not overwritten by the worker default and that caller-controlled untrusted metadata cannot override the canonical language decision.

### 12.4 P1 — Multilingual embedding router excludes Russian and is not wired into active paths

`LANGUAGE_MODEL_MAP` in `embeddings_multilang.py` defines `vi`, `ar`, `th`, `id`, `en` and `mixed`, but no `ru`. `detect_language()` likewise maps only those languages and returns `mixed` for Russian. Short text samples under 20 characters are classified as English without detection.

Repository search found the router exported by the AI package, but did not identify a production call site in active Celery ingestion, `IngestionOrchestrator`, or the LangGraph request path. The router therefore cannot be treated as the active multilingual embedding strategy.

**Required correction:** make an explicit architecture decision for one consistent multilingual embedding model versus language-specific models. If routing remains, add Russian and mixed-language handling, remove the unconditional short-text English assumption (or mark low-confidence/unknown), and wire the same deterministic model/version selection into both document ingestion and query embedding. Persist embedding model ID, model revision, dimensions and preprocessing version with the index. Do not mix incompatible embedding spaces in one vector index; model changes require a versioned index and controlled re-embedding/reindex strategy.

### 12.5 P1 — Active ingestion and query use a single configured embedding provider, not language routing

The active Celery task constructs one provider using the configured Gemini/OpenAI/Ollama backend and embeds every chunk through that provider. `AIComponents.initialize()` similarly creates one embeddings provider for LangGraph queries. The language-aware router is not injected into either path.

A single multilingual model could be a valid design, but the current default Ollama model is `mxbai-embed-large`, and no inspected code or benchmark establishes that this model is suitable for Russian/English cross-lingual pharmacy retrieval. Provider choice alone is not evidence of multilingual capability.

**Required correction:** choose and pin an embedding model with documented RU/EN support; validate it on the actual pharmacy corpus and cross-lingual queries. Ensure ingestion and query use the exact same model family, revision, dimensions, normalization and query/document instruction conventions. Record the model identity alongside each indexed chunk and reject incompatible query vectors/indexes.

### 12.6 P2 — BM25 simple configuration is safe from English stemming but not a Russian linguistic analyzer

The vector store selects PostgreSQL `simple` for every language other than English. This avoids inappropriate English stemming, but `simple` tokenization does not normalize Russian inflections, grammatical cases, word forms or common morphology. A query using one form of a Russian medication-related term may fail to match a document using another form.

**Required correction:** benchmark `simple` against an explicitly selected Russian-aware lexical analyzer or a domain-specific normalization strategy. Preserve exact drug names, INN/active ingredients, strengths, dosage forms and Cyrillic/Latin transliterations. Add adversarial cases for inflections, ё/е, hyphenation, abbreviations, brand/generic names and transliteration. Do not apply aggressive normalization to dosage strings or clinically meaningful negation.

### 12.7 P2 — Query language defaults to English unless explicitly supplied

`QueryContext.language` defaults to `en`. LangGraph uses the context language for BM25 configuration and answer instructions. The inspected contract does not itself establish reliable request-language detection or prove that the API always supplies a validated language matching the user's actual query.

If a Russian query reaches the RAG path with the default context, BM25 may use English configuration and answer instructions may request English. This is a contract/integration risk; actual API propagation requires an end-to-end test.

**Required correction:** define a trusted language-resolution policy at the request boundary. Validate explicit user/application language, detect the query language when absent, handle mixed RU/EN queries and short medication-name-only queries conservatively, and pass one resolved language through query transformation, retrieval, answer generation and evaluation. Language must never be inferred from jurisdiction or patient identity.

### 12.8 P1 — No end-to-end evidence for Russian retrieval or cross-lingual pharmacy queries

The inspected evaluator measures recall over supplied source IDs and a language label; it does not execute the embedding, ingestion, BM25/vector/hybrid retrieval or answer-generation paths. The separate retrieval benchmark script exists, but no inspected RU/EN result artifact establishes representative Russian corpus coverage, Russian Recall@K, ranking quality or clinical answer support.

**Required correction:** create a versioned synthetic/de-identified RU/EN benchmark with pharmacist-reviewed gold sources and queries covering:
1. Russian query to Russian source.
2. English query to English source.
3. Russian query to English source and vice versa, where clinically appropriate.
4. Cyrillic, Latin transliteration, INN and brand-name variants.
5. Medication name + strength + dosage form + route.
6. Negation, contraindication, interaction and dosage statements.
7. OCR-derived Russian PDFs and mixed-language documents.
8. Missing/ambiguous language and safe abstention.

Report per-language and cross-language Recall@K, MRR/nDCG, context precision/recall, answer faithfulness, citation entailment, medication entity accuracy and negation preservation. Keep source approval, jurisdiction, effective date and tenant/patient scope checks enabled in the benchmark.

### 12.9 Multilingual readiness status

- Russian listed in central RAG defaults: **configured, but not consistently applied by active ingestion**.
- Russian loader/OCR language configuration: **not present in the active worker default**.
- Russian canonical document language: **at risk of being overwritten to English when config.language is absent**.
- Russian embedding router: **not supported by the router map/detector**.
- Router connected to active ingestion/query paths: **not established; targeted search found no call site**.
- One provider used for active ingestion and query: **implemented; RU/EN suitability not measured**.
- Russian BM25: **uses PostgreSQL simple configuration; morphology quality not established**.
- RU/EN end-to-end retrieval quality: **not demonstrated by the inspected metric unit tests**.
- Clinical-grade Russian support: **not established**.

No application source changes, database operations, migrations, CI runs or deployments were performed as part of this review.


## 13. Document parsing, OCR, pharmaceutical chunking and compression

Source baseline: static inspection of the active Celery ingestion path, `TextNormalizer`, `MedicalChunker`, PDF/DOCX/HTML loaders, RAG schemas, LangGraph compression node and `ContextualCompressor`, plus existing unit tests and chunking design documentation. No PDF/DOCX ingestion, OCR engine, external LLM, embedding, database operation or benchmark was executed.

### 13.1 P1 — Preprocessing removes line boundaries required by medical section detection

`TextNormalizer.WHITESPACE_PATTERN` matches all whitespace, including newlines, and `normalize()` replaces those sequences with a single space before attempting the `"- \\n"` hyphenated-line-break repair and newline collapsing. Consequently, the later newline-specific operations cannot recover the original line/paragraph boundaries.

The active ingestion path runs `DocumentPreprocessor.process()` before `MedicalChunker.chunk()`. The medical chunker detects section headings by iterating over `document.content.split("\\n")`; it also ignores candidate heading lines longer than 100 characters. After preprocessing has flattened line breaks, a multi-section document is likely to be treated as one long line and the section heading detector will not recognize its headings.

**Impact:** the default `medical` strategy may silently degrade into generic splitting; headings and the relationship between section labels and their content are not reliably preserved.

**Required correction:** normalize whitespace while preserving paragraph and line boundaries; repair hyphenated line breaks before generic whitespace normalization; preserve structural separators from PDF/DOCX/HTML. Add an integration test that passes a multi-section source through the exact preprocessor → chunker sequence and asserts that dosage, indications, contraindications and interactions remain distinct and correctly typed.

### 13.2 P1 — Chunk token budget is a character heuristic, not a tokenizer budget

`MedicalChunker._count_tokens()` returns `len(text) // 4`. This is not the tokenizer for the configured embedding or generation model and can substantially misestimate token counts across Cyrillic, Latin drug nomenclature, Arabic, Thai, tables, numeric strings and mixed-language content.

The overlap implementation also slices the previous chunk using `overlap_tokens * 4` characters. This is only a rough character window; it can start or end inside a clinically meaningful expression, dosage value, unit, table row or negation clause. The medical strategy's overlap is based on the prior part's trailing characters rather than sentence/structure-aware context.

**Required correction:** use the exact configured tokenizer or a conservative model-aware token counter, persist tokenizer/model version, and implement overlap at sentence/paragraph/row boundaries. Add tests with long Cyrillic and mixed RU/EN passages, dosage strings, decimals, units, abbreviations and long unbroken tokens. Enforce a hard upper bound using the actual target tokenizer.

### 13.3 P1 — PDF OCR fallback misses partially scanned pages and Russian OCR language

The PDF loader calls OCR only when `page.get_text("text").strip()` is empty. A page with a small amount of selectable text plus scanned image regions will not receive OCR, so missing medication tables, warnings or dosage text can be silently omitted.

The OCR language map contains `vi`, `en`, `ar`, `th` and `id`, but not `ru`. An unsupported language code falls back to `eng`, so a Russian-only OCR configuration can invoke English Tesseract data instead of Russian. OCR exceptions are caught and converted to an empty string; the page is then skipped if no text remains.

**Required correction:** support page/region-level OCR for partially scanned pages, explicitly map Russian to the installed Tesseract language pack, verify requested OCR language availability at startup, and distinguish OCR failure from genuinely empty pages. Emit structured per-page ingestion warnings/status and do not mark a document complete when clinically relevant pages failed extraction. Add fixtures for text PDFs, scanned RU PDFs, mixed RU/EN pages, partially scanned pages and OCR failure.

### 13.4 P1 — PDF table extraction is flattened and failures are silently swallowed

PDF table extraction converts each detected table to Markdown and appends it to the page text. Exceptions are caught and only logged at debug level; the loader continues with ordinary page text. The ingestion task does not establish a table-extraction completeness gate or a durable warning in the resulting document metadata.

The chunker subsequently splits the combined page content using generic text separators. There is no table-aware chunk boundary or contract guaranteeing that a header remains attached to every row/value fragment. A long table may be split across chunks, leaving numeric values without their column labels or medication identity.

**Required correction:** preserve tables as structured objects with table ID, page, header cells, row IDs and cell coordinates; repeat required headers when serializing bounded row groups; keep each dosage/value row with its medicine identity and units. Record extraction errors and table counts in job outcomes. Add PDF fixtures for multi-page tables, merged cells, repeated headers, decimal values, strength/unit columns and extraction failures. Do not silently treat table-extraction failure as a complete successful parse.

### 13.5 P1 — DOCX table structure and paragraph heading hierarchy are flattened

The DOCX loader appends paragraphs as plain text and converts each table row into a pipe-separated string. It does not preserve paragraph style/heading level, section hierarchy, table identity, header-row semantics, cell coordinates or relationships between a table and its surrounding explanatory text. The full DOCX is emitted as one Document, then passed through generic normalization and chunking.

**Required correction:** preserve DOCX heading styles and hierarchy, paragraph/table order, table IDs, header rows, cell coordinates and relevant neighboring context. Add fixtures for nested headings, merged cells, multi-page tables, repeated headers, lists and dosage/contraindication tables. Confirm that chunks preserve the table's medicine identity, strength, form, route and unit associations.

### 13.6 P1 — Parent-child chunk retrieval is a target design, not an implemented contract

The chunking design documentation describes parent-child retrieval as a target capability. The inspected `Chunk` schema has no `parent_chunk_id`, parent section record, child-to-parent relation or source span offsets. The active chunker creates independent chunks with document ID and chunk index only. The inspected retrieval schema and active LangGraph flow operate on retrieved chunks; no parent expansion stage was found.

**Required correction:** do not claim parent-child retrieval as implemented. If adopted, add versioned parent/child identity and source offsets, enforce the same tenant/patient/jurisdiction/effective-date filters on parent expansion, cap expanded context, preserve exact child citations, and test cross-tenant/cross-patient parent access denial. A child retrieval must never authorize an unfiltered parent fetch.

### 13.7 P1 — Contextual compression lacks Russian-specific instruction

The active LangGraph `compress_node` passes `ctx.language` to `ContextualCompressor`. The compressor's language instruction map includes Vietnamese, Arabic, Thai, Indonesian and English, but no Russian. Unknown languages fall back to the English instruction. The final generation node has an explicit Russian instruction, but this does not correct the earlier compression/judging stage.

**Impact:** for Russian queries, sentence relevance scoring is prompted in English even though the source sentences may be Russian. This can lower selection quality or remove relevant clinical evidence before answer generation.

**Required correction:** add Russian instructions and evaluate compressor sentence selection on pharmacist-reviewed RU/EN cases. Compare evidence before and after compression for medication identity, strength, form, dose, route, negation, contraindications, conditions and warnings. Consider a fail-open-to-original-evidence policy when the scorer fails or returns malformed/incomplete indices; do not let an unvalidated scorer silently discard clinical qualifiers.

### 13.8 P1 — Compression can remove clinically decisive evidence without a preservation gate

For chunks with more than the configured sentence count, the compressor selects up to three sentences using an LLM relevance score. If no sentence reaches the threshold, it still retains the top two scored sentences. There is no deterministic preservation check for medication name, strength, units, dosage form, route, negation, exception/condition clauses or warning language before compressed text is passed to generation.

The compressor preserves the original chunk citation ID, but citation identity alone does not prove that the retained sentence still supports all claims made from that source.

**Required correction:** introduce domain-aware protected spans/clauses and a post-compression evidence-integrity check. Keep medication/dose/route/units, negation, conditions, contraindications and warnings attached to their supporting statement. If integrity cannot be established, pass the original chunk or abstain from compression. Add adversarial tests where the highest-scoring sentence omits a negation, exception, unit or dosage qualifier.

### 13.9 P2 — Sentence splitting and fallback compression are not clinically validated

The compressor uses punctuation-based sentence splitting and filters fragments shorter than 11 characters. This can mishandle abbreviations, bullet lists, table rows, decimal/unit expressions and structured labels. The lexical fallback uses exact whitespace-token overlap and does not normalize Russian inflections, transliteration or pharmaceutical synonyms. It may rank semantically relevant RU/EN sentences poorly.

**Required correction:** use structure-aware sentence segmentation and preserve list/table boundaries; test abbreviations, decimals, units, Cyrillic/Latin drug names, bullets and multilingual clauses. Measure fallback retrieval/compression quality separately and record when fallback scoring was used.

### 13.10 Test coverage and readiness status

- Preprocessor preserves paragraph/section boundaries through the active ingestion path: **not established; current normalizer flattens whitespace**.
- Medical section chunking: **implemented as heading heuristics, but vulnerable to preprocessing boundary loss**.
- Exact tokenizer-based chunk budgets: **not implemented; character/4 estimate is used**.
- Pharmaceutical-aware overlap: **not implemented; character-slice overlap is used**.
- PDF OCR: **blank-page fallback exists; partial-page OCR and Russian mapping are missing**.
- PDF table extraction: **basic Markdown conversion exists; structured table integrity and failure gate are not established**.
- DOCX parsing: **paragraphs and pipe-separated tables extracted; heading/table structure is flattened**.
- Parent-child retrieval: **documented as target architecture, not implemented in inspected schema/path**.
- Russian contextual compression: **not configured; English fallback is used**.
- Compression preservation of dose/units/negation/conditions: **no deterministic integrity gate established**.
- End-to-end RU/EN document parsing and clinical chunk quality: **not demonstrated by the inspected unit tests**.

No application source changes, database operations, migrations, CI runs or deployments were performed as part of this review.


## 14. Retrieval and ranking quality

Source baseline: static inspection of active `AIComponents.initialize()`, `LangGraphRAG`, `PgVectorStore`, query transformation, PostgreSQL/pgvector Alembic migration, retrieval unit tests and the offline retrieval benchmark runner/dataset. No benchmark was executed during this audit; no live model, embedding provider, database or deployment was invoked.

### 14.1 Implemented retrieval path

The active path is:
1. Retain the original user query.
2. Generate up to the configured number of Multi-Query variations and optionally one HyDE query.
3. Embed each query using the single active embedding provider.
4. For each query and each authorized access-level filter set, run vector and PostgreSQL full-text search in parallel.
5. Fuse vector and BM25 result lists with Reciprocal Rank Fusion (RRF).
6. Deduplicate chunks across query/filter variants and retain up to `max_context_docs`.
7. Apply LLM relevance grading, bounded rewrite retries, contextual compression and answer generation.

The production pgvector migration creates an HNSW index using `vector_cosine_ops`, `m=16` and `ef_construction=200`. Vector SQL orders by cosine distance; PostgreSQL full-text search uses `english` for English and `simple` for other languages. Hybrid search retrieves up to `2 * top_k` candidates from each of vector and BM25 before RRF and returns at most `top_k` fused candidates per query/filter call.

### 14.2 P1 — No active reranker despite declared reranking configuration

`PgVectorStore` accepts an optional `RerankerPort`, but the active `AIComponents.initialize()` constructs it without a reranker. No concrete reranker implementation or runtime factory/injection was found in the active construction path. `RAG_RERANK_TOP_N` is declared in configuration but is not passed into runtime construction. The optional reranker exception handler also falls back to fused results without surfacing a retrieval warning if a reranker is supplied later and fails.

**Impact:** current ranking is RRF-only. There is no active cross-encoder or other dedicated semantic reranking stage to refine the fused candidates against the original user question.

**Required correction:** evaluate a reranker on the same pharmacist-reviewed benchmark before adopting one. If adopted, inject it explicitly, wire its top-N setting, emit a bounded warning/metric on failure and define whether fallback is acceptable for each clinical query class. Do not claim reranking is active today.

### 14.3 P1 — Russian query transformation falls back to English

`QueryContext.language` is passed into the active query transformer, but the language-instruction maps in `QueryTransformer.transform_with_hyde()` and `generate_multi_query()` contain `vi`, `ar`, `th`, `id` and `en`, not `ru`. Unknown languages use the English instruction.

**Impact:** for a Russian request, the original Russian query is retained (a useful safeguard), but Multi-Query and HyDE may generate English retrieval text. This can be harmful when the indexed corpus is Russian-only, terminology is jurisdiction-specific, or cross-lingual embedding quality is not established.

**Required correction:** add explicit Russian transformation instructions and test RU-only, EN-only and mixed-language corpora. Assert preservation of drug name, active ingredient, strength, dosage form, units, negation, route and patient-context qualifiers in every generated variant. Track retrieval results by original and transformed query separately.

### 14.4 P1 — LLM document grading sees only the first 800 characters of each chunk

`LangGraphRAG._grade_one()` sends `hit.chunk.content[:800]` to the relevance classifier. Chunks can be larger than this excerpt under the configured chunk budget. A relevant dosage, warning, interaction or contraindication appearing later in a chunk is invisible to the grader, which can reject an otherwise relevant retrieved result.

The grading decision is also binary: a candidate is retained when the model response starts with `YES`. There is no structured relevance score, evidence-span output or clinical-field coverage check.

**Required correction:** grade the complete bounded chunk or a structure-aware excerpt that includes the relevant section/title and all protected clinical spans. Return structured relevance plus supporting span(s); validate output schema and test cases where the only relevant information appears near the end of a chunk. Measure grader false-negative rate separately for dosage, interactions, contraindications and negation queries.

### 14.5 P2 — No retrieval relevance threshold or calibrated score semantics

The active graph does not apply a configured minimum vector similarity or calibrated relevance threshold before document grading. The declared `RAGSettings.similarity_threshold` is passed to `PromptCache`, not to vector retrieval. Vector search converts `1 - cosine_distance` into a bounded [0, 1] value; RRF then replaces raw similarity with a rank-fusion score. These values are different score semantics and neither is a calibrated probability of clinical relevance.

**Required correction:** keep vector similarity, RRF score, reranker score and calibrated relevance as separately named fields. Establish thresholds only from a labelled corpus and evaluate abstention/false-negative trade-offs. Do not interpret RRF score as confidence.

### 14.6 P2 — RRF and reranking settings do not fully control the runtime

`RAG_RRF_K` is declared but is not passed from `AIComponents.initialize()` to `PgVectorStore.hybrid_search()`; the method default `rrf_k=60` is used. `RAG_RERANK_TOP_N` is also not an effective setting because no reranker is injected. Existing architecture documentation already records these ineffective controls; this retrieval review confirms the active call path.

**Required correction:** either wire and contract-test the settings or remove them from environment templates until they have effect. Add tests that modify each supported setting and assert the runtime search arguments change.

### 14.7 P2 — Multi-query fan-out increases retrieval work, but fusion is local to each query

Each query variant is searched independently. Each `hybrid_search()` performs its own vector/BM25 fusion, after which `retrieve_node()` deduplicates across variants and retains the highest per-call score for each chunk. It does not perform a second rank-fusion across the original query, Multi-Query variants and HyDE results.

With up to the original query + configured Multi-Query variants + one HyDE query, and two or three access-level filter sets, the graph can fan out to multiple hybrid searches per request. The concurrency semaphore bounds active calls, but does not itself reduce total search count.

**Impact:** a chunk consistently retrieved across several independent query formulations does not receive an explicit cross-query consensus boost. Query variants can also increase latency and database load without a measured gain in clinical recall.

**Required correction:** compare current max-score deduplication with a second-stage rank fusion across query variants. Report recall, nDCG, MRR, p50/p95 latency and candidate count by query strategy; retain only transformations that improve measured quality.

### 14.8 P1 — Existing retrieval benchmark is not a clinical medication benchmark or full RAG evaluation

The repository includes `scripts/evaluate_rag_retrieval.py` and an expanded manually labelled synthetic pharmacy-operations SOP dataset. It exercises the `PgVectorStore.hybrid_search()` path against an isolated disposable schema, includes cross-tenant decoy chunks, and reports retrieval metrics (Recall@K, Precision@K, MRR, nDCG) and latency percentiles. The runner explicitly excludes LLM generation, answer groundedness, citation precision/recall, provider token cost and production-scale throughput.

The inspected benchmark queries and corpus are English pharmacy operations/SOP content (e.g. receiving, cold chain, returns, stock count, privacy and dispensing workflow). It does not establish medication-reference retrieval quality for drug monographs, active ingredients, strength/form/route/dose, drug interactions, contraindications, clinical negation, Russian morphology or RU↔EN cross-language retrieval. It also tests the vector-store hybrid search directly, not the full active LangGraph pipeline with Multi-Query, HyDE, grading, rewrite and compression.

**Required correction:** keep the existing SOP benchmark for workflow retrieval, but create a separate pharmacist-reviewed synthetic/de-identified medication benchmark. Include exact drug entities, ingredient synonyms, brand/generic pairs, strength/unit/form/route, dosage and frequency, contraindications, interaction pairs, explicit negation, jurisdiction/effective-date cases, RU/EN monolingual and cross-lingual queries, and adversarial near-neighbor distractors. Run component ablations and full LangGraph end-to-end evaluation. Store immutable dataset and code revision hashes with every result.

### 14.9 P2 — Existing tests are contract tests, not measured retrieval-quality evidence

The inspected unit tests verify query preservation, retrieval concurrency limits, bounded graph configuration, tenant filter contracts and vector schema/index presence. These are useful correctness safeguards. They do not establish recall, ranking quality, clinical entity coverage, query rewrite fidelity, RU/EN performance, production latency or quality improvement from HyDE/Multi-Query.

No benchmark run or result artifact was generated during this audit. Historical benchmark artifacts, if any, must be tied to their exact source revision, dataset and embedding model before they can be compared with the current code.

### 14.10 Retrieval readiness summary

- PostgreSQL/pgvector HNSW cosine index: **implemented in Alembic migration; deployment-specific index health/performance not measured here**.
- BM25 + vector hybrid retrieval: **implemented**.
- Reciprocal Rank Fusion: **implemented with default k=60**.
- Dedicated reranker: **not injected into active runtime**.
- Original query retained alongside generated variants: **implemented**.
- Russian Multi-Query/HyDE prompt instructions: **missing; English fallback is used**.
- LLM relevance grading: **implemented, but only first 800 characters are evaluated**.
- Calibrated retrieval confidence/threshold: **not established**.
- Existing SOP retrieval benchmark: **implemented; synthetic/English workflow scope, not clinical medication evidence**.
- Full LangGraph RU/EN medication retrieval benchmark: **not demonstrated**.
- Production-scale retrieval latency and quality: **not established by this static review**.

No application source changes, CI runs, migrations, database operations or deployments were performed as part of this review.

## 15. RAG Answer Generation & Clinical Grounding

Scope: static review of the active main implementations of LangGraphRAG, ContextualCompressor, MedicalGuardrails, PharmacistAgent, AgentHarness, the RAG response schemas and related unit tests. This section evaluates the transition from retrieved evidence to the final user-visible answer. It does not establish runtime behavior in a deployed environment.

### 15.1 Positive controls confirmed

- The LangGraph generation prompt explicitly instructs the model to answer only from retrieved evidence, treat the question/evidence as untrusted data, abstain when evidence is insufficient, and use only supplied citation IDs.
- Compressed context retains a deterministic src-{chunk_uuid} identifier and source/version labels for each retained chunk.
- RAG citation validation rejects missing citations and citation IDs that are not present in the retrieved source set.
- The agent's structured SafetyReview fails closed when the reviewer invocation raises an exception.
- The harness revalidates citation IDs after output guardrails/post-processing, reducing the chance that a post-processing step silently removes or fabricates a citation.
- The no-relevant-document route returns an explicit no-answer response after bounded rewrites.

These controls establish useful provenance and fail-closed behavior for several technical failures. They do not establish clinical claim correctness.

### 15.2 P1 — Runtime citation validation checks identifier membership, not claim-level entailment

LangGraphRAG._validate_answer_citations() extracts citation IDs from the answer and verifies that every extracted ID belongs to the retrieved source set. AgentHarness._validate_rag_citations() applies a similar allowlist check to the final agent answer. The agent reviewer also checks citation-ID membership.

None of these runtime checks verifies that:
- every factual/clinical claim has its own citation;
- the cited source actually supports the associated claim;
- a sentence containing multiple clinical claims is fully supported;
- each citation attached to a claim is relevant, rather than merely one citation somewhere in the answer being valid;
- a revised answer from SafetyReview has not introduced a new unsupported clinical claim.

The separate offline citation_correctness evaluator requires an entailment judge, but it is not wired into the production response path. Its current sentence-level logic also accepts a sentence when any one of its cited sources supports the sentence; this does not fully solve multi-claim/multi-citation attribution.

**Required correction:** generate an atomic claim-to-source structure. Each claim must carry its own exact source IDs and be checked against the corresponding source text. Split compound statements into atomic claims before entailment evaluation. Missing, invalid or unsupported citations on a critical clinical claim must trigger ABSTAIN/BLOCK, not merely an aggregate warning.

### 15.3 P1 — Evidence sufficiency is defined as document relevance, not clinical evidence coverage

The active graph considers retrieval sufficient when at least one document passes the binary relevance grader (MIN_RELEVANT_DOCS = 1). The no-answer route is selected only when no documents pass after the bounded rewrite attempts.

This does not establish that the retrieved evidence contains all attributes required to answer the question. For example, a chunk mentioning the correct medicine may still lack the requested strength, formulation, route, dosage, frequency, duration, contraindications, interaction context, population or jurisdiction. The graph has no explicit evidence-coverage contract for these required fields and no deterministic conflict/staleness decision at answer time.

The generation prompt asks the LLM to abstain when evidence is insufficient, but this remains a model instruction rather than a validated evidence-completeness gate. A single broadly relevant chunk can therefore reach generation even when a critical requested fact is absent.

**Required correction:** classify the question into required evidence fields, build a coverage matrix from retrieved sources, and define explicit abstention rules for missing, conflicting, expired, unapproved or jurisdiction-inapplicable evidence. Relevance must not be treated as clinical sufficiency.

### 15.4 P1 — Dosage guardrail is a substring heuristic, not dose-to-source verification

MedicalGuardrails._contains_unverified_dosage() searches the answer with a narrow dosage regex and then checks whether any supplied source's string representation contains the word dosage or the substring mg. It does not compare the medication identity and the exact dose/strength/concentration, unit, route, frequency, duration or patient context in the answer against the cited source.

Consequences:
- an unrelated mg occurrence anywhere in any retrieved source can make a dosage claim appear source-backed;
- a source containing the word dosage can satisfy the check without containing the dose stated in the answer;
- common variants such as 500 mg every 6 hours, mcg, micrograms, units/kg, concentration-based dosing and route-specific instructions are not comprehensively covered by the regex;
- the current action is to append a disclaimer, not to reject or abstain from an unverified high-risk dosage claim.

The unit test verifies disclaimer addition when sources are empty; it does not verify exact dose matching or rejection of a wrong dose.

**Required correction:** replace substring checks with structured medication/dose extraction and exact source-linked comparison. Critical mismatches or unverified dosage claims must fail closed and require pharmacist verification.

### 15.5 P1 — The agent reviewer is not a claim-level clinical verifier

SafetyReview contains is_safe, needs_revision, revised_response and new_warnings. The reviewer prompt asks the LLM to reject dangerous or unsupported dosage/medication claims, but the result does not contain a structured list of claims, supporting evidence spans, source IDs or per-claim verification decisions.

When the reviewer returns a revised response, the code subsequently checks only that citation IDs in the final text belong to the retrieved source set. A valid ID can therefore remain attached to a revised claim that the source does not support. The reviewer failure path is fail-closed, which is positive, but a successful structured response is not proof of entailment.

The reviewer receives the agent's RAG source summaries, where chunk content is truncated to 500 characters. This is not a complete evidence package for verifying claims whose support occurs later in the chunk.

**Required correction:** make review output structured and evidence-bound. Prefer a reviewer that returns per-claim findings and does not freely rewrite clinical content. If a revised answer is generated, send it through the same complete claim extraction, source-entailment, medication-entity and dosage validation gates before release.

### 15.6 P2 — RAG answer confidence is not meaningfully populated

On the normal generate_node success path, the node returns the answer, model name, latency and token count, but does not return a confidence value. LangGraphRAG.run() then constructs RAGResponse with float(final.get("confidence") or 0.0). Consequently, the normal successful generation path reports confidence=0.0 unless another node populated it.

This value is not a calibrated clinical confidence score. It must not be exposed or interpreted as one. Retrieval scores, RRF scores, LLM relevance decisions and answer confidence are different quantities.

**Required correction:** either remove/rename the field until a defined calibration method exists, or provide a documented, independently validated confidence contract. Never derive clinical confidence directly from vector similarity or RRF scores.

### 15.7 P2 — Compression preserves source IDs but not necessarily all clinically material evidence

The compressor attaches the original chunk citation ID to the compressed text, which is a useful provenance control. However, it can retain only up to three selected sentences; if no sentence meets the relevance threshold, it still keeps the top two scored sentences. This can produce a cited but incomplete representation of the original chunk. The generation layer does not receive an explicit list of omitted critical fields.

This finding is consistent with the document parsing/compression risks already recorded in Section 13; it is repeated here because it directly affects answer grounding.

**Required correction:** preserve clinical entities, strengths, units, routes, dose/frequency/duration, negation, contraindications, warnings, table headers and relevant exceptions deterministically. If compression cannot preserve a required fact and its context, retain the original evidence or abstain.

### 15.8 P2 — Test coverage validates citation syntax and guardrail contracts, not clinical grounding

The inspected tests cover:
- accepting a citation ID that belongs to the retrieved source set;
- rejecting missing or fabricated citation IDs;
- use of the guardrail validated-output contract;
- a dosage disclaimer when no sources are supplied;
- offline metric helper behavior with mocked entailment judges;
- Ragas adapter behavior with fake metric classes and fixed scores.

The inspected test set does not demonstrate:
- claim-level citation entailment through the actual LangGraph generation path;
- multi-claim sentences with partial evidence support;
- reviewer revisions that introduce unsupported claims;
- exact medication/dose/unit/route/frequency matching against cited source passages;
- reliable abstention when one relevant document lacks a requested critical attribute;
- conflict, supersession and jurisdiction-aware answer generation;
- a full PharmacistAgent + RAG + MCP answer evaluation using a real, explicitly configured evaluation judge.

No test suite was executed as part of this static audit. Test presence is not evidence of a passing run.

### 15.9 Recommended generation and release contract

1. **Atomic claims:** represent each factual claim separately with a stable claim ID, claim type, medication entities/attributes, criticality and exact supporting source IDs.
2. **Claim-to-evidence binding:** resolve each source ID to the original document version and exact page/section/span. Validate each claim against its cited evidence; do not accept mere ID membership.
3. **Medication attribute integrity:** preserve and validate ingredient, brand/generic identity, strength/concentration, dosage form, route, dose, units, frequency, duration, population and relevant contraindications/interactions.
4. **Evidence coverage and abstention:** define required fields per question type. Missing or conflicting critical evidence, stale/unapproved sources or jurisdiction mismatch must trigger ABSTAIN and pharmacist escalation.
5. **Reviewer constraints:** the reviewer should return structured verification findings. Any rewritten answer must pass the same validation pipeline again.
6. **Deterministic safety gates:** exact dose/entity/negation checks and tenant/patient isolation remain deterministic controls; Ragas/LLM judges are supplementary offline quality signals.
7. **End-to-end evaluation:** use a versioned, pharmacist-reviewed synthetic/de-identified corpus covering RU/EN, dosage and formulation variants, compound claims, negation, interactions, contraindications, conflicting/expired sources and adversarial near-neighbor medications. Report per-criticality metrics and hard-fail safety cases separately from aggregate Ragas scores.

### 15.10 Answer-generation readiness summary

- Evidence-only generation instruction: **implemented as a prompt instruction**.
- Stable source IDs in compressed context: **implemented**.
- Missing/fabricated citation-ID rejection: **implemented**.
- Claim-level citation entailment in the production response path: **not established**.
- Clinical evidence completeness/coverage gate: **not established**.
- Exact dosage-to-source verification: **not implemented; current check is heuristic**.
- Structured claim-level reviewer output: **not implemented**.
- Safe revalidation of reviewer-rewritten clinical claims: **not established**.
- Calibrated answer confidence: **not established; normal generation path defaults to 0.0**.
- Full end-to-end pharmacist-reviewed clinical answer benchmark: **not demonstrated**.

No application source changes, CI runs, migrations, database operations or deployments were performed as part of this review.

## 16. AI API Response Contract & Streaming Consistency

Scope: static review of the active main implementations of the FastAPI AI router, AgentHarness sync/stream paths, PharmacistAgent graph event mapping, PromptCache and AgentResponse/StreamingEvent schemas. This section records code-level contract findings only; no HTTP integration test, browser SSE test or deployed runtime verification was performed.

### 16.1 Positive controls confirmed

- Both POST endpoints validate the selected pharmacy tenant and validate that a selected patient is active and belongs to that pharmacy.
- Both endpoints derive the same HMAC-scoped session namespace from user, pharmacy, patient, purpose and client session ID.
- MCP authorization context is set around the sync execution and inside the streaming generator, then reset in a finally block.
- The synchronous route declares the canonical AgentResponse Pydantic response model.
- AgentHarness streaming has explicit start/status/answer/complete/error event concepts and records cancellation/error status in its OpenTelemetry span.
- Both sync and streaming harness paths execute input preprocessing, output post-processing and the post-processing citation-ID allowlist check on cache misses. Cached responses are returned from the cache path without repeating generation.

### 16.2 P1 — FastAPI SSE frames use escaped backslash-n sequences instead of actual line delimiters

In src/pharmaviyum/api/v1/ai.py, the streaming endpoint yields strings containing the Python source literal `\\n\\n` for event separators and for the [DONE] frame. In a Python string literal, the doubled backslashes produce literal backslash-plus-n characters, not newline characters. Server-Sent Events require each event to be terminated by an actual blank line.

The same delimiter is used for the exception event. Consequently, the endpoint's emitted body is not correctly framed as standard SSE from the inspected source. This is a direct protocol-level defect, not merely a frontend formatting preference.

**Required correction:** use actual newline characters (Python source literal `\n\n`) in the emitted SSE frame, set/retain the text/event-stream media type, and add an HTTP-level test that consumes the response body and verifies multiple independently parseable frames, JSON payloads and the terminal [DONE] frame. Include error and client-disconnect cases.

### 16.3 P1 — Streaming omits the generated session ID

QueryRequest.session_id is optional. The sync AgentResponse returns the raw session ID, including a newly generated ID when the client omitted it. The streaming endpoint generates the same kind of ID internally, but its start event contains only trace_id; no stream event returns the raw session ID.

A client that omits session_id on the first streaming request therefore cannot learn the server-generated conversation ID from the response and cannot reliably continue the same conversation on a later request.

**Required correction:** include the opaque client-facing session ID in the first streaming event (and define the same response contract for sync and stream). Do not expose the internal HMAC-derived checkpoint/session identifier.

### 16.4 P1 — Sync and streaming cache payloads are not symmetric for MCP tool results

The sync AgentHarness.run cache payload stores answer, warnings, tool_results, rag_sources and model_used. The streaming _astream_events cache payload stores answer, warnings, rag_sources and model_used, but omits tool_results.

The streaming cache-hit event derives tool_result_count from cached tool_results, so entries written by streaming report zero tool results. More importantly, if a streaming request populates the exact cache and a later sync request hits that entry, the sync harness returns an empty tool_results list by default. The FastAPI sync response then omits the MCP source records and tool-call records that were used to produce the answer.

The cache key is shared between the sync and streaming harness paths, so this is a cross-path data-contract inconsistency.

**Required correction:** define one canonical versioned cache payload and use the same serializer/deserializer in sync and streaming. Preserve tool result provenance and tool-call metadata where appropriate, and add round-trip tests for sync-write/stream-read and stream-write/sync-read.

### 16.5 P1 — Streaming final answer omits MCP tool-result sources

On a streaming cache miss, the harness collects executor tool_results but the final answer event exposes only rag_sources in its sources field. The sync API constructs its sources list from both successful tool results and RAG chunks.

As a result, an answer based partly or primarily on MCP data can have tool results in the sync response but no equivalent tool provenance in the streaming answer event. The stream only reports a tool_result_count, which is not enough to identify the source records or inspect their provenance.

**Required correction:** define a common source envelope for RAG chunks and tool results, including source type, stable ID, bounded content/summary and metadata. Return the same provenance contract in the sync response and the terminal streaming answer event. Keep tool-call execution records separate from source citations where their semantics differ.

### 16.6 P2 — Sync response drops the harness cache-hit flag

AgentHarness.run returns cache_hit=True on a cache hit and cache_hit=False on a miss. The FastAPI query_agent route constructs AgentResponse without passing cache_hit, whose schema default is False. Therefore the synchronous API reports cache_hit=False even when the harness returned a cached response.

The streaming answer event does expose cache_hit. The two API modes therefore disagree on an operationally useful response field.

**Required correction:** pass the harness cache_hit value into AgentResponse and test both cache-hit and cache-miss cases for sync and streaming.

### 16.7 P1 — Confidence and safety_score are hard-coded heuristics, not evaluated quality signals

The sync endpoint assigns confidence=0.9 and safety_score=0.95 when the warnings list is empty, and confidence=0.7 and safety_score=0.8 whenever any warning exists. These values are not calculated by a calibrated model, clinical verifier or risk engine. A warning-free answer is not necessarily clinically correct or safe, and a warning may describe a non-critical operational condition.

The AgentResponse.is_safe property treats safety_score >= 0.9 and absence of critical warnings as safe. Because the endpoint maps every warning string to severity="warning", it does not preserve any critical severity classification from upstream.

**Required correction:** remove misleading numeric confidence/safety values until their semantics, calibration dataset, thresholds and validation procedure exist. Use explicit state fields such as validation_status, requires_human_review and structured warning severity, each populated from defined checks. Do not infer clinical safety from absence of warnings.

### 16.8 P2 — Human-review flag is not reliably derived from current warning codes

The sync route sets requires_human_review only when the exact string human_review_required occurs in result.warnings. The inspected producer paths use codes such as reviewer_failed_closed, safety_block_triggered, citation_validation_failed, output_safety_block and dosage_unverified_disclaimer_added; no producer for human_review_required was found in the inspected active path.

This means the response flag can remain false even when a safety/review-related warning is present. The current implementation also assigns every warning the same severity value.

**Required correction:** define a central warning taxonomy and map each warning code to severity and escalation policy. Derive requires_human_review from that policy, not from one magic string. Add exhaustive tests for every safety-critical warning code.

### 16.9 P2 — Streaming event schema is not enforced by the endpoint

A StreamingEvent Pydantic schema exists with event_type and data fields, but AgentHarness emits untyped dictionaries using event as the discriminator, and the FastAPI streaming route serializes those dictionaries directly. No endpoint-level schema validation or versioned event envelope was established in this review.

The code also emits status messages as free-form text. The current event contract is therefore implicit and can drift between the harness, API and frontend.

**Required correction:** establish a versioned SSE envelope with a stable event discriminator, typed payloads, sequence/request identifiers and documented terminal/error semantics. Validate events before serialization and add contract tests against the OpenAPI/client-facing event specification.

### 16.10 P2 — API response loses token usage and warning severity metadata

AgentResponse defines total_tokens_used, but the sync route does not populate it and the inspected AgentHarness result does not expose a token total. The route converts all warning strings into Warning objects with severity="warning", regardless of their actual risk category. Streaming returns warning strings rather than the same structured warning objects.

This creates avoidable differences in observability, frontend rendering and downstream audit handling.

**Required correction:** either implement measured token accounting end-to-end or mark the field unavailable rather than silently defaulting to zero. Share a structured Warning schema across sync and streaming, including stable code, severity, message and safe details.

### 16.11 P2 — Route-level streaming contract tests were not found in the inspected test search

The inspected unit tests cover AgentHarness event sequencing, cache-hit completion and telemetry span behavior. The search did not locate an HTTP-level test for POST /api/v1/ai/query/stream that validates actual SSE delimiters, JSON parsing, [DONE], generated session ID, error framing or client cancellation through FastAPI.

The presence of harness unit tests does not prove the route emits valid SSE or that the browser can consume it.

**Required correction:** add ASGI-level endpoint tests and a frontend/client contract test. Verify sync/stream parity for answer, warnings, source records, tool calls, model, cache_hit, session_id, trace_id and terminal status.

### 16.12 Recommended canonical API contract

1. **Shared response envelope:** define one versioned response contract for sync and stream, with session_id, trace_id, answer, sources, tool calls, structured warnings, validation status, model metadata, cache metadata and timing.
2. **SSE transport:** emit standards-compliant frames with actual newline delimiters; define start, status, source/tool activity, answer, warning, complete and error events. Include terminal semantics and session_id in start.
3. **Single cache schema:** version the cache payload and preserve equivalent provenance/metadata for sync and streaming. Invalidate or safely migrate older payload versions.
4. **Trustworthy quality fields:** do not synthesize confidence/safety scores from warning presence. Publish only measured, documented and calibrated indicators.
5. **Consistent warnings:** one shared warning taxonomy with explicit severity, escalation and human-review mapping.
6. **Contract testing:** cover sync and streaming cache cross-reads, tool-backed and RAG-backed answers, missing/invalid citations, empty sources, safety blocks, reviewer failure, disconnects, SSE framing and frontend deserialization.

### 16.13 API/streaming readiness summary

- Tenant and selected-patient validation on both endpoints: **implemented in the inspected route code**.
- HMAC-scoped session derivation: **implemented**.
- Sync response Pydantic schema: **implemented**.
- Standards-compliant SSE framing: **not satisfied by the inspected string literals**.
- Generated session ID returned by streaming: **not implemented**.
- Sync/stream cache payload parity: **not implemented**.
- MCP tool provenance parity between sync and stream: **not implemented**.
- Sync cache_hit propagation: **not implemented**.
- Calibrated confidence and safety scores: **not established; current values are hard-coded heuristics**.
- Reliable human-review mapping: **not established**.
- Route-level SSE contract verification: **not demonstrated**.
- Token accounting and consistent structured warnings: **not established**.

No application source changes, test executions, CI runs, migrations, database operations or deployments were performed as part of this review.

## 17. AI Observability, OpenTelemetry & Production Monitoring

Scope: static review of active main implementations for OpenTelemetry provider setup, FastAPI middleware, AgentHarness and LangGraph spans, MCP tool spans, LangChain token callbacks, Prometheus metrics, monitoring endpoints, JSON logging and telemetry privacy tests. No production environment variables, collector, dashboard, deployed metrics endpoint or exported trace data were inspected. No tests were executed.

### 17.1 Positive controls confirmed

- The application owns one process-wide OpenTelemetry TracerProvider, uses ParentBased sampling with a bounded ratio sampler, configures an OTLP gRPC batch span processor when an endpoint is supplied, and flushes/shuts down the provider during application lifespan shutdown.
- Resource attributes include service name, service version and deployment environment.
- FastAPI request auto-instrumentation is deliberately gated behind an explicit opt-in and development/test environment check. SQLAlchemy and HTTPX auto-instrumentation are similarly gated.
- Manual low-cardinality spans exist for AgentHarness model selection/execution/streaming, RAG graph nodes/retrieval, and MCP tool execution.
- The AI telemetry facade allowlists span names, span attributes, LangSmith metadata keys and tags. Content tracing is restricted to development/test opt-in; LangChain automatic content tracing is disabled otherwise. Session identifiers are not exported to LangSmith.
- Privacy unit tests verify span attribute allowlisting, exception-content exclusion from the telemetry facade, and redacted LangSmith payload summaries.
- Prometheus metric labels for model, MCP tool, RAG query type and AI stages are bounded by allowlists. HTTP request metrics use route templates rather than raw dynamic paths as labels.
- The Prometheus registry defines HTTP, DB, Redis, Celery/worker, RAG stage, tool-call, LLM token/cost and evaluation metrics. RAG graph nodes record query transformation, retrieval, document grading, query rewrite, context compression, generation and guardrails durations; the full RAG run records total pipeline duration.
- MCP registry usage records emit tool-call count and duration metrics. The RAG run uses UsageMetadataCallbackHandler and returns token usage in its RAG response object.

### 17.2 P1 — API trace_id can diverge from the actual OpenTelemetry trace ID

AgentHarness._current_trace_id() reads the current OpenTelemetry span context and generates a random UUID when no valid current span exists. The FastAPI application configures FastAPI auto-instrumentation only when an explicit opt-in is enabled in development/test; production and staging are excluded by _allow_sensitive_client_instrumentation(). RequestIDMiddleware only adds request.id to a span when a recording span is already active; it does not create a server/root span.

In the normal production configuration path inspected, there is therefore no application-created FastAPI server span guaranteed to be active when AgentHarness.run() or _astream_events() calls _current_trace_id(). The returned/context trace_id can consequently be the fallback UUID, while subsequent manually created OpenTelemetry spans start their own SDK trace IDs. PharmacistAgent passes this fallback trace_id into MCPClient metadata, but it does not make it the actual OpenTelemetry trace ID.

**Impact:** API trace_id, MCP metadata and exported OpenTelemetry traces may not correlate. Operators may be unable to find the trace corresponding to a failed or slow AI request using the trace_id returned to the client.

**Required correction:** create a PHI-safe server/root span for every AI request in all environments, with explicit reviewed attributes only; derive trace_id from that active span; propagate W3C trace context across supported service boundaries; attach request.id as a correlation attribute; and add integration tests asserting that response trace_id equals the exported span trace ID for sync, streaming, cache-hit and error paths.

### 17.3 P1 — OpenTelemetry export is opt-in and disabled by default

OTelSettings.enabled defaults to false. If enabled without exporter_endpoint, configure_opentelemetry logs a warning and creates no span exporter; spans remain local to the process. A configured endpoint is required for export.

This means the repository's presence of spans and exporter code does not prove production traces are being exported. The deployed FastAPI Cloud environment variables and collector connectivity were not inspected in this static audit.

**Required correction:** explicitly configure OTEL_ENABLED and the OTLP endpoint in each intended environment; verify collector TLS/authentication, connectivity, sampling, service/resource identity and shutdown flush. Add a deployment readiness/operational check that distinguishes SDK enabled, exporter configured and successful export. Do not report tracing as operational based solely on code initialization.

### 17.4 P1 — LLM token and estimated-cost metrics do not cover all configured providers

PharmaviyumCallbackHandler records ai_llm_tokens_used_total and ai_llm_cost_estimate_usd_total from LLM callback usage metadata. In _build_llm(), this callback is wired only for the QwenCloud provider. The Ollama, Gemini and Groq constructors do not attach an equivalent handler in the inspected code.

LangGraphRAG.run() separately installs UsageMetadataCallbackHandler and returns total token usage in RAGResponse, but this callback path does not call record_llm_usage() or the cost tracker. The generation node itself reports tokens_used=0 in its state result.

**Impact:** Prometheus token/cost counters are provider- and execution-path-dependent, and cannot currently be treated as complete AI usage or billing/cost attribution. The presence of token counters does not prove all model calls are counted.

**Required correction:** implement a provider-neutral usage callback or normalize usage from each provider's response; record input/output tokens and model/provider consistently for router, RAG transformation/grading/compression/generation, reviewer and agent calls. Keep unknown usage/cost explicitly unknown rather than zero. Add provider contract tests for Ollama, QwenCloud, Gemini and Groq, including streaming usage.

### 17.5 P2 — Qwen callback uses static provider identifiers instead of request-level correlation

The QwenCloud LLM constructor creates PharmaviyumCallbackHandler with session_id="provider" and trace_id="qwencloud". These values are fixed at model construction and are not derived from the active request. The callback logs this static trace_id for LLM/tool lifecycle messages.

**Impact:** callback log records cannot reliably correlate an individual LLM call to the request trace or session. The static values are not PHI, but they are not request correlation identifiers.

**Required correction:** pass request-scoped trace context through LangChain RunnableConfig/callback metadata, use the active OpenTelemetry span context for each invocation, and never attach raw patient/session identifiers to metric labels or exported telemetry.

### 17.6 P2 — Full agent execution duration metric is declared but not observed in the inspected call sites

AI_AGENT_EXECUTION_DURATION is declared as a Prometheus histogram, but no observe/increment call for it was found in the inspected repository search. AI_REQUESTS_TOTAL is updated by LangGraphRAG.run(), so it measures RAG pipeline invocations rather than all top-level PharmacistAgent/AgentHarness API requests, including cache hits and requests that fail before entering RAG.

The RAG pipeline stage histograms are more complete: query_transform, retrieval, document_grading, query_rewrite, context_compression, generation, guardrails and rag_pipeline have explicit recording calls.

**Required correction:** instrument the outer AgentHarness request lifecycle, including cache hits, guardrail blocks, router/agent/reviewer failures, timeouts and cancellations. Separate ai_agent_requests_total from rag_pipeline_requests_total and record end-to-end duration exactly once per request. Remove unused metric declarations or wire them to their documented lifecycle.

### 17.7 P2 — SQLAlchemy and HTTPX spans are intentionally absent from production auto-instrumentation

The application only enables SQLAlchemy and HTTPX instrumentation when explicit sensitive-client opt-in is true and the environment is development/dev/test. Production and staging are excluded.

This is a defensible privacy default, but it means the inspected production tracing setup does not automatically provide DB query spans or outbound HTTP client spans. Manual model/router/RAG/MCP spans do not replace dependency-level latency/error visibility.

**Required correction:** either document this as an intentional observability limitation and provide equivalent safe DB/provider metrics, or add narrowly scoped production instrumentation with SQL parameter/content capture disabled, URL/query/credential redaction, and privacy regression tests. Do not enable raw SQL or HTTP payload capture to solve trace coverage.

### 17.8 P2 — Prometheus metrics endpoint has no application-level authorization dependency

The GET /metrics handler in src/pharmaviyum/api/v1/monitoring.py has no authentication/authorization dependency, unlike the detailed MCP health endpoint which requires CurrentSuperuser.

The registry includes internal operational information such as request/error rates, DB/Redis/worker state, AI stage timings, model labels, tool usage, token counters, estimated cost counters and evaluation scores. The source does not establish whether FastAPI Cloud/network controls restrict access to this endpoint; external reachability is therefore unverified.

**Required correction:** restrict scraping to trusted monitoring infrastructure using network policy/private ingress or a dedicated authenticated scrape mechanism. Verify deployed reachability from an unauthenticated external client. Do not expose detailed metrics publicly by default.

### 17.9 P2 — General JSON logging does not enforce a central PHI/secret redaction policy

The AI-specific ObservabilityTracer applies allowlists and avoids exporting exception content. However, the general JSONFormatter serializes record.getMessage(), exception message and formatted traceback without a redaction stage. LoggingMiddleware includes the raw request URL path in its message. Generic logger.exception calls elsewhere can therefore serialize exception text and stack details that have not passed through the AI telemetry allowlist.

The inspected request middleware does not log request bodies or query parameters, and the AgentHarness logs error types rather than raw exception text. These are positive controls, but they do not establish a global logging boundary.

**Required correction:** implement a central logging redaction/filter policy for credentials, tokens, connection strings, patient identifiers, prescription data and clinical content; prefer route templates over raw URL paths; sanitize exception messages while retaining exception type and safe error codes; and test all logging handlers/formatters with seeded PHI and secret values. Verify platform stdout log retention/access controls separately.

### 17.10 P2 — Manual LangSmith metadata export methods exist, but active production call sites were not established

ObservabilityTracer initializes a LangSmith client when a key is available and provides redacted log_to_langsmith, log_tool_call and log_evaluation methods. Repository search found the method definitions and tests but did not establish active application call sites invoking them. Automatic LangChain content tracing is deliberately disabled unless development/test content opt-in is enabled.

**Impact:** LangSmith integration should not be represented as end-to-end operational tracing merely because the client and facade exist. Its current active production coverage is not established by the inspected call graph.

**Required correction:** either wire explicit metadata-only events into the request/agent/RAG/tool lifecycle with privacy-safe trace correlation and tests, or document LangSmith as configured-but-unused/optional. Keep prompt, answer, retrieved text, patient data and raw session IDs excluded from production export.

### 17.11 Observability readiness summary

- Single application-owned OpenTelemetry provider and OTLP batch exporter support: **implemented**.
- OpenTelemetry enabled by default: **no; disabled unless configured**.
- Successful production OTLP export: **not established; deployment configuration/collector not inspected**.
- Production FastAPI server/root span: **not established; built-in auto-instrumentation explicitly excludes production/staging**.
- API response trace_id matching actual exported trace: **not established; fallback UUID can diverge from SDK trace ID**.
- Manual AgentHarness/RAG/MCP spans: **implemented**.
- Provider-neutral LLM token/cost accounting: **not implemented; callback wired only for QwenCloud, RAG usage callback is separate**.
- Full AgentHarness request duration/request count metrics: **not established; declared histogram unused in inspected call sites and request counter is RAG-scoped**.
- RAG stage duration/error metrics: **implemented for the inspected graph stages**.
- Bounded Prometheus labels and AI telemetry attribute allowlists: **implemented**.
- Production SQLAlchemy/HTTPX auto-instrumentation: **intentionally disabled by inspected environment gate**.
- Metrics endpoint application-level authorization: **not implemented; perimeter restriction unverified**.
- Global PHI/secret redaction for all JSON logs: **not established**.
- Active metadata-only LangSmith call sites: **not established**.

No application source changes, test executions, CI runs, migrations, database operations or deployments were performed as part of this review.

## 18. AI Execution Reliability & Resilience

Scope: static review of active main implementations for LLM construction, AgentHarness sync/stream execution, PharmacistAgent LangGraph loop and executor, LangGraphRAG deadlines/concurrency/token budgeting, MCPClient retries/circuit breaker, ToolCallingLayer and Qwen demo provider policy. No runtime fault injection, load test, provider outage simulation, test execution or deployment inspection was performed.

### 18.1 Positive controls confirmed

- Cloud LLM adapters configure finite provider request timeouts: QwenCloud 30 seconds with retries explicitly disabled, Gemini 30 seconds and Groq 30 seconds. These are provider-call timeouts, not end-to-end request deadlines.
- MCPClient wraps each registry tool invocation in asyncio.wait_for with a finite 30-second default timeout.
- MCPClient disables automatic retries for tools whose metadata execution_class is write, explicitly acknowledging that a write may have succeeded even when its response timed out.
- MCP read-tool calls have bounded retry attempts and exponential fixed delays; the MCP client has a per-tool circuit-breaker mechanism.
- LangGraphRAG.run wraps the entire RAG graph invocation in asyncio.timeout, defaulting to 90 seconds, and configures an explicit recursion limit derived from the bounded rewrite count.
- RAG retrieval and document grading each use per-invocation asyncio.Semaphore limits (defaults 6 and 4 respectively).
- RAG token budgeting checks the combined generation prompt before the generation LLM call and returns a controlled warning rather than silently truncating clinical evidence.
- RAG graph node wrappers explicitly mark and re-raise asyncio.CancelledError. AgentHarness.astream ends its span in a finally block and marks incomplete streams as cancelled.
- PharmacistAgent bounds graph iteration at five and truncates each planner tool-call batch to ten calls. Executor calls are sequential in the active path inspected.
- The Qwen demo profile explicitly documents that automatic provider fallback and provider circuit breaker are not implemented, and disables provider retries to avoid accidental quota consumption.

### 18.2 P1 — No end-to-end deadline covers AgentHarness and PharmacistAgent execution

LangGraphRAG.run has its own 90-second execution timeout, but AgentHarness.run(), AgentHarness._astream_events() and PharmacistAgent.run() do not apply a shared request deadline around memory load, guardrails, model routing, agent graph, reviewer, post-processing, memory save and cache operations.

AgentSettings.streaming_timeout_seconds is declared with a 60-second default, but no active use of this setting was found in the inspected request execution path. The RAG timeout does not bound the full pharmacist-agent request.

**Impact:** a request may spend up to the RAG deadline and then continue through planner/tool execution/reviewer and persistence. Streaming can remain open beyond the configured streaming timeout value because that setting is not enforced in the inspected path.

**Required correction:** define one request-level monotonic deadline at the API boundary and propagate remaining time through AgentHarness, PharmacistAgent, RAG and MCP. Each downstream operation must receive min(component timeout, remaining request budget). Enforce cancellation on deadline, return a controlled timeout response and test sync/stream paths including disconnects and cleanup.

### 18.3 P1 — MCP retries can multiply a tool call to a long latency and are not bounded by an agent-wide budget

MCPClient defaults to max_retries=3 and timeout_seconds=30. For a read tool, the initial call plus three retries can consume up to four 30-second attempts. Between attempts it sleeps 1, 2 and 4 seconds. This is a theoretical upper bound of 127 seconds for one exhausted read-tool call, excluding local overhead.

PharmacistAgent.executor_node processes tool calls sequentially and accepts up to ten calls per planner iteration. The graph permits up to five iterations. There is no shared tool-call deadline or total retry/time budget across the agent execution.

**Impact:** repeated tool failures can cause very long agent execution times even though each individual tool call is nominally bounded. The per-call timeout does not provide a useful end-to-end latency guarantee.

**Required correction:** use a shared request deadline and a cumulative tool budget (count, elapsed time and retry attempts). Reduce retries when the remaining deadline cannot accommodate another attempt. Set a strict per-request maximum tool count and test worst-case timeout composition.

### 18.4 P1 — Ollama timeout configuration is not passed to ChatOllama

OllamaSettings.timeout_seconds defaults to 60 seconds, but dependencies._build_llm() constructs ChatOllama with model, base_url, temperature and num_predict only. The configured timeout is not passed to the client in the inspected constructor call.

Cloud providers receive configured timeout values, but the local Ollama path does not consume its corresponding setting in this factory.

**Impact:** the application configuration advertises a bounded Ollama timeout that is not established by the inspected construction path. Actual Ollama request timeout behavior is delegated to library/transport defaults and remains unverified.

**Required correction:** wire the supported ChatOllama request timeout explicitly, verify the installed LangChain Ollama integration's accepted parameter, and add a test that proves a stalled Ollama request is cancelled within the configured bound.

### 18.5 P1 — MCP circuit breaker state is process-local and lacks a controlled half-open probe

MCPClient stores circuit state in an in-memory dictionary keyed by tool name. After five failed call cycles it opens the circuit for 60 seconds. Once the cooldown elapses, _is_circuit_open deletes the state and immediately permits calls; there is no half-open state or single-probe lock.

This state is not shared between application replicas and is lost on process restart. Concurrent requests after cooldown can all pass through and hit a still-failing dependency.

**Impact:** the breaker cannot coordinate outage protection across FastAPI replicas, and recovery traffic can produce a thundering herd.

**Required correction:** use a shared circuit state or explicitly accept/document per-process isolation; implement closed/open/half-open states with one controlled probe, bounded concurrent in-flight calls, recovery thresholds and observable transitions. Test concurrent callers, multiple replicas and process restart behavior.

### 18.6 P2 — MCP retry loop retries broad exception classes without transient-error classification or jitter

MCPClient retries every generic Exception except PermissionError, in addition to timeout errors. The retry loop does not distinguish transient network/provider failures from permanent validation, configuration, dependency-health or application errors. Backoff is deterministic min(2**attempt, 10) with no jitter.

This can retry failures that cannot succeed on another attempt and synchronize retries from multiple replicas during an outage.

**Required correction:** classify retryable errors explicitly; do not retry authorization, validation, unsupported operation, configuration or other permanent failures. Add bounded exponential backoff with jitter and honor Retry-After where supported. Keep write tools non-retryable unless an explicit idempotency key and authoritative deduplication contract exist.

### 18.7 P2 — MCPSettings retry and circuit-breaker values are not wired into MCPClient construction

MCPSettings declares tool_timeout_seconds, max_retries, circuit_breaker_threshold and circuit_breaker_timeout. The active dependency module creates a module-level MCPClient() without passing these settings. MCPClient therefore uses its own constructor defaults (30 seconds, 3 retries, threshold 5, cooldown 60 seconds) regardless of the MCPSettings values.

The defaults currently match, but environment overrides to MCPSettings do not control the instantiated client.

**Required correction:** construct MCPClient from the settings explicitly and validate all bounds. Add configuration tests proving environment overrides change the effective client policy.

### 18.8 P2 — RAG concurrency limits are per request, not global admission control

LangGraphRAG.retrieve_node and grade_documents_node instantiate new semaphores for each graph invocation. They limit concurrent retrieval variants to six and grading calls to four within one RAG request, but do not cap aggregate concurrency across simultaneous requests or worker replicas.

No global AI admission semaphore, bounded request queue or provider-wide concurrency limiter was established in the inspected active API/AI dependency path.

**Impact:** per-request bounds do not prevent aggregate provider/database saturation under concurrent user load. N simultaneous requests can each create their own bounded set of retrieval and grading operations.

**Required correction:** introduce shared per-process and, where required, distributed concurrency/admission controls for expensive model, embedding, vector retrieval and external tool calls. Define queue limits, overload response (429/503), fairness and backpressure. Load-test across multiple replicas and verify that cancellation releases permits.

### 18.9 P2 — Token budget is enforced for RAG generation, not the complete agent prompt lifecycle

TokenBudgetManager is constructed and injected into LangGraphRAG. Its check_input call is in the RAG generate node and checks the combined RAG system and evidence prompt before the generation LLM call.

The inspected PharmacistAgent planner and reviewer calls invoke their models directly without a corresponding TokenBudgetManager preflight. The planner prompt includes conversation history, memory, retrieved evidence and tool results; reviewer prompt includes the draft, question, tool results and RAG sources.

**Impact:** the RAG generation budget does not establish a bound for all LLM calls in the overall agent. Planner/reviewer contexts can exceed their provider/model context windows or incur unbounded prompt cost relative to the RAG budget.

**Required correction:** define per-model input/output budgets for router, planner, RAG transform/grading/compression/generation, reviewer and memory summarization. Preflight each complete prompt with the selected model tokenizer or clearly marked conservative estimate; never silently drop clinical evidence, dosage, negation or warnings.

### 18.10 P2 — ModelRouter fallback is a model alias, not provider failover

AIComponents constructs ModelRouter with fast, main and complex models and assigns fallback to get_llm_main(). The router's _get_model fallback behavior only selects a configured dictionary entry/default when a key is missing; it does not catch an invocation failure and retry against another provider.

The Qwen demo documentation explicitly states that automatic LLM fallback is intentionally disabled and provider circuit breaker/cooldown is planned, not implemented.

**Impact:** model routing selects a model by complexity but does not provide resilience to an unavailable provider. A failed QwenCloud call does not automatically switch to Ollama, Gemini, Groq or another configured backend.

**Required correction:** keep demo free-quota policy explicit. If provider failover is later approved, classify errors and define a safe provider/model compatibility matrix, jurisdiction/privacy policy, embedding independence, quota/cost controls and clinical quality gates. Never silently send clinical/patient context to another provider or paid endpoint.

### 18.11 P2 — ToolCallingLayer resilience features are not on the active PharmacistAgent execution path

ToolCallingLayer implements parallel execution, fallback chains, result validation and a separate in-memory circuit breaker. However, the active AI dependency setup constructs PharmacistAgent with MCPClient directly, and PharmacistAgent.executor_node calls MCPClient.call_tool directly. No active production construction/injection of ToolCallingLayer was established in the inspected call graph.

The active executor is sequential, uses MCPClient's own retries/breaker and truncates calls to ten. ToolCallingLayer's ToolSpec.timeout_seconds is not the timeout governing these direct calls.

**Impact:** documented/declared ToolCallingLayer capabilities must not be counted as active production controls. Its parallelism, fallback chain, schema validation and second breaker do not protect the inspected active agent path.

**Required correction:** either integrate a single supported orchestration layer into PharmacistAgent with trusted context propagation and one shared budget, or remove/mark unused duplicate abstractions. Avoid stacking independent retry and circuit-breaker layers.

### 18.12 P2 — Cancellation is partly handled correctly, but whole-agent deadline/cancellation behavior is not verified

RAG traced nodes explicitly catch asyncio.CancelledError and re-raise it. AgentHarness.astream uses a finally block to end its span and mark an incomplete stream as cancelled. MCP calls use asyncio.wait_for, which cancels the awaited coroutine on timeout. PharmacistAgent executor's broad except Exception does not normally swallow asyncio.CancelledError on supported modern Python versions.

However, there is no request-wide deadline in the active AgentHarness/PharmacistAgent path and no executed integration test proving cancellation propagates through graph nodes, MCP tool operations, reviewer, memory/cache persistence and API streaming disconnect.

**Required correction:** preserve cancellation as a control signal throughout the complete graph; never convert it to a normal tool failure or retry. Define behavior for operations that may have external side effects, use idempotency/operation status for writes, and test disconnect/timeout at every stage with cleanup and checkpoint consistency assertions.

### 18.13 Execution reliability readiness summary

- Per-provider finite cloud LLM request timeouts: **configured for QwenCloud, Gemini and Groq**.
- Ollama configured timeout passed to client: **not implemented in inspected factory**.
- End-to-end AgentHarness/PharmacistAgent deadline: **not implemented in inspected path**.
- RAG graph deadline: **implemented, 90-second default**.
- Streaming timeout setting: **declared but not wired in inspected path**.
- MCP per-call timeout: **implemented, 30-second default**.
- MCP read retries: **implemented, three retries with deterministic backoff and no jitter**.
- MCP write retries: **disabled by execution class**.
- MCP error classification: **not implemented; generic exceptions are retried**.
- MCP circuit breaker: **implemented in-memory per process/tool, without controlled half-open probe**.
- Provider circuit breaker/fallback: **not implemented; Qwen demo fallback intentionally disabled**.
- RAG retrieval/grading concurrency: **bounded per request, not globally**.
- Global AI admission/backpressure: **not established**.
- Agent loop/tool-call count bounds: **implemented (five iterations, up to ten calls per iteration)**.
- Shared total tool/time budget: **not implemented**.
- RAG generation token budget: **implemented**.
- Full agent prompt token budget: **not established**.
- ToolCallingLayer parallel/fallback features in active agent path: **not established; active PharmacistAgent calls MCPClient directly**.
- Cancellation propagation: **some explicit safeguards implemented; full end-to-end behavior not demonstrated**.
- Runtime fault-injection/load tests: **not executed in this audit**.

No application source changes, test executions, CI runs, migrations, database operations or deployments were performed as part of this review.


## 19. AI Security, Privacy & Threat Modeling

Scope: static review of active main authentication dependencies and token issuers, AI API request boundary, pharmacy tenant resolution, MCP authorization context and registry, patient-history tool, pharmacist-agent planner/reviewer prompts, RAG prompt construction, application middleware, rate-limit setup, Redis connection configuration and related security tests. No exploit execution, token replay, penetration test, runtime environment inspection, database access, test execution or deployment inspection was performed.

### 19.1 Positive controls confirmed

- AI query and streaming request schemas bound query length to 2,000 characters, require a positive explicit pharmacy ID, and require selected patient and controlled purpose to be supplied together.
- AI API validates that the selected patient is active and belongs to the authorized pharmacy before starting the harness.
- AI conversation session HMAC binds pharmacy, authenticated user, selected patient, purpose and client session ID. Staging/production reject a missing application secret in the inspected core settings.
- MCPAuthorizationContext is an immutable request-scoped dataclass. It validates user, pharmacy, patient, purpose and role fields; missing context fails closed.
- MCPClient and MCPToolRegistry derive authority from the trusted ContextVar context, reject identity mismatches, validate tool input with Pydantic, and enforce tool role metadata. Model-provided tenant/user/role values are not treated as authority.
- MCP data capabilities require trusted request context; initialize/initialized are the only public protocol methods in the inspected MCP server.
- get_patient_history requires exact equality between model-supplied patient ID and trusted selected_patient_id, pharmacist role, a controlled purpose and active patient ownership in the trusted pharmacy.
- get_patient_history writes metadata-only PHIAccessAudit decisions and commits the audit before returning patient data. Audit commit failure prevents the tool from returning the patient response.
- MCP write tools are fail-closed until a trusted approval verifier is configured; the active registered tools inspected are read-only.
- RAG query transformation and generation prompts explicitly treat user questions and retrieved evidence as untrusted data. Several RAG prompt sections HTML-escape question/evidence values before interpolation. The pharmacist planner also instructs the model not to follow instructions in tool or retrieved content and marks reference context as untrusted.
- Provider API keys use Pydantic SecretStr in AI settings. Core application configuration requires a secret of at least 32 characters in staging/production. Password hashing uses bcrypt, and JWT decoding pins the configured algorithm rather than accepting an algorithm supplied by the token.
- Existing contextual-compression security tests include delimiter-injection examples and assert that retrieved text and query delimiters are escaped. Existing patient-history tests cover selected-patient mismatch, missing purpose, non-pharmacist denial and audit commit failure using a test-double session.

### 19.2 P1 — Refresh and password-reset JWTs can pass the active access-token dependency

The active CurrentUser dependency in modules/auth/deps.py imports decode_access_token from core/oauth2.py. That decoder verifies the signature using the configured API secret and validates standard JWT expiry, but it does not require a token-type claim.

The modular authentication routes issue:
- access tokens with type=access;
- refresh tokens with type=refresh and a 30-day default lifetime;
- password-reset tokens with type=password_reset and a 48-hour lifetime.

These token types use the same application signing key. The active get_current_user dependency calls the legacy decoder, which accepts any correctly signed, unexpired token containing a usable subject. It then resolves the subject against user ID, username or email. Consequently, a refresh token or password-reset token can be presented as a Bearer access token and may authenticate as the corresponding active user. This is a source-level token-confusion vulnerability, not a runtime exploit result.

There are also two token issuance paths: the legacy /api/v1/auth/token endpoint issues untyped access tokens through core/oauth2.py, while the modular /api/v1/auth/login/access-token route issues typed tokens through core/security. This split makes consistent validation harder.

**Impact:** a password-reset capability intended only to change a password, or a refresh capability intended only to rotate credentials, may also authorize protected API operations for its remaining lifetime.

**Required correction:** consolidate token issuance and decoding behind one canonical security module. Require type=access in the Bearer dependency; use type-specific decoders for refresh and password reset. Migrate or retire the legacy untyped issuance endpoint with an explicit compatibility plan. Add negative API tests proving refresh and password-reset tokens cannot access CurrentUser routes, alongside positive access-token tests. Consider explicit issuer/audience claims and signing-key separation as defense in depth.

### 19.3 P1 — Pharmacy membership does not establish a clinical pharmacist role

The User.role property returns admin for every platform superuser and pharmacist for every other account. PharmacyMembership stores user_id, pharmacy_id and is_active but does not carry a pharmacy-specific role or permission grant.

AI API copies current_user.role into trusted MCPAuthorizationContext. MCP registry filters tools by required_roles, and get_patient_history independently requires role pharmacist. Since every ordinary account is assigned that role by the User property, the role check does not establish that the user is actually a pharmacist or has a clinical PHI permission in the selected pharmacy.

This is the same unresolved authorization design gap recorded in Section 7.3, restated here as an AI security threat because it directly gates clinical tool access.

**Impact:** any ordinary active user with an active pharmacy membership is represented to the AI layer as a pharmacist. The tenant boundary still works, but least-privilege clinical authorization is not established.

**Required correction:** resolve a role and explicit permission set from the authenticated user's active membership in the selected pharmacy. Separate platform operator privileges from pharmacy roles. Require a dedicated clinical permission for patient-history access and other PHI operations; deny by default when role/permission is missing or ambiguous. Add two-user/one-pharmacy tests for cashier, pharmacist, manager and pharmacy administrator, including cross-pharmacy role differences.

### 19.4 P1 — AI rate limiting is declared but not connected to the active application

The repository contains a rate_limit.py helper with setup_rate_limiting(), rate_limit_ai() and a SlowAPI Limiter configuration. However, the active src/pharmaviyum/main.py does not import or call setup_rate_limiting(). The inspected AI routes do not apply the rate_limit_ai decorator. The helper itself is therefore not evidence that the active /api/v1/ai/query or /api/v1/ai/query/stream routes are rate limited.

The separate core configuration defaults RATE_LIMIT_ENABLED to false. No effective per-user/per-tenant AI request limiter was established in the active application assembly.

**Impact:** authenticated users may repeatedly invoke expensive LLM, embedding, retrieval and MCP operations without an application-level rate limit in the inspected path. Authentication alone does not protect against accidental loops, compromised accounts or resource-exhaustion attempts.

**Required correction:** wire one limiter into the actual FastAPI application and protect synchronous and streaming AI routes, authentication and other expensive endpoints. Use distributed storage for multi-replica deployments; key AI quotas by authenticated user and pharmacy with IP-based abuse protection as an additional dimension. Define separate concurrency/admission limits and clear 429/Retry-After behavior. Verify the limiter is active in the assembled app, not merely declared in a helper module.

### 19.5 P1 — Safety reviewer prompt does not establish an untrusted-data boundary

PharmacistAgent.reviewer_node constructs one HumanMessage by interpolating the user question, generated draft, tool_results and rag_sources directly into a review_prompt. These fields can contain user-controlled or externally sourced text. The reviewer SystemMessage only says that it is a strict medical safety reviewer; unlike the planner and RAG prompts, it does not explicitly instruct the reviewer to treat every embedded question, draft, tool result and retrieved passage as untrusted data and never follow instructions within them. The interpolated values are not placed in a structured, escaped evidence envelope.

The reviewer is a safety gate that can approve the draft, reject it or replace it. An indirect prompt injection inside a retrieved document or tool output could therefore influence the review decision.

**Impact:** prompt-injection defenses are not consistent across the agent's model calls. The presence of an explicit untrusted-data instruction in the planner does not automatically protect the separate reviewer invocation.

**Required correction:** provide the reviewer with a fixed system policy that explicitly treats all dynamic fields as untrusted evidence, never as instructions. Pass question, draft, tool results and source records through a typed structured payload with robust delimiter escaping or a structured model interface. Keep deterministic checks outside the LLM reviewer for citation membership, medication identity/strength/form, dosage units, negation and critical contraindications. Add adversarial tests that place instruction-like text in each dynamic field and assert that it cannot alter reviewer policy or authorize unsupported clinical claims.

### 19.6 P2 — Patient-history tool returns more PHI than its explicit include flags require

PatientHistoryRequest has include_allergies, include_conditions, include_prescriptions and include_orders flags. However, PatientHistory always includes patient full_name, age, gender, blood_type, loyalty_tier and preferred_language. These fields are returned even when all four include flags are false. The current patient-history tool test explicitly disables all four flags but still expects the tool to return a PatientHistory object.

The response therefore combines clinically relevant data with demographic and commercial/customer attributes regardless of the specific purpose or minimum fields required for the task.

**Impact:** every authorized invocation may expose more personal information to the LLM context than the current task requires. This increases the amount of PHI processed by downstream models, checkpoints, caches and observability paths.

**Required correction:** define purpose-specific minimum-necessary response projections. Make each returned field opt-in only when required by a validated workflow and permission. Exclude loyalty tier and other commercial attributes from clinical history unless a separate business purpose authorizes them. Add schema and tool tests asserting exact field allowlists for each purpose and include the LLM prompt boundary in privacy review.

### 19.7 P2 — Some MCP authorization denials occur before the PHI audit function

MCPToolRegistry.call_tool checks required_roles before invoking the registered tool function. get_patient_history writes PHIAccessAudit rows only after its function starts. Therefore, a registry-level role denial occurs before the patient-history audit code and is not recorded as a PHI access denial by that tool.

The current security test uses a fake session to verify audit writes and fail-closed behavior; it does not prove database-backed audit persistence or the full registry-to-audit path. This is consistent with the existing PHI governance documentation.

**Impact:** the audit trail may not contain every attempted PHI tool invocation or authorization denial, which weakens incident investigation and access-review completeness.

**Required correction:** add a centralized audit decision point before role-based denial for PHI-designated tools, using trusted actor, tenant, selected patient, purpose, tool and request metadata. Ensure audit failure fails closed for PHI operations. Add database-backed tests for registry-level denial, selected-patient denial, successful read and audit storage failure.

### 19.8 P2 — Production Redis transport encryption is not enforced by application configuration

The active Redis client builds its connection pool from REDIS_URL and configures connection limits and socket timeouts. The core settings accept a redis:// URL and do not require rediss:// when ENVIRONMENT is staging or production. No runtime FastAPI Cloud Redis URL or network policy was inspected.

**Impact:** source configuration does not prevent a production deployment from connecting to Redis without TLS. This matters because Redis stores AI memory, prompt cache and other state that may contain patient-linked or sensitive operational data. This finding does not establish that the current deployed Redis connection is plaintext.

**Required correction:** require TLS for remote production Redis connections, validate the URL scheme in production configuration, verify certificate validation and avoid insecure TLS overrides. Document private-network requirements, Redis ACLs, credential rotation, backup retention and encryption at rest. Verify the actual provider connection settings separately.

### 19.9 P2 — Security configuration is split across multiple settings and authentication modules

The active app entry point imports AI settings from ai.config, while authentication, middleware, Redis and core security modules import core.config or the legacy src/pharmaviyum.config. There are two token implementations: core/oauth2.py and core/security/__init__.py. There are also separate CORS/rate-limit helper modules and middleware configuration paths.

Some settings intentionally map compatible environment names, but the duplicated configuration/authentication paths make it harder to prove that production validation, token semantics, rate limiting and transport security are consistently applied by the assembled application.

**Required correction:** consolidate canonical application settings and authentication/token services. Remove obsolete duplicate helpers after call-site migration. Add startup validation tests against the actual app factory so security-critical environment values and middleware are demonstrably wired.

### 19.10 Security readiness summary

- AI request pharmacy binding and active patient ownership check: **implemented in inspected API path**.
- HMAC session binding to user/pharmacy/patient/purpose/session: **implemented**.
- Trusted MCP context and fail-closed missing-context behavior: **implemented**.
- MCP registry schema and role checks: **implemented, but upstream pharmacy-specific role is not**.
- Patient-history exact selected-patient and same-tenant checks: **implemented**.
- PHI audit before patient-history response: **implemented, database-backed end-to-end proof not established**.
- MCP write approval: **fail-closed until verifier is configured**.
- RAG/planner untrusted-context instructions: **implemented in inspected prompts**.
- Reviewer untrusted-context boundary: **not established**.
- Access/refresh/password-reset token type separation at CurrentUser boundary: **not implemented; P1 token-confusion risk**.
- Pharmacy-specific clinical role/permission: **not implemented; P1**.
- AI endpoint rate limiting: **helper declared but not wired into active app path**.
- Patient-history minimum-necessary projection: **not implemented; response includes extra demographic/commercial fields**.
- Redis TLS enforcement in production settings: **not implemented; actual deployed transport unknown**.
- Global PHI/secret log redaction: **see Section 17; not established**.
- Database-level tenant RLS: **see Sections 10 and 14; not established**.
- Runtime penetration testing, exploit validation and security test execution: **not performed**.

No application source changes, test executions, CI runs, migrations, database operations or deployments were performed as part of this review.

## 20. Release Engineering & Software Supply-Chain Security

Scope: static review of the main-branch GitHub Actions CI and Demo deployment workflows, Python dependency declarations/lockfile contract, application Dockerfile, Ansible backend Compose template and deployment tasks, and documented Demo/Production environment boundary. No workflow was triggered, no image was built or pulled, no registry artifact or attestation was inspected, no deployment was performed, and no runtime environment was queried. Findings describe repository configuration only.

### 20.1 Positive controls confirmed

- Python dependencies are exactly pinned in pyproject.toml and resolved through uv.lock; CI and container builds use uv sync --frozen.
- Production and Demo are explicitly separated: FastAPI Cloud is the public synthetic-data Demo host; Production targets the pharmacy server through Ansible with per-site secrets and operational data.
- The Demo deployment workflow is manually dispatched from main, requires a change reference and Demo-only credentials, waits for CI success for the exact source SHA, checks Demo schema compatibility read-only, and does not run Alembic migrations.
- The Demo workflow verifies that the newly serving runtime reports the expected build SHA, staging environment, debug=false and CPython 3.15.0, then checks liveness, readiness, frontend routes, invalid-auth behavior and protected POS access.
- Main CI gates image publication on unit tests, integration tests, security scan, RAG evaluation and CPython 3.15 compatibility.
- The GHCR build tags the image with the source commit SHA, records OCI revision/source labels, and enables BuildKit provenance and SBOM generation.
- Production Ansible pulls the application image using backend_image@backend_image_digest rather than a mutable application tag.
- The Dockerfile uses a multi-stage Python/frontend build, installs runtime dependencies without dev groups, creates a non-root appuser, defines a healthcheck and deliberately keeps migrations out of application startup.
- Python dependency security checks include pip-audit and Bandit; Ansible has a separate syntax/lint workflow.

### 20.2 P2 — Docker base images and OS package inputs are not immutable

The Dockerfile uses python:3.15.0-slim and oven/bun:1.4.4 tags rather than reviewed image digests. Both builder and production stages install OS packages after apt-get update without a dated/snapshotted repository or exact package-version contract. The Python builder also upgrades pip, setuptools and wheel without exact version pins before installing uv==0.13.8.

The tags and package repository state can resolve to different underlying bytes on later builds even when the application source SHA and uv.lock are unchanged. This weakens byte-for-byte reproducibility and complicates forensic reconstruction of a historical image.

Required correction: pin base images by reviewed digest, pin build tooling and OS packages or use a controlled snapshot, record the resulting image digest and build metadata, and define a deliberate update cadence with vulnerability review. Do not confuse an immutable final GHCR digest with a reproducible rebuild.

### 20.3 P2 — Ansible database and cache images still use mutable tags

The active Ansible backend Compose template uses pgvector/pgvector:pg16 and valkey/valkey:8-alpine (the latter can be overridden by REDIS_IMAGE). These are mutable tags, unlike the application image which Ansible pulls by digest.

A later redeployment can therefore pull a different database/cache image without a corresponding reviewed infrastructure change. Database image drift is particularly sensitive because major-version and extension compatibility affect persistent volumes and recovery procedures.

Required correction: pin PostgreSQL/pgvector and Valkey images by reviewed immutable digest, record exact versions, and require backup/restore and compatibility validation before changing database image digests. Validate the override path so it cannot silently bypass the pinning policy.

### 20.4 P2 — GitHub Actions dependencies use version tags rather than immutable commit SHAs

The inspected CI, Demo deployment and Ansible quality workflows reference third-party actions using tags such as actions/checkout@v4.4.0, astral-sh/setup-uv@v7, docker/build-push-action@v6, oven-sh/setup-bun@v2, docker/setup-buildx-action@v3, docker/login-action@v3, actions/setup-python@v5 and actions/upload-artifact@v4.

Version tags are more specific than floating major tags, but they are still mutable Git references. The workflows do not establish an enforced full-SHA pinning policy or automated reviewed update mechanism in the inspected files.

Required correction: pin each third-party action to a verified full commit SHA, retain the human-readable version in a comment, and use an automated dependency update process with review. Apply the same policy to reusable workflows and external action dependencies.

### 20.5 P2 — Final container image is not scanned after build

The CI security job runs pip-audit against the Python dependency environment and Bandit against selected application code. The build job subsequently publishes a multi-stage Docker image with an OS package layer and a frontend build/runtime payload. No container image vulnerability scan or policy gate is present after the image is built in the inspected CI workflow.

pip-audit does not inventory Debian OS packages, base-image vulnerabilities or every artifact copied into the final image. SBOM generation is enabled, which is useful, but generating an SBOM is not the same as evaluating it against a vulnerability database or enforcing severity policy.

Required correction: scan the exact built image digest (including OS packages and language ecosystems), define severity/exception/expiry policy, publish scan results with the image, and block promotion for unaccepted critical/high findings. Preserve a controlled exception process rather than silently suppressing findings.

### 20.6 P2 — Image provenance is generated but deployment-time provenance verification is not established

The GHCR build enables provenance and SBOM generation, and the Production Ansible task pins the application image by digest. However, the inspected Ansible deployment tasks pull the digest without a visible verification step that checks an approved signer/identity, source repository, source commit, build workflow and provenance predicate before deployment.

A digest establishes which bytes are requested; by itself it does not establish who built those bytes or whether they came from the approved workflow.

Required correction: define a trusted build identity and provenance policy, sign or attest the image using the approved identity, and verify the attestation against repository/workflow/ref policy before Ansible promotes the digest. Record the verified digest and source commit in release evidence.

### 20.7 P2 — Demo and Production have different artifact paths and assurance levels

The Demo workflow builds the React frontend, stages static assets and invokes the FastAPI Cloud CLI against the checked-out source SHA. Separately, main CI builds and publishes a GHCR image with provenance/SBOM, and the Ansible Production path deploys an image digest.

The Demo workflow verifies the runtime source SHA and performs useful smoke checks, but the inspected workflow does not promote the same GHCR image digest that the Production path consumes. Thus source revision parity is checked, while byte-for-byte artifact parity between Demo and Production is not established.

Required correction: document the intentional platform-specific build distinction. If artifact parity is a requirement, produce a single immutable release artifact and promote that artifact through compatible environments; otherwise retain explicit per-platform build attestations and compare source revision, dependency lock, build inputs and runtime contract.

### 20.8 Release engineering readiness summary

- Python dependency lock and frozen installation: **implemented**.
- Demo/Production environment separation: **documented and enforced by workflow intent; actual deployed isolation not inspected here**.
- Demo manual approval/change reference and exact-source CI gate: **implemented in workflow**.
- Demo runtime commit/environment/Python/readiness smoke checks: **implemented in workflow; not executed in this audit**.
- GHCR image tag by source SHA and digest output: **implemented**.
- BuildKit provenance and SBOM generation: **enabled; registry attestations not inspected**.
- Production application image deployment by digest: **implemented in Ansible task**.
- Docker base-image digest pinning: **not implemented in inspected Dockerfile**.
- OS package snapshot/version pinning: **not established**.
- Ansible PostgreSQL/Valkey image digest pinning: **not implemented in inspected Compose template**.
- Third-party GitHub Actions full-SHA pinning: **not implemented in inspected workflows**.
- Final container image vulnerability scan: **not established in inspected CI workflow**.
- Deployment-time provenance/signature verification: **not established in inspected Ansible deployment path**.
- Demo/Production byte-identical artifact promotion: **not established; separate deployment artifact paths**.
- Build, image scan, signature and deployment execution: **not performed in this audit**.

No application source changes, test executions, CI runs, image builds, registry operations, migrations, database operations or deployments were performed as part of this review.

## 21. Database Reliability, Transaction Integrity & Data Consistency

Scope: static review of active main implementations for POS checkout, payment webhook settlement, pending-sale cancellation, goods receipt, inventory movement service and ledger model/migration, SQLAlchemy session/engine configuration, outbox event creation/dispatch, and related integration test definitions. The review did not connect to any database, execute migrations or tests, run concurrent requests, inspect production schema state, or validate live backup/restore. Code-level mechanisms are distinguished from runtime evidence.

### 21.1 Positive controls confirmed

- POS checkout obtains a PostgreSQL transaction-scoped advisory lock derived from pharmacy ID and idempotency key before looking up an existing sale.
- Sale model and migration enforce unique pharmacy_id + idempotency_key and unique receipt number. Payment enforces unique sale_id + idempotency_key and unique provider reference.
- Replayed checkout requests compare product/quantity lines, discount and payment method (and cash received for cash sales); conflicting reuse returns HTTP 409 rather than creating another sale.
- Checkout locks eligible inventory lots with SELECT FOR UPDATE, orders FEFO by expiry then inventory ID, and allocates only available non-expired stock. Inventory mutations are routed through apply_inventory_movement.
- Inventory movement service uses a pharmacy-scoped transaction advisory lock, rechecks the immutable command for a repeated key, locks the target inventory row, validates on-hand/reserved invariants, and writes the balance update and movement journal in the caller's transaction.
- Inventory movement migration/model provide tenant-scoped idempotency uniqueness, lot identity foreign key, balance and delta checks, supported movement type checks, actor identity checks, and append-only UPDATE/DELETE/TRUNCATE triggers.
- Cash checkout, non-cash reservation, sale lines, payment state, allocation rows, inventory movements and the pos.sale.created outbox event are staged before one checkout commit. Insufficient stock explicitly rolls back the partial work.
- Payment webhook locks the sale, payment and inventory rows; checks HMAC-SHA256, event status and amount; settles or releases the existing reservations; writes corresponding inventory movements and aggregate version 2 outbox event in the same transaction.
- Pending-sale cancellation locks sale/payment/inventory records, releases reservations through the ledger, marks pending payments failed and writes a version 2 outbox event. Already-cancelled replay returns the terminal sale without repeating the release.
- Goods receipt uses a pharmacy-scoped movement idempotency key, locks an existing lot, enforces unique product_id + pharmacy_id + lot_number, and rolls back on integrity conflict.
- get_db rolls back when an exception escapes the request dependency and commits after a successful yield. Explicit route commits are present for transactional POS write paths.
- SQLAlchemy engine config includes pool_pre_ping, configurable pool size, max overflow, pool timeout and recycle; query duration/errors, connection hold time and pool occupancy/timeout metrics are instrumented.
- Outbox event creation deliberately does not commit or publish; it stages the event in the caller's business transaction. Dispatcher claims with FOR UPDATE SKIP LOCKED, uses lease/fencing tokens, preserves per-aggregate ordering, retries transient failures with exponential backoff/jitter, dead-letters permanent failures and bounds automatic attempts.
- Existing integration test definitions cover FEFO allocation, expired-lot exclusion, insufficient-stock rollback, same-key checkout replay, cash/card payment flows, failed-payment release, cancellation replay, movement idempotency, concurrent same-key movement and concurrent distinct-key stock adjustment.

### 21.2 P1 — Payment webhook authenticity is a shared-secret envelope, not a provider-specific replay-safe protocol

The active webhook verifies HMAC-SHA256 over the raw body using one PAYMENT_WEBHOOK_SECRET, then trusts normalized payment_id, provider_name, provider_payment_id, status and amount fields. Its docstring explicitly assigns provider-specific signature verification to an adapter before this endpoint. No provider event ID, signed timestamp/nonce, bounded replay window, key ID/rotation contract or provider-specific verifier is visible in this endpoint.

The payment state transition is idempotent for a repeated terminal status with the same provider payment ID, and the database has a unique provider reference. This limits duplicate effects after a successful first transition, but it does not establish provider-origin authenticity or freshness unless the upstream adapter reliably enforces those properties. If the shared secret is used directly by multiple senders or the endpoint is exposed without a verified provider adapter, a captured valid body remains replayable while the payment is pending.

Required correction: define and enforce a provider-specific verification boundary, validate signed timestamp and event ID, persist provider event IDs under a unique constraint, reject stale/replayed events, bind provider identity to the configured adapter, and test key rotation and duplicate/out-of-order delivery. Do not claim the current generic HMAC endpoint is equivalent to a full payment-provider webhook integration.

### 21.3 P1 — POS checkout has no explicit concurrent last-unit integration test in the inspected test module

The checkout implementation locks inventory rows and the movement service serializes balance changes. The inspected tests/integration/test_pos_checkout.py covers sequential checkout replay and insufficient stock rollback, but its test definitions do not include two simultaneous checkout requests competing for the last available unit. Separate inventory movement tests do exercise concurrent same-key idempotency and distinct-key oversell prevention, but that is not the same as concurrent end-to-end checkout including sale, allocation, payment and outbox records.

Required correction: add PostgreSQL-backed concurrent checkout tests for (a) two distinct idempotency keys competing for the last unit, (b) same-key concurrent identical requests, (c) same-key concurrent conflicting payloads, (d) multi-lot/multi-product overlapping allocations and deadlock behavior, and (e) concurrent webhook versus cancellation. Assert sale count, payment count, allocations, journal deltas, persisted stock and outbox versions after both transactions finish. Tests were not run in this audit.

### 21.4 P2 — Payment provider event identity and transition ordering are not fully represented

The Payment model uniquely constrains provider_name + provider_payment_id, but provider event identity is not stored independently. The webhook treats a repeated event as already processed only when the current payment status equals the incoming status and provider payment ID matches. Different event IDs for the same payment, provider-specific ordering, and explicit reconciliation of contradictory success/failure notifications are not represented as durable provider-event records.

Required correction: persist immutable provider event identity and payload digest, define an explicit payment transition state machine, and reconcile late/contradictory provider events through an auditable exception workflow rather than relying only on the current Payment status.

### 21.5 P2 — Tenant isolation is enforced in application queries and composite relationships, not proven by database row-level security

The inventory movement foreign key binds inventory ID, pharmacy ID and product ID together; movement idempotency and POS sale idempotency are pharmacy-scoped. POS routes call require_pharmacy_tenant, and the inventory movement service checks that the locked lot belongs to the supplied pharmacy.

These are valuable controls, but the inspected inventory movement migration does not enable PostgreSQL RLS or define tenant policies. A database credential capable of unrestricted table access can bypass application-level tenant predicates. This is a defense-in-depth gap, not evidence that the current API query paths leak tenants.

Required correction: decide and document whether Pharmacy Edge's DB role is intentionally a trusted single-tenant application role. If shared/multi-tenant DB credentials or direct SQL access are in scope, implement and test RLS with a transaction-local tenant context, least-privilege grants and connection-pool context reset tests. Do not introduce RLS without validating worker, migration, admin and background-task access paths.

### 21.6 P2 — Database connection budget is configured per process, not bounded against total deployment topology

The main SQLAlchemy engine defaults to pool_size=5, max_overflow=5 and pool_timeout=30 seconds, with environment-configurable values. These values apply to each process/engine instance. The repository also defines separate application and Celery worker processes and can run multiple replicas; no single deployment-wide calculation or enforced upper bound was established by the inspected code.

If each process/replica creates its own engine, aggregate possible PostgreSQL connections can exceed the intended database connection budget as replicas and workers scale. Pool timeout metrics exist, but a 30-second wait can create long request latency under saturation.

Required correction: calculate maximum connections across web replicas, Celery workers, beat/maintenance processes, migrations and operational access; reserve capacity for administration; set per-process pools accordingly; and validate with load tests and database-side connection metrics. Record the actual FastAPI Cloud/Neon connection budget separately; it was not inspected here.

### 21.7 P2 — POS receipt lot creation is protected by a unique constraint but has no explicit race-focused route test

Goods receipt first checks for an existing idempotency movement, then selects a matching lot FOR UPDATE; when no row exists it creates a new lot. A row lock cannot lock a row that does not yet exist. The unique constraint on product_id + pharmacy_id + lot_number is the final duplicate-lot guard, and the route converts an IntegrityError into HTTP 409 after rollback.

The database guard prevents two committed duplicate lot rows, but the inspected receipt tests establish sequential idempotency rather than concurrent first receipt of the same new lot. The losing request returns a conflict rather than transparently replaying the winning receipt.

Required correction: add a concurrent first-receipt test and decide whether HTTP 409 is the intended conflict contract or whether the losing transaction should reload the committed lot and resolve by idempotency key. Verify that different idempotency keys for the same lot cannot accidentally apply the same receipt twice.

### 21.8 P2 — Outbox provides durable at-least-once delivery, not end-to-end business application

The Edge outbox stores event IDs and aggregate versions, and the dispatcher uses leases/fencing and retries. The related architecture contract states that Central currently records a durable inbox receipt with processing_status=accepted; that acknowledgement is receipt, not application of sale/payment/inventory effects. The Central domain-event consumer and end-to-end reconciliation are not established by the reviewed implementation.

Required correction: retain the at-least-once delivery contract, implement an idempotent Central consumer with durable applied/rejected states, per-aggregate ordering and gap detection, and add reconciliation between Edge business ledgers and Central projections. Do not describe a Central accepted receipt as a completed cross-site transaction.

### 21.9 P2 — Backup, restore and disaster-recovery readiness cannot be established from application code

The inspected code and migration definitions establish transaction-level controls, not backup frequency, PITR retention, encryption, restore isolation, RPO/RTO, WAL/archive integrity or a tested recovery procedure. No live database configuration or backup artifacts were inspected.

Required correction: document per-environment backup ownership, encrypted backup storage, retention, PITR, restore drills, measured RPO/RTO, and post-restore reconciliation of inventory ledger, sale/payment state and outbox. A configured backup job alone is not evidence of recoverability.

### 21.10 Database and transaction readiness summary

- POS idempotency key serialization and database uniqueness: **implemented in code/schema**.
- FEFO row locking and stock allocation: **implemented in code**.
- Inventory movement ledger, balance checks and append-only triggers: **implemented in migration/model; live schema not verified**.
- Sale/payment/inventory/outbox atomic write boundary: **implemented in inspected route code**.
- Insufficient-stock rollback: **covered by integration test definition; not executed**.
- Sequential checkout replay and conflicting key reuse: **covered by integration test definition; not executed**.
- Concurrent inventory movement idempotency/oversell: **covered at movement-service level; not executed**.
- Concurrent end-to-end POS checkout last-unit race: **not covered in inspected test module**.
- Payment webhook HMAC and terminal replay handling: **implemented; provider-specific authenticity/freshness depends on an upstream adapter not established here**.
- Payment provider event ID/replay window: **not established**.
- Pending cancellation reservation release and replay: **implemented and represented in integration tests; not executed**.
- Goods receipt duplicate lot guard: **database unique constraint implemented; concurrent first-receipt route behavior not tested in inspected module**.
- SQLAlchemy pool limits and DB metrics: **implemented per process; total deployment connection budget not established**.
- Application-level tenant checks and composite lot identity FK: **implemented; RLS not established in inspected migration**.
- Edge outbox lease/retry/dead-letter: **implemented and represented in integration tests; not executed**.
- Central durable receipt: **implemented; Central business event application/reconciliation not established**.
- Backup/restore, PITR, RPO/RTO and disaster recovery: **not established by this static review**.
- Database connections, migrations, integration tests, load tests and restore drills: **not run**.

No application source changes, test executions, CI runs, database connections, migrations, data writes, backup operations or deployments were performed as part of this review.

## 22. System Architecture, Domain Boundaries & Integration Consistency

Scope: static review of the active FastAPI entry point and runtime router aggregator on main, the legacy router aggregator, both mounted authentication route modules, AI dependency composition, frontend package manifest and API-client generation script, and Central/Edge sync ingress/dispatcher contracts. This is a source-level architecture review only. No import graph tooling, application startup, OpenAPI generation, frontend build, Celery worker startup, network integration or end-to-end workflow was executed. Absence claims are limited to the inspected paths and repository search results.

### 22.1 Positive controls confirmed

- The runtime is a single FastAPI application entry point in src/pharmaviyum/main.py, which mounts the versioned API router, health router, middleware, lifespan-managed infrastructure and static frontend. This is consistent with a modular-monolith deployment rather than a fleet of independently deployed domain microservices.
- The active API router aggregator is explicitly src/pharmaviyum/api/v1/__init__.py and imports domain routers for AI, drug catalog, dashboard, ingestion, monitoring, medical devices, orders, patients, patient purchases, POS, sync, pharmacy entities, products and users.
- AI dependency construction is centralized in src/pharmaviyum/ai/dependencies.py. AIComponents owns the composition of LangGraphRAG, AgentHarness, MCPClient, checkpointer, evaluator and ingestion orchestrator, while the FastAPI lifespan initializes shared infrastructure once.
- AI request state has a separately documented patient-scoped HMAC namespace design, including an explicit no-patient scope and purpose-bound v4 namespace. The implementation/documentation explicitly avoids treating Redis memory or checkpoint IDs as global session identifiers.
- The Edge outbox dispatcher emits a versioned event envelope with immutable event ID, edge node, event type/schema version, aggregate identity/version and occurrence time. It authenticates to Central over HTTPS using enrolled node credentials, uses lease fencing and preserves per-aggregate ordering.
- Central sync ingress derives pharmacy identity from authenticated Edge node enrollment, rejects node identity mismatch, durably stores the inbox event and rejects reuse of an event ID with different content. The endpoint explicitly documents that accepted means durable receipt, not domain application.
- The repository has architecture decision records for Central/Edge offline-first design and patient-scoped AI state, plus a readiness roadmap that states the modular-monolith-first strategy and tenant/patient isolation invariants.

### 22.2 P1 — Two authentication route implementations are mounted in the same runtime API

The active aggregator imports and mounts both src/pharmaviyum/api/v1/auth.py and src/pharmaviyum/modules/auth/routes/login.py. The former defines /api/v1/auth/register, /api/v1/auth/token and /api/v1/auth/me, uses src/pharmaviyum.config, src.pharmaviyum.db.session.get_db and the legacy OAuth2/JWT helpers. The modular router defines /auth/login/access-token, /auth/refresh, /auth/logout, password recovery and reset, uses src.pharmaviyum.core.config, src.pharmaviyum.shared.core.database.get_session and a separate token helper set; it is included with prefix /api/v1, producing /api/v1/auth/... paths.

These are not merely two files with one inactive implementation: both are mounted. They expose overlapping authentication responsibilities through different token contracts, session dependencies, settings modules and lifecycle behavior. The route sets are not identical, so clients may obtain different token shapes and encounter different refresh/revocation semantics depending on endpoint used.

Required correction: define one canonical authentication domain and API contract; explicitly deprecate/remove or isolate the legacy route set; consolidate token issuer/audience/expiry, password policy, refresh rotation/revocation, user lookup and DB session dependencies; add OpenAPI route inventory and compatibility tests proving only intended endpoints are mounted. Do not migrate clients until token compatibility and existing sessions are accounted for.

### 22.3 P1 — Runtime router and legacy router aggregator create two competing API composition sources

main.py imports api_v1_router from src/pharmaviyum/api/v1/__init__.py. A separate src/pharmaviyum/api/v1/router.py builds api_router/system_router and includes different endpoints such as debug, feature flags and prescription placeholders. It is not imported by the inspected runtime entry point. The legacy file therefore does not describe the routes actually mounted by the application.

This creates a maintenance hazard: contributors can add a route to the legacy aggregator and assume it is live, or update one aggregator while leaving the runtime router unchanged. Prior static review also found endpoint behavior differs between the legacy prescription placeholder and the runtime pharmacy_entities prescription handlers.

Required correction: retain one authoritative router composition module, remove or clearly quarantine obsolete aggregators, and add a test that inspects the runtime app route table against an explicit expected route manifest. Generate API documentation only from the runtime-mounted app.

### 22.4 P1 — Multiple configuration and database-session namespaces weaken domain ownership

The active auth route modules import settings from both src.pharmaviyum.config and src.pharmaviyum.core.config, and database sessions from src.pharmaviyum.db.session and src.pharmaviyum.shared.core.database. The AI dependency layer separately uses src.pharmaviyum.database.AsyncSessionLocal. These distinct namespaces may be intentional compatibility boundaries, but the inspected active paths demonstrate multiple configuration/session entry points in one application.

This raises the risk of different DATABASE_URL, SECRET_KEY, token issuer/audience, transaction commit behavior or pool settings being consumed by different domains. It also complicates dependency overrides in tests and makes it harder to reason about one request's transaction boundary.

Required correction: define one canonical application Settings object and one canonical async session factory/dependency contract, then migrate domains incrementally with explicit compatibility adapters. Add startup assertions that critical settings agree during transition and tests that all mounted routes use the intended session factory and rollback/commit semantics. Do not blindly replace imports before comparing current settings models and database lifecycles.

### 22.5 P2 — API client generation is not a reproducible contract pipeline in the inspected frontend workflow

scripts/generate-api-client.sh checks a local /health endpoint on localhost:8000, then runs npx openapi-typescript-codegen against the live /openapi.json URL and writes to frontend/shadcn-admin/src/client. The frontend package manifest inspected does not declare openapi-typescript-codegen. The script does not pin the generator version, capture an OpenAPI artifact, validate a diff, or prove generated output is part of the frontend build/CI contract. A previous repository audit recorded that the expected generated client directory and POS service/model files were absent from the inspected branch; that state was not revalidated as a separate full-tree inventory in this section.

This makes client generation dependent on a developer's local running backend and an unpinned npx package resolution. API changes can therefore drift from TypeScript consumers without a deterministic CI failure.

Required correction: pin the generator as a dev dependency or tool, export OpenAPI from the exact source revision in CI, generate into a stable tracked or build artifact location, fail CI on uncommitted generated diff, and add contract tests for high-risk POS, inventory, auth and sync endpoints. Keep generated files machine-owned; do not hand-edit them.

### 22.6 P2 — Frontend package dependencies are range-based and API ownership is not visible from the manifest

The frontend package manifest uses caret ranges for many runtime and development dependencies, while the inspected script invokes an API generator through npx rather than a declared package dependency. A lockfile can make installs reproducible when frozen installation is consistently enforced, but the manifest alone does not prove that all frontend CI/deployment paths use the same lockfile and frozen mode. The package manifest also does not itself establish which feature owns each API client or how domain DTOs are mapped into UI models.

Required correction: verify the frontend lockfile is committed and every build path uses frozen lockfile installation; declare all code-generation tools; define domain-owned API modules and typed mapping boundaries; and prevent UI components from embedding transport-specific request logic for POS, inventory and clinical workflows.

### 22.7 P2 — Modular-monolith domain boundaries are visible in router names but not fully established as dependency rules

The runtime aggregator exposes domain-oriented routers, and the AI composition root centralizes AI services. However, this static review did not establish enforced package boundaries preventing POS from importing unrelated domain internals, API modules from directly depending on persistence models across domains, or shared modules from becoming a dumping ground. No import-linter/architecture test or dependency graph was executed or confirmed in the inspected workflow paths.

Required correction: define domain ownership and allowed dependency direction (API → application/use-case → domain ports; infrastructure adapters implement ports), keep cross-domain access behind explicit application contracts, and enforce rules with import-linter or equivalent CI architecture tests. Do not split into microservices until independent scaling, deployment or security boundaries justify the operational cost.

### 22.8 P2 — Central/Edge sync is a transport and durable-receipt capability, not a complete replicated domain

Edge outbox delivery and Central inbox receipt are implemented, including event identity, schema version, aggregate version and idempotent receipt. The current Central ingress explicitly stops after durable receipt; no Central domain-event consumer, inventory/finance application, aggregate gap recovery or end-to-end reconciliation was established in the reviewed implementation. This is consistent with the separate Central Inbox Consumer Readiness document and must not be represented as completed two-way synchronization.

Required correction: keep the transport contract separate from domain projection/application; implement a durable consumer lifecycle (received → validated → pending/order-gap → applied/rejected/quarantined), schema compatibility policy, per-aggregate checkpointing, replay and reconciliation. Until then, label Central sync as durable ingress/receipt, not full inventory or financial synchronization.

### 22.9 P2 — AI, Redis, Celery and API lifecycles are composed but not proven as independently scalable domain services

The FastAPI lifespan initializes Redis and AIComponents within the web process. AIComponents composes the agent, RAG, MCP, checkpointer and ingestion orchestrator. This is a valid modular-monolith composition approach, but the inspected files do not establish separate scaling/health ownership for AI execution, ingestion workers and API request serving. A web process can therefore have a broad startup dependency surface, while worker-specific lifecycle and failure isolation need separate verification.

Required correction: keep the monolith until metrics justify extraction, but define explicit lifecycle/readiness contracts per workload: web API, AI execution, Celery ingestion/dispatch, Redis and PostgreSQL. Ensure slow or optional AI initialization does not accidentally prevent unrelated pharmacy operations where product policy allows degraded operation; keep critical security/data dependencies fail-closed. Validate worker bootstrap and shutdown paths independently.

### 22.10 Architecture readiness summary

- Single FastAPI deployment with domain-oriented routers: **implemented**.
- One authoritative runtime router aggregator: **not achieved; a separate legacy aggregator remains**.
- Single authentication route/token contract: **not achieved; two auth implementations are mounted**.
- Single canonical settings/session dependency boundary: **not established across inspected domains**.
- AI composition root and shared lifespan initialization: **implemented**.
- Patient-scoped AI session/checkpoint design: **documented and implemented in reviewed paths; runtime E2E not executed here**.
- Frontend OpenAPI client generation: **script exists; pinned/reproducible CI contract not established**.
- Enforced modular-monolith dependency rules: **not established in inspected workflows**.
- Versioned Edge outbox and durable Central inbox receipt: **implemented in reviewed paths**.
- Central domain-event application and reconciliation: **not established**.
- Separate workload lifecycle/readiness contracts: **not fully established by this review**.
- Application startup, OpenAPI generation, frontend build, Celery startup, architecture tests and end-to-end sync: **not executed**.

No application source changes, test executions, CI runs, database connections, migrations, frontend builds, worker starts, sync operations or deployments were performed as part of this review.

## 23. Pharmacy Domain Completeness & Business Workflow Integrity

Scope: static review of active POS, pharmacy entity, order and patient-purchase API modules; Inventory, InventoryMovement, Prescription, Supplier and Order models; POS and inventory integration-test definitions; selected authenticated frontend routes; and the existing pharmacy workflow traceability evidence. This section assesses whether business capabilities form complete executable workflows, not whether their names appear in navigation or documentation. No tests, frontend build, API requests, database queries, migration checks or live pharmacy operations were executed. Findings describe repository source only.

### 23.1 POS sale lifecycle — transactional backend exists; pharmacist workflow is incomplete

Confirmed backend capabilities:
- Pharmacy-scoped product search and lot lookup expose available stock, reservations, lot number and expiry; expired lots are excluded from sellable availability, while missing expiry is surfaced as a flag.
- Checkout validates pharmacy membership, active sellable products, positive total and cash received; it creates sale/line/payment records, allocates stock FEFO (expiry then inventory ID), and records inventory movements plus a versioned outbox event in the same transaction.
- Cash checkout decrements stock and completes payment; external payment checkout reserves stock until the signed webhook settles or releases it.
- Tenant-scoped idempotency and advisory locking protect repeated checkout requests; same-key conflicting request content returns HTTP 409.
- A specific sale can be read by ID. Pending-payment cancellation releases reservations, marks pending payments failed and is replay-safe.

Business workflow gaps:
- The active React POS feature component returns null. The route exists but does not provide a usable cashier workspace.
- Checkout request and sale model do not carry patient or prescription identity. The POS transaction therefore cannot prove that a required prescription was checked and linked before dispensing.
- The inspected POS router exposes single-sale lookup, not a sale-list/history endpoint or cashier/register session lifecycle.
- Cancellation is limited to awaiting-payment sales. It is not a completed-sale return, refund, void or compensating stock transaction.
- The POS integration test module covers important checkout, FEFO, idempotency and payment paths, but those tests were not executed in this audit. A full browser journey is not established.

Assessment: **Partial — transactional POS backend primitives exist; end-user dispensing and cashier workflow is not complete.**

### 23.2 Prescription validation and dispensing — record CRUD is not a dispensing workflow

The Prescription model stores patient ID, optional product ID, prescription number, dosage, instructions, status and issue/expiry timestamps. The active pharmacy-entity API exposes list/create endpoints protected by CurrentSuperuser. The create handler constructs a Prescription from the request and commits it; the inspected handler does not validate that the patient belongs to a pharmacy authorized for the operator, nor does it bind the record to an authenticated pharmacist workflow. The model has no pharmacy ownership field.

Checkout does not accept a prescription reference or patient ID. No source-level transition was established for prescription verification, validity/expiry checks, pharmacist review, remaining repeats/refills, controlled-medicine rules, dispense quantity, partial dispensing, or linking dispensed items and lot allocations back to the prescription.

Required correction: design a jurisdiction-aware prescription aggregate with explicit pharmacy/patient ownership, verified prescriber/source, normalized prescribed medication and directions, validity and refill rules, pharmacist review/override audit, and dispense records linked to POS sale lines and exact lot allocations. Enforce the rules server-side; AI must not authorize or bypass dispensing.

Assessment: **Partial at data-record level; prescription-to-dispensing workflow not established.** This is a P0 business and safety dependency before claiming prescription dispensing.

### 23.3 Defectura and automatic replenishment — no executable replenishment domain established

The active inventory model stores reorder_level, and GET /api/v1/inventory supports a low_stock filter based on quantity minus reserved quantity. Mortarium has read-only low-stock/inventory overview capability. These provide stock visibility, not Defectura workflow execution.

The inspected active API/model paths and repository code search did not establish a Defectura entity, demand calculation, replenishment proposal, approval state, supplier/source selection, or conversion into a purchase order. There is no confirmed lifecycle for a manually curated shortage list either.

Required correction: retain Defectura as one Inventory workflow with two demand-input mechanisms: (1) manual pharmacist/manager selection of required medicines and pharmacy goods; (2) system-generated proposals from configured min/max or reorder policies, sales velocity, lead time, safety stock and eligible on-hand/reserved quantities. Both mechanisms should produce one reviewable demand document with source, rationale, suggested quantity, exclusions, approver and status. Approval should create or update a procurement request; it must not silently create a supplier order or mutate stock.

Assessment: **Not established as an executable domain workflow.** Low-stock filtering is implemented; Defectura and automatic replenishment execution are not confirmed.

### 23.4 Procurement and supplier purchasing — supplier directory and standalone receiving only

Supplier is a directory record with name, code and contact fields. The active supplier API exposes privileged list/create operations. The reviewed source did not establish PurchaseOrder, purchase-order lines, supplier-product terms, approval, submission, acknowledgement, delivery, invoice matching, or supplier-return lifecycle.

POST /api/v1/pos/inventory/receive can receive a quantity into a pharmacy lot and records a goods_receipt movement with idempotency. Its request is not linked to a supplier, purchase order, purchase-order line, invoice, delivery note or discrepancy record. It is therefore a standalone stock-receipt operation, not procurement receiving.

Required correction: implement a traceable lifecycle such as draft → submitted → approved → sent → partially received / received → invoiced / closed, with explicit cancellation and discrepancy states. Receiving must match purchase-order lines and preserve expected, delivered, accepted, rejected and outstanding quantities, supplier documents, lot/expiry details, user approvals and inventory movement references. Partial receipts and duplicate delivery-document handling require idempotency and concurrency tests.

Assessment: **Partial — supplier records and standalone lot receipt exist; procurement-to-inventory traceability is not established.**

### 23.5 Inventory, lot control and stocktake — movement primitives exist; operational control process is incomplete

Confirmed:
- Inventory is pharmacy- and product-scoped, lot-aware, with on-hand, reserved and reorder quantities plus expiry.
- Database checks enforce non-negative quantity/reservation and reservation not exceeding on-hand.
- InventoryMovement records typed stock/reservation deltas, before/after balances, actor, reason, reference and idempotency key. Its model restricts movement semantics and ties the movement to the exact pharmacy/product/lot identity.
- Physical balance changes in the reviewed operational paths use the movement service. POS uses FEFO and row locks; goods receipt rejects expired lots.
- Inventory metadata edits and manual stock adjustments are restricted to CurrentSuperuser in the reviewed pharmacy entity API. Physical quantity cannot be changed through the metadata update schema.

Gaps:
- No complete stocktake/cycle-count aggregate was established: no count session, blind/dual count, frozen snapshot, variance review, approval or posting lifecycle.
- The adjustment endpoint is a privileged one-step delta operation; a reason and idempotency key are required, but a count evidence record and separate variance approval are not established.
- Expiry visibility and FEFO exist, but an operational quarantine, recall, near-expiry disposition and controlled write-off workflow was not established.
- A legacy ProductBatch model/list endpoint remains separate from pharmacy-owned Inventory lots; the endpoint is superuser-only and the model has no pharmacy_id. It must not be treated as the authoritative tenant-scoped operational lot workflow.

Assessment: **Partial — strong balance and movement primitives exist; stocktake, variance governance and expiry-disposition workflows are not established.**

### 23.6 Inter-pharmacy transfers — movement vocabulary is not a transfer workflow

The InventoryMovement model permits transfer_in and transfer_out movement types, but the reviewed active API and model paths did not establish a transfer aggregate or dispatch/receipt endpoints. The frontend transfers route returns null. No end-to-end transfer workflow test was identified in the reviewed traceability evidence.

Required correction: implement a transfer document with source and destination pharmacies, requested/approved quantities, product and exact lot identity, dispatch confirmation, in-transit custody, destination receipt, partial receipt, rejection, loss/damage discrepancy, cancellation-before-dispatch and paired source/destination movements. Enforce both tenant authorizations, prevent self-transfer and overselling, preserve aggregate version and idempotency, and reconcile interrupted/offline transfers.

Assessment: **Not established.** Movement enum values alone do not prove transfer execution.

### 23.7 Returns, refunds, voids and supplier returns — no complete compensating workflow established

The reviewed POS API supports cancellation only before external payment settlement. No completed-sale customer return/refund endpoint, return authorization, returned-item condition/eligibility decision, refund provider operation, receipt reversal, or auditable stock disposition was established.

The InventoryMovement model allows an accepted_return type, but the existence of a movement type does not implement the customer-return workflow. No source path was established that verifies the original sale line and lot, prevents returning more than sold/previously returned, records refund state, and posts the correct stock or quarantine movement. Supplier return is also not established.

Required correction: distinguish customer return, refund, void, pending-sale cancellation and supplier return as separate state machines. Link every return to the original sale/payment/line/lot; enforce cumulative returned quantity; capture reason, condition, approval and refund status; use compensating ledger entries rather than editing or deleting the original sale. Returned stock must not become sellable automatically: require explicit inspection/disposition.

Assessment: **Not established as an executable workflow.**

### 23.8 Patient history and online orders — separate legacy records, not unified order fulfillment

The pharmacist-facing patient history endpoint requires explicit pharmacy and purpose, active membership, active patient ownership and writes metadata-only PHI access audit. It returns a minimal purchase projection from PatientPurchase.

The endpoint's own docstring states that it returns only the legacy PatientPurchase ledger; POS Sale history is not represented until the sale/patient linkage is implemented. Thus the pharmacist history surface is access-controlled, but it is not yet a complete history of the transactional POS sales audited in Section 23.1.

The Order model contains patient_id, total_amount, status and created_at, but no item lines. Creating an order stores a generic pending record. Completing it creates one aggregate PatientPurchase row with category order and quantity one, not product-level fulfillment, batch allocation, dispensing or pickup evidence. The orders API is superuser-gated for create/status mutation in the reviewed paths.

Required correction: define whether Order is a true fulfillment aggregate or remove the misleading product/dispensing implication. If retained, add item-level lines, price snapshots, stock reservation, fulfillment/pickup, cancellation and payment states. Link completed POS sales to patient history through explicit, privacy-governed references, not by inferring a patient from a cashier session.

Assessment: **Partial — patient history read controls exist; POS-to-patient history completeness and item-level order fulfillment do not.**

### 23.9 Frontend workflow delivery and test evidence

The inspected active frontend route components for POS, inventory, procurement, transfers, prescriptions and patients render null (POS mounts a feature component that itself returns null). Sidebar entries and generated routes therefore do not represent usable pharmacy workspaces.

Backend test definitions provide meaningful coverage for POS checkout/FEFO/payment and inventory movement atomicity/idempotency. They do not establish a complete browser workflow across patient selection, prescription verification, dispensing, payment, receipt and patient history. The reviewed workflow evidence also identifies no procurement, transfer, return/refund, stocktake or shift-close end-to-end tests.

No test was executed during this audit. Test-file presence is not a passing test result.

### 23.10 Prioritized domain readiness summary

- POS transaction backend, FEFO allocation, payment reservation/settlement, cancellation of pending payment: **implemented in reviewed source; tests defined, not run**.
- Usable POS cashier UI: **not implemented in inspected active component**.
- Patient-linked POS sale and prescription-linked dispensing: **not established**.
- Prescription record CRUD: **implemented for privileged operators; clinical dispensing lifecycle not established**.
- Inventory lot balance, movement ledger, idempotent adjustment and low-stock query: **implemented in reviewed source**.
- Defectura manual demand list and automatic replenishment proposal: **not established**.
- Supplier directory and standalone lot receiving: **implemented in reviewed source**.
- Purchase orders, line-level procurement, partial receipt, invoice/delivery matching and discrepancy approval: **not established**.
- Stocktake/cycle count and variance approval: **not established**.
- Inter-pharmacy transfer dispatch/receipt: **not established**.
- Completed-sale returns/refunds and supplier returns: **not established**.
- Pharmacist patient-history access control and PHI audit: **implemented in reviewed source; it reads the legacy PatientPurchase ledger**.
- Unified POS sale history and item-level order fulfillment: **not established**.
- Frontend workflows for the reviewed operational routes: **not delivered in inspected active components**.
- Browser E2E, migrations, database schema, payment-provider integration and live runtime behavior: **not validated**.

Recommended delivery order:
1. Restore a usable POS workspace and link each sale to a patient only through explicit, authorized selection.
2. Implement prescription verification/review and dispense records linked to sale lines and exact lots before enabling prescription-required dispensing.
3. Implement Defectura as the single replenishment workspace, supporting manual demand and automatic proposals.
4. Add purchase orders and supplier-linked receiving with partial quantities and discrepancy controls.
5. Add stocktake/variance approval, expiry quarantine/write-off and inter-pharmacy transfer lifecycles.
6. Add completed-sale returns/refunds and supplier returns as auditable compensating workflows.
7. Reconcile patient history and online orders against the canonical sale/fulfillment ledger.
8. Add browser-level business journey tests and execute them in isolated CI/staging before making delivery claims.

No application source changes, test executions, CI runs, database connections, migrations, payment-provider calls, frontend builds, stock mutations or deployments were performed as part of this review.
