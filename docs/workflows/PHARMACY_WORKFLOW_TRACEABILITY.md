# Pharmacy Workflow Implementation Traceability

[English](./PHARMACY_WORKFLOW_TRACEABILITY.md) · [Русский](./PHARMACY_WORKFLOW_TRACEABILITY.ru.md)

**Audit type:** source-level implementation traceability  
**Baseline inspected:** `main` at `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`  
**Documentation branch:** `docs/pharmacy-business-value-kpis`  
**Runtime / production access:** none

## 1. Purpose and evidence rules

This matrix connects the 12 operational workflow groups to repository evidence: domain models, API contracts, frontend routes/components, and automated tests.

A model, endpoint, navigation item, mock screen, RAG document, or test plan does not by itself prove that a complete pharmacy workflow is executable.

Status labels:

- **Implemented + tested (backend):** a real API/domain transition exists and a relevant automated test exercises its behavior. This does not imply a complete UI or production validation.
- **Partial:** some domain or API capability exists, but one or more required workflow transitions, controls, UI surfaces, or tests are missing.
- **Not implemented / not verified:** no executable end-to-end capability was established from the inspected source.
- **AI guidance only:** Mortarium can explain a workflow or read authorized ERP data; it does not execute the business transaction.

## 2. Workflow traceability matrix

| # | Pharmacy process | Domain / API evidence | Frontend evidence | Test evidence | Source-based status |
|---:|---|---|---|---|---|
| 1 | Opening preparation and shift readiness | No shift-opening entity, register-opening API, opening checklist state, or staff readiness transaction was identified. | No operational shift-opening screen was identified. | No shift-opening test was identified. | **Not implemented / not verified.** |
| 2 | Patient consultation and medicine dispensing | Product and pharmacy inventory models; POS product search, lot lookup, checkout, FEFO allocation, payment state, receipt, inventory movement and outbox event. Checkout request has no patient or prescription reference, so it is not a patient-linked clinical dispensing workflow. | Active POS route imports `Pos`, but `frontend/shadcn-admin/src/features/pos/index.tsx` currently returns `null`. Patient route is also a null component. | `tests/integration/test_pos_checkout.py` covers checkout, FEFO, stock movement, idempotency and payment webhook behavior. | **Partial.** Transactional POS backend is implemented and integration-tested; patient consultation, prescription linkage and usable POS UI are not established. |
| 3 | Prescription and treatment-order clarification | `Prescription` model and privileged list/create endpoints under `/api/v1/prescriptions`. The separate placeholder prescription router returns an empty list / 404 and is not the operational implementation. Checkout does not accept or validate a prescription. | `prescriptions.tsx` returns `null`. | No prescription-to-dispensing integration test was identified. | **Partial.** Basic privileged record CRUD exists; verification, clinical validation, pharmacist review and dispense linkage are not established. |
| 4 | Online orders and patient follow-up | `Order` model and `/orders/`, `/orders/{id}`, `/orders/{id}/status`. The model has no item lines; completion writes one aggregate `PatientPurchase` row, not a product-level fulfillment record. | `orders.tsx` returns `null`. | `tests/api/test_orders.py` covers order API behavior and cross-tenant isolation. | **Partial.** Generic patient order records exist; online-order intake, item fulfillment, pickup workflow, messaging and patient follow-up are not established. |
| 5 | Availability across branches and patient redirection | Inventory and POS lookup are scoped to an authorized pharmacy. No cross-branch availability aggregation or complete transfer dispatch/receipt lifecycle was identified. | `transfers.tsx` returns `null`. | No cross-branch transfer workflow test was identified. | **Not implemented / not verified** for the requested cross-branch workflow. Single-pharmacy stock lookup exists. |
| 6 | Supplier orders, delivery notes and goods receiving | Supplier model and privileged `/api/v1/suppliers` list/create endpoints. `POST /api/v1/pos/inventory/receive` can create a lot and record a goods-receipt movement, but its request has no supplier, purchase-order, invoice, delivery-note or discrepancy reference. No purchase-order domain model/lifecycle was identified. | `suppliers.tsx` and `procurement.tsx` return `null`. | No supplier purchase-order or goods-receipt integration test was identified. | **Partial.** Supplier records and standalone lot receipt exist; procurement-to-receiving traceability does not. |
| 7 | Shelf replenishment and out-of-stock management | Inventory stores reorder levels; inventory listing supports low-stock filtering; Mortarium can read low-stock/inventory overview. No replenishment request or supplier purchase-order workflow was identified. | Inventory and procurement routes return `null`. | No replenishment lifecycle test was identified. | **Partial.** Stock visibility exists; replenishment execution is not established. |
| 8 | Stock control, discrepancies and inventory-count preparation | `Inventory` is the pharmacy/lot balance; `InventoryMovement` is the movement ledger. A privileged adjustment endpoint accepts a reason and idempotency key. | `inventory.tsx` and `batches.tsx` return `null`. | `tests/integration/test_inventory_movement_ledger.py` covers atomicity/idempotency. No full stocktake/count-and-reconciliation test was identified. | **Partial.** Movement and adjustment primitives exist; controlled stocktake, dual count, discrepancy workflow and approval are not established. |
| 9 | Pharmacy documents, reports and deadlines | `GET /api/v1/dashboard/summary` exposes operational aggregates. No general task/deadline register or shift-close report lifecycle was identified. | Dashboard is present; workflow-specific reporting surfaces were not verified. | Dashboard scope tests exist; no end-of-day report workflow test was identified. | **Partial.** Dashboard reporting exists; operational document/deadline management is not established. |
| 10 | Team coordination and external professional communication | User, pharmacy and membership records provide identity/access foundations. No staff task assignment, handover message, doctor communication, call log or representative-contact workflow was identified. | No corresponding active workflow screen was established. | No coordination/communication workflow test was identified. | **Not implemented / not verified.** |
| 11 | Shift reconciliation, closing and handover | POS sales/payments and inventory movements exist, but no cashier-shift/register close model, cash reconciliation transaction, handover record or unresolved-task ownership lifecycle was identified. | No operational closing/handover screen was identified. | No shift-close or handover test was identified. | **Not implemented / not verified.** |
| 12 | Mortarium support across pharmacy workflows | Five registered read-only MCP tools: product search, inventory overview, expiring inventory, sales summary and workflow guide. Request-scoped identity and pharmacy context are used; tools do not mutate ERP records. Patient-scoped API and LangGraph state isolation code is merged; staged end-to-end validation remains open. | Mortarium assistant UI exists as a bounded decision-support surface; this is not transaction execution. | `tests/unit/ai/test_pharmacy_operations_mcp.py` covers tool registration/schema contracts. Patient-scoped API session HMAC v3 and Agent/RAG checkpoint namespaces were merged by PR #287 with regression tests; staged PostgreSQL checkpoint + Redis memory session-switch validation remains a release gate. | **Implemented as read-only assistance; patient-scoped state code merged, staged validation pending.** |

## 3. Important reconciliations

### 3.1 POS backend exists; older documentation is stale

The inspected source contains a mounted POS router with:

- `GET /api/v1/pos/products/search`;
- `GET /api/v1/pos/products/{product_id}/lots`;
- `POST /api/v1/pos/checkout`;
- `POST /api/v1/pos/payments/webhook`;
- `POST /api/v1/pos/inventory/receive`.

The checkout path persists sale lines, payment state, receipt identity, FEFO lot allocations, inventory movements and an outbox event. Cash checkout decrements stock; non-cash checkout reserves stock pending a signed payment webhook. Idempotency and key stock/payment invariants have integration coverage.

Therefore, statements in older POS/load-test audit documents that say the backend has no checkout/receipt/FEFO transaction must be updated or qualified. The remaining limitation is that this backend capability is not yet a complete pharmacy workflow: the active POS React feature currently renders `null`, checkout is not linked to patient/prescription records, and returns/refunds/cash-shift close are not established by this audit.

### 3.2 Goods receipt is not procurement receiving

The standalone lot-receipt endpoint is not a purchase-order lifecycle. It does not establish supplier authorization, purchase-order matching, invoice/delivery-note matching, partial receipt, discrepancy approval or supplier return handling.

### 3.3 Patient history is a protected read surface

The patient-purchase listing endpoint requires `CurrentSuperuser`, but its query selects `PatientPurchase` directly without joining `Patient` or constraining `Patient.pharmacy_id`; it also has no patient selector. The `Patient.pharmacy_id` column is nullable. This is a global administrative listing, not a pharmacist-scoped patient-history API. The superuser gate limits who can call it, so this audit does not claim ordinary pharmacist access; however, tenant-scoped authorization, explicit patient selection, legacy/unassigned-patient handling and audit requirements must be designed before exposing patient history in the pharmacist UI. Add negative tests proving that one pharmacy cannot retrieve another pharmacy's patient purchases.

### 3.4 UI navigation is not a delivered workflow

Several active routes currently return `null`, including POS, patients, prescriptions, inventory, batches, suppliers, orders, transfers and procurement. A sidebar entry or generated route is not evidence of a usable workflow.

## 4. Priority implementation sequence

1. **P0 — Restore real operational UI surfaces** for POS and pharmacist workflow, wired to the existing contracts; verify browser-level journeys.
2. **P0 — Prescription and patient linkage**: define patient/prescription association, server-side validation, professional review and audit before dispensing.
3. **P0 — Patient data access controls**: implement tenant-scoped patient-purchase access and complete staged LangGraph patient-session isolation validation; add negative cross-pharmacy and cross-patient tests.
4. **P1 — Procurement lifecycle**: purchase order, supplier lines, delivery/invoice references, partial receipt, discrepancy handling and auditable lot posting.
5. **P1 — Returns, refunds, voids and stock reversals** with idempotent compensating movements.
6. **P1 — Stocktake and inter-branch transfers** with dispatch/receipt confirmation, discrepancy handling and tenant-safe concurrency.
7. **P1 — Cash shifts and end-of-day reconciliation** with cashier/register ownership, expected-vs-counted cash, variance approval and handover ownership.
8. **P2 — Online order fulfillment and communications**: item-level order lifecycle, pickup identity checks, patient notifications and follow-up.
9. **P2 — Operational tasking and reporting**: opening/closing checklists, deadlines, assigned owners and exception queues.

## 5. Validation boundary

This is a repository source audit, not proof of deployed behavior. No production database, production patient records, payment provider, live pharmacy or FastAPI Cloud runtime was accessed. A passing CI run proves only the checks executed by that run; it does not make an unimplemented UI or business workflow complete.

Before changing implementation status, require evidence from all relevant layers: model/schema, authorized API, frontend behavior, automated tests, migration compatibility and a reproducible runtime validation.

## Follow-up source audit — main 481a86aa

The current main branch adds PHI governance documentation and pharmacy-scope predicates to the reviewed Patient Repository paths, with regression tests. See [PHI access governance](../architecture/PHI_ACCESS_GOVERNANCE_AUDIT.md), [PHI read-surface inventory](../security/PHI_READ_SURFACE_INVENTORY.md), and `tests/unit/test_patient_repository_tenant_scope.py`. The patient-history workflow remains partial: these repository predicates do not create a pharmacist-facing history API or prove minimal response fields, read auditing, pagination, or cross-tenant API denial. Keep P0.3 open until those API-level controls are implemented and tested. Source-level only; no production validation.
