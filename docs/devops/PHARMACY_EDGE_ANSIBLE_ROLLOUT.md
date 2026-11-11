# Pharmacy Edge Fleet — Ansible Deployment and Operations Plan

**Status:** Target operating model; not yet deployed.  
**Scope:** Starter production profile for 1–10 pharmacy Edge sites; designed to scale later without changing site identity or sync contracts.  
**Principle:** Ansible configures infrastructure and releases. Pharmaviyum application services own business transactions and synchronization.

## 0. Starter production profile: 1–10 pharmacies

This is the first validation and rollout envelope. The target architecture and inventory model are designed for up to 100 pharmacy Edge sites, but 100-site operation is not yet validated. Current Ansible rollout policy remains capped at 10 sites until the 1–10 profile passes its full test gates.

### Operating topology

| Pharmacy count | Initial topology | Required behavior |
|---|---|---|
| 1 | One independent Edge node at the pharmacy; Central services may remain on the existing managed platform | Local POS and local database are the site's operational boundary; WAN loss must not block permitted local transactions |
| 2–3 | One Edge node per pharmacy plus one Central control/sync endpoint | Each site has its own identity, credentials, database and backup lifecycle |
| 4–10 | Same Central + per-site Edge topology, deployed in controlled batches | One failed or offline site must not block healthy sites; deploy and verify one site at a time |

Do not place all pharmacies on one shared local database. Each pharmacy Edge owns its local transactional data and durable event journal. Central receives authorized events through the application Sync Engine; Ansible provisions and updates infrastructure but does not implement business synchronization.

### Initial deployment rules

- Current active rollout limit: 10 pharmacy Edge sites. This is an operational safety limit, not the intended architecture ceiling. The configured target fleet capacity is 100; larger rollout waves remain disabled until separately validated and approved.
- Deploy one Edge host at a time (`serial: 1`) and stop on failure. Do not use unattended fleet-wide parallel rollout at this stage.
- Use a separate immutable `pharmacy_id` / `site_code` per pharmacy and separate credentials per Edge node.
- A single-pharmacy installation may operate as an isolated Edge deployment. Central sync is enabled only when the Central endpoint and sync contract are configured and verified.
- For 2–10 pharmacies, Central is the control and synchronization plane; it is not a synchronous dependency for POS checkout, payment, dispensing or local stock commits.
- Every Edge needs durable local PostgreSQL storage, tested local backups, UPS-backed graceful shutdown, time synchronization and monitored disk capacity.
- Edge-to-Central connectivity should be outbound authenticated TLS/VPN. Do not expose PostgreSQL, Valkey or the backend directly to the public internet.
- Mortarium AI remains optional and isolated. Its unavailability or resource saturation must not stop pharmacy workflows.

### Starter rollout gates

1. Lab: one non-production Edge node, synthetic data only.
2. Pilot: one real pharmacy after local backup/restore and offline-mode tests pass.
3. Small network: expand to 2–3 sites, then 4–10, with explicit operator approval between batches.
4. At each site, verify database readiness, application readiness, local POS synthetic transaction, backup freshness, disk/UPS status and sync backlog/last-sync state.
5. Stop the rollout on any failed readiness check. Report unreachable sites as not updated; never silently skip them.

### Scope boundary

The repository currently has a single Compose backend/database/cache deployment shape. The documented offline-first Central/Edge behavior is a target architecture, not proof that the transactional outbox/inbox, conflict resolution, durable sync engine, site failover or offline POS behavior are already implemented. The 1–10 profile must not be advertised as production-ready until those application-level acceptance tests pass.

## 1. Verified repository baseline

The current `main` branch contains:

- `ansible/inventory/production/hosts.yml` with one `pharmacy-server-01` host.
- `ansible/playbooks/deploy.yml` targeting `pharmacy_servers`; it validates an immutable release tag, checks Docker/Compose, deploys roles and checks only the backend `/health` endpoint.
- `ansible/roles/app-backend/` which writes an environment file, copies a Compose definition, pulls a backend image, starts PostgreSQL and Valkey, runs Alembic migrations, then starts the backend.
- `ansible/roles/postgresql/` which currently prepares a directory and reports container status; PostgreSQL itself is created by Compose.
- `ansible/playbooks/backup.yml` which writes a local compressed `pg_dump`, prunes local files by age and installs a cron entry.
- `ansible/playbooks/rollback.yml` which rolls back the backend image and checks `/health`; it does not restore a database backup.
- A Compose definition containing `db`, `redis` (Valkey image) and `backend`. It does not define an Nginx service.
- An Nginx role exists, but it is not included in the current deployment playbook.

These are repository facts, not a claim that the playbooks have been executed successfully on a real pharmacy server.

## 2. Target inventory

Use separate, explicit inventories for development, lab, staging and production. Keep secrets out of inventory files.

Suggested production inventory:

```text
ansible/
  inventories/
    development/hosts.yml
    lab/hosts.yml
    staging/hosts.yml
    production/
      hosts.yml
      group_vars/
      host_vars/
```

Suggested logical groups:

```yaml
all:
  children:
    central:
      hosts:
        central-control-01:
    pharmacy_edges:
      children:
        pharmacy_edges_canary:
          hosts: {}
        pharmacy_edges_wave_01:
          hosts: {}
        pharmacy_edges_wave_02:
          hosts: {}
    monitoring:
      hosts:
        observability-01:
```

The example is a schema sketch only. Real hostnames, addresses, site IDs, SSH identities and secrets must come from the operator's approved inventory source. Do not use `127.0.0.1` as a production default.

Every Edge host must have explicit non-secret metadata: immutable `pharmacy_id`, `site_code`, `edge_node_id`, environment, hardware profile, storage paths, network/VPN profile and backup destination. Validate uniqueness of site and node identities before deployment.

## 3. Role boundaries

### Shared host baseline

- `common`: supported OS packages, time synchronization, users and base directories.
- `security`: SSH hardening, firewall policy, unattended security updates policy, disk encryption prerequisites and audit settings.
- `networking` / `vpn`: outbound authenticated Central connectivity, TLS material deployment and site network policy.
- `docker`: pinned Docker Engine and Compose plugin versions, daemon configuration and log rotation.
- `ups_monitoring`: NUT client/server configuration where supported, UPS telemetry and low-battery shutdown policy.
- `node_exporter` / `otel_collector`: host and service telemetry.

### Central roles

- `central_api`: central application deployment.
- `sync_ingress`: authenticated Edge event ingestion and operational sync visibility.
- `central_data`: central PostgreSQL and backup policy, only where self-managed.
- `mortarium_ai`: isolated AI runtime/gateway, model configuration and bounded resource policy.
- `observability`: metrics, traces, logs and alerting.

### Edge roles

- `pharmacy_edge`: local API and worker deployment.
- `edge_postgresql`: local transactional database, storage layout, health checks and backup configuration.
- `edge_cache`: cache/queue only for explicitly non-authoritative or recoverable state.
- `edge_sync`: deploy/configure the application Sync Engine; Ansible does not transport business events itself.
- `edge_backup`: local encrypted backup and off-site transfer agent.
- `edge_health`: readiness, disk, DB, backup age, outbox backlog and last successful sync checks.

Prefer a shared role with explicit `deployment_role: central|edge` only when the tasks and security boundaries are genuinely shared. Do not hide Central-only services inside every pharmacy deployment.

## 4. Production Mortarium AI profile (Ansible / on-premises)

The Ansible/on-premises production profile is deliberately separate from the FastAPI Cloud demo profile.

| Concern | Demo: FastAPI Cloud | Production target: Ansible / on-premises |
|---|---|---|
| LLM provider | QwenCloud API | Local Ollama runtime |
| Model profile | `qwen3.8-flash` | `Qwen3.5 9B Q4_K_M` (target default; hardware validation required) |
| Network dependency for generation | External provider connectivity | Local inference after model/runtime provisioning |
| Credentials | QwenCloud API key in FastAPI Cloud secrets | No external LLM API key required for local inference; protect any registry/download credentials separately |
| Quota/cost controls | Provider free quota + application guard | Local CPU/GPU/RAM/disk capacity, concurrency and queue limits |
| Deployment owner | FastAPI Cloud configuration/release | Ansible roles and approved on-premises release process |

The demo's QwenCloud settings, free-tier assumptions and API key must not be copied into the production Ansible inventory or Edge environment. Likewise, the on-premises Ollama profile must not be treated as proof that the FastAPI Cloud demo has a local model available.

### Production placement

- Deploy the primary Mortarium AI runtime on the Central on-premises platform by default, behind an authenticated internal API boundary.
- Do not install a model runtime on every pharmacy Edge node by default. An optional site-local inference node is a separate hardware-profile decision and must be explicitly enabled per site.
- Keep POS checkout, inventory commits, dispensing authorization, payment and audit transactions independent of Mortarium and Ollama.
- If Central AI is unreachable, AI-dependent features degrade gracefully; each Edge continues its permitted local business workflows and queues eligible synchronization events.
- A local Edge AI runtime, if later approved, may provide optional assistant functionality only. It must not authorize dispensing, payment, stock mutation or override deterministic business rules.

### Ansible responsibilities for the production AI runtime

The target Ansible role (for example, `mortarium_ai`) should own:
- pinned Ollama runtime version and service configuration;
- explicit model identifier/revision and model artifact integrity verification;
- model storage path, disk-space preflight and retention policy;
- CPU/GPU/RAM resource limits and concurrency/queue bounds validated against the actual host profile;
- internal-only listener binding, firewall rules and authenticated service-to-service access;
- startup/readiness checks that verify the model is actually loaded and can complete a bounded synthetic inference;
- structured operational metrics, logs and traces without prompts, secrets or patient-identifying payloads;
- controlled model/runtime upgrades, canary validation and rollback to a previously verified artifact;
- service restart policy and graceful shutdown behavior.

Do not expose Ollama's unauthenticated management/API port directly to the public internet. Place an authenticated application gateway in front of model inference. Restrict which application services and MCP tools can invoke AI capabilities.

### Production acceptance gates

Before enabling the production profile:
1. Validate the selected quantized model on the exact target CPU/GPU/RAM profile; record model artifact hash, inference latency, throughput, peak memory and disk usage.
2. Run representative synthetic pharmacy prompts and the approved RAG evaluation suite; validate citation grounding, medication entity accuracy, negation preservation, multilingual retrieval and patient/tenant isolation.
3. Verify that AI saturation or process failure does not degrade POS transaction latency or availability.
4. Test Central WAN/runtime outage and confirm Edge offline workflows remain operational.
5. Verify internal authentication, network policy, secret handling, telemetry redaction and auditability.
6. Test model upgrade and rollback without changing business data or database schema.
7. Record the exact model/runtime versions and benchmark evidence in the release artifact.

The model name above is a documented target profile, not evidence that Ollama or this model is already installed, benchmarked or running on production hardware. Hardware sizing, concurrency limits, latency SLOs and whether any Edge site receives local inference remain subject to measured pilot results.

## 5. Playbook responsibilities

Suggested entry points:

- `site.yml`: orchestration only; imports the role-specific playbooks.
- `bootstrap.yml`: first-time OS, SSH, VPN and host identity setup.
- `central.yml`: central services.
- `pharmacy-edge.yml`: one or more Edge sites.
- `deploy.yml`: deploy a pinned application release.
- `update.yml`: controlled staged release with preflight and postflight checks.
- `backup.yml`: run/verify backups and verify off-site transfer.
- `restore.yml`: explicit restore workflow, requiring a selected backup and target.
- `healthcheck.yml`: read-only service and operational health report.
- `disaster-recovery.yml`: documented Central or site recovery procedure.

Keep inventory selection explicit on every operator command. Production playbooks must fail closed if the selected environment, site identity, image digest, backup target or required secrets are missing.

## 6. Target capacity: up to 100 pharmacies

The long-term capacity target is 100 independent Edge sites. The architecture must not encode the starter limit of 10 as a domain or identity limit. Use stable site IDs, per-site credentials, isolated databases and versioned sync contracts so that the same site model works from one pharmacy through one hundred.

### Inventory and technical scaling model

- Keep Central and Edge in separate inventory groups. Edge sites belong to explicit canary and rollout-wave child groups; do not infer deployment order from host naming.
- Keep one host record per pharmacy Edge with immutable `pharmacy_id`, `site_code` and `edge_node_id`. Enforce uniqueness across the complete fleet before any write operation.
- Prefer a CMDB-backed/dynamic inventory for a real 100-site fleet. A static YAML inventory remains acceptable for the 1–10 pilot, with reviewed inventory changes.
- Keep per-site variables and credentials isolated. Do not share a database password, SSH identity or application secret across all sites.
- The starter deployment playbook remains capped at 10 sites and `serial: 1`. The future fleet profile may raise the allowed inventory count only after staged rollout, health gates, sync compatibility and recovery tests have passed.
- At 100 sites, Ansible remains the provisioning/release control plane. It must not become the business-event transport or central POS dependency. Sync traffic, metrics and backups require independent bounded queues, retries and central capacity planning.

A candidate rollout sequence is:

1. One isolated lab Edge site.
2. Five pilot pharmacies.
3. Twenty pharmacies.
4. Thirty pharmacies.
5. The remaining forty-four pharmacies.

The lab site is separate from the 100 production pharmacies. The 5 + 20 + 30 + 45 production waves total 100. These are planning examples, not enabled defaults. Adjust each wave to the approved inventory; never assume all hosts are reachable.

Ansible `serial` can limit each play to a batch, but it is not a substitute for release gates. After every batch:

- verify application readiness, not only process liveness;
- verify local PostgreSQL read/write checks;
- verify Sync Engine readiness and outbox/inbox health;
- verify last successful Central sync where WAN is available;
- verify disk capacity, clock synchronization and UPS telemetry;
- verify backup freshness and backup integrity;
- run a pharmacy-safe synthetic transaction test in the approved test mode;
- stop the rollout on any failed or unreachable site until triaged.

Use explicit maintenance windows and an operator approval between waves. A disconnected site should be reported as not updated, not silently skipped.

## 7. Release and migration rules

- Build once in CI and deploy the same immutable image digest to lab, pilot and production.
- Do not use `latest` or mutable release tags as deployment identity.
- Validate the database migration against a production-like copy before rollout.
- Use expand/contract migrations: deploy backward-compatible schema first, then application versions, then remove obsolete schema only after the compatibility window.
- Do not run a fleet-wide database migration independently on every Edge if the migration is intended for Central only.
- Edge application and event schema versions must be compatible with the Central sync contract during staggered rollout.
- A backend rollback does not automatically reverse a database migration. Define forward-fix or tested restore strategy for each migration.
- Keep application, schema and event-contract compatibility visible in release metadata.

## 8. Backup and restore controls

The current backup playbook creates a local SQL dump and retains seven days of local files. Before production fleet use, add:

- explicit backup integrity check (for example, inspect the dump with the matching PostgreSQL client);
- encryption before off-site transfer;
- a remote destination independent of the pharmacy host;
- retention policy by business and regulatory requirements;
- backup age and transfer monitoring;
- a tested restore playbook;
- restore verification of schema, critical row counts and application invariants;
- documented RPO/RTO per site and Central.

The current cron command references `/opt/ansible/playbooks/backup.yml` and `/opt/ansible/vault.key`. Verify that these paths, permissions, key lifecycle and execution environment are actually provisioned before enabling the cron job. Do not distribute a reusable Vault password as an unmanaged plaintext file across the fleet.

A backup is not accepted as recoverable until a restore test has succeeded on an isolated target.

## 9. Security and secrets

- Use per-site credentials and per-node identities; avoid one shared credential for all pharmacies.
- Prefer an external secret manager; Ansible Vault is an acceptable controlled fallback.
- Use `no_log: true` for tasks handling secrets.
- Do not expose PostgreSQL, Valkey or backend ports directly to the public internet.
- Prefer outbound Edge-to-Central connectivity through authenticated TLS/VPN; do not require inbound public SSH to pharmacy sites.
- Restrict the Docker socket and membership of the `docker` group; Docker access is effectively root-equivalent.
- Rotate certificates and credentials with a tested overlap window.
- Store audit and operational telemetry without patient-identifying payloads unless explicitly required and protected.

## 10. Required Ansible quality gates

Before a role is eligible for production:

- YAML syntax and `ansible-lint` pass.
- Molecule tests cover converge, idempotence, verify and destroy.
- A second playbook run reports no unexpected changes.
- `--check --diff` is reviewed where modules support it.
- Secrets are absent from output, diffs and CI artifacts.
- A failure-injection test proves a failed host/batch stops later rollout.
- Restore and rollback are exercised in an isolated lab.
- Production inventory is protected and reviewed separately from role code.

## 11. Current blockers before declaring 100-site capacity production-ready

1. No implemented transactional outbox/inbox or Edge-to-Central Sync Engine was found in the audited paths.
2. Production inventory currently has one placeholder host; a reviewed CMDB-backed 100-site inventory and uniqueness validation are not yet implemented.
3. Deployment validates only `/health`; operational readiness and synchronization checks are missing.
4. PostgreSQL lifecycle is mostly Compose-managed; the Ansible PostgreSQL role is not a full lifecycle/HA role.
5. Nginx role is not wired into the current deployment, and current Compose has no Nginx service.
6. Backup is local-only; integrity validation, off-site copy and tested restore are not established.
7. Rollback changes the backend image only; it does not handle schema compatibility or data recovery.
8. UPS, VPN, site identity, host security and centralized fleet monitoring are not yet proven as deployed capabilities.

## 12. Implementation order

1. Complete the full Ansible quality and recovery gates for one lab Edge, then one pilot pharmacy, then 2–3 and up to 10 sites. Keep the active rollout limit at 10 throughout this phase.
2. Complete ADR-0002 and the domain-level Central/Edge contracts.
3. Implement and test transactional outbox/inbox and the Sync Engine in the application.
4. Build a lab Edge Compose/deployment profile with durable local PostgreSQL.
5. Add lab inventory and Ansible role tests; do not repoint production inventory yet.
6. Add backup integrity, off-site transfer and a restore playbook; demonstrate recovery.
7. Add Central inventory, Edge identity/VPN, readiness and sync monitoring.
8. Run the lab and five-site pilot failure exercises before widening rollout.
9. Only after the 1–10 profile is proven, add and validate the 100-site dynamic inventory, staged wave controller, central observability capacity, backup throughput and recovery capacity.

## References

- `docs/adr/ADR-0002-offline-first-central-edge.md`
- `docs/devops/README.md`
- `ansible/ansible.cfg`
- `ansible/playbooks/deploy.yml`
- `ansible/playbooks/backup.yml`
- `ansible/playbooks/rollback.yml`
- `ansible/roles/app-backend/files/docker-compose-backend.yml`
- Ansible rolling execution: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_strategies.html
- Ansible testing strategy: https://docs.ansible.com/projects/ansible/latest/reference_appendices/test_strategies.html
