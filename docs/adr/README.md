# Architecture Decision Records

ADRs capture decisions that affect system boundaries, data ownership, security, operations or long-term implementation.

## Decision index

| ID | Decision | Status | Implementation note |
|---|---|---|---|
| [ADR-0001](./ADR-0001-websocket-gateway.md) | Keep WebSocket inside FastAPI initially | Accepted | Current handlers are development templates; production auth and controls are incomplete |
| [ADR-0002](./ADR-0002-offline-first-central-edge.md) | Central + Pharmacy Edge target topology | Proposed | Synchronization and Ansible foundations do not prove fleet readiness |
| [ADR-0003](./ADR-0003-patient-scoped-ai-state.md) | Bind Mortarium state to patient context | Proposed; staging gate pending | Implementation merged by [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287); staged E2E evidence and production activation are not confirmed |
| [ADR-0004](./ADR-0004-offline-ragas-evaluation.md) | Isolate Ragas in offline evaluation | Accepted | Not a production request-path dependency |

## Status vocabulary
- **Proposed:** not yet an accepted operational contract; implementation and/or validation may be incomplete.
- **Accepted:** direction approved; implementation may still be partial.
- **Implemented:** code, tests and operational controls satisfy the decision; link evidence.
- **Superseded:** replaced by a later ADR; retain for history.

An Accepted ADR does not prove production readiness.

## ADR authoring standard
Include status/date, context, constraints, decision, alternatives, consequences, security/data implications, migration plan, validation evidence and references. Do not silently rewrite a historical decision. Create a new ADR that supersedes it when architecture changes.
