# Pharmacy Workflow Documentation

This section describes the operational model of a pharmacy. It is the business workflow reference; API contracts, database models and tests remain the source of truth for what is currently executable.

## Canonical documents
- [Pharmacy workflow — English](./pharmacy-workflow.en.md): branch operations, catalog, patients, prescriptions, dispensing, POS, inventory, procurement, transfers, returns, audit and Mortarium.
- [Pharmacy workflow — Russian](./pharmacy-workflow.ru.md): Russian-language companion.
- [Mortarium pharmacy operations](../ai/mortarium-pharmacy-operations.md): pharmacist-facing AI workflows and tool boundaries.
- [System context](../architecture/system-context.md): technical component and authority boundaries.
- [Offline capability matrix](../devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md): offline support and restrictions.

## End-to-end operational chain
Supplier and purchase order → receiving and discrepancy check → batch/lot/expiry registration → inventory availability → pharmacist workspace and product search → patient/prescription validation when required → FEFO batch selection → cart and sale validation → payment and receipt → inventory movement and audit → patient/transaction history → analytics and optional Mortarium assistance.

This is a business sequence, not proof that every step is integrated end to end in the deployed application. Benchmark and load-test documents track implementation gaps. Do not claim a completed POS/dispensing scenario based only on a list endpoint or a rendered UI.

## Domain invariants
- Tenant and branch ownership must be established server-side.
- Drug reference, medicinal product, pharmacy SKU, batch and inventory balance are distinct concepts.
- A generic product is not automatically interchangeable with a reference product.
- Stock changes require a traceable business event.
- Batch/expiry-aware dispensing follows applicable FEFO and professional rules.
- Returns, cancellations, write-offs, recalls and transfers require explicit state transitions and audit history.
- Prescription and controlled-medicine checks depend on jurisdiction and must not be bypassed by AI.
- AI suggestions do not authorize dispensing, payment, stock mutation or regulatory exceptions.
- Only workflows explicitly marked offline-capable in the capability matrix may proceed offline.

## Workflow specification standard
For each workflow, document actor/role, preconditions, authorization scope, input validation, state transitions, idempotency, transactional side effects, failure/compensation behavior, offline policy and tests. Mark incomplete behavior as a requirement or target, never as implemented capability.

## Implementation traceability

- [Pharmacy workflow implementation traceability — English](./PHARMACY_WORKFLOW_TRACEABILITY.md)
- [Трассировка реализации аптечных процессов — Русский](./PHARMACY_WORKFLOW_TRACEABILITY.ru.md)

The matrix maps each operational process to repository models, APIs, frontend routes, tests and evidence-based implementation status. It is a source-level audit, not a production validation.

## P0 implementation audit

- [P0 Pharmacist Workspace implementation audit — English](./P0_PHARMACIST_WORKSPACE_IMPLEMENTATION_AUDIT.md)
- [Аудит реализации P0 Pharmacist Workspace — Русский](./P0_PHARMACIST_WORKSPACE_IMPLEMENTATION_AUDIT.ru.md)

This source-level audit records current endpoint contracts, authorization boundaries, frontend/client state and required implementation dependencies. It is not production validation.

## P0 delivery gates

- [P0 Pharmacist Workspace acceptance gates — English](./PHARMACIST_WORKSPACE_P0_ACCEPTANCE.md)
- [Критерии приёмки P0 Pharmacist Workspace — Русский](./PHARMACIST_WORKSPACE_P0_ACCEPTANCE.ru.md)
- [P0.2 Patient, Prescription and Dispensing domain contract — English](../architecture/P0_2_PRESCRIPTION_DISPENSING_DOMAIN_CONTRACT.md)
- [Доменный контракт P0.2: пациент, рецепт и отпуск — Русский](../architecture/P0_2_PRESCRIPTION_DISPENSING_DOMAIN_CONTRACT.ru.md)

The P0.2 contract is a proposed design gate. It does not claim that the workflow has been implemented or validated.
