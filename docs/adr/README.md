# Architecture Decision Records

[English](README.md) · [Русский](README.ru.md)

ADRs capture decisions that affect system boundaries, data ownership, security, operations or long-term implementation.

## Decision index

| ID | Decision | Status | Implementation note |
|---|---|---|---|
| [ADR-0001](./ADR-0001-websocket-gateway.md) · [RU](./ADR-0001-websocket-gateway.ru.md) | Keep WebSocket inside FastAPI initially | Accepted | Current handlers are development templates; production auth and controls are incomplete |
| [ADR-0002](./ADR-0002-offline-first-central-edge.md) · [RU](./ADR-0002-offline-first-central-edge.ru.md) | Central + Pharmacy Edge target topology | Proposed | Synchronization and Ansible foundations do not prove fleet readiness |
| [ADR-0003](./ADR-0003-patient-scoped-ai-state.md) · [RU](./ADR-0003-patient-scoped-ai-state.ru.md) | Bind Mortarium state to patient context | Proposed; staging gate pending | Implementation merged by [PR #287](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/287); staged E2E evidence and production activation are not confirmed |
| [ADR-0004](./ADR-0004-offline-ragas-evaluation.md) · [RU](./ADR-0004-offline-ragas-evaluation.ru.md) | Isolate Ragas in offline evaluation | Accepted | `eval` group in `pyproject.toml`; not a production request-path dependency |
| [ADR-0005](./ADR-0005-tenant-scoped-pricing-and-pharmacy-rbac.md) · [RU](./ADR-0005-tenant-scoped-pricing-and-pharmacy-rbac.ru.md) | Tenant-scoped pricing and pharmacy RBAC | Proposed | Requires explicit currency policy, additive data migration and pharmacy-scoped role administration |
| [ADR-0006](./ADR-0006-inventory-movement-ledger.md) · [RU](./ADR-0006-inventory-movement-ledger.ru.md) | Append-only inventory movement ledger | Proposed | Inventory remains the balance projection; all mutation paths and reconciliation must be migrated and verified |\n| [ADR-0007](./ADR-0007-central-inbox-consumer.md) · [RU](./ADR-0007-central-inbox-consumer.ru.md) | Ordered, idempotent Central Inbox domain consumer | Proposed | Inbox is receipt-only; stock baseline/events and source-aware sale projection block consumer activation |

## Status vocabulary
- **Proposed:** not yet an accepted operational contract; implementation and/or validation may be incomplete.
- **Accepted:** direction approved; implementation may still be partial.
- **Implemented:** code, tests and operational controls satisfy the decision; link evidence.
- **Superseded:** replaced by a later ADR; retain for history.

An Accepted ADR does not prove production readiness.

## ADR authoring standard
Include status/date, context, constraints, decision, alternatives, consequences, security/data implications, migration plan, validation evidence and references. Do not silently rewrite a historical decision. Create a new ADR that supersedes it when architecture changes.
