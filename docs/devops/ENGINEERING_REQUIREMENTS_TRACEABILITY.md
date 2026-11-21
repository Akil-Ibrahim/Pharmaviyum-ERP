# Engineering Requirements Traceability — Pharmaviyum

[English](./ENGINEERING_REQUIREMENTS_TRACEABILITY.md) · [Русский](./ENGINEERING_REQUIREMENTS_TRACEABILITY.ru.md)

**Status:** Initial repository-documentation traceability baseline  
**Baseline commit:** `1cf4c6afbc738df95986480d99340db0a76e9e8c` (`main`, 2026-11-21)  
**Primary requirements:** [Engineering Benchmark Requirements](./ENGINEERING_BENCHMARK_REQUIREMENTS.md)  
**Related workflow evidence:** [Pharmacy Workflow Traceability](../workflows/PHARMACY_WORKFLOW_TRACEABILITY.md)  
**Runtime / production verification:** Not performed by this document.

## 1. Purpose and evidence contract

This document connects engineering requirements to architecture decisions, implementation surfaces, automated tests and CI/operational evidence. It is a traceability index and gap register, not a certification of implementation or production readiness.

A requirement is **closed** only when all applicable links are present and current:

`Requirement → Architecture decision / control → Implementation → Automated test → CI artifact → Environment verification`

Evidence states:

- **DOCUMENTED:** described in a source document or ADR; implementation is not implied.
- **SOURCE-OBSERVED:** a source audit identified code or a test; execution and runtime behavior are not implied.
- **CI-PASS:** the named check passed on the exact commit under review.
- **RUNTIME-VERIFIED:** validated in the named non-production or production environment with reproducible evidence.
- **OPEN:** required implementation, test, decision or evidence is missing.
- **BLOCKED:** work cannot safely proceed until a dependency or release gate is resolved.

Do not promote a row to CI-PASS or RUNTIME-VERIFIED based on a historical run, another commit, a different environment or a documentation-only change. Every evidence reference must include a commit SHA, environment, command/check name and artifact or log location.

## 2. Cross-domain traceability matrix

| ID | Requirement domain | Architecture / decision anchor | Implementation and test evidence currently referenced | Evidence state | Gap / exit condition |
|---|---|---|---|---|---|
| AR-01 | Architecture vision, system context, bounded contexts and ownership | [Architecture vision](../architecture/pharmaviyum-architecture.en.md), [system context](../architecture/system-context.md), ADR index | Architecture documents and ADR-0001…0008 exist. This matrix has not independently verified every runtime dependency or ownership boundary. | DOCUMENTED | Add/verify C4 container and component views, context ownership matrix, dependency rules and automated architecture tests. Link each bounded context to owning module, schema and migration authority. |
| AR-02 | Architecture decisions and lifecycle | [ADR index](../adr/README.md) | ADR-0001…0008 have explicit Proposed/Accepted/partial implementation states. | DOCUMENTED | Ensure every material decision has alternatives, consequences, migration/rollback, security implications, owner and validation evidence. Never equate Accepted with Implemented. |
| IF-01 | Production/Demo isolation and data boundary | Production/Demo infrastructure baseline proposed in PR #388 (not yet merged into this branch) | Baseline defines separate DB credentials/branches, Redis endpoints, secrets and synthetic-only Demo data. Neon project metadata previously confirmed PostgreSQL major 18 for Production; Demo provisioning and live endpoint separation are not evidenced here. | DOCUMENTED / OPEN | Verify actual Production and Demo resource IDs, endpoints, credentials, network policy, secrets and synthetic-data controls without exposing secret values. Add automated negative tests proving cross-environment credentials and data cannot be reused. |
| IF-02 | PostgreSQL, pgvector and Redis compatibility | [Engineering benchmark](./ENGINEERING_BENCHMARK_REQUIREMENTS.md), [technology stack](../technology-stack.md) | Version targets are documented. Managed Redis server version and hosted pgvector extension version require runtime inspection. Legacy Compose is explicitly unsupported and retains PostgreSQL 16 / Redis 7 pins. | DOCUMENTED / OPEN | Capture `SHOW server_version`, `pg_extension` version for vector, Redis `INFO server` or provider equivalent, client versions and TLS/auth settings. Do not change persistent-volume major versions without a rehearsed migration. |
| IF-03 | Backup, restore, migration and disaster recovery | [Production operations runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.md), [release runbook](../operations/RELEASE_RUNBOOK.md) | Procedures are documented in operations material; this traceability review has no current restore-drill artifact or measured RPO/RTO. | DOCUMENTED / OPEN | Execute isolated backup/restore and migration rollback drills. Record data checks, duration, RPO/RTO, failure handling and artifacts. Production readiness requires approved objectives and a successful rehearsal. |
| SE-01 | RBAC, tenant isolation and authorization | [PHI governance audit](../architecture/PHI_ACCESS_GOVERNANCE_AUDIT.md), [PHI read-surface inventory](../security/PHI_READ_SURFACE_INVENTORY.md), ADR-0005 | Source audit records pharmacy-scope controls and regression tests, while also documenting global superuser paths and incomplete API/database-backed negative coverage. | SOURCE-OBSERVED / OPEN | Inventory every read/write path, enforce tenant predicates at query boundaries, define privileged support policy and run two-tenant API integration tests for allow/deny cases. |
| SE-02 | PHI access audit, minimization and telemetry privacy | PHI governance audit and PHI read-surface inventory | Governance requirements are documented. Dedicated append-only PHI access audit implementation, purpose-bound support access and complete response-field minimization are not established by the cited audit. | DOCUMENTED / OPEN | Implement durable allowed/denied access events, append-only DB controls, purpose/reason/expiry, DTO allowlists and redaction tests across logs, traces, metrics, MCP and background jobs. |
| AI-01 | LangGraph RAG retrieval and answer quality | [AI system design](../ai/AI_LLM_SYSTEM_DESIGN.md), [RAG architecture audit](../rag_architecture_audit.md), [Ragas evaluation](../ai/ragas-pharmaceutical-evaluation.md), ADR-0004 | Benchmark specifies Recall@K, Precision@K, MRR, nDCG, Ragas-supported answer/context metrics and custom citation/clinical metrics. Existing retrieval evaluator is identified in source requirements. | DOCUMENTED / SOURCE-OBSERVED | Verify pinned Ragas API/version, versioned golden dataset, expert labels, reproducible baseline, confidence intervals and CI regression thresholds. Ragas scores are not clinical ground truth. |
| AI-02 | Pharmacy-specific clinical safety | Engineering benchmark sections 4–5; AI safety/red-team documents | Required metrics include medication/ingredient/strength/dose/form/route accuracy, negation, interactions, contraindications, unsupported claims and escalation. Dataset coverage and expert adjudication are not proven by documentation alone. | DOCUMENTED / OPEN | Build pharmacist-reviewed synthetic golden set; define denominators and critical-error taxonomy; run adversarial, multilingual EN/RU, negation and citation-support tests. Clinical thresholds require qualified reviewer approval. |
| AI-03 | Agent Harness, LangGraph, MCP tool safety and patient context | ADR-0003; [Mortarium operations](../ai/mortarium-pharmacy-operations.md); [patient session isolation](../ai/patient-session-isolation.md) | Workflow audit identifies five read-only MCP tools and merged patient-scoped state code, with staged PostgreSQL checkpoint + Redis session-switch validation still open. | SOURCE-OBSERVED / OPEN | Test unauthorized tool calls, tool arguments, pharmacy/patient switching, stale checkpoint reuse, retries/loops, final business-state verification and staged persistence behavior. Tool success alone is not task success. |
| QE-01 | Backend/API, database and contract quality | [Testing guide](../guides/TESTING.md), benchmark requirements | Workflow audit references POS checkout, inventory-ledger and orders tests. This document does not independently execute those tests. | SOURCE-OBSERVED | Map each critical route/domain transition to unit, integration, contract and migration tests. Capture current commit CI artifacts and add missing failure/rollback/concurrency tests. |
| QE-02 | Frontend and pharmacy E2E workflows | [Pharmacy workflow traceability](../workflows/PHARMACY_WORKFLOW_TRACEABILITY.md) | The workflow audit reports several operational routes rendering `null`, including POS, patients, prescriptions, inventory, batches, suppliers, orders, transfers and procurement. POS backend tests do not prove usable checkout UI. | SOURCE-OBSERVED / OPEN | Restore P0 POS and pharmacist UI, link patient/prescription only after security controls, then Playwright-test complete browser journeys including stock/payment state. |
| QE-03 | Performance, load and capacity | Benchmark requirements; [DevOps roadmap](./README.md) | k6 entry point and suggested concurrency profiles are documented. No current staging capacity result is established here. | DOCUMENTED / OPEN | Execute read-only synthetic staging profiles; separately test ERP, transactional POS, search, RAG/AI and background jobs. Publish p50/p95/p99, errors, throughput, saturation and workload details. |
| OP-01 | OpenTelemetry, SLI/SLO, alerting and incident response | [OpenTelemetry guide](../observability/opentelemetry.md), [operations runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.md) | Instrumentation and target stack are documented; end-to-end trace coverage, alert delivery and MTTD/MTTR drills are not proven by this matrix. | DOCUMENTED / OPEN | Trace FastAPI→DB/Redis→Celery→LangGraph/RAG/MCP/model paths; verify propagation, redaction, collector delivery, alerts and incident exercises. Define SLOs from representative baselines. |
| OP-02 | Deployment, rollback and release control | [FastAPI Cloud runbook](../deployment/FASTAPI_CLOUD.md), [release runbook](../operations/RELEASE_RUNBOOK.md) | CI workflows and manual hosted deployment path are documented. A green CI run on a docs branch is not production deployment evidence. | DOCUMENTED / OPEN | Verify protected branch rules, required checks, artifact provenance, deployment approval, post-deploy smoke tests and rollback rehearsal on the current release path. |
| BV-01 | Business KPI evidence and NDA boundary | [Business value and KPI specification](../workflows/PHARMACY_BUSINESS_VALUE_AND_KPIS.md) | KPI framework separates Pharmacist, Pharmacy and Company outcomes; benchmark requires measured evidence. | DOCUMENTED | Bind each KPI to an event definition, source, denominator, cohort and measurement window. Do not publish NDA-covered financial metrics or claim impact without reproducible measurements. |

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
| Status | DOCUMENTED / SOURCE-OBSERVED / CI-PASS / RUNTIME-VERIFIED / OPEN / BLOCKED |
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
