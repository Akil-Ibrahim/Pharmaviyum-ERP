# Engineering Requirements Traceability — Pharmaviyum

[English](./ENGINEERING_REQUIREMENTS_TRACEABILITY.md) · [Русский](./ENGINEERING_REQUIREMENTS_TRACEABILITY.ru.md)

**Status:** Initial repository-documentation traceability baseline  
**Source baseline:** `4a8dda568a906c950456b146319d8590ddcdb1a2` (`main` at PR #402 creation)  
**Deployment-boundary documentation:** PR #402, Ansible pharmacy-server model; merge status must be checked separately.  
**Primary requirements:** [Engineering Benchmark Requirements](./ENGINEERING_BENCHMARK_REQUIREMENTS.md)  
**Related workflow evidence:** [Pharmacy Workflow Traceability](../workflows/PHARMACY_WORKFLOW_TRACEABILITY.md)  
**Runtime / production verification:** Not performed by this document.

## 1. Purpose and evidence contract

This document connects engineering requirements to architecture decisions, implementation surfaces, automated tests and CI/operational evidence. It is a traceability index and gap register, not a certification of implementation or production readiness.

A requirement is **closed** only when all applicable links are present and current:

`Requirement → Architecture decision / control → Implementation → Automated test → CI artifact → Environment verification`

## 1.1 Unified Operational Evidence Model

Pharmaviyum uses one maturity scale for every requirement and end-to-end workflow. The matrix records exactly one **highest currently proven level** per row. The level describes the strength of evidence, not the importance, completeness percentage or release approval.

| Level | Name | Minimum acceptance evidence |
|---|---|---|
| **L0** | Documented | Requirement, intended behavior, owner and objective exit condition are documented. No implementation is implied. |
| **L1** | Implemented | Relevant implementation is identified in source at a named commit; configuration and ownership are traceable. Source presence alone does not prove execution. |
| **L2** | Unit verified | Relevant unit tests pass on the exact commit; test command, run, results and artifact are recorded. |
| **L3** | Integration verified | Dependencies and persistence boundaries are exercised together (for example API + database + Redis); positive, negative and failure-path assertions pass on the exact commit. |
| **L4** | End-to-end workflow verified | A representative user journey is executed from entry point to durable business outcome. Required side effects, authorization, audit, idempotency and failure behavior are asserted, not merely HTTP success. |
| **L5** | Operationally verified | The workflow is validated in a controlled staging/pre-production environment with relevant observability, security, load, recovery, backup/restore and rollback evidence. Applicable controls must be exercised, not just documented. |
| **L6** | Production verified | The exact release is verified in the identified production environment using an approved, safe procedure; deployment identity, smoke/workflow results, telemetry and rollback readiness are recorded. No real patient data may be introduced for testing. |

### Rules for assigning a level

- Assign levels **per requirement and per critical workflow**, never as a blanket badge for the application. The application has no single maturity level.
- A workflow is capped at the lowest level of any mandatory step or control. Optional steps do not lower the level unless the requirement makes them mandatory.
- A higher level inherits all lower-level evidence; it cannot be awarded by a single passing test or screenshot.
- L1 requires source evidence. L2 requires exact-commit unit-test evidence. L3 requires integration evidence. L4 requires complete journey evidence and asserted durable outcomes. L5/L6 require environment-specific operational evidence.
- CI is a delivery mechanism for evidence, not a maturity level. A green pipeline does not automatically mean L2, L3 or L4: the relevant test scope and artifacts must be identified.
- A test passing against mocks cannot prove a real integration. A backend API test cannot prove a usable browser workflow. A successful tool call cannot prove that the intended pharmacy task completed.
- Production verification is not permission to perform unsafe clinical actions. Use synthetic test tenants and approved non-clinical transactions; production checks must be read-only or explicitly approved and controlled.
- If evidence is stale, belongs to another commit/environment, or cannot be reproduced, do not count it toward the current level. Record the gap and retain the last defensible level.
- **NOT TESTED**, **NOT AVAILABLE** and **BLOCKED** are gap/limitation annotations, not maturity levels. They never replace the single L0–L6 value.

For every level, retain the evidence provenance: exact commit SHA, test/check and command, run ID, environment and release/deployment ID where applicable, timestamp, immutable artifact/log/trace, reviewer/owner, limitations and next exit condition. Never promote a row based on a historical run, another SHA or another environment.



## 2. Cross-domain traceability matrix

| ID | Requirement domain | Architecture / decision anchor | Implementation and test evidence currently referenced | Evidence level | Gap / exit condition |
|---|---|---|---|---|---|
| AR-01 | Architecture vision, system context, bounded contexts and ownership | [Architecture vision](../architecture/pharmaviyum-architecture.en.md), [system context](../architecture/system-context.md), ADR index | Architecture documents and ADR-0001…0008 exist. This matrix has not independently verified every runtime dependency or ownership boundary. | L0 — Documented | Add/verify C4 container and component views, context ownership matrix, dependency rules and automated architecture tests. Link each bounded context to owning module, schema and migration authority. |
| AR-02 | Architecture decisions and lifecycle | [ADR index](../adr/README.md) | ADR-0001…0008 have explicit Proposed/Accepted/partial implementation states. | L0 — Documented | Ensure every material decision has alternatives, consequences, migration/rollback, security implications, owner and validation evidence. Never equate Accepted with Implemented. |
| IF-01 | Production/Demo isolation and data boundary | [Canonical Production/Demo infrastructure baseline](../deployment/PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.md); deployment-boundary documentation updated in PR #402 | The canonical model is FastAPI Cloud for isolated synthetic Demo only and Ansible deployment of the same application stack to the pharmacy server for Production. Production uses local PostgreSQL and supporting services defined by the approved Pharmacy Edge profile. Real host inventory, per-site credentials and site approvals remain protected. Actual site provisioning and live endpoint separation require site-level evidence. | L0 — Documented | Verify actual Production and Demo resource IDs, endpoints, credentials, network policy, secrets and synthetic-data controls without exposing secret values. Add automated negative tests proving cross-environment credentials and data cannot be reused. |
| IF-02 | PostgreSQL, pgvector and Redis compatibility | [Engineering benchmark](./ENGINEERING_BENCHMARK_REQUIREMENTS.md), [technology stack](../technology-stack.md) | Application dependency versions are controlled by manifests and lockfiles. Production PostgreSQL, pgvector and cache/broker service versions must be inspected on the pharmacy server against the approved Pharmacy Edge profile; Demo service metadata is not evidence of Production versions. The legacy docker-compose.prod.yml retains PostgreSQL 16 / Redis 7 and is not an approved deployment path. | L0 — Documented | Capture `SHOW server_version`, `pg_extension` version for vector, Redis `INFO server` or provider equivalent, client versions and TLS/auth settings. Do not change persistent-volume major versions without a rehearsed migration. |
| IF-03 | Backup, restore, migration and disaster recovery | [Production operations runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.md), [release runbook](../operations/RELEASE_RUNBOOK.md) | Procedures are documented in operations material; this traceability review has no current restore-drill artifact or measured RPO/RTO. | L0 — Documented | Execute isolated backup/restore and migration rollback drills. Record data checks, duration, RPO/RTO, failure handling and artifacts. Production readiness requires approved objectives and a successful rehearsal. |
| SE-01 | RBAC, tenant isolation and authorization | [PHI governance audit](../architecture/PHI_ACCESS_GOVERNANCE_AUDIT.md), [PHI read-surface inventory](../security/PHI_READ_SURFACE_INVENTORY.md), [PHI route-to-test map](../security/PHI_ROUTE_TO_TEST_TRACEABILITY.md), ADR-0005 | Source audit records pharmacy-scope controls and regression tests, while also documenting global superuser paths and incomplete API/database-backed negative coverage. | L1 — Implemented (source observed) | Inventory every read/write path, enforce tenant predicates at query boundaries, define privileged support policy and run two-tenant API integration tests for allow/deny cases. |
| SE-02 | PHI access audit, minimization and telemetry privacy | PHI governance audit, PHI read-surface inventory and route-to-test map | Partial implementation now exists: `PHIAccessAudit` triggers, audited AI-profile and pharmacist patient-history routes, explicit purpose/pharmacy membership checks, and minimum-field response contracts. However, Compose reuses the PostgreSQL bootstrap `POSTGRES_USER` as runtime `DATABASE_URL`, so the application role may bypass trigger-only immutability. MCP `get_patient_history` is pharmacy-scoped but lacks selected-patient/purpose binding and PHI audit. Legacy admin purchase listing and general patient/order superuser paths also remain broader. Complete route coverage, least-privilege DB roles, support-access policy and telemetry redaction proof remain open. | L1 — Implemented (source observed) | Extend audit and purpose controls to remaining PHI read surfaces; test audit-persistence failure; govern global superuser access; verify DTO allowlists and redaction across logs, traces, metrics, MCP and background jobs. Do not promote beyond L1 without exact-commit test artifacts and broader database-backed coverage. |
| AI-01 | LangGraph RAG retrieval and answer quality | [AI system design](../ai/AI_LLM_SYSTEM_DESIGN.md), [RAG architecture audit](../rag_architecture_audit.md), [Ragas evaluation](../ai/ragas-pharmaceutical-evaluation.md), ADR-0004 | Benchmark specifies Recall@K, Precision@K, MRR, nDCG, Ragas-supported answer/context metrics and custom citation/clinical metrics. Existing retrieval evaluator is identified in source requirements. | L1 — Implemented (source observed) | Verify pinned Ragas API/version, versioned golden dataset, expert labels, reproducible baseline, confidence intervals and CI regression thresholds. Ragas scores are not clinical ground truth. |
| AI-02 | Pharmacy-specific clinical safety | Engineering benchmark sections 4–5; AI safety/red-team documents | Required metrics include medication/ingredient/strength/dose/form/route accuracy, negation, interactions, contraindications, unsupported claims and escalation. Dataset coverage and expert adjudication are not proven by documentation alone. | L0 — Documented | Build pharmacist-reviewed synthetic golden set; define denominators and critical-error taxonomy; run adversarial, multilingual EN/RU, negation and citation-support tests. Clinical thresholds require qualified reviewer approval. |
| AI-03 | Agent Harness, LangGraph, MCP tool safety and patient context | ADR-0003; [Mortarium operations](../ai/mortarium-pharmacy-operations.md); [patient session isolation](../ai/patient-session-isolation.md) | Workflow audit identifies five read-only MCP tools and merged patient-scoped state code, with staged PostgreSQL checkpoint + Redis session-switch validation still open. MCP `get_patient_history` is not bound to the selected patient/purpose and does not emit PHI audit; it can query any active patient in the same pharmacy. This is a separate open security gate. | L1 — Implemented (source observed) | Test unauthorized tool calls, tool arguments, pharmacy/patient switching, stale checkpoint reuse, retries/loops, final business-state verification and staged persistence behavior. Tool success alone is not task success. |
| QE-01 | Backend/API, database and contract quality | [Testing guide](../guides/TESTING.md), benchmark requirements | Workflow audit references POS checkout, inventory-ledger and orders tests. This document does not independently execute those tests. | L1 — Implemented (source observed) | Map each critical route/domain transition to unit, integration, contract and migration tests. Capture current commit CI artifacts and add missing failure/rollback/concurrency tests. |
| QE-02 | Frontend and pharmacy E2E workflows | [Pharmacy workflow traceability](../workflows/PHARMACY_WORKFLOW_TRACEABILITY.md) | The workflow audit reports several operational routes rendering `null`, including POS, patients, prescriptions, inventory, batches, suppliers, orders, transfers and procurement. POS backend tests do not prove usable checkout UI. | L1 — Implemented (source observed) | Restore P0 POS and pharmacist UI, link patient/prescription only after security controls, then Playwright-test complete browser journeys including stock/payment state. |
| QE-03 | Performance, load and capacity | [Engineering benchmark](./ENGINEERING_BENCHMARK_REQUIREMENTS.md); [capacity workload model](../performance/CAPACITY_WORKLOAD_MODEL.md); [DevOps roadmap](./README.md) | Canonical sizing: 100 pharmacies, 6 employees/pharmacy (600 total), 3 POS stations/pharmacy (300 total), 1 dedicated manager-office computer/pharmacy (100 total; 400 workstation/computer positions overall), 14 public operating hours/day (08:00–22:00 local time), 200 visits/pharmacy/day (20,000 total/day). Existing k6 entry point and stress profiles are documented; no representative staging capacity result is established. | L0 — Documented | Approve arrival/peak distribution, role split, shift overlap, visit-to-sale conversion, basket/workflow mix, register utilization, AI demand and infrastructure limits. Then execute staged 1→10→25→50→100 tenant tests, 3 concurrent cashier journeys/pharmacy and a separately labelled 300-register upper-bound profile. Retain exact-SHA reports and saturation evidence; do not infer RPS/VUs from daily visits. |
| OP-01 | OpenTelemetry, SLI/SLO, alerting and incident response | [OpenTelemetry guide](../observability/opentelemetry.md), [operations runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.md) | Instrumentation and target stack are documented; end-to-end trace coverage, alert delivery and MTTD/MTTR drills are not proven by this matrix. | L0 — Documented | Trace FastAPI→DB/Redis→Celery→LangGraph/RAG/MCP/model paths; verify propagation, redaction, collector delivery, alerts and incident exercises. Define SLOs from representative baselines. |
| OP-02 | Deployment, rollback and release control | [FastAPI Cloud runbook](../deployment/FASTAPI_CLOUD.md), [release runbook](../operations/RELEASE_RUNBOOK.md) | CI validates the repository. The manually triggered FastAPI Cloud workflow deploys Demo only. Production application releases use reviewed Ansible playbooks and operator-approved pharmacy-server execution. A green CI run or documentation PR is not Production deployment evidence. | L0 — Documented | Verify protected branch rules, required checks, artifact provenance, deployment approval, post-deploy smoke tests and rollback rehearsal on the current release path. |
| BV-01 | Business KPI evidence and NDA boundary | [Business value and KPI specification](../workflows/PHARMACY_BUSINESS_VALUE_AND_KPIS.md) | KPI framework separates Pharmacist, Pharmacy and Company outcomes; benchmark requires measured evidence. | L0 — Documented | Bind each KPI to an event definition, source, denominator, cohort and measurement window. Do not publish NDA-covered financial metrics or claim impact without reproducible measurements. |


## 2.1 Focused PHI source review — 2026-11-21 (historical snapshot)

A read-only review of the current `main` source was performed against the PHI governance and read-surface audits (audit baseline recorded as `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`). This is source evidence only; no database, production runtime, or patient data was accessed.

Confirmed implementation and evidence limits:

- `GET /api/v1/patients/{patient_id}`, phone lookup and list routes resolve a pharmacy scope for ordinary users. `resolve_pharmacy_scope` permits a superuser to omit `pharmacy_id`, which intentionally results in a global scope. The unit test `tests/unit/modules/auth/test_tenant.py::test_superuser_can_use_global_scope` explicitly preserves that behavior.
- Patient create/update/delete routes are superuser-only. The create route accepts an optional `pharmacy_id`; when a superuser omits it, the service can create a patient with nullable `Patient.pharmacy_id`. This is a source-observed unowned-record path, not proof that such records exist in Production.
- `PatientResponse` includes conditions and treatment notes, allergies, insurance policy number, consultations and purchase history. The detail and phone-lookup routes return this broad DTO. Purpose-specific response-field minimization is therefore not demonstrated by these paths.
- `GET /patient-purchases/` requires a superuser and explicit `pharmacy_id`, joins `Patient`, and filters by `Patient.pharmacy_id`. Its current regression tests compile the SQL using mocks; they do not prove two-tenant isolation against persisted database rows.
- `AuditLog` is a generic mutation-oriented model. The inspected patient read handlers do not emit a dedicated allowed/denied PHI access event. No append-only database enforcement was established by this source review.

Relevant source/test anchors: `src/pharmaviyum/api/v1/endpoints/patients.py`, `src/pharmaviyum/modules/auth/tenant.py`, `src/pharmaviyum/services/patient.py`, `src/pharmaviyum/models/patients/patient.py`, `src/pharmaviyum/schemas/patient.py`, `src/pharmaviyum/models/audit_log.py`, `src/pharmaviyum/api/v1/patient_purchases.py`, `tests/unit/modules/auth/test_tenant.py`, `tests/unit/test_patient_purchases_scope.py`.

**Evidence assignment:** SE-01 remains **L1** (tenant-aware source controls exist, but global privileged scope and database-backed two-tenant negative proof remain open). SE-02 remains **L0** for the dedicated PHI access-audit/minimization requirement: a generic audit model exists, but the required PHI access contract and enforcement are not demonstrated. Do not promote either row based on this source review alone.

Next exit conditions: require an explicit, governed pharmacy context for patient creation; introduce purpose-specific patient DTOs; define a time-bounded, reason-coded privileged-support policy; add durable allowed/denied PHI access auditing with append-only enforcement; and execute two-tenant integration tests with synthetic fixtures, including null-owner denial and audit-failure behavior.

## 2.2 Follow-up PHI source review — 2026-11-22

This section supersedes the implementation-status statements in the historical 2026-11-21 snapshot above. It is a source/test inspection of current `main` at `2616b4209fc037b1e4f1899b876478bf72258641`; no Production runtime, database, or patient data was accessed.

- Standard patient list/detail/phone/visit responses now use `PatientSummaryResponse`; the inspected standard contract excludes conditions, allergies, insurance, consultations and purchase history. The legacy broad `PatientResponse` remains in the codebase but is not the current standard route response.
- `GET /api/v1/patients/{patient_id}/ai-profile` requires explicit `pharmacy_id` and a bounded purpose code, denies platform superusers, requires active `PharmacyMembership`, verifies active patient ownership, and writes metadata-only allowed/denied `PHIAccessAudit` records. `tests/integration/test_ai_patient_profile_access.py` covers allowed access, missing membership, cross-pharmacy denial and superuser denial.
- `GET /api/v1/patient-purchases/{patient_id}/history` is the pharmacist-facing history route. It requires explicit pharmacy and purpose, active membership and active patient ownership; it denies superusers and unassigned legacy patients; it returns a minimum-field projection and records allowed/denied audit decisions. `tests/integration/test_patient_history_tenant_scope.py` covers allowed access, cross-pharmacy denial, missing membership, null-owner denial and superuser denial.
- The legacy `GET /patient-purchases/` remains superuser-only and requires an explicit `pharmacy_id`; the query now joins `Patient` and filters by `Patient.pharmacy_id`. It still returns a broader administrative purchase projection and does not emit the new PHI access audit event.
- `PHIAccessAudit` has database triggers against UPDATE, DELETE and TRUNCATE, and `tests/integration/test_phi_access_audit_immutability.py` exercises them. However, Ansible Compose uses the same bootstrap `POSTGRES_USER` for backend/worker/beat `DATABASE_URL`; the repository does not provision a separate non-superuser runtime role. Trigger-only immutability is therefore not proven against the actual application credential.
- MCP `get_patient_history` receives trusted user/pharmacy/role context, but not the selected patient or purpose. Its schema accepts a model-supplied patient ID, it can read any active patient within that pharmacy, returns a broad clinical/demographic summary, and does not write `PHIAccessAudit`. This remains a patient-context isolation and audit gap.
- `Patient.pharmacy_id` remains nullable and superuser-only patient creation still accepts an omitted pharmacy ID; the unowned-record creation path remains a blocker. General patient/order routes also retain global superuser scope. Purpose-bound platform support access, complete read-surface auditing, audit-failure injection tests and end-to-end telemetry redaction remain incomplete.

**Evidence level remains L1.** The route-specific integration tests exist in source, but this review does not promote the entire PHI surface to L2/L3: exact-current-commit CI evidence and coverage for all patient/order/admin/MCP/export/background-job reads are still required.

## 3. Priority release blockers

The following are not documentation polish; they require implementation and evidence before the affected workflows can be called production-ready:

1. **P0 — Patient/PHI access governance:** complete read-surface inventory, query-boundary tenant isolation, purpose-bound privileged access, durable PHI access audit, field minimization and negative two-tenant tests.
2. **P0 — Operational pharmacist UI:** POS and core pharmacist workflows must be usable in the browser; backend endpoints and navigation placeholders are insufficient.
3. **P0 — Patient/prescription-linked dispensing:** define authorization, validation, pharmacist review, audit and transactional linkage before enabling clinical dispensing workflows.
4. **P0 — Patient-scoped AI state:** complete staged persistence/session-switch validation across PostgreSQL checkpoints and Redis-backed memory.
5. **P1 — Recovery proof:** backup/restore, migration rollback and recovery objectives must be exercised in isolated staging.
6. **P1 — AI evaluation proof:** versioned expert-reviewed dataset, citation correctness, medication entity/negation checks and regression gates.
7. **P1 — Operational proof:** telemetry privacy, end-to-end trace coverage, alert delivery, SLOs and rollback exercises.
8. **P1 — Capacity proof:** representative synthetic staging workloads with measured limits; planning assumptions must not be presented as capacity results.

## 4. Required evidence record

For every requirement, maintain a linked evidence record with:

| Field | Required value |
|---|---|
| Requirement ID | Stable ID from this matrix |
| Owner | Named engineering role/team |
| ADR / control | ADR ID or explicit policy reference |
| Implementation | File/module/API/schema and commit |
| Test | Test file, case ID and exact command |
| CI | Workflow, run ID, conclusion and tested SHA |
| Runtime | Environment, deployment/release ID and timestamp |
| Artifact | Immutable report/log/trace reference |
| Maturity level | One value: L0–L6, with evidence link(s) |
| Limitations | Mocks, synthetic data, missing service or untested path |
| Exit condition | Objective condition required to close the row |

## 5. Governance rules

- The benchmark requirements document remains the canonical measurement contract; this matrix links it to architecture and implementation evidence.
- The pharmacy workflow matrix remains the canonical operational-process audit; do not duplicate its detailed workflow descriptions here.
- ADR status is not implementation status.
- CI is commit-specific. A pass on a previous SHA must not be copied to a newer SHA.
- Production verification requires explicit environment evidence; repository source review and Codespaces are insufficient.
- A missing measurement is NOT TESTED or UNAVAILABLE, never zero or PASS.
- Do not use real patient data in benchmark, Demo or evaluation datasets.
- Keep financial outcomes covered by NDA out of public documentation and CV claims.

## 6. Immediate next actions

1. Re-audit the current main source against the existing PHI read-surface inventory and close or update each finding with code-level evidence.
2. Produce a route-to-test map for P0 patient, prescription and POS workflows.
3. Verify current runtime versions and Production/Demo separation using read-only provider/database inspection.
4. Run the benchmark suite in isolated staging and publish a versioned report.
5. Add a release evidence checklist that links each blocking row to the exact CI and runtime artifacts.

**Current conclusion:** Pharmaviyum has a substantial documented engineering framework and several source-observed backend controls. The matrix deliberately keeps infrastructure, PHI governance, pharmacist UI, staged AI isolation, recovery, observability and capacity evidence open until current, reproducible artifacts are attached. This is not a production-readiness declaration.
