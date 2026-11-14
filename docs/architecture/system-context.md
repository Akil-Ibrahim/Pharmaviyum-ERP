# Pharmaviyum System Context and Architecture

**Status:** Current architecture reference

## Purpose
Pharmaviyum is a pharmacy ERP/CRM platform. The deterministic application and transactional database are the system of record. Mortarium is an AI-assisted pharmacist workspace; it is not the authority for dispensing, pricing, stock mutation, payment, permissions or regulatory decisions.

## Logical context
The system consists of a React/TypeScript frontend, a FastAPI modular monolith, authentication and tenant authorization, pharmacy domain modules, PostgreSQL, Redis-compatible cache/memory, Celery workers, Mortarium's LangGraph agent/RAG workflows, MCP tools and OpenTelemetry. These are logical components, not necessarily separate deployable services.

## Runtime boundaries

| Boundary | Responsibility | Authority |
|---|---|---|
| React frontend | Interaction, forms, navigation and presentation | No business authority; client input is untrusted |
| FastAPI API | Authentication dependencies, request validation, tenant context and API contracts | Enforces access before protected operations |
| Domain modules | Pharmacy, patient, catalog, inventory, procurement, POS and audit rules | Authoritative application behavior |
| PostgreSQL | Transactional records, constraints and durable state | System of record |
| Redis | Bounded cache and dialogue memory | Derived/ephemeral state, not the business ledger |
| Celery workers | Asynchronous jobs such as document ingestion | Must preserve authorization and tenant metadata |
| Mortarium | Retrieval, synthesis and authorized tool orchestration | Advisory only |
| External providers | LLM, embeddings, payment and regulatory integrations | Independent trust and availability boundary |

## Request and data-flow invariants
1. Authenticate the caller before protected operations.
2. Resolve pharmacy membership from server-side identity; a client tenant ID is not proof of authorization.
3. Validate patient membership in the authorized pharmacy before patient-specific work.
4. Apply tenant and patient filters inside data access and retrieval, not only in the UI.
5. Validate business commands deterministically before database writes.
6. Persist transactional changes and required audit/outbox records atomically.
7. Treat retrieved documents, user messages, model output and MCP results as untrusted data.
8. Keep patient identifiers, prompts, completions and clinical content out of telemetry.

## Central + Pharmacy Edge
Central + Edge is a target architecture documented in [ADR-0002](../adr/ADR-0002-offline-first-central-edge.md), not a description of the current FastAPI Cloud deployment.

The intended model is:
- Pharmacy Edge owns local transactions explicitly approved for offline execution.
- Central coordinates identity, policy/catalog distribution, synchronization and network reporting.
- Synchronization uses at-least-once transport with idempotent business effects; global exactly-once delivery is not assumed.
- Mortarium and external LLM availability must not be prerequisites for local POS or inventory transactions.

See the [offline capability matrix](../devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md) and [Ansible rollout guide](../devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md).

## Current implementation versus target
- Current hosted application path: FastAPI Cloud, with data/cache services provisioned separately.
- Current backend: FastAPI modular monolith.
- Current AI orchestration: LangGraph Agent and LangGraph RAG, Agent Harness and MCP registry.
- Current WebSocket handlers: development scaffolds, not production-safe.
- Central + Edge: staged target; fleet-wide production readiness is not established.
- Development Compose versions do not upgrade production databases or caches.

## Change policy
Record cross-cutting decisions in the ADR directory. Update this document when system boundaries, trust relationships, data ownership or deployment topology materially change. Diagrams and prose must distinguish implemented behavior from target design.
