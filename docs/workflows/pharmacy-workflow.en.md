# Pharmaviyum Pharmacy Workflow
[English](./pharmacy-workflow.en.md) · [Русский](./pharmacy-workflow.ru.md)

**Document type:** Business & Operational Workflow Specification  
**Language:** English  
**Status:** Working baseline  
**Scope:** Pharmacy operations, POS, inventory, procurement, dispensing, audit, ERP integration and Mortarium

## 1. Purpose

This document defines how Pharmaviyum models the real operational workflow of a pharmacy.

It is a business-level specification. It describes what must happen in the pharmacy and what controls must exist before a workflow is considered operationally complete. Technical implementation details belong in the architecture and API documentation.

The core principle is:

> **Model the pharmacy workflow first, implement deterministic business rules second, and add AI assistance third.**

Mortarium supports pharmacists and operational teams; it does not replace deterministic pharmacy controls or make critical transactional decisions.

## 2. Pharmacy Workflow Map

The main operational chain is:

**Supplier → Procurement → Receiving → Batch & Expiry → Inventory → Pharmacist Workspace → Drug Search → Patient / Prescription → FEFO → POS → Payment → Receipt → Inventory Movement → Patient History → Audit → Analytics / Mortarium**

The platform is organized around these operational domains:

1. Pharmacy / Branch
2. Pharmacist Workspace
3. Drug Catalog
4. Patients
5. Prescriptions & Dispensing
6. POS & Sales
7. Inventory & Batches
8. Procurement & Suppliers
9. Transfers
10. Returns, Write-offs & Recall
11. Cash & Payments
12. Audit & Compliance
13. Exception-First Operations
14. ERP Integration
15. Mortarium Intelligence

## 3. Pharmacy / Branch

A pharmacy belongs to a tenant or pharmacy organization and operates as a distinct branch.

A branch has:

- staff and roles;
- operating configuration;
- storage locations;
- inventory;
- cash operations;
- suppliers and procurement activity;
- sales and returns;
- audit records.

All business operations must preserve tenant and branch isolation.

## 4. Pharmacist Workspace

The Pharmacist Workspace is the primary operational workspace for daily pharmacy activity.

It should provide fast access to:

- drug search;
- patient selection;
- prescription validation;
- product and batch information;
- expiry status;
- FEFO selection;
- cart and POS;
- returns and cancellations;
- stock information;
- alerts and exceptions;
- relevant patient history.

The workspace should be optimized for real pharmacy work rather than administrative navigation.

### Exception-First principle

Important exceptions should be visible without requiring the pharmacist to search for them.

Examples:

- expired batch;
- batch approaching expiry;
- low stock;
- blocked or recalled product;
- inventory discrepancy;
- failed ERP synchronization;
- pending receiving discrepancy;
- transaction requiring authorization.

## 5. Drug Catalog & Search

Drug search is a first-class pharmacy capability.

Search may use:

- trade / brand name;
- INN (International Nonproprietary Name);
- active ingredient;
- barcode / GTIN;
- manufacturer;
- SKU;
- regulatory identifier;
- ATC classification.

The conceptual hierarchy is:

**DrugReference → MedicinalProduct → PharmacyProduct → Batch → Inventory**

### Reference and generic products

A reference/original product and a generic product are separate medicinal-product records.

Shared active ingredients do not automatically make two products interchangeable. Interchangeability depends on applicable pharmaceutical, regulatory and professional rules.

ATC is a classification system and is not a substitute for a complete trade-product catalog.

## 6. Patient & Prescription

A sale may be associated with a patient when the workflow requires or permits it.

Patient-related operations must respect:

- authentication;
- authorization;
- tenant isolation;
- patient access rules;
- audit requirements.

Prescription workflows should validate the information required by the applicable business and regulatory rules before dispensing.

The system should distinguish:

- OTC sale;
- prescription dispensing;
- controlled or restricted workflows where applicable;
- incomplete or invalid prescription states.

## 7. POS / Sale Workflow

The primary POS workflow is:

**Search → Product → Batch → Expiry → FEFO → Patient / Prescription → Cart → Payment → Receipt → Inventory → History → Audit**

A sale should have a deterministic lifecycle.

A typical successful transaction:

1. Pharmacist searches for a product.
2. System identifies the medicinal/pharmacy product.
3. System identifies eligible batches.
4. Expired or blocked batches are excluded.
5. FEFO selects the appropriate eligible batch.
6. Patient/prescription information is attached when required.
7. Product enters the cart.
8. Pharmacist confirms the transaction.
9. Payment is recorded.
10. Receipt is issued.
11. Inventory is decreased through an auditable inventory movement.
12. Patient history is updated when applicable.
13. Audit information is recorded.

### Critical rule

AI must not be the source of truth for:

- price calculation;
- batch eligibility;
- expiry validation;
- inventory quantity;
- payment status;
- receipt finalization;
- authorization.

## 8. Batch & Expiry Control

Inventory must be tracked at batch level whenever batch tracking is required.

Each batch should carry information such as:

- product;
- batch / lot number;
- quantity;
- expiry date;
- receiving information;
- location;
- status.

Expiry status should be visually understandable:

- 🟢 **Green** — good expiry horizon;
- 🟡 **Yellow** — approaching expiry;
- 🔴 **Red** — urgent / hot expiry window.

Expired inventory must not be sellable.

A configurable policy should define the exact yellow and red thresholds rather than hard-coding a universal number of days.

## 9. FEFO

FEFO means **First Expired, First Out**.

When multiple eligible batches exist, the system should prefer the batch with the earliest expiry date, subject to business rules.

FEFO must be:

- deterministic;
- reproducible;
- auditable;
- independent of LLM output.

A pharmacist may need an explicit override workflow for exceptional cases. Overrides must be authorized and audited.

## 10. Inventory & Stock Movements

Inventory is not only a quantity field. The platform should maintain an auditable movement history.

Examples of movements:

- receiving;
- sale;
- return;
- transfer out;
- transfer in;
- write-off;
- stocktake adjustment;
- quarantine;
- release from quarantine;
- recall-related movement.

The system should make it possible to answer:

**What changed, for which product and batch, by how much, when, where, and why?**

Inventory updates should be idempotent where repeated requests or integration events are possible.

## 11. Procurement & Receiving

Procurement workflow:

**Supplier → Purchase Order → Order Items → Receiving → Batch / Expiry → Inventory**

A purchase order should have a controlled lifecycle.

Receiving should record:

- supplier;
- product;
- quantity;
- purchase price;
- batch / lot;
- expiry;
- storage location where applicable;
- discrepancies.

Receiving must not silently convert an expected quantity into available stock when the physical receipt differs from the order.

Discrepancies should become operational exceptions.

## 12. Suppliers

Supplier records should support:

- identification;
- contact information;
- supplied products;
- purchase orders;
- receiving history;
- supplier returns;
- commercial information where applicable.

Supplier relationships should remain separate from the medicinal-product reference model.

## 13. Transfers Between Pharmacies

Inter-branch transfers should use an explicit lifecycle:

**Requested → Approved → Dispatched → In Transit → Received → Reconciled**

The source branch and destination branch must not both treat the same stock as available during transit.

Differences between dispatched and received quantities must create an exception and an audit record.

## 14. Returns, Refunds & Cancellations

The platform should distinguish:

- customer return;
- supplier return;
- transaction cancellation / void;
- refund;
- inventory reversal.

A return must not simply delete the original sale.

The system should preserve the original transaction and create the appropriate reversal or return records.

Authorization rules may be required for:

- completed-sale cancellation;
- refunds;
- return acceptance;
- inventory restoration.

## 15. Write-offs, Quarantine & Recall

Write-offs may be required for:

- expired products;
- damaged products;
- inventory discrepancies;
- other approved operational reasons.

Quarantine is used when stock must be prevented from normal sale or dispensing while its status is investigated.

Recall workflow should support:

**Identify → Block → Locate → Quarantine → Notify / Process → Return or Dispose → Record**

Recall and quarantine must operate at the appropriate product/batch level.

## 16. Stocktake

Stocktake should compare:

**System Quantity ↔ Physically Counted Quantity**

Differences should produce controlled adjustments rather than silent edits.

A stocktake should record:

- scope;
- location;
- counted quantity;
- system quantity;
- difference;
- reason;
- responsible user;
- approval where required;
- resulting inventory movement.

## 17. Cash Shift & Payments

POS operations should support a cash-shift lifecycle such as:

**Open Shift → Transactions → Cash Movements → Reconciliation → Close Shift**

Payment workflows should distinguish:

- payment;
- refund;
- cash movement;
- reconciliation result.

Payment completion must be deterministic and must not depend on Mortarium.

## 18. Audit & Compliance

Important pharmacy actions should produce an audit trail.

An audit record should answer:

- who;
- what;
- when;
- where;
- object;
- previous state;
- new state;
- reason;
- result.

Audit data should cover sensitive and operationally important actions, including inventory adjustments, batch blocking, returns, refunds, overrides, prescription-related actions, permissions and integration failures.

## 19. Exception-First Operations

Pharmacy operations should surface exceptions rather than forcing staff to discover them manually.

Examples:

- expired inventory;
- approaching expiry;
- low stock;
- unexpected stock movement;
- receiving discrepancy;
- transfer discrepancy;
- failed ERP synchronization;
- payment/reconciliation issue;
- recalled batch;
- AI recommendation awaiting human review.

Mortarium can help summarize, prioritize or explain exceptions, but the underlying business state remains authoritative.

## 20. ERP Integration

Pharmaviyum is designed to coexist with existing pharmacy ERP systems, including C#, Java or 1C-based systems.

Integration should use an explicit adapter/integration layer rather than coupling the business core directly to a specific ERP.

Integration operations should consider:

- idempotency;
- retries;
- duplicate events;
- mapping;
- synchronization state;
- reconciliation;
- failure queues;
- audit.

A pilot deployment may run Pharmaviyum alongside an existing ERP before broader replacement or expansion.

## 21. Mortarium Intelligence Layer

Mortarium is the intelligence layer above the operational business core.

Potential authorized use cases include:

- natural-language patient-history queries;
- operational summaries;
- inventory analysis;
- sales analysis;
- forecasting;
- document assistance;
- exception explanation;
- pharmacist-facing conversational assistance.

Mortarium must operate within authorization boundaries.

It should not have unrestricted access to pharmacy data or unrestricted ability to perform critical transactions.

The intended model is:

**Business Core = source of truth**  
**Mortarium = controlled intelligence and assistance**

## 22. End-to-End Example

A typical dispensing transaction:

1. Pharmacist opens the workspace.
2. Pharmacist searches by brand, INN or barcode.
3. Pharmaviyum identifies the pharmacy product.
4. Eligible batches are retrieved.
5. Expired and blocked batches are excluded.
6. FEFO selects the appropriate batch.
7. Pharmacist attaches the patient and prescription when required.
8. Product is added to the cart.
9. Pharmacist confirms the sale.
10. Payment is processed.
11. Receipt is created.
12. Inventory movement is recorded.
13. Patient history is updated when applicable.
14. Audit event is recorded.
15. Relevant operational data becomes available to analytics and Mortarium.

## 23. Implementation Readiness Model

A workflow should not be considered production-ready merely because one API endpoint or UI screen exists.

Each workflow should be evaluated across seven layers:

1. **Domain Model**
2. **Database / Migration**
3. **Backend API**
4. **Business Rules**
5. **Frontend**
6. **Automated Tests**
7. **Audit / Idempotency / Operational Safety**

A workflow is operationally complete only when the required layers have been implemented and validated for its risk level.

## 24. Implementation Status

The following status categories should be used in project planning:

- **Implemented** — verified in the current codebase and covered by appropriate tests.
- **Partial** — important pieces exist, but the end-to-end workflow is incomplete.
- **Planned** — defined as a target but not yet implemented.
- **Needs Validation** — implementation exists but requires workflow, integration or production-level verification.

The status must be updated against the actual repository state rather than assumed from documentation.

## 25. Non-Negotiable Business Controls

The following principles are foundational:

1. Expired inventory must not be sellable.
2. FEFO must be deterministic.
3. Inventory changes must be auditable.
4. Critical transactions must be idempotent where retries are possible.
5. Returns and cancellations must preserve transaction history.
6. Tenant and patient access controls must be enforced server-side.
7. AI must not be the authority for critical pharmacy transactions.
8. Original/reference and generic products must remain distinguishable.
9. Batch-level restrictions must be enforceable.
10. ERP synchronization failures must become visible operational exceptions.
11. Human authorization remains required for workflows that require professional or operational judgment.
12. Business Core remains the source of truth for operational state.


## 26. Related business-value and KPI specification

The [Pharmacy Business Value & KPI Specification](./PHARMACY_BUSINESS_VALUE_AND_KPIS.md) defines the business-value model, six primary CV KPIs, supporting operational measures, measurement-contract requirements and evidence rules. The primary engineering measurement source remains [ENGINEERING_BENCHMARK_REQUIREMENTS.md](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md). Domain context is informed by the [AI in the Pharmacy article](https://medium.com/@ibrahimengpy/ai-in-the-pharmacy-how-technology-can-support-the-pharmacist-a755ba3a2c9a). These references do not imply that every described capability is implemented or production-validated.


## 27. Article-derived day-to-day pharmacy workflows

This section makes the practical workflows described in [AI in the Pharmacy: How Technology Can Support the Pharmacist](https://medium.com/@ibrahimengpy/ai-in-the-pharmacy-how-technology-can-support-the-pharmacist-a755ba3a2c9a) explicit. It expands the operational model; it does not assert that every workflow is currently implemented.

### 27.1 Opening preparation and shift readiness

1. The opening pharmacist arrives before the public opening time.
2. Review the handover from the previous shift: unresolved tasks, patient/order follow-ups, stock or prescription issues, supplier matters and operational exceptions.
3. Check staff/role readiness and the pharmacy workspace.
4. Review urgent stock, expiry, prescription and online-order exceptions.
5. Confirm that required systems, POS/cash operations and integrations are available; record failures for follow-up.
6. Prepare the pharmacy for customer service and record completion or outstanding exceptions.

### 27.2 Patient consultation and medicine dispensing

1. Identify the patient when the workflow and applicable rules require it.
2. Retrieve only authorized patient context, including relevant previous dispensing records and interaction history.
3. Clarify the patient's request and identify the medicine or medical device.
4. Search and compare medicine information; distinguish brand, active ingredient, strength, dosage form and pack/quantity.
5. Check prescription or treatment-order requirements where applicable.
6. Verify relevant dosage, quantity and other prescription details; flag missing, inconsistent or uncertain information for pharmacist review.
7. Check product availability and eligible batches, expiry and restrictions.
8. Apply the deterministic dispensing/POS workflow, including FEFO where relevant.
9. Complete the professional consultation, dispense and record the transaction.
10. Update the permitted patient/dispensing history and audit trail.

AI may retrieve and organize context, compare records and flag items for verification. The pharmacist remains responsible for clinical assessment and the final professional decision.

### 27.3 Prescription and treatment-order clarification

1. Receive or review a prescription/treatment order.
2. Locate the relevant patient and prescription records under role-based access.
3. Check completeness, medicine identity, dosage, quantity and applicable restrictions.
4. Identify ambiguity, mismatch or missing information.
5. Refer questions to the responsible pharmacist and, when appropriate, contact the prescriber/doctor for clarification.
6. Record the clarification, its source, the decision and the resulting action.
7. Do not allow AI to resolve a clinical ambiguity or authorize dispensing on its own.

### 27.4 Online orders and patient follow-up

1. Receive and review incoming online orders.
2. Validate order details and identify the requested products.
3. Check stock, eligible batches and fulfillment constraints.
4. Prepare the order or flag unavailable items and exceptions.
5. Contact the patient when clarification, availability information or collection coordination is required.
6. After the interaction or dispensing, conduct patient feedback/follow-up calls when part of the pharmacy's service process.
7. Record contact outcome, unresolved questions and next actions in the appropriate system record.

### 27.5 Availability checks across branches and patient redirection

1. Search the current branch's available, eligible stock.
2. If unavailable, check authorized stock availability at other branches.
3. Confirm that the displayed quantity is current enough for the intended decision and distinguish on-hand, reserved, quarantined and otherwise unavailable stock.
4. Contact the responsible/on-duty pharmacist or branch when confirmation is needed.
5. Inform the patient of the verified availability and, where appropriate, direct them to another pharmacy.
6. Record the referral/availability outcome where the workflow requires it.
7. Do not promise availability based only on stale or unconfirmed synchronization data.

### 27.6 Supplier orders, delivery notes and goods receiving

1. Identify missing or low-stock products and prepare a replenishment requirement.
2. Review supplier/product information and create or update a purchase order through the authorized process.
3. Receive the supplier delivery and its delivery note.
4. Compare the delivery note and purchase order with the physically received goods.
5. Verify product identity, quantity, batch/lot and expiry; record discrepancies, damage or missing items.
6. Register accepted goods through the receiving workflow and update inventory only for verified quantities.
7. Place accepted products in their designated storage/shelf locations in time for sale, following storage and stock-rotation rules.
8. Route discrepancies and supplier issues to an accountable operator and retain the audit evidence.

### 27.7 Shelf replenishment and out-of-stock management

1. Identify products that need shelf replenishment or are unavailable.
2. Check backroom and branch stock, batch status and expiry.
3. Replenish shelves from eligible stock using the applicable rotation rules.
4. If stock is insufficient, record the shortage and assess replenishment or inter-branch sourcing.
5. Create or escalate the required supplier order or branch transfer.
6. Track the shortage until resolved and make the current availability state visible to staff.

### 27.8 Stock control, discrepancies and inventory-count preparation

1. Monitor stock balances, low-stock items, expiry dates and restricted/prescription stock.
2. Investigate unexpected stock movements and discrepancies.
3. Prepare the inventory count by defining scope, locations, products/batches, responsibilities and count timing.
4. Perform physical counts and compare them with system quantities.
5. Investigate variances and record reasons and supporting evidence.
6. Approve and post controlled adjustments through auditable inventory movements.
7. Use count results to identify process weaknesses and corrective actions.

### 27.9 Pharmacy documents, reports and deadlines

1. Collect and review operational documents, supplier documents and internal pharmacy information.
2. Prepare required reports and recurring operational summaries.
3. Track reporting deadlines and outstanding submissions.
4. Validate source data and route incomplete or inconsistent information for correction.
5. Retain document versions, responsible users, timestamps and submission/approval status as required.

AI may locate, summarize and structure authorized documents or prepare report drafts. A responsible employee must validate content and approve formal submissions.

### 27.10 Team coordination and external professional communication

1. Coordinate tasks, workload and exceptions among pharmacists and other pharmacy team members.
2. Communicate unresolved patient, prescription, stock and supplier issues to the responsible colleague.
3. Contact doctors/prescribers when professional clarification is required.
4. Communicate with medical representatives about product-related or informational matters within applicable policy.
5. Record material decisions, commitments and follow-up actions in the appropriate operational record.
6. Ensure that open work is assigned rather than left as undocumented verbal knowledge.

### 27.11 Shift reconciliation, closing and handover

Approximately 30 minutes before shift end, the outgoing employee should begin a controlled close-out:

1. Reconcile medicine dispensing records and relevant transactions for the shift.
2. Review patient-related records and follow-ups that require action, subject to access permissions.
3. Review online orders, pending collections, unresolved availability requests and patient callbacks.
4. Review stock, prescription, supplier, cash/POS and system exceptions relevant to the shift.
5. Complete required reports and meet applicable submission deadlines.
6. Confirm that the pharmacy workspace and operational state are ready for the next shift.
7. Prepare a structured handover for the incoming pharmacist: current tasks, unresolved exceptions, patient/order follow-ups, supplier matters, stock issues, deadlines and accountable owners.
8. Require acknowledgement of the handover and preserve an auditable record of what was transferred and what remains open.

A shift is not operationally complete merely because the user logs out. Outstanding work must have an owner, status and next action.

### 27.12 AI support mapped to these workflows

Mortarium may assist with:
- retrieving authorized patient and previous-dispensing context;
- finding and comparing medicine and prescription information;
- highlighting dosage, quantity or record inconsistencies for pharmacist review;
- checking stock information and summarizing shortages;
- organizing supplier, purchase-order and delivery-note information;
- preparing inventory-count summaries and discrepancy explanations;
- locating documents and drafting operational reports;
- summarizing team handovers, open tasks and deadlines;
- answering natural-language questions across authorized pharmacy data.

For every AI-assisted workflow, enforce role/tenant/patient authorization before retrieval, source attribution, validation and audit. AI output is advisory; the pharmacist or authorized operator validates it and performs/approves consequential actions. Critical inventory, prescription, dispensing, payment and accounting state changes remain deterministic, permission-checked and auditable.

## Implementation traceability

See the [P0 Pharmacist Workspace implementation and acceptance gates](./PHARMACIST_WORKSPACE_P0_ACCEPTANCE.md) for the delivery contract covering POS UI, patient/prescription linkage, tenant-scoped patient history and staged Mortarium isolation validation.

See the [Pharmacy Workflow Implementation Traceability](./PHARMACY_WORKFLOW_TRACEABILITY.md) matrix for the source-based mapping from each pharmacy process to domain models, API contracts, frontend routes, automated tests and current implementation status. The matrix distinguishes backend capabilities from complete user-facing workflows.
