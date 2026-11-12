# Ansible for Pharmaviyum Pharmacy Edge

## 1. What Ansible is

Ansible is an agentless IT automation and configuration-management tool. It connects to Linux hosts over SSH and applies declarative playbooks describing the desired system state. Pharmacy servers do not need a permanently installed Ansible agent.

For Pharmaviyum, Ansible is the controlled operations layer used to prepare and maintain Pharmacy Edge servers. It standardizes host configuration, reduces manual configuration drift, deploys reviewed application releases, verifies readiness, and runs approved maintenance procedures consistently.

Ansible does not replace the Pharmaviyum application, PostgreSQL, local POS, or Central synchronization service. It automates the infrastructure on which those components run.

## 2. Initial rollout boundary: 1–10 pharmacies

The initial operating profile is limited to **a maximum of 10 pharmacy Edge sites**. Start with one lab pharmacy, validate the full lifecycle, then expand to 2–3 sites and gradually toward 10. Deployments use a serial value of one: a failed host or readiness check must stop progression to the next site.

The ten-site limit is an enforced operational guardrail, not proof that ten production sites have already been validated. Do not raise it without a separate capacity, security, resilience, and rollout review.

Each pharmacy must have a unique site identity, database credentials, Edge sync identity, backup namespace, and operational owner.

## 3. Target operating model

A pharmacy has a dedicated Edge host on its local network. Local POS workflows must not require a continuous WAN connection to Central for every transaction. The Edge host retains local operational data and synchronizes with Central when connectivity is available.

Ansible runs from a protected automation controller or approved CI runner. It connects to the selected Edge host over a restricted SSH management path. It is not a public web service and must not run from an employee POS workstation.

```text
Protected Ansible Controller
          | SSH over restricted management network
          v
Pharmacy Edge Host (one site)
  - Docker Engine and Compose
  - Pharmaviyum API
  - Local PostgreSQL and cache
  - Local sync services and backup artifacts
          | HTTPS synchronization when WAN is available
          v
Pharmaviyum Central
```

## 4. Pharmacy prerequisites

Before onboarding a site, verify:

1. A supported Linux server or VM is available; assess CPU, memory, disk, and power protection.
2. The host has a stable hostname and reserved management IP.
3. SSH is reachable only from the approved management network or controller.
4. A dedicated non-root automation account has narrowly scoped privilege escalation.
5. SSH host keys are verified out of band; do not disable host-key checking.
6. Docker Engine and Compose meet the versions pinned by the repository.
7. Required outbound access to the approved container registry and Central endpoint is available.
8. Time synchronization, firewall policy, disk monitoring, and UPS monitoring are configured.
9. A unique pharmacy/site identity and separately issued credentials are available.
10. A change reference, maintenance window, rollback owner, and recovery contact are recorded.

Never reuse another pharmacy's database password, Edge token, or site identity.

## 5. Prepare the Ansible controller

Use an isolated, access-controlled controller such as AWX/AAP or an approved CI runner.

- Pin Ansible Core and collection versions.
- Store SSH keys and Vault credentials in the controller's secret store.
- Restrict who can launch deployment, migration, backup, and restore jobs.
- Require approval for protected inventories and production environments.
- Keep inventories and playbooks in version control; never commit secrets or decrypted Vault files.
- Record operator, commit, release digest, target site, change reference, and job result.

The controller should have network access only to the management endpoints it needs.

## 6. Create a one-site inventory

Begin with one lab host. Supply actual connection details through a protected inventory source.

The repository includes an isolated lab inventory at `ansible/inventory/lab/hosts.yml`. It reads the lab host, SSH user, and lab database password from protected runtime environment variables; it uses a non-production pharmacy ID and site code. Review that file before use. Do not copy its lab identity or credentials into production. Production inventory must define a real SSH endpoint/user, unique `pharmacy_id` and `site_code`, and a unique per-pharmacy `postgres_password` for every host.

## 7. Configure release inputs and secrets

Provide required values at job runtime or through encrypted variables:

- `PHARMAVIYUM_APP_VERSION`: immutable release tag or approved image digest; never use `latest`.
- `PHARMAVIYUM_BACKEND_IMAGE_DIGEST`: approved immutable `sha256:<64-hex>` image digest.
- `PHARMAVIYUM_GHCR_USERNAME` and `PHARMAVIYUM_GHCR_TOKEN`: least-privilege registry credentials.
- Per-host `pharmacy_id`, `site_code`, `ansible_host`, and `ansible_user`; IDs and site codes must be unique.
- A unique per-host `postgres_password`, supplied through encrypted host variables or the secret manager (the lab inventory reads `PHARMAVIYUM_LAB_POSTGRES_PASSWORD`).
- Explicit approved versions for every package in `docker_package_names` via `docker_package_versions`; deployment fails closed while any pin is missing.
- Edge node UUID, Edge token, and Central HTTPS sync URL: configure all three together, or leave all three disabled until sync onboarding is approved.

Do not put secrets in shell history, command-line arguments, tickets, or source control. Prefer protected controller credentials and masked runtime variables. Ensure job logs do not disclose secret values.

## 8. Deployment workflow

1. Review the target commit and playbook diff.
2. Confirm the inventory contains only the approved pharmacy hosts and no more than ten sites.
3. Run syntax, lint, unit, and role tests in CI.
4. Test in an isolated lab before any pharmacy pilot.
5. Verify immutable image reference, unique site credentials, and change approval.
6. Run the deployment playbook against the lab or explicitly approved target.
7. Verify `/ready` and inspect container, database, disk, and sync health.
8. Perform a POS smoke test and verify that a temporary WAN outage does not block local sales.
9. Record the release digest and evidence before adding another site.

From the repository's `ansible/` directory, the lab command is:

```bash
ansible-playbook -i inventory/lab/hosts.yml playbooks/deploy.yml --limit pharmacy-edge-lab-01
```

The controller must provide all required lab connection/release variables and approved Docker package pins at runtime. The lab inventory is isolated and must never point to a live pharmacy. The production inventory remains the default in `ansible.cfg`, so always pass the intended lab inventory explicitly for lab work.

Never run a production deployment from an unreviewed branch.

## 9. Database migrations are separate

Application deployment must not implicitly run Alembic migrations. A migration is a separate reviewed change requiring its own playbook, compatibility checks, explicit approval and change reference, verified backup, controlled target selection, and post-migration readiness validation. Do not use the normal deployment workflow as a shortcut for schema changes.

## 10. Backup and recovery

A backup stored only on the pharmacy Edge host is not disaster recovery. Before production acceptance, define and test:

- encrypted off-site storage independent of the pharmacy host;
- site-scoped remote identities and least-privilege upload permissions;
- checksum and artifact verification after transfer;
- centrally controlled retention and deletion authority;
- documented RPO and RTO;
- restore from the remote copy into an isolated database;
- business-level validation of critical tables, row counts, migration version, and application readiness.

Never test restore by overwriting the live pharmacy database. Review a successful isolated restore drill before declaring a site recoverable.

## 11. Security and operational safeguards

- Use SSH key authentication, host-key verification, least privilege, and protected controller credentials.
- Keep secrets out of Git, logs, process arguments, and plaintext inventories.
- Pin production container images by immutable digest.
- Expose only required services; database ports must not be publicly reachable.
- Use unique database credentials and Edge synchronization identities per pharmacy.
- Use Ansible check mode where supported, but never treat it as a substitute for lab testing.
- Keep roles idempotent and verify that a second run produces no unexpected changes.
- Stop on readiness failure; do not continue to the next pharmacy.
- Keep deployment, migration, backup, restore, and rollback as separate auditable operations.

## 12. Site acceptance checklist

A site is not accepted merely because a playbook exits successfully. Require evidence for:

- [ ] Host hardening, SSH, firewall, time sync, and UPS monitoring.
- [ ] Reproducible Ansible execution and clean second-run idempotency.
- [ ] Immutable application release and successful readiness checks.
- [ ] Local POS transaction during WAN outage.
- [ ] Safe sync replay after connectivity returns.
- [ ] No duplicate sales or inventory movements after retry/replay.
- [ ] Verified local and encrypted off-site backups.
- [ ] Successful isolated restore from the off-site copy.
- [ ] Monitoring for disk, database, backup age, sync backlog, and last successful sync.
- [ ] Documented site owner, RPO/RTO, rollback owner, and support contact.

## 13. Current limitations

This guide defines the intended process and initial ten-site boundary. It does not claim that the production acceptance checklist is complete. Lab evidence is still required for the full Pharmacy Edge lifecycle, off-site backup and restore, business-level recovery, offline POS acceptance, UPS monitoring, and end-to-end synchronization recovery.

Do not deploy to real pharmacy hosts until the relevant changes are approved and the lab and pilot gates have passed.
