## Production and Demo Infrastructure Baseline

This is the canonical deployment boundary for Pharmaviyum. It distinguishes the public demonstration environment from the pharmacy-server Production deployment. A documented target is not evidence of a completed deployment.

| Concern | Public Demo | Production |
|---|---|---|
| Application hosting | FastAPI Cloud | Pharmacy server / Pharmacy Edge, deployed and configured with Ansible |
| Application release | Manually approved GitHub Actions Demo workflow from `main` | Reviewed immutable application image/release deployed by the approved Ansible process |
| Application runtime | FastAPI API and React frontend | Same application technology stack, packaged for the pharmacy-server runtime |
| Data services | Dedicated isolated Demo PostgreSQL and required Demo cache/worker services | Local PostgreSQL and cache/worker services on the pharmacy server, as defined by the approved Compose/Ansible profile |
| Secrets | Demo-only FastAPI Cloud variables and protected GitHub Environment secrets | Per-site credentials from Ansible Vault or an approved secret manager; never committed to Git |
| Data | Synthetic demonstration data only | Pharmacy operational data, protected under the applicable security, privacy, backup and retention controls |
| AI profile | QwenCloud Demo profile where configured | Local Ollama profile is the documented target; hardware and model acceptance remain required |

## Deployment and isolation rules

- FastAPI Cloud is exclusively the public Demo host. No Production application, database, migration or release workflow may target FastAPI Cloud.
- Production application deployment is performed to the pharmacy server through Ansible. GitHub Actions may validate code, build and publish immutable artifacts, and test Ansible; it must not silently SSH to or deploy to a live pharmacy server.
- Demo and Production must have separate database instances, credentials, cache endpoints/namespaces, signing keys, API credentials and runtime configuration. Demo must never connect to a Production pharmacy server or Production data store.
- Demo is synthetic-data-only. Never place real patients, prescriptions, customers, pharmacy transactions or confidential business data in Demo.
- The pharmacy server is the local operational boundary for its pharmacy site. POS, inventory and other approved deterministic workflows must not require FastAPI Cloud or a WAN connection to complete local transactions.
- Ansible is the infrastructure configuration and release orchestration layer; it does not implement pharmacy business logic or synchronize business transactions.
- Production secrets and real inventory/host details must remain in protected operator-controlled inventory and secret-management systems. Public examples must use placeholders.
- Do not claim that Ansible production rollout is complete merely because playbooks, inventories or CI checks exist. Record lab/pilot execution, readiness, backup/restore, rollback and site acceptance evidence separately.
- Do not use retired Render infrastructure as an active dependency.

## Version and verification policy

Application and service versions must be pinned in the dependency lockfiles, container definitions and Ansible variables appropriate to each deployment profile. PostgreSQL, pgvector, Redis/Valkey, Python, Docker Engine and Compose versions must be verified against the actual runtime before they are described as deployed versions. A compatibility target is not an observed server version. **Current Ansible implementation gap:** the pharmacy-server Compose template still uses mutable image tags `pgvector/pgvector:pg16` and `valkey/valkey:8-alpine`; all runtime images must be changed to reviewed immutable digests and the exact versions recorded before live Production rollout.

**Additional build-reproducibility gap:** the application `Dockerfile` still references tag-based base images (`python:3.15.0-slim` and `oven/bun:1.4.4`) rather than immutable image digests. It also upgrades `pip`, `setuptools` and `wheel` without exact pins and installs OS packages from the moving apt repository state. The final GHCR application image is deployed by digest, which makes that published artifact immutable; it does not make a future rebuild byte-for-byte reproducible. Before claiming hermetic/reproducible builds, pin reviewed base-image digests, build-tool versions and OS package sources/versions, and record the resulting SBOM/provenance. CI service images and GitHub Actions references should be reviewed under the same supply-chain pinning policy.

PostgreSQL major-version changes require an approved backup, compatibility, migration, restore-test, maintenance-window and rollback plan. Never attach an existing data volume to a different PostgreSQL major version.

See the [FastAPI Cloud Demo runbook](FASTAPI_CLOUD.md), the [Pharmacy Edge Ansible rollout plan](../devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md), the [Ansible guide](../devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md), and the [Production operations runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.md).