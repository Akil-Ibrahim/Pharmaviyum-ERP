# ADR: Off-site encrypted backup architecture for Pharmacy Edge

- Status: Proposed
- Scope: Pharmacy Edge PostgreSQL backups for the 1-site lab, 1-site pilot, 2–3-site and 10-site rollout; design must remain operable at 100 sites.
- Applies to: Ansible backup/restore automation and the independent backup destination.
- Does not authorize: production credential creation, provider provisioning, live backup transfer, retention deletion, restore, or deployment.

## Context

The current Ansible backup playbook creates a gzip-compressed PostgreSQL dump on the Pharmacy Edge host, verifies gzip integrity and SHA-256, writes a manifest, and prunes expired local artifacts only after verification. PR #250 adds an isolated restore drill to a new local database. These controls improve local artifact integrity but do not protect against Edge disk failure, theft, ransomware, site fire, or loss of the whole pharmacy.

A local checksum is not an independent trust anchor if the host and its backup directory are compromised together. A local backup is not a disaster-recovery copy. The remote repository must have separate credentials, independent failure domains, and a tested restore path.

## Decision proposal

Adopt a provider-neutral off-site backup contract, with **restic** as the encrypted repository and snapshot layer and an independently operated **append-only REST endpoint** (or a compatible object-storage implementation with equivalent immutability controls) as the remote repository.

Do not bind the implementation to a provider until storage ownership, region, data residency, pricing, retention, service limits, and credentials are approved.

### Target data flow

1. PostgreSQL is dumped on Pharmacy Edge using the existing verified local backup process.
2. The Edge backup agent verifies the dump and manifest before upload.
3. The agent encrypts and uploads a snapshot to a remote repository over TLS. Encryption keys are generated and escrowed outside the Edge host; the Edge host must not be the only place holding the recovery key.
4. Each pharmacy has a stable immutable `pharmacy_id` and a separate repository namespace/repository. Hostname is metadata, not site identity.
5. Edge upload credentials are site-scoped and append-only. They must not be able to delete snapshots, run retention pruning, or access another pharmacy's repository.
6. A separate protected controller identity performs repository checks, retention/prune, and restore authorization. Its credentials are not installed on Pharmacy Edge.
7. The controller records backup completion, snapshot ID, site ID, timestamp, byte count, verification result, and repository location in centralized monitoring without logging secrets or patient data.
8. Restore retrieves the remote snapshot into an isolated database/environment first. Live cutover remains a separate, explicitly approved change.

## Security requirements

- Encrypt before data leaves the Edge host; TLS protects transport but does not replace at-rest encryption.
- Keep repository password/key material in the approved secret manager or controller vault. Never commit secrets, print them, pass them as command-line arguments, or persist them in world-readable environment files.
- Escrow recovery material independently from the backup repository and test that authorized operators can retrieve it. Losing the repository key makes the backup unrecoverable.
- Use unique credentials and repository boundaries per pharmacy. No shared fleet-wide Edge upload credential.
- Edge upload identity: minimum permissions, append-only, no delete/prune, no cross-site listing or reads.
- Retention identity: controller-only, audited, MFA/approval protected where supported. Retention must not run from a compromised Edge host.
- Enforce TLS certificate validation. Do not use insecure TLS flags or plaintext transport.
- Apply encryption at rest at the storage layer as defense in depth; document the actual provider and region.
- Protect manifests and metadata as operationally sensitive. Avoid patient names, prescription contents, or other unnecessary personal data in backup metadata and logs.
- Define repository lifecycle, account recovery, credential rotation, revocation, and incident response before production use.

## Reliability and retention requirements

- A remote snapshot is accepted only after upload completion and an independent remote integrity check; successful process exit alone is insufficient.
- Verify snapshot readability and metadata from the controller side.
- Retain multiple recovery points according to approved business, legal, and regulatory requirements. Seven local days is not a remote retention policy.
- Use a retention policy with daily/weekly/monthly tiers only after RPO/RTO, storage cost, and regulatory obligations are approved.
- Protect against accidental or malicious deletion using append-only permissions, object versioning/immutability where available, and a separate retention identity.
- Alert on missed backup windows, stale last-success timestamp, upload failures, integrity failures, repository capacity, credential expiry, and retention failures.
- A failed remote upload must not trigger local backup deletion. Local cleanup is allowed only after a verified remote snapshot exists and the configured local safety window is preserved.
- Avoid simultaneous fleet-wide uploads. Use controlled concurrency and per-site jitter/backoff so 10 sites do not overload the WAN or central endpoint.

## Restore and disaster-recovery acceptance

A restore is not accepted solely because the SQL dump imports.

The isolated restore drill must verify:
- remote snapshot can be discovered and fetched using the recovery identity;
- repository integrity and snapshot identity match the selected pharmacy;
- the database restores into a new isolated database, never over the live DB;
- schema and Alembic revision are present and expected;
- critical business invariants and representative row counts are checked without exposing patient data;
- application startup/readiness succeeds against the isolated database;
- a POS smoke test and sync/outbox consistency checks pass in a lab environment;
- restore duration and data-loss window are measured and recorded.

Document per-site and Central RPO/RTO only after repeatable timed drills. Do not advertise an RPO/RTO based on backup frequency alone.

## Ansible implementation contract

The future implementation should be split into independently testable roles/playbooks:

- `backup_local`: create and verify a local database dump; publish immutable local artifact and manifest.
- `backup_offsite`: upload only a verified artifact; use site-scoped append-only credentials; verify remote snapshot; never prune local data on upload failure.
- `backup_maintenance`: controller-only repository checks and retention/prune; require explicit environment/target guardrails.
- `restore_offsite_drill`: controller-authorized remote restore to an isolated target; verify site identity, repository, snapshot, checksum/integrity, schema, business invariants, and app readiness.
- `backup_monitoring`: export last-success, age, bytes, snapshot ID, verification status, and failure reason as metrics/events.

All roles must be idempotent where applicable, support safe check mode where meaningful, use `no_log: true` for secret-bearing tasks, avoid shell interpolation where `command.argv` is sufficient, and have Molecule tests for success, retries, credential failure, network outage, corrupt artifact, wrong site identity, retention failure, and partial restore cleanup.

## Rollout gates

| Stage | Required evidence before proceeding |
|---|---|
| Lab, 1 site | Encrypted remote upload, remote verification, key escrow/retrieval, isolated remote restore, application readiness, measured RPO/RTO |
| Pilot, 1 pharmacy | Realistic backup window, WAN interruption/retry, credential revocation/rotation, restore operator runbook, alert delivery |
| 2–3 pharmacies | Site isolation, independent repository access, bounded concurrency, no cross-site restore, tested recovery under simultaneous failures |
| Up to 10 pharmacies | Fleet dashboard, capacity/cost model, retention controller, restore drill cadence, incident procedures and operational ownership |
| Design ceiling 100 | Capacity and rate-limit tests, per-site identity and credentials, sharded/concurrent scheduling, centralized audit/monitoring, disaster-recovery exercise |

The declared architecture ceiling of 100 sites is a design target, not evidence that the current deployment is ready for 100 sites. Active rollout remains capped separately.

## Open decisions required before implementation

1. Approved storage provider and account owner.
2. Storage region/data residency and applicable privacy/regulatory requirements.
3. Expected database size and daily change rate per pharmacy.
4. Approved RPO/RTO for each pharmacy and Central.
5. Retention schedule and legal hold requirements.
6. Secret manager/controller and recovery-key escrow owner.
7. Whether the remote endpoint is a managed append-only restic service or an object store with equivalent least-privilege/immutability guarantees.
8. Monitoring destination and on-call/incident owner.

## Current status and safety boundary

This ADR is a design proposal only. PR #250 currently provides local backup verification and an isolated local restore drill; it does not implement off-site encryption, remote storage, remote verification, remote restore, or production DR. No provider, credentials, secrets, production hosts, or live pharmacy data are configured or changed by this document.
