# Pharmacy Edge Fleet — Ansible Deployment and Operations Plan

**Status:** Target operating model; not yet deployed.  
**Scope:** Initial Ansible validation for 1–10 pharmacy Edge sites, with an explicit architecture target of up to 100 sites.  
**Principle:** Ansible configures infrastructure and releases. Pharmaviyum application services own business transactions and synchronization.

## 1. Verified repository baseline

The current `main` branch contains:

- `ansible/inventory/production/hosts.yml` with one `pharmacy-server-01` host.
- `ansible/playbooks/deploy.yml` targeting `pharmacy_servers`; it validates release and Edge sync settings, checks Docker/Compose, deploys roles in controlled waves and verifies `/ready`.
- `ansible/roles/app-backend/` which writes an environment file, copies a Compose definition, pulls a backend image, starts PostgreSQL and Valkey, then starts the backend. Database migrations are a separate, explicitly approved release operation.
- `ansible/roles/postgresql/` which currently prepares a directory and reports container status; PostgreSQL itself is created by Compose.
- `ansible/playbooks/backup.yml` which creates a local compressed PostgreSQL dump, verifies gzip integrity and SHA-256, writes a manifest, and prunes expired local artifacts only after a new backup has been verified. `ansible/playbooks/restore.yml` performs a non-destructive restore drill into a separately named database on exactly one explicitly confirmed Edge host. Scheduling is delegated to a protected automation controller.
- `ansible/playbooks/rollback.yml` which rolls back the backend image and checks `/health`; it does not restore a database backup.
- A Compose definition containing `db`, `redis` (Valkey image) and `backend`. It does not define an Nginx service.
- An Nginx role exists, but it is not included in the current deployment playbook.

These are repository facts, not a claim that the playbooks have been executed successfully on a real pharmacy server.

## 0.1 Starter rollout: 1–10 pharmacies

The first engineering objective is to make one pharmacy Edge deployment safe and repeatable, then validate 2–3 and finally 4–10 sites. The active Ansible rollout limit is deliberately set to 10 and deployment is serial (`serial: 1`) with fail-fast behavior. The limit is operational, not an architecture ceiling.

For each site, use its own immutable `pharmacy_id`, `site_code`, Edge node ID, Edge token, SSH identity and PostgreSQL credential. Per-site secrets must come from encrypted host variables or an approved secret manager. Global defaults for the PostgreSQL password and Edge token are intentionally empty, preventing accidental credential reuse. The lab inventory reads only its own test password from `PHARMAVIYUM_LAB_POSTGRES_PASSWORD`. The production inventory has no localhost fallback.

The Docker role supports only Debian/Ubuntu hosts, requires explicit per-site or per-OS package-version pins for Docker Engine and plugins, and verifies installed versions against those pins. Set `docker_package_versions` in approved host/group variables before provisioning a fresh host. The deployment user is not added to the `docker` group because Docker socket access is effectively root-equivalent.

A single pharmacy may run as an isolated Edge. Central sync is enabled only when that site's node ID, token and HTTPS Central URL are all configured and pass validation. POS and local transactional workflows must not wait on the Central API.

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

## Production Mortarium AI profile (Ansible / on-premises)

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

## 4. Playbook responsibilities

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

## 5. Target capacity: up to 100 pharmacies

The target architecture supports up to 100 independent Edge sites through stable site identity, per-site secrets, isolated local databases, Central/Edge inventory groups and versioned sync contracts. The starter playbook currently enforces a maximum of 10 hosts; the 100-site profile is not enabled until the starter quality gates and later fleet-scale tests pass.

Use a CMDB-backed dynamic inventory for the full fleet. Keep Central and Edge in separate groups and divide Edge hosts into explicitly approved canary/wave child groups. `ansible/inventory/examples/fleet-100.yml` is a non-runnable schema example.

A candidate rollout sequence is:

1. One isolated lab Edge site.
2. Five pilot pharmacies.
3. Twenty pharmacies.
4. Thirty pharmacies.
5. The remaining forty-four pharmacies.

The lab site is separate from production. The 5 + 20 + 30 + 45 production waves total 100; these are planning examples, not enabled defaults. Adjust wave sizes to the approved inventory and never assume every site is reachable.

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

## 6. Release and migration rules

- Build once in CI and deploy the same immutable image digest to lab, pilot and production.
- Supply `PHARMAVIYUM_BACKEND_IMAGE_DIGEST` as `sha256:<64-hex>`; Ansible pulls and writes the digest reference rather than resolving a mutable tag. Rollback requires the previous verified image digest as well as its release label.
- Do not use `latest` or mutable release tags as deployment identity.
- Run `ansible/playbooks/migrate.yml` as a separate, explicitly approved operation before `deploy.yml`; it requires `migration_approved=true` and a non-empty change reference.
- The migration playbook starts only DB/cache dependencies, verifies PostgreSQL readiness, creates a pre-migration compressed dump, verifies the gzip archive and records its SHA-256 before running Alembic from the pinned release image.
- Validate the database migration against a production-like copy before rollout. A valid gzip archive and checksum prove archive integrity only; they do not replace an isolated restore drill or off-site backup.
- Use expand/contract migrations: deploy backward-compatible schema first, then application versions, then remove obsolete schema only after the compatibility window.
- Do not run a fleet-wide database migration independently on every Edge if the migration is intended for Central only.
- Edge application and event schema versions must be compatible with the Central sync contract during staggered rollout.
- A backend rollback does not automatically reverse a database migration. Define forward-fix or tested restore strategy for each migration.
- Keep application, schema and event-contract compatibility visible in release metadata.

## 7. Backup and restore controls

The current backup playbook creates a local gzip-compressed SQL dump, verifies the gzip stream and published SHA-256, writes a metadata manifest, serializes backup runs with a lock, and retains local files according to `backup_retention_days`. The restore playbook verifies an independently supplied SHA-256 and restores into a new, isolated database on one explicitly confirmed host; it never overwrites the live application database and leaves a successful restore target for operator inspection. These are useful local verification controls, but they are still not a disaster-recovery solution. Before production fleet use, add:

- explicit backup integrity check (for example, inspect the dump with the matching PostgreSQL client);
- encryption before off-site transfer;
- a remote destination independent of the pharmacy host;
- retention policy by business and regulatory requirements;
- backup age and transfer monitoring;
- off-site backup verification and restore from the remote copy;
- restore verification of critical business row counts and application invariants (the current drill checks basic schema presence and Alembic metadata only);
- documented RPO/RTO per site and Central.

Backup scheduling is intentionally not installed by the playbook on pharmacy Edge hosts. Run it from a protected automation controller (for example AWX/AAP or an approved scheduler) that obtains Vault/secret-manager credentials at runtime. Do not distribute a reusable Vault password as an unmanaged plaintext file across the fleet.

A backup is not accepted as recoverable until a restore test has succeeded on an isolated target.

## 8. Security and secrets

- Use per-site credentials and per-node identities; avoid one shared credential for all pharmacies.
- Prefer an external secret manager; Ansible Vault is an acceptable controlled fallback.
- Use `no_log: true` for tasks handling secrets.
- Do not expose PostgreSQL, Valkey or backend ports directly to the public internet.
- Prefer outbound Edge-to-Central connectivity through authenticated TLS/VPN; do not require inbound public SSH to pharmacy sites.
- Restrict the Docker socket and membership of the `docker` group; Docker access is effectively root-equivalent.
- Rotate certificates and credentials with a tested overlap window.
- Store audit and operational telemetry without patient-identifying payloads unless explicitly required and protected.

## 9. Required Ansible quality gates

Before a role is eligible for production:

- YAML syntax and `ansible-lint` pass.
- Molecule tests cover converge, idempotence, verify and destroy.
- A second playbook run reports no unexpected changes.
- `--check --diff` is reviewed where modules support it.
- Secrets are absent from output, diffs and CI artifacts.
- A failure-injection test proves a failed host/batch stops later rollout.
- Restore and rollback are exercised in an isolated lab.
- Production inventory is protected and reviewed separately from role code.

## 10. Current blockers before declaring 100-site production readiness

1. The repository now contains a durable Edge outbox dispatcher and Central inbox ingress foundation; full operational acceptance, end-to-end reconciliation, conflict workflows, fleet load tests and production recovery evidence remain outstanding.
2. Production inventory has one placeholder host, not a 100-site fleet source.
3. Deployment now checks `/ready`, but site-level POS synthetic transaction, backup integrity, sync backlog/last-sync and UPS checks are not yet wired into Ansible postflight.
4. PostgreSQL lifecycle is mostly Compose-managed; the Ansible PostgreSQL role is not a full lifecycle/HA role.
5. Nginx role is not wired into the current deployment, and current Compose has no Nginx service.
6. Backup is local-only; off-site copy and restore-from-off-site are not established. The new isolated restore drill is a basic schema check, not a full application recovery acceptance test.
7. Rollback changes the backend image only; it does not handle schema compatibility or data recovery.
8. UPS, VPN, site identity, host security and centralized fleet monitoring are not yet proven as deployed capabilities.

## 11. Implementation order

1. Complete Ansible hardening and test gates for one lab Edge, then one pilot pharmacy, then 2–3 and up to 10 sites. Keep the active rollout limit at 10 throughout this phase.
2. Complete ADR-0002 and the domain-level Central/Edge contracts.
3. Complete end-to-end tests for the durable outbox/inbox and sync processing contract.
4. Build a lab Edge Compose/deployment profile with durable local PostgreSQL.
5. Add lab inventory and Ansible role tests; do not repoint production inventory yet.
6. Add backup integrity, off-site transfer and a restore playbook; demonstrate recovery.
7. Add Central inventory, per-site Edge identity/VPN, readiness and sync monitoring.
8. Run lab and small-pilot failure exercises before widening rollout.
9. Only after 1–10 is proven, enable the 100-site dynamic inventory, staged wave controller, central observability capacity, backup throughput and recovery capacity.

## References

- `docs/adr/ADR-0002-offline-first-central-edge.md`
- `docs/devops/README.md`
- `ansible/ansible.cfg`
- `ansible/playbooks/deploy.yml`
- `ansible/playbooks/backup.yml`
- `ansible/playbooks/migrate.yml`
- `ansible/playbooks/rollback.yml`
- `ansible/roles/app-backend/files/docker-compose-backend.yml`
- Ansible rolling execution: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_strategies.html
- Ansible testing strategy: https://docs.ansible.com/projects/ansible/latest/reference_appendices/test_strategies.html
