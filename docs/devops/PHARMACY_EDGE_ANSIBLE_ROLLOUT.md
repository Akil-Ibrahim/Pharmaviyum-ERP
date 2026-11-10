# Pharmacy Edge Fleet — Ansible Deployment and Operations Plan

**Status:** Target operating model; not yet deployed.  
**Scope:** Central infrastructure and 100 pharmacy Edge sites.  
**Principle:** Ansible configures infrastructure and releases. Pharmaviyum application services own business transactions and synchronization.

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

## 5. Safe rollout policy for 100 pharmacies

A candidate rollout sequence is:

1. One isolated lab Edge site.
2. Five pilot pharmacies.
3. Twenty pharmacies.
4. Thirty pharmacies.
5. The remaining forty-four pharmacies.

The lab site is separate from the 100 production pharmacies. The 5 + 20 + 30 + 45 production waves total 100. Adjust the final wave to the actual approved fleet inventory; never assume the inventory contains exactly 100 reachable hosts. Never assume the inventory contains exactly 100 reachable hosts.

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
- Do not use `latest` or mutable release tags as deployment identity.
- Validate the database migration against a production-like copy before rollout.
- Use expand/contract migrations: deploy backward-compatible schema first, then application versions, then remove obsolete schema only after the compatibility window.
- Do not run a fleet-wide database migration independently on every Edge if the migration is intended for Central only.
- Edge application and event schema versions must be compatible with the Central sync contract during staggered rollout.
- A backend rollback does not automatically reverse a database migration. Define forward-fix or tested restore strategy for each migration.
- Keep application, schema and event-contract compatibility visible in release metadata.

## 7. Backup and restore controls

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

## 10. Current blockers before 100-site deployment

1. No implemented transactional outbox/inbox or Edge-to-Central Sync Engine was found in the audited paths.
2. Production inventory has one placeholder host, not a 100-site fleet source.
3. Deployment validates only `/health`; operational readiness and synchronization checks are missing.
4. PostgreSQL lifecycle is mostly Compose-managed; the Ansible PostgreSQL role is not a full lifecycle/HA role.
5. Nginx role is not wired into the current deployment, and current Compose has no Nginx service.
6. Backup is local-only; integrity validation, off-site copy and tested restore are not established.
7. Rollback changes the backend image only; it does not handle schema compatibility or data recovery.
8. UPS, VPN, site identity, host security and centralized fleet monitoring are not yet proven as deployed capabilities.

## 11. Implementation order

1. Complete ADR-0002 and the domain-level Central/Edge contracts.
2. Implement and test transactional outbox/inbox and the Sync Engine in the application.
3. Build a lab Edge Compose/deployment profile with durable local PostgreSQL.
4. Add lab inventory and Ansible role tests; do not repoint production inventory yet.
5. Add backup integrity, off-site transfer and a restore playbook; demonstrate recovery.
6. Add Central inventory, Edge identity/VPN, readiness and sync monitoring.
7. Run the lab and five-site pilot failure exercises before widening rollout.

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
