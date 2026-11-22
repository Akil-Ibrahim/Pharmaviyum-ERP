# Documentation Governance and Single Source of Truth

**Status:** Canonical documentation policy  
**Applies to:** Public Pharmaviyum repository, Demo documentation, Production deployment documentation and engineering evidence  
**Last reviewed:** 2026-11-22

## 1. Purpose

This document defines how project documentation is structured, verified, translated and maintained. It is the repository-wide policy for preventing conflicting architecture statements, stale instructions, unsupported readiness claims and broken references.

This policy does not override application configuration, source code, approved deployment profiles or measured operational evidence. When documentation conflicts with those sources, record the discrepancy and update the documentation from verified evidence.

## 2. Canonical environment boundary

| Concern | Public Demo | Production |
|---|---|---|
| Application hosting | FastAPI Cloud | Pharmacy server |
| Application release | Protected, manually dispatched Demo workflow | Reviewed Ansible playbooks and operator-approved release |
| Application stack | Pharmaviyum application stack | Same application technology stack, configured for the approved Pharmacy Edge profile |
| Data services | Isolated Demo PostgreSQL/pgvector and cache/worker dependencies | Pharmacy-server-local PostgreSQL and supporting services as defined by the approved Pharmacy Edge profile |
| Data | Synthetic only | Real pharmacy data only under private operational and compliance controls |
| Credentials | Demo-only FastAPI Cloud variables and protected Demo GitHub Environment secrets | Per-site secrets from Ansible Vault or an approved secret manager |
| Operational evidence | Demo deployment SHA, health/readiness and smoke checks | Site-specific rollout, runtime, backup/restore, security, health and rollback acceptance evidence |

FastAPI Cloud is Demo-only. It must never host or deploy the Production application, Production database, migrations or Production release workflow.

The public repository contains the Demo implementation, reusable Ansible roles/playbooks and general deployment procedures. The private Production implementation/source code, confidential business logic and Production release artifacts remain restricted under NDA and are not published here. Public Ansible playbooks describe the deployment automation contract; their presence does not mean the private Production application source or artifacts are included in this repository. The repository must not contain real Production host addresses, live inventory, SSH credentials, per-site secrets, private customer/patient data or approvals for executing changes against live pharmacies.

The existence of Ansible playbooks does not prove that a pharmacy server has been deployed or accepted. Do not claim Production rollout, fleet readiness, backup recovery or operational acceptance without current evidence for the exact site and release.

## 3. Source-of-truth hierarchy

When sources disagree, resolve them in this order:

1. **Runtime and repository facts:** current source code, dependency manifests and lockfiles, Docker/Compose files, Ansible roles/playbooks, CI workflows and automated tests.
2. **Approved environment configuration:** the canonical Demo profile and the approved Pharmacy Edge Production profile. Never infer Production settings from Demo provider metadata.
3. **Verified evidence:** exact-commit CI results, reproducible test artifacts, runtime version endpoint, health/readiness, controlled lab/pilot results, backup/restore drills and site acceptance records.
4. **Architecture decisions:** accepted ADRs and canonical architecture contracts. An ADR describes a decision; it does not prove implementation.
5. **Canonical requirements:** the Engineering Benchmark Requirements document and its Russian translation define business sizing assumptions and the engineering measurement contract.
6. **Operational and domain documentation:** runbooks, workflow traceability, security audits, AI/RAG standards and developer guides must align with the sources above.
7. **README, interview and presentation material:** summary documents must link to canonical references and must not introduce independent technical claims.

If the highest available source is ambiguous or unverified, mark the statement as an assumption or open question. Do not silently select the most convenient interpretation.

## 4. Evidence and maturity labels

- **Implemented:** the relevant source-code path exists at the inspected revision.
- **Unit verified:** the named unit tests passed on the exact commit.
- **Integration verified:** the relevant dependencies and persistence boundaries were exercised together.
- **End-to-end verified:** a representative user workflow reached and asserted its durable business outcome.
- **Operationally verified:** the exact workflow was exercised in a controlled staging/lab environment with relevant security, observability, recovery and rollback evidence.
- **Production verified:** the exact release was verified on the identified Production site under an approved procedure, with retained evidence.
- **Planned / target:** intended future behavior; not implemented or operationally proven.
- **Historical:** accurate only for the dated revision/environment stated in the record.
- **Not verified / unknown:** evidence is absent or insufficient.

A passing CI run proves only the checks that actually ran on that exact SHA. A source audit, diagram, ADR, mock, synthetic benchmark or successful HTTP response does not independently prove a complete business workflow or Production readiness.

## 5. Business sizing baseline

The canonical planning scenario is maintained in the Engineering Benchmark Requirements document and its Russian translation. It currently specifies:

- 100 pharmacies as a future design target, not proven fleet capacity;
- 200 daily visitors per pharmacy;
- 6 total employees per pharmacy, across all roles;
- 3 POS checkout stations per pharmacy;
- 1 additional dedicated computer in the manager's office per pharmacy;
- 14 public operating hours per day, 08:00–22:00 local pharmacy time;
- 4 physical workstation/computer positions per pharmacy (3 POS + 1 manager-office computer).

The three cashier workflows are included within the six employee positions. The manager-office computer adds equipment, not an employee or an automatically concurrent user. AI request volume and peak concurrency must be measured; they must not be inferred from visitor counts.

## 6. Documentation ownership and synchronization

- The English document is the canonical editorial source when a paired Russian translation exists, unless a document explicitly states otherwise.
- EN/RU pairs must have the same technical meaning, status, scope, assumptions, limitations, links and release gates. Translation must not add or omit claims.
- Update both language versions in the same change.
- Update indexes and inbound links whenever a document is added, moved, renamed or retired.
- Keep dated test reports historical. Do not rewrite historical environment facts to resemble the current baseline; add a clear superseded/current-context note instead.
- Do not copy provider-specific instructions from Demo into Production documentation.
- Keep root README and interview material concise; link to canonical technical documents instead of duplicating operational instructions.
- Every claim about an implemented capability must identify a code path or test/evidence reference where practical.
- Use absolute dates and exact commit SHAs for time-sensitive test and deployment evidence.

## 7. Links, commands and examples

- Prefer repository-relative links for files within this repository.
- Verify relative links against the target branch tree before completing a documentation change.
- External links must point to the canonical upstream/vendor or primary project source where possible.
- Commands must be safe for the stated environment. Label destructive, migration, restore, secret rotation and live deployment commands explicitly and require the appropriate approval.
- Examples must use placeholders or synthetic values. Never place real passwords, tokens, private endpoints, customer/patient data or unredacted logs in documentation.
- Public Demo credentials may be published only when explicitly approved by the repository owner. They must be clearly marked as Demo-only, isolated from Production, backed only by synthetic data and never reused in Production. Do not describe their privilege level unless it has been verified.

## 8. Required documentation review checklist

Before merging documentation changes, verify:

1. Demo and Production boundaries are consistent in every affected document.
2. Production deployment instructions point to Ansible and the pharmacy server.
3. FastAPI Cloud instructions are explicitly Demo-only.
4. Data-service and runtime versions match manifests/configuration or are clearly labelled as targets requiring runtime verification.
5. Historical records are visibly marked historical and do not masquerade as current configuration.
6. Business sizing matches the canonical benchmark.
7. EN/RU pairs agree.
8. All local links resolve; external links are checked where practical.
9. Secrets, private host data and patient information are absent.
10. Implementation and readiness claims match code, tests and evidence.
11. Indexes and cross-references are updated.
12. The final report states what was checked, what changed, what remains unknown and which exact commit was reviewed.

## 9. Canonical entry points

- [Repository overview](../README.md)
- [Documentation index](./README.md)
- [Production/Demo infrastructure baseline](./deployment/PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.md)
- [Pharmacy Edge Ansible rollout](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md)
- [Engineering benchmark requirements](./devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md)
- [Engineering requirements traceability](./devops/ENGINEERING_REQUIREMENTS_TRACEABILITY.md)
- [Pharmacy workflow traceability](./workflows/PHARMACY_WORKFLOW_TRACEABILITY.md)
- [Production operations runbook](./operations/PRODUCTION_OPERATIONS_RUNBOOK.md)
