# Pharmaviyum Pharmacy Workflow

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
