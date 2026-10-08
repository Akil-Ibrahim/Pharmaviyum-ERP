# Pharmaviyum Architecture
## Architecture Vision and Engineering Principles

**Status:** Living architecture document  
**Languages:** English / Russian  
**Project:** Pharmaviyum CRM  
**Primary backend:** FastAPI  
**Frontend:** React + Vite + TypeScript  
**AI layer:** Mortarium

---

## 1. Architecture Vision

Pharmaviyum is evolving from a pharmacy CRM into a **Pharmacy Operating Platform**.

The platform is designed around real pharmacy workflows rather than around technology alone. The architecture must support:

- daily pharmacist operations;
- POS and dispensing workflows;
- inventory and FEFO control;
- patients, prescriptions, orders and suppliers;
- pharmacy-chain administration;
- integration with existing C#/Java/1C ERP systems;
- AI-assisted work through Mortarium;
- cloud deployment;
- self-hosted/on-premise deployment for pharmacies that require local data control.

The core principle is:

> **Deterministic business logic controls pharmacy operations. AI assists people; it does not control critical transactions.**

---

## 2. FastAPI Decision

FastAPI is the primary backend framework.

This choice fits the current architecture because Pharmaviyum is API-first and combines:

- React/Vite frontend;
- asynchronous PostgreSQL access;
- Redis/Valkey;
- background workers;
- RAG and vector search;
- LLM integrations;
- MCP tools;
- observability;
- Docker deployment;
- ERP integration APIs.

Django could also support these requirements, but moving to Django would not provide a necessary architectural advantage for the current system. FastAPI keeps the API boundary explicit and works naturally with asynchronous I/O and typed schemas.

This is an architectural decision, not a statement that FastAPI is universally better than Django.

---

## 3. High-Level Architecture

```text
                         Pharmaviyum Platform
                                  |
              +-------------------+-------------------+
              |                                       |
       Business Core                           Mortarium AI
              |                                       |
       +------+------+                         +------+------+
       |      |      |                         |             |
      POS  Inventory Patients              RAG/LLM      AI Tools
       |      |      |                         |             |
       +------+------+                        +------+------+
              |        \                              |
          PostgreSQL   Redis/Valkey              Controlled data
              |                                      access
              +----------------+---------------------+
                               |
                     Integration Layer
                               |
                    Existing ERP / External Systems
```

The Business Core and Intelligence Layer are intentionally separated conceptually even when they currently share a process/container.

---

## 4. Business Core

The Business Core is deterministic.

Critical operations must not depend on an LLM response.

Examples:

- creating a sale;
- calculating totals;
- accepting payment;
- selecting an eligible batch;
- FEFO allocation;
- preventing expired-product sale;
- inventory reservation;
- stock movement;
- receiving an order;
- dispensing;
- patient purchase recording;
- audit logging;
- ERP synchronization.

For these operations, the system should use explicit validation, database transactions, state machines and idempotency.

---

## 5. Pharmacy Domain Model

The drug catalog follows a layered model:

```text
DrugReference
   |
   +-- INN / active ingredients / ATC
   |
MedicinalProduct
   |
   +-- reference/original or generic
   +-- brand
   +-- manufacturer
   +-- strength
   +-- dosage form
   +-- route
   +-- package
   +-- GTIN / regulatory ID
   |
PharmacyProduct
   |
Batch
   |
Inventory
   |
POS / Dispensing
```

A matching active ingredient does **not** automatically mean that two products are interchangeable. Reference/original and generic/analog products remain distinct records.

ATC is a classification system, not a complete international trade-product catalog.

---

## 6. POS

POS is a first-class operational workflow.

The pharmacist should be able to search by:

- brand/trade name;
- INN;
- barcode/GTIN;
- manufacturer;
- SKU;
- regulatory identifier;
- ATC.

The POS flow is designed around:

```text
Search
  -> Product
  -> Eligible Batch / FEFO
  -> Cart
  -> Patient (when applicable)
  -> Payment
  -> Receipt
  -> Audit
```

Expired batches must never be sellable.

Expiry status is represented operationally as:

- green — normal shelf life;
- yellow — approaching expiry;
- red — critical/near expiry.

The exact thresholds are business configuration, not AI decisions.

---

## 7. Inventory and FEFO

Inventory selection is deterministic.

FEFO means:

> First Expire, First Out.

The system must consider batch expiry, availability and other business constraints when selecting stock.

Mortarium may explain inventory patterns or highlight risks, but it must not silently change stock quantities or execute inventory operations.

---

## 8. State Machines

Business entities should have explicit state transitions.

Examples:

```text
Order:
draft -> submitted -> approved -> received -> completed
                         -> cancelled

Sale:
draft -> confirmed -> paid -> completed
                    -> cancelled
```

The actual states may evolve with the domain, but transitions should be explicit, validated and auditable.

---

## 9. Idempotency

Idempotency is required for operations that can be retried.

Important examples:

- POS/payment requests;
- order creation;
- inventory movements;
- ERP synchronization;
- webhook/event processing;
- external integration calls.

A retry must not create a duplicate sale, payment, stock movement or ERP record.

---

## 10. Audit Trail

Pharmacy operations require an auditable history.

The audit model should capture, where applicable:

- who performed the action;
- what action occurred;
- when it occurred;
- where/from which terminal or service;
- which object was affected;
- previous value;
- new value;
- reason/context;
- result.

Audit data is part of the Business Core, not an optional AI feature.

---

## 11. Event-Driven Direction

The architecture should gradually expose domain events such as:

- SaleCompleted;
- InventoryChanged;
- BatchExpiring;
- LowStockDetected;
- OrderReceived;
- PatientPurchaseRecorded.

Events can feed notifications, analytics, forecasting and AI workflows without putting AI inside the critical transaction path.

This is an evolutionary direction; not every event requires a separate microservice.

---

## 12. Mortarium Intelligence Layer

Mortarium is the AI layer of Pharmaviyum.

Its role is to assist pharmacists and administrators with:

- natural-language queries;
- document retrieval;
- patient-history assistance where authorized;
- inventory analysis;
- sales/revenue analysis;
- forecasting;
- explanations and summaries;
- workflow assistance.

Mortarium should operate through explicit, permission-aware tools.

The preferred model is:

```text
User
  -> Pharmaviyum API
  -> Authorization
  -> Approved Mortarium tool
  -> Authorized business data
  -> AI reasoning
  -> Explanation / recommendation
  -> Human decision
```

Mortarium should not receive unrestricted database access.

---

## 13. Human-in-the-Loop

For consequential pharmacy operations:

> **AI recommends; an authorized human decides.**

AI output must not silently:

- dispense a medicine;
- approve a payment;
- modify inventory;
- change a prescription;
- change patient identity;
- create an irreversible business transaction.

Where an AI recommendation affects an operational decision, the UI should make the recommendation and its source/context visible.

---

## 14. RAG

RAG is a controlled retrieval mechanism, not simply a chatbot.

Sources may include authorized:

- pharmacy documents;
- internal knowledge;
- patient-related records when permitted;
- product information;
- inventory data;
- orders and operational records.

Retrieval must respect:

- tenant boundaries;
- user permissions;
- patient ownership/access rules;
- document scope;
- audit requirements.

The model should receive only the context necessary for the authorized task.

---

## 15. AI Security and Network Isolation

A critical architectural principle is:

> Mortarium must not have unrestricted outbound internet access.

However, this principle must be implemented safely.

**Current implementation status:** Mortarium AI code is presently integrated into the main FastAPI backend process/container. Therefore, simply marking the existing backend Docker network as internal would also block legitimate backend dependencies such as configured cloud LLM/embedding providers and could break application functionality.

The target architecture is:

```text
                         Internal Pharmacy Network
                                  |
                         +--------+--------+
                         |                 |
                    Business API      Mortarium Runtime
                         |                 |
                    PostgreSQL       Approved internal tools
                    Redis/Valkey             |
                         |                    |
                         +---------+----------+
                                   |
                         Controlled AI Gateway
                                   |
                         Optional external
                         LLM/embedding provider
```

The AI runtime should eventually be separated from the main backend and given tightly controlled egress.

If web research is introduced later, it should use a dedicated controlled Web Research Service/Gateway rather than opening unrestricted internet access for Mortarium.

The target security model is:

- default-deny outbound network access for Mortarium;
- allow only explicitly required internal services;
- allow external AI providers only through an approved gateway;
- enforce authorization before tool execution;
- log sensitive AI tool calls;
- test that forbidden external connections fail.

This is an architectural target, not a claim that network isolation is already fully implemented.

---

## 16. RBAC and Tenant Isolation

Pharmaviyum must enforce authorization at the backend boundary.

Typical dimensions include:

- tenant/pharmacy chain;
- pharmacy location;
- user role;
- patient access scope;
- operational permissions.

The frontend must never be treated as the security boundary.

Mortarium inherits the same authorization model. It does not receive broader access simply because the request comes through an AI interface.

---

## 17. ERP Integration

Pharmaviyum is designed to coexist with existing pharmacy ERP systems.

Existing C#, Java or 1C systems do not need to be replaced immediately.

Integration should use an explicit Integration Layer:

```text
Existing ERP
    |
ERP Adapter
    |
Integration Layer
    |
Pharmaviyum Business Core
    |
Mortarium / Analytics
```

This supports pilot-first deployment and gradual migration.

The integration layer should define contracts for:

- products;
- prices;
- stock;
- purchases;
- sales;
- patients;
- suppliers;
- orders;
- documents;
- identifiers.

---

## 18. Cloud and On-Premise

The business logic should remain as consistent as possible between deployment models.

### Cloud

```text
GitHub
  -> GitHub Actions
  -> immutable container image
  -> Render
```

### On-Premise

```text
GitHub
  -> GitHub Actions
  -> immutable container image
  -> GHCR
  -> Ansible
  -> Pharmacy server
```

On-premise deployment should include, as the architecture matures:

- PostgreSQL;
- Redis/Valkey;
- application containers;
- workers;
- reverse proxy;
- migrations;
- health checks;
- backups;
- restore procedures;
- rollback procedures;
- observability.

---

## 19. Modular Monolith First

The preferred current architecture is a **modular monolith**, not a collection of premature microservices.

Logical modules can include:

- Auth / RBAC;
- Patients;
- Drug Catalog;
- Products;
- Inventory;
- POS;
- Orders;
- Dispensing;
- Suppliers;
- ERP Integration;
- Audit;
- Analytics;
- Mortarium.

A module should have a clear boundary even when deployed in the same application.

Service extraction should happen only when there is a demonstrated operational or scaling reason.

---

## 20. Work Queue and Exception-First UX

The operational UI should focus on actions and exceptions rather than only dashboards.

Examples:

- expiring batches;
- low stock;
- failed ERP synchronization;
- pending orders;
- unusual inventory movements;
- AI recommendations awaiting review;
- failed integrations;
- unresolved operational errors.

This allows the system to function as an operational tool, not just a reporting interface.

---

## 21. Architecture Principles

1. Business correctness before AI sophistication.
2. Deterministic core for critical operations.
3. Human control over consequential AI recommendations.
4. Least-privilege access.
5. Tenant and patient isolation.
6. No unrestricted AI database access.
7. No unrestricted Mortarium internet access.
8. Immutable deployment artifacts.
9. Idempotent critical operations.
10. Complete operational auditability.
11. Pilot-first integration with existing ERP.
12. Cloud and on-premise compatibility.
13. Modular monolith before microservices.
14. Events where they provide real business value.
15. Security must be enforced by architecture, not only by UI.

---

## 22. Architecture Decision Records

### ADR-001 — FastAPI as Backend
FastAPI is retained as the primary backend framework because it fits the API-first, asynchronous and integration-heavy architecture.

### ADR-002 — React/Vite as Frontend
The frontend remains React + Vite + TypeScript. A migration to Next.js is not required by the current architecture.

### ADR-003 — Modular Monolith
Pharmaviyum starts as a modular monolith to reduce operational complexity and preserve development velocity.

### ADR-004 — Mortarium Is Not the Business Core
AI is an intelligence layer. Critical transactions remain deterministic.

### ADR-005 — Human-in-the-Loop
AI recommendations do not automatically execute consequential pharmacy operations.

### ADR-006 — Controlled AI Network
Mortarium should eventually run with default-deny outbound network access and use approved gateways for any required external AI/web capability.

### ADR-007 — ERP Coexistence
Existing ERP systems are integrated through adapters instead of being replaced during the first deployment phase.

### ADR-008 — Cloud + On-Premise
The same core application is designed to support both managed cloud deployment and self-hosted pharmacy infrastructure.

---

## 23. Implementation Status

### Implemented / established
- FastAPI backend;
- React/Vite frontend;
- PostgreSQL + pgvector;
- Redis/Valkey;
- Mortarium/RAG foundations;
- international drug catalog layer;
- POS domain direction;
- FEFO/expiry-control direction;
- GitHub Actions as primary CI/CD;
- Docker deployment;
- Ansible on-premise deployment foundation.

### In progress / evolving
- POS operational workflow;
- international catalog ingestion;
- ERP integration contracts;
- complete business audit model;
- domain event architecture;
- production-grade backup/restore;
- on-premise hardening;
- Mortarium authorization boundaries.

### Future target
- separate Mortarium runtime;
- controlled AI gateway;
- default-deny AI egress;
- dedicated web-research gateway if needed;
- stronger policy enforcement around AI tools;
- deeper event-driven workflows.

---

## 24. Engineering Philosophy

Pharmaviyum follows **Business-oriented Engineering** and **Systems Thinking**.

A technical decision should be evaluated against:

- the real pharmacy workflow;
- business value;
- patient and operational risk;
- implementation cost;
- deployment constraints;
- integration with existing systems;
- maintainability;
- security;
- the path from pilot to production.

The goal is not to build the most technologically complex pharmacy system.

The goal is to build a system that can be safely used in a real pharmacy.
