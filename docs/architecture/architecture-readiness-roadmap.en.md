# Architecture Readiness Roadmap

**Review date:** 2026-11-19  
**Scope:** architecture and operational readiness of Pharmaviyum ERP/CRM  
**Decision:** retain the Modular Monolith; close evidence gaps before adding distributed-system complexity.

This roadmap converts the current Architecture Vision, ADR register, Offline Capability Matrix and Mortarium RAG audit into verifiable engineering gates. It is not a certification of production safety or regulatory compliance.

## 1. Target architecture principles

1. **Modular monolith first.** Keep one deployable FastAPI application while enforcing explicit domain boundaries. Extract a service only when independent scaling, ownership, security isolation or release cadence is demonstrated by measured evidence.
2. **Tenant isolation is a system invariant.** Tenant identity comes from authenticated server-side authorization, never from an untrusted request field alone. Every query, cache, memory namespace, checkpoint, event and background job must preserve tenant scope.
3. **Patient context is a separate security boundary.** Patient-scoped state must not be reused by another patient, including the explicit no-patient scope.
4. **PostgreSQL is the durable source of truth.** Redis is an acceleration and short-lived state layer, not the only record of a business transaction.
5. **Events are contracts, not implementation details.** Use transactional outbox/inbox, schema versions, idempotency keys, ordering rules and replay controls for Central/Edge synchronization.
6. **AI is an evidence-producing subsystem.** Retrieval provenance, citation validation, clinical safety evaluation, context isolation and human escalation are part of the product contract.
7. **Operational readiness is part of architecture.** A capability is not complete until it has telemetry, alerting, recovery, migration and rollback procedures.

## 2. Readiness gates

| Gate | Priority | Required evidence | Exit condition |
|---|---|---|---|
| Patient and tenant isolation | P0 | API, Redis and PostgreSQL checkpoint integration tests; cross-tenant rejection; sync/stream parity | All synthetic isolation scenarios pass in CI; staged verification plan approved |
| Inventory integrity | P1 | Append-only movement ledger; atomic sale/return/transfer mutations; idempotency and reconciliation tests | Every stock mutation is represented by a durable movement; reconciliation detects drift |
| Pharmacy RBAC and pricing | P1 | Tenant-scoped role matrix, currency/price policy, migration and authorization tests | No cross-pharmacy read/write path; roles and price rules are explicit and auditable |
| Central/Edge synchronization | P1 | Versioned event contracts, transactional outbox/inbox, ordering, retries, deduplication, conflict policy | Replay and duplicate delivery are safe; offline/online transitions pass integration tests |
| RAG quality and safety | P1 | Versioned RU/EN golden set; Ragas and domain metrics; citation and negation tests | Quality thresholds are explicit, reproducible and blocking in CI for safety regressions |
| Production operations | P1 | OTel traces/metrics/logs, PHI redaction, SLOs, alerts, backup restore and rollback drills | Critical user journeys have measurable SLOs and tested recovery procedures |
| Architecture governance | P2 | ADR ownership, dependency rules, threat model, data classification, change review | Material decisions have an owner, alternatives, consequences and validation evidence |

## 3. Work sequence

### Gate 0 — Prove patient and tenant isolation

The patient-scoped HMAC namespaces for API sessions, Agent checkpoints and RAG checkpoints are present on `main` through PR #287. Unit tests verify distinct namespace derivation. That is necessary but not sufficient.

Required integration sequence using synthetic records and disposable services:

- Reuse one client session for Patient A, Patient B and no-patient requests.
- Exercise both synchronous and streaming API routes.
- Verify the API rejects a patient that does not belong to the authenticated pharmacy.
- Persist and retrieve Redis short-term memory, summary and episodic state without cross-scope reads.
- Persist LangGraph checkpoints in PostgreSQL and verify independent thread state.
- Verify missing production/staging `SECRET_KEY` fails closed.
- Document the impact of secret rotation and legacy checkpoint retention before changing keys or deleting old state.

**Release rule:** do not claim the patient-isolation control is production-verified until CI evidence and a controlled staging run both exist. Never use real patient records for these tests.

### Gate 1 — Make inventory correctness structural

Implement ADR-0006 as the canonical inventory write model:

- Append-only movement records for receipts, sales, returns, adjustments and transfers.
- Atomic transaction boundary between the business command, stock projection and outbox event.
- Idempotency key bound to tenant, command type and aggregate.
- Explicit lot/batch and expiry allocation rules.
- Reconciliation job comparing the stock projection with movement history.
- No direct stock quantity mutation outside the inventory domain service.

**Release rule:** migrate each write path incrementally; retain a reconciliation report and rollback path for every migration stage.

### Gate 2 — Enforce tenant-scoped authorization and pricing

Implement ADR-0005 as an executable authorization model:

- Define role × resource × action matrix, including cashier, pharmacist, manager and tenant administrator.
- Resolve pharmacy scope from authenticated membership and enforce it in application services and database queries.
- Define currency, tax, rounding, price-list and effective-date policies.
- Add negative tests for cross-tenant reads, writes, exports, background jobs and AI tools.
- Record privileged changes in an append-only audit trail.

**Release rule:** no tenant-scoped feature is complete based only on UI hiding or route-level checks.

### Gate 3 — Make Central/Edge synchronization deterministic

Complete ADR-0002 and ADR-0007 with an explicit protocol:

- Transactional outbox at the Edge and durable inbox at Central.
- Immutable event ID, tenant ID, aggregate ID/version, schema version and occurred-at timestamp.
- Idempotent consumer and duplicate-payload conflict detection.
- Per-aggregate ordering and gap detection.
- Retry/backoff, poison-message quarantine and operator replay.
- Explicit conflict policy for each offline-capable command.
- Version compatibility and staged rollout for Edge nodes.

**Release rule:** offline cash sale, local stock lookup and local transaction persistence must survive restart and replay without double-posting. Regulated/online-only operations remain blocked offline as specified in the capability matrix.

### Gate 4 — Treat RAG as a measurable clinical evidence pipeline

- Maintain a versioned golden dataset in Russian and English with provenance and reviewer approval.
- Measure retrieval recall@k, MRR/nDCG, context precision/recall, faithfulness and answer relevancy.
- Keep domain-specific checks for citation correctness, medication entity/dosage/form accuracy, negation preservation, clinical hallucination and patient-context isolation.
- Test prompt injection in user queries, retrieved documents, memory summaries and tool outputs.
- Make reranker, RRF and contextual-compression settings either wired to runtime or removed from configuration; avoid configuration that appears active but is ignored.
- Preserve exact source IDs through retrieval, generation, reviewer revision and API response.
- Keep Ragas and expensive evaluators outside the production request path; run deterministic safety regression checks in CI.

**Release rule:** no model or retrieval change is promoted solely on anecdotal examples. Publish dataset version, metric deltas and known failure classes.

### Gate 5 — Operationalize the platform

- Propagate trace context across FastAPI, SQLAlchemy, Redis, Celery, MCP and LLM calls.
- Redact patient identifiers, prompts, retrieved text, tokens and credentials from logs and span attributes.
- Define SLOs for login, POS checkout, inventory mutation, AI response and Edge synchronization.
- Alert on error budget burn, queue age, outbox/inbox lag, database pool saturation, Redis availability and AI provider failures.
- Test database backup restoration, migration forward/rollback strategy, Redis loss and provider outage.
- Use readiness probes that validate dependencies and initialization, not merely process liveness.
- Keep production migrations additive and explicitly approved; never bootstrap or reset a non-empty production database.

## 4. Architecture Definition of Done

A material capability is **Implemented** only when all applicable items are true:

- [ ] An accepted ADR or an explicit documented reason why no ADR is needed.
- [ ] Domain ownership and allowed dependency direction are clear.
- [ ] Authentication, tenant scope and patient/data classification are enforced server-side.
- [ ] Database constraints and transaction boundaries protect invariants.
- [ ] Unit, integration and failure-path tests cover the contract.
- [ ] CI runs the relevant tests and security checks.
- [ ] Metrics, traces and privacy-safe logs make failures diagnosable.
- [ ] Migration, rollback, retention and recovery behavior are documented.
- [ ] A runbook identifies operator action and escalation criteria.
- [ ] Production activation has evidence separate from code merge.

ADR status vocabulary must remain strict: **Proposed** is not approved; **Accepted** approves direction; **Implemented** requires code, tests and operational evidence; **Superseded** preserves historical context.

## 5. Explicit non-goals

- Do not split the Modular Monolith into microservices without measured need.
- Do not treat Redis as the system of record for sales, inventory or clinical records.
- Do not enable offline banking authorization, fiscalization, e-prescriptions or regulated workflows without jurisdiction-specific approval and verified integration.
- Do not claim HIPAA/GDPR or other regulatory compliance from architecture documents alone.
- Do not rotate HMAC secrets or purge legacy checkpoints without a retention, migration and rollback plan.

## 6. Current evidence boundary

As of this review:

- Patient-aware API, Agent and RAG namespace derivation is present on `main` via PR #287.
- Unit-level namespace tests exist.
- Integration fixtures for PostgreSQL and Redis exist in the repository.
- The new synthetic API/Redis/PostgreSQL isolation integration suite is being proposed separately; its CI result and staged execution must be checked before treating the gate as passed.
- ADR-0005, ADR-0006, ADR-0002 and ADR-0007 remain architectural work, not completed production capabilities.
- Production readiness, clinical safety and regulatory compliance are not inferred from a successful code merge.

**Review cadence:** revisit this roadmap after each gate, update evidence links and owners, and do not upgrade maturity labels without test and operational proof.
