# ADR-0002: Offline-first Central + Pharmacy Edge Architecture

## Status

Proposed — target architecture approved for design work; implementation and production rollout are not complete.

## Context

Pharmaviyum targets a pharmacy network of 100+ sites. A pharmacy must continue its permitted local work when the WAN link or the central platform is unavailable. POS and inventory transactions must not depend on Mortarium, a cloud LLM, or a live connection to the central control plane.

The current repository contains a FastAPI modular monolith, PostgreSQL/pgvector, Valkey, POS checkout/payment/FEFO code and Ansible deployment scaffolding. The current Ansible production inventory describes one `pharmacy-server-01`; the current Compose stack is a single-node application/database/cache deployment. A production-grade offline synchronization protocol and 100-site fleet deployment are not yet implemented.

## Decision

Adopt a **Central + Pharmacy Edge** topology while retaining a modular-monolith application architecture initially.

### 1. Pharmacy Edge — local operational authority

Each pharmacy site receives a locally deployed Pharmaviyum Edge instance containing:

- the Pharmaviyum API and deterministic business modules;
- a local PostgreSQL database for that pharmacy's operational transactions;
- a durable synchronization outbox and inbox;
- a local cache of the catalog, policies and other data explicitly approved for offline use;
- a local worker for synchronization and bounded background jobs;
- local audit records and health/backup agents.

POS checkout, local inventory movements, local audit, and other explicitly approved workflows execute against the local database in one ACID transaction. These operations must remain available during WAN or central-service outages.

A single Edge host plus UPS improves continuity during power and WAN interruptions but is still a hardware single point of failure. Site-level hardware redundancy, spare-node recovery, UPS runtime and generator requirements must be selected from the business RTO/RPO and site risk assessment; they are not assumed to exist.

### 2. Central Platform — network coordination and consolidated view

The central platform provides:

- pharmacy/site registry and device identity;
- user, role and policy distribution;
- versioned catalog/reference-data distribution;
- central reporting and eventually consistent network-wide read models;
- synchronization ingestion, deduplication and monitoring;
- cross-site workflows that require coordination;
- Mortarium AI, RAG, analytics and model routing.

The central platform is not a synchronous dependency for local POS. During a central outage, Edge sites continue permitted local operations and retain events for later delivery.

### 3. Synchronization contract

Implement synchronization as an application capability, not as an Ansible task or a Redis-only queue.

- Write the business change and its outbox event in the same PostgreSQL transaction.
- Assign every event a globally unique immutable event ID, pharmacy/site ID, edge-node ID, aggregate type/ID, aggregate version, schema version and occurrence metadata.
- Deliver events at least once over authenticated TLS connections. Consumers must be idempotent.
- Persist processed event IDs in an inbox with a unique constraint so retries and replays cannot apply the same effect twice.
- Preserve ordering within an aggregate stream; do not assume global ordering across pharmacies.
- Retry transient failures with bounded exponential backoff and jitter; retain poison events for inspection and controlled replay.
- Record acknowledgements and synchronization checkpoints durably.
- Version event contracts and support a compatibility window for staggered Edge upgrades.
- Treat the central network view as eventually consistent and expose its last-sync time and stale-data state.

Exactly-once network delivery is not assumed. The target is at-least-once transport with effectively-once business effects through durable idempotency.

### 4. Conflict and ownership rules

Do not use last-write-wins for stock, sales, payments, dispensing, or audit events.

- A sale and its stock decrement are committed locally as one transaction and carry a unique operation/idempotency key.
- A pharmacy owns its local sale and local stock ledger.
- Cross-pharmacy stock transfers use an explicit transfer workflow with source reservation/dispatch and destination receipt; a central dashboard value is not permission to sell stock at another site.
- Central catalog/policy changes are versioned and distributed to Edge. Each Edge reports the version it has applied.
- Conflicts are resolved by domain-specific commands, validation and, where necessary, human review; never by silently overwriting financial or inventory history.
- Patient and prescription data is synchronized only under explicit authorization, data-minimization and retention rules.

### 5. Offline capability and external dependencies

Maintain an explicit capability matrix with at least these states: supported offline, supported with restrictions, online-only, and blocked pending legal/integration validation.

External fiscalization, e-prescription verification, payment-provider authorization, controlled-medicine registries and other government/provider services must not be simulated as available while disconnected. Whether a transaction can be legally completed offline is a jurisdiction-specific compliance decision. The application must clearly represent pending, rejected and unavailable external operations.

Mortarium is non-critical to POS. If central AI or the LLM provider is unavailable, local pharmacy transactions continue. Any optional local AI capability is isolated, resource-bounded and cannot authorize dispensing, payment or stock mutation.

### 6. Ansible and fleet operations

Ansible is the configuration and lifecycle-management plane for Central and Edge infrastructure. It must not implement pharmacy business logic or synchronize transactional data.

Target inventory groups:

- `central` — central API/control plane, sync ingress, observability and AI services;
- `pharmacy_edges` — site Edge nodes;
- `pharmacy_edges_canary` — explicitly selected pilot/canary sites;
- optional site subgroups and host variables for network, UPS, storage and hardware capabilities.

Target playbooks should be separated by lifecycle: bootstrap, configure, deploy, update, backup, restore, healthcheck and disaster recovery. Use immutable image digests, Ansible Vault or an external secret manager, least-privilege service accounts, idempotent roles, preflight checks, post-deploy health checks and explicit rollback gates.

Fleet updates must be staged (lab -> pilot -> small canary -> controlled waves), with a successful health and synchronization check before proceeding. A failed site or batch must stop further rollout. The exact batch sizes are configuration and release-policy decisions, not hard-coded assumptions.

Ansible must configure VPN/TLS identity, firewall policy, storage, Docker/Compose, PostgreSQL, Edge services, UPS monitoring (for example NUT), backup agents and observability. It must not copy live database files between sites or run ad-hoc SQL to reconcile business events.

### 7. Data protection and recovery

- Encrypt site-to-central transport and protect local disks/backups according to the deployment threat model.
- Keep local database backups and encrypted off-site copies; define WAL/PITR strategy where the selected storage and operational model support it.
- Back up configuration and secrets through approved secret-management procedures, never plaintext Git files.
- Define RPO/RTO separately for local pharmacy operations, central reporting and AI services with the business.
- Test restore on isolated infrastructure and verify database consistency and application-level invariants.
- Monitor UPS state, disk capacity, database health, outbox backlog, last successful sync, failed events and backup age.
- A successful backup job is not proof of recoverability; a restore test is required.

## Consequences

### Positive

- WAN or central outages do not automatically stop approved local pharmacy workflows.
- Local transaction durability is separated from network delivery.
- Central reporting and AI can scale independently from POS traffic.
- A single application codebase can be deployed in Central and Edge roles without prematurely splitting the modular monolith into microservices.
- Ansible provides repeatable, auditable configuration for a growing fleet.

### Costs and risks

- Edge introduces distributed-systems concerns: duplicate delivery, ordering, schema compatibility, conflicts, clock skew, partial outages and per-site operations.
- Each site requires database lifecycle management, monitoring, backups, restore tests and secure device identity.
- Network-wide data is eventually consistent, not instantly current.
- Offline operation must be constrained by legal and external-service requirements.
- A single Edge server remains a site hardware failure domain until a redundant local topology is designed and tested.

## Implementation sequence

1. Audit current domain models, tenant/site identity, POS transactions, audit trail and migration strategy.
2. Define the offline capability matrix and event contracts before writing synchronization code.
3. Implement transactional outbox/inbox, event versioning, idempotent ingestion and sync observability.
4. Add Edge deployment configuration and isolated integration/failure tests.
5. Build Ansible Central/Edge inventories, roles, staged rollout, backup and restore verification.
6. Validate in a lab pharmacy, then a small pilot, then controlled fleet waves.
7. Set production RPO/RTO and SLOs from measured business requirements and restore/failure exercises.

## Non-goals

- No immediate Kubernetes requirement.
- No immediate microservice decomposition.
- No synchronous cloud dependency for local POS.
- No last-write-wins inventory reconciliation.
- No claim that offline fiscalization, e-prescription or other external legal workflows are supported until validated.
- No production rollout or live infrastructure mutation as part of this ADR.

## References

- `docs/architecture/pharmaviyum-architecture.ru.md`
- `docs/architecture/PHARMACY_POS_CATALOG_AUDIT.md`
- `docs/devops/README.md`
- `ansible/inventory/production/hosts.yml`
- `ansible/playbooks/deploy.yml`
- `ansible/roles/app-backend/files/docker-compose-backend.yml`
- Ansible execution strategies: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_strategies.html
