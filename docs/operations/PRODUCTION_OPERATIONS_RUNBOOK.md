# Production Operations Runbook

**Status:** Operational baseline for the Ansible-managed pharmacy-server Production deployment. Verify host, inventory, secret source and service ownership before executing production actions.

## Operating principles
- Production is separate from local Compose, CI and test services.
- Green CI is not a deployment; a submitted deployment is not a successful deployment.
- Do not run schema migrations, data cleanup, cache flushes or checkpoint deletion as generic troubleshooting.
- Preserve deployment ID, commit SHA, timestamps, health results and redacted logs.
- Never place credentials, patient identifiers, prompts or clinical payloads in incident records.

## Service ownership map

| Component | Responsibility | Verification |
|---|---|---|
| Pharmacy server application stack (Ansible-managed) | API and frontend serving for the local pharmacy site | Ansible release result, immutable image digest, container state, logs, /health, /ready and authenticated pharmacy-safe smoke tests |
| PostgreSQL | Transactional and checkpoint persistence | Compose-managed local `db` container on the pharmacy server: container/readiness state, connections, query latency, backup age and restore evidence. The Ansible `postgresql` role is not a full database lifecycle/HA role |
| Redis-compatible service | Cache and dialogue memory | Compose service `redis` (default image Valkey 8): connectivity, memory/connection limits, evictions and latency |
| Celery worker | Async tasks such as ingestion | Compose service `celery-worker`: container/process health, queue depth, task age, retries and failed-task review; verify independently of API readiness |
| LLM / embedding provider | Optional AI inference and embeddings | Provider status, timeout/error rate, quota and latency |
| Telemetry backend | Traces, metrics and logs | Collector delivery, dashboards and alert delivery |

The current Ansible `app-backend` role starts `db`, `redis`, `backend`, `celery-worker` and `celery-beat` from the pharmacy-server Compose definition. Verify each service independently: `/ready` confirms API dependencies, not Celery worker health.

## Health-check sequence
1. Inspect deployment state and identify the deployed commit.
2. Request /health. This is a liveness signal, not proof that dependencies are usable.
3. Request /ready and investigate each component that is not ready.
4. Verify PostgreSQL and Redis connectivity through supported readiness checks.
5. Verify authentication and tenant-scoped read-only API behavior with a synthetic or approved test account.
6. Verify a low-risk pharmacy workflow in the approved smoke-test environment.
7. Verify Mortarium separately. An AI provider outage is not the same as core ERP unavailability.

Record timestamp, deployed SHA and redacted response. Never publish tokens or complete connection strings.

## Incident triage

### API unavailable
Check the Ansible rollout result, target host, container state, startup logs and recent changes. Distinguish process failure from dependency readiness failure. Stop the rollout if the new revision is unhealthy. Use the approved Ansible rollback procedure and the previous verified immutable image digest. Do not run a database downgrade or destructive cleanup as the first response.

### PostgreSQL unavailable
Check the local database service, pharmacy-server network policy, connection limits and application errors. Avoid restart loops and unbounded retries. Do not reset, recreate or restore the database without an approved incident owner and verified recovery point. Stop promotion if schema compatibility is uncertain.

### Redis unavailable
Determine whether cache, dialogue memory, queues or multiple responsibilities are affected. Preserve persistent business records; Redis is not the sales or inventory ledger. Never flush Redis globally as a first response. Identify key ownership and retention before targeted deletion.

### Celery backlog or ingestion failure
Inspect worker health, queue depth, oldest task age, retry counts and error classes. Verify broker/backend reachability and task idempotency before retry. Do not bulk replay tasks until duplicate-write and tenant-metadata behavior are understood.

### Mortarium / LLM degradation
Check provider availability, rate limits, latency, timeouts and RAG dependencies. Preserve core deterministic pharmacy workflows. Degrade optional AI through an approved configuration/release change if necessary. Do not present model output as verified clinical advice during degradation.

## Release and rollback
Production application releases target the pharmacy server and are orchestrated through the Ansible playbooks in this repository. The production inventory, per-site credentials, real host details and execution approvals remain operator-controlled and must not be committed. Use the [Pharmacy Edge Ansible rollout plan](../devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) and [Ansible guide](../devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md). The public [FastAPI Cloud Demo runbook](../deployment/FASTAPI_CLOUD.md) applies only to Demo and must never be used for Production.

Before release, verify CI and approval for the exact approved Production source commit and immutable image digest in the controlled Production release pipeline. Public Demo CI is not evidence that a Production artifact was built or validated. Also verify backup/restore evidence, the migration plan, environment variables, smoke tests and rollback target.

Rollback the application revision only when the previous revision is compatible with the current schema. Database rollback is a separate high-risk operation. Prefer backward-compatible expand/contract migrations. Restore from backup only under an approved recovery plan.

## Backup and restore
- `ansible/playbooks/backup.yml` creates and verifies a local PostgreSQL dump when invoked; it does not install or schedule itself. Verify that an approved protected automation controller or scheduler actually invokes it and supplies secrets securely. `backup_enabled: true` is not evidence that a schedule exists.
- Verify local retention and the documented isolated restore drill. Off-site upload is a separate explicitly approved invocation to a pre-provisioned, site-scoped Restic repository; it does not provision the repository/ACLs or prove restore from the remote copy. See the Off-site Backup Architecture; do not assume a cloud-provider PITR service exists.
- Define Redis and checkpoint retention separately.
- The local `backup.yml` artifact is gzip-compressed SQL, not encrypted by that playbook. File modes `0700`/`0600` restrict access but are not encryption; verify approved host/storage-level encryption and recovery-key handling for local backup retention.
- Protect Restic/repository encryption keys outside Git; Restic encryption protects the remote repository, not the plaintext source dump retained on the pharmacy server.
- Record backup age and retention.
- Perform restore drills on isolated infrastructure and verify application invariants.
- A successful backup job is not proof that a restore works.

See [Offsite Backup Architecture](../devops/OFFSITE_BACKUP_ARCHITECTURE.md) and [Production Engineering](./PRODUCTION_ENGINEERING.md).

## Incident/change record
Include incident/change ID, owner, affected service/environment, timestamps, impact, deployed SHA, redacted evidence, mitigation, data-integrity verification and follow-up owners.

## Explicit non-goals
This runbook does not authorize production migrations, patient-data deletion, Redis/checkpoint cleanup, secret changes, PostgreSQL/Redis/Valkey/Python upgrades, enabling unreviewed WebSockets or promoting the Edge fleet.
