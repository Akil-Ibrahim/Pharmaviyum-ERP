# ADR: Off-site encrypted backup architecture for Pharmacy Edge

- Status: Proposed
- Scope: 1-site lab and pilot, 2–3-site and 10-site rollout; design target up to 100 pharmacies.
- Authorization: design only. This document does not authorize provider provisioning, credential creation, backup transfer, retention deletion, restore, or deployment.

## Context

The local backup workflow creates a gzip-compressed PostgreSQL dump on Pharmacy Edge, verifies gzip integrity and SHA-256, writes a manifest, and prunes expired local artifacts only after a new backup is verified. A separate first implementation slice now exists in `ansible/playbooks/backup-offsite.yml` with operator instructions in `ansible/OFFSITE_BACKUP.md`: it uploads an already verified dump, checksum and manifest to a pre-existing site-scoped Restic REST repository. The playbook does not provision that repository or its server-side ACLs, and no live Production endpoint or credentials are established by the repository. The local restore drill remains separate and does not restore from the remote repository. These controls do not yet protect a site with an accepted end-to-end disaster-recovery capability.

## Proposed decision

Use **restic** as the encrypted snapshot/repository layer and an independently operated **append-only REST endpoint**, or an object-storage implementation with equivalent immutability and least-privilege guarantees. Keep the storage provider abstract until account ownership, region/data residency, pricing, limits, retention, and compliance requirements are approved.

### Target data flow

1. Edge creates and verifies the PostgreSQL dump using the existing local workflow.
2. Only a verified artifact is encrypted and uploaded over certificate-validated TLS.
3. Each pharmacy has a stable immutable `pharmacy_id` and its own repository boundary. Hostname is metadata, not site identity.
4. Edge receives a unique site-scoped append-only upload credential. It cannot delete/prune snapshots or access another site's repository.
5. A separate protected controller identity performs repository checks, retention/prune, and restore authorization. It is never installed on Edge.
6. Recovery keys are escrowed independently from both Edge and the backup repository. Key retrieval is tested.
7. The controller records site ID, snapshot ID, timestamp, bytes, verification result, and repository location in centralized monitoring; no secrets or patient data are logged.
8. Remote restore always targets a new isolated database/environment first. Live cutover is a separate approved change.

## Security requirements

- Encrypt before data leaves Edge. TLS is transport protection, not a substitute for backup encryption.
- Store credentials and recovery keys in an approved secret manager/controller vault; never commit, log, expose in process arguments, or place in world-readable files.
- Use unique per-site credentials and repository boundaries; no fleet-wide Edge upload key.
- Edge identity is append-only and least-privileged. Retention and restore authority are controller-only, audited, and approval-protected.
- Validate TLS certificates; do not use insecure TLS flags or plaintext transport.
- Enable storage-side encryption/versioning/immutability as defense in depth where supported.
- Document key escrow ownership, rotation, revocation, account recovery, and incident response.
- Keep metadata free of patient names, prescription contents, and unnecessary personal data.

## Reliability and retention requirements

- Accept a remote snapshot only after upload completion and an independent remote integrity/readability check. A successful upload process exit alone is insufficient.
- Failed remote upload must never trigger local backup deletion.
- Local cleanup is allowed only after a verified remote snapshot exists and a configured local safety window is preserved.
- Retention must be approved against legal/regulatory obligations and recovery objectives. Seven local days is not a remote retention policy.
- Protect against malicious deletion through append-only access, storage immutability/versioning where available, and separate retention credentials.
- Alert on missed windows, stale last-success, upload/integrity failures, capacity, credential expiry, and retention failures.
- Use bounded concurrency, per-site jitter and backoff; do not start synchronized fleet-wide uploads.

## Restore acceptance criteria

A restore is not accepted merely because SQL imports. An isolated drill must verify:
- remote snapshot discovery and retrieval using recovery credentials;
- repository integrity, snapshot identity, and pharmacy/site identity;
- restore into a new isolated database, never over the live DB;
- schema and expected Alembic revision;
- critical business invariants and representative row counts without exposing patient data;
- application startup/readiness against the isolated database;
- POS smoke test and sync/outbox consistency checks in a lab;
- measured restore duration and data-loss window.

Publish RPO/RTO only after repeatable timed drills. Backup frequency alone does not prove RPO/RTO.

## Ansible implementation contract

Keep the workflow split into independently testable units and track their implementation state:
- `backup_local`: implemented in `ansible/playbooks/backup.yml`; creates and verifies the local DB dump and metadata manifest.
- `backup_offsite`: initial upload slice implemented in `ansible/playbooks/backup-offsite.yml`; requires a pre-provisioned site-scoped Restic REST repository and protected per-site credentials, and verifies the remote snapshot metadata plus streamed artifact hashes. It has not been operationally validated against a live repository.
- `backup_maintenance`: not implemented; controller-only repository checks and retention/prune still require explicit environment/target guardrails.
- `restore_offsite_drill`: not implemented; the existing `ansible/playbooks/restore.yml` is a local isolated-database drill, not a remote restore.
- `backup_monitoring`: not implemented; last-success, age, bytes, snapshot ID, verification state and failure reason are not yet integrated into monitoring.

Roles must be idempotent where applicable, support meaningful check mode, use `no_log: true` for secret-bearing tasks, prefer `command.argv` to shell interpolation, and include Molecule coverage for success, retries, network outage, bad credentials, corrupt artifact, wrong site, retention failure, and partial restore cleanup.

## Rollout gates

| Stage | Evidence required |
|---|---|
| Lab, 1 site | Encrypted remote upload, remote verification, key escrow/retrieval, isolated remote restore, app readiness, measured RPO/RTO |
| Pilot, 1 pharmacy | Backup-window validation, WAN interruption/retry, credential rotation/revocation, runbook, alert delivery |
| 2–3 pharmacies | Site isolation, no cross-site restore, bounded concurrency, simultaneous-failure recovery |
| Up to 10 pharmacies | Fleet dashboard, capacity/cost model, retention controller, drill cadence, incident ownership |
| Design ceiling 100 | Capacity/rate-limit tests, per-site identity/credentials, controlled scheduling, centralized audit/monitoring, fleet DR exercise |

The 100-site ceiling is an architecture target, not evidence of current 100-site readiness. Active rollout remains separately capped.

## Decisions required before implementation

1. Approved storage provider and account owner.
2. Region/data residency and applicable privacy/regulatory requirements.
3. Expected DB size and daily change rate per pharmacy.
4. Approved RPO/RTO for each pharmacy and Central.
5. Retention schedule and legal-hold requirements.
6. Secret manager/controller and recovery-key escrow owner.
7. Managed append-only restic endpoint versus object storage with equivalent guarantees.
8. Monitoring destination and on-call/incident owner.

## Current safety boundary

This remains a proposed architecture and does not authorize Production disaster-recovery operations. The repository now contains an initial off-site upload implementation in `ansible/playbooks/backup-offsite.yml` (documented in `ansible/OFFSITE_BACKUP.md`). It uses Restic encryption, requires an existing site-scoped HTTPS repository and protected per-site credentials, validates local artifacts and site identity, then verifies the remote snapshot metadata and streams the uploaded artifacts back for SHA-256 comparison. `ansible/tests/test_offsite_backup_guardrails.sh` tests synthetic controller-side preflight/guardrail behavior only; it does not connect to a live Restic repository. Still outstanding are provider/repository provisioning and server-side ACL validation, recovery-key escrow, remote repository integrity checks and retention management, remote restore into an isolated database, application/POS business-invariant validation, monitoring, measured RPO/RTO and site acceptance. No Production endpoint, credentials, secrets or live pharmacy data are configured by this repository, and no Production DR readiness is established.
