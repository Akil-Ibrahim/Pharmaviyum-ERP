# Restic off-site backup upload (first implementation slice)

## Scope

`playbooks/backup-offsite.yml` uploads one already verified local PostgreSQL dump, its SHA-256 sidecar and its YAML manifest to an existing site-scoped Restic REST repository.

- Restic version is pinned by the playbook to `0.19.1`; the binary must be installed at `/usr/bin/restic` by a separately reviewed host-provisioning change.
- The repository URL must use `rest:https://` and end in the immutable `pharmacy_id`.
- Each pharmacy must have its own Restic repository, encryption password, REST username and REST password, supplied through protected Ansible Vault/host variables.
- The REST account must be provisioned server-side as append-only and restricted to that pharmacy's repository. The client playbook cannot prove the server's ACL or immutability policy.
- TLS certificate verification remains enabled. Do not use `--insecure-tls`.
- The playbook does not initialize repositories, prune snapshots, delete local artifacts, or change retention.
- Approval and site/repository/credential validation run on the Ansible controller before SSH. The actual upload is serial, fail-closed and limited to the active 1–10-site wave; inventory architecture ceiling remains 100.

## Required protected per-pharmacy variables

Store these in encrypted `host_vars` or an approved secrets integration; never commit plaintext values:

| Variable | Requirement |
|---|---|
| `pharmacy_id` | Stable unique ID; matches repository suffix |
| `site_code` | Stable pharmacy/site code |
| `restic_repository_url` | `rest:https://<approved-endpoint>/<pharmacy_id>` |
| `restic_repository_password` | Unique repository encryption password, at least 20 characters |
| `restic_rest_username` | Unique site-scoped append-only REST identity |
| `restic_rest_password` | Secret for that REST identity |

The repository must already be initialized by a separately controlled provisioning procedure. The playbook intentionally fails if `restic snapshots --json` cannot open it.

## Explicit operator invocation

Run only after local backup creation has completed and its payload, checksum and manifest exist:

```bash
cd ansible
ansible-playbook -i inventory/production/hosts.yml playbooks/backup-offsite.yml \
  --limit <exact-pharmacy-edge-host> \
  --ask-vault-pass \
  -e offsite_backup_approved=true \
  -e offsite_backup_approval_reference=<change-or-approval-reference> \
  -e offsite_backup_file=/opt/pharmaviyum/backups/pharmaviyum_<timestamp>.sql.gz
```

Do not place secrets in `-e`, shell arguments, CI logs or command-line URLs. The upload task uses environment variables and `no_log`.

## Verification boundary

The playbook verifies the local gzip stream, SHA-256 and manifest/site identity before upload. Restic's normal backup verification remains enabled (the playbook does not disable extra verification). It then confirms the returned snapshot ID, host, pharmacy/site tags and source path in the remote snapshot list, and streams the SQL dump, checksum sidecar and manifest back through `restic dump | sha256sum` to compare their hashes with the local originals. The read-back is streamed to the hash process, not written as a second full dump to disk. It does download the full compressed artifact set again, so schedule it with the pharmacy WAN bandwidth and backup window in mind.

This is an initial upload slice, **not yet a complete disaster-recovery guarantee**. It does not yet run a full remote repository data check, test recovery-key escrow, restore remotely into an isolated database, or validate application/POS invariants. Do not publish RPO/RTO or mark a site DR-ready until those separate acceptance tests pass.

## Explicitly out of scope

- Provider/account selection, region/data residency and billing.
- Provisioning REST server/object storage or append-only ACLs.
- Credential creation/rotation/revocation and recovery-key escrow.
- Remote retention/prune and local artifact cleanup.
- Scheduling, fleet-wide jitter/backoff and monitoring integration.
- Remote restore/cutover and production execution.

All of these require separate review and approval. Failed uploads must leave local artifacts untouched.
