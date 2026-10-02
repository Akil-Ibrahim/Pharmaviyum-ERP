# Mortarium AI Security & Execution Boundaries

## Purpose

Mortarium is the AI layer integrated into Pharmaviyum — Pharmacy ERP/CRM. The AI model acts as an intelligent interface to permitted pharmacy data and business operations. It is not the source of truth and does not have unrestricted system access.

## Core security principle

Mortarium operates within explicitly defined execution boundaries.

The LLM must never be treated as an administrator of Pharmaviyum. Business rules, authorization, data integrity, and persistence remain under the control of the application backend.

```text
Pharmacist
    |
    v
Mortarium / LLM
    |
    v
RAG / Context
    |
    v
MCP Tools
    |
    v
FastAPI Business Logic
    |
    v
PostgreSQL
```

The LLM may request an operation, but the backend remains responsible for deciding whether that operation is valid and authorized.

## No direct database access

The LLM must not receive direct access to PostgreSQL.

Mortarium must not:

- open database connections directly;
- receive database handles or ORM sessions;
- execute arbitrary SQL;
- generate and execute unrestricted SQL queries;
- bypass FastAPI business logic;
- modify database records outside approved application tools.

Database access remains an internal backend responsibility.

## No arbitrary SQL

Generic SQL execution is prohibited for LLM-facing MCP tools.

MCP tool schemas must not expose generic execution parameters such as:

- `sql`
- `raw_sql`
- `sql_query`
- `statement`
- `query_text`

Business operations must instead be represented by explicit, domain-specific tools, for example:

- `get_patient_history`
- `search_products`
- `check_inventory`
- `find_expiring_batches`
- `create_purchase_order`
- `confirm_stock_transfer`

This keeps the AI interface aligned with pharmacy workflows rather than exposing the database as a generic execution environment.

## No source-code modification

Mortarium must not be able to modify its own source code or Pharmaviyum source code.

The LLM must not have access to:

- source-code write operations;
- arbitrary filesystem access;
- repository write operations;
- deployment credentials;
- CI/CD credentials;
- `.env` files or secrets;
- shell commands or arbitrary scripts.

Application code changes are performed through the normal development and CI/CD process.

AI-generated code suggestions may be reviewed by developers, but the running Mortarium instance cannot modify its own implementation.

## Controlled MCP execution

MCP tools are explicitly classified by execution type:

- `read` — retrieves permitted information;
- `write` — performs a business operation that changes state.

Write tools require explicit confirmation from the pharmacist/user before execution.

The intended flow is:

```text
LLM proposes
    -> User/Pharmacist confirms
    -> MCP tool executes
    -> FastAPI validates
    -> Database changes
    -> Audit Log records
```

The model cannot silently convert a conversational request into an unrestricted state-changing operation.

## Backend as the business authority

FastAPI remains responsible for:

- authentication;
- authorization;
- RBAC;
- pharmacy/location scope;
- business rules;
- validation;
- transaction handling;
- inventory integrity;
- FEFO rules;
- patient-data access control;
- audit logging.

Mortarium does not replace these controls.

Even when an operation is requested through an MCP tool, the backend must independently validate the operation before changing system state.

## Pharmacy and patient data boundaries

Mortarium may access only the context permitted for the authenticated user and requested operation.

Patient-related information remains subject to existing access-control and scope rules.

RAG retrieval and MCP operations must not become a mechanism for bypassing those restrictions.

The AI model must not be allowed to retrieve arbitrary patient, pharmacy, inventory, or financial data simply because it can formulate a technically valid request.

## Auditability

Protected business operations must remain auditable.

Important state-changing operations should be traceable to:

- authenticated user;
- pharmacy/location scope;
- requested operation;
- executed tool;
- affected business entity;
- execution result;
- confirmation where required.

The Audit Log remains part of the ERP/CRM control layer and is not delegated to the LLM.

## Closed internet does not replace application security

A restricted or closed network environment provides an additional security boundary, but it is not sufficient by itself.

Even without general Internet access, an unrestricted model could potentially cause damage if it had access to:

- the database;
- arbitrary SQL;
- source code;
- filesystem operations;
- shell commands;
- deployment credentials.

Therefore, Mortarium security is based primarily on least privilege, explicit tool boundaries, backend authorization, validation, and auditability.

Network isolation is an additional layer rather than the primary authorization mechanism.

## Security objective

> **Mortarium can reason about permitted pharmacy information and request permitted business operations, but it cannot directly control Pharmaviyum infrastructure.**

The system must preserve this separation:

**AI reasoning ≠ business authority ≠ database authority ≠ infrastructure authority**

This separation is a fundamental security principle for Mortarium.
