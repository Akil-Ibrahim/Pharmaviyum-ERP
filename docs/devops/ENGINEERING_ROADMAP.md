# Engineering Roadmap and Delivery Stages

**Principle:** Advance by evidence and exit criteria, not by calendar labels or infrastructure ambition.

## Current delivery baseline
The repository is a FastAPI modular monolith with a React/TypeScript frontend, PostgreSQL-backed state, Redis-compatible cache/memory, Celery task infrastructure and Mortarium LangGraph AI/RAG. FastAPI Cloud is the hosted application path with a manually controlled release workflow.

Pharmacy Edge / Central is a staged target. The 100-pharmacy figure is a design target, not evidence of current production capacity. See [ADR-0002](../adr/ADR-0002-offline-first-central-edge.md).

## Stage 0 — Engineering foundation
**Goal:** Reproducible development and safe delivery.

Work: maintain pyproject.toml + uv.lock, frontend lockfile, lint/format/type/test/security CI, documented runtime compatibility and reviewed PR gates.

Exit: clean setup from docs, reproducible lock, required checks green on exact PR SHA, no implicit production deployment from ordinary PR validation.

## Stage 1 — Pharmacy workflow correctness
**Goal:** Prove critical business transactions before scaling.

Work: map actors, authorization, state transitions and audit effects; verify receiving, batch/expiry, inventory movements, FEFO, POS, payment, returns and transfers; test idempotency, concurrency, cancellation and reconciliation.

Exit: synthetic end-to-end scenarios, ledger/inventory invariants after success and failure, tenant/role tests, and no claims based only on list/read endpoints.

## Stage 2 — Capacity and performance baseline
**Goal:** Measure representative workload.

Work: execute [Stage 1 load testing](./STAGE_1_LOAD_TESTING.md); model browsing, search, authenticated reads/writes and AI separately; record RPS, concurrency, p50/p95/p99, errors, DB saturation, Redis latency, worker backlog and provider latency.

Exit: reproducible workload and baseline report, assumptions separated from measurements, bottlenecks documented and thresholds reviewed.

## Stage 3 — Observability and operational reliability
**Goal:** Diagnose failures across API, data services, workers and AI.

Work: validate W3C trace propagation, bounded spans, dashboards and alerts; define timeouts, bounded retries, backpressure and graceful shutdown; validate readiness and incident response.

Exit: traces for agreed workflows, alert delivery tested, runbooks map alerts to recovery actions, telemetry privacy review passed.

## Stage 4 — Data protection and recovery
**Goal:** Demonstrate recoverability.

Work: define RPO/RTO, configure PostgreSQL backup/PITR where supported, define Redis/checkpoint retention, perform isolated restore drills and review secret rotation/access control.

Exit: measured restore time and integrity checks, retention owners documented, recovery steps tested and patient-data lifecycle reviewed.

## Stage 5 — Mortarium AI quality and safety
**Goal:** Make AI quality measurable and isolate patient context.

Work: bind authenticated tenant/patient context across API, memory, cache and checkpoints; evaluate English/Russian retrieval; measure citation entailment, medication entity accuracy, negation and hallucination; run offline Ragas plus deterministic regressions; test prompt injection and unsafe tools.

Exit: zero cross-patient leakage in the defined suite, approved dataset and reviewer process, thresholds approved by qualified reviewers, versioned evidence and explicit human-review boundaries.

## Stage 6 — Pharmacy Edge pilot
**Goal:** Prove local operation and synchronization at a small controlled scope.

Work: validate Ansible on lab hardware; test local POS during WAN outage; test durable outbox/inbox, duplicate delivery, ordering and poison events; validate offline capability, backup/restore and staged upgrades.

Exit: lab/pilot acceptance, no duplicate business effects under replay, visible sync backlog/stale state, restore and rollback tested, rollout limit within approved scope.

## Stage 7 — Controlled multi-site expansion
**Goal:** Expand only when pilot evidence supports it.

Work: canary and wave rollout, Central ingestion/reporting capacity tests, site-failure isolation, central-outage tests and support/patching procedures.

Exit: capacity evidence for each expansion, no unresolved critical security/data-integrity findings, recovery objectives met and explicit approval to raise rollout limit.

## Delivery gates
A stage is complete only when code/configuration are reviewed, automated checks pass on the target commit, operational evidence is retained, security/privacy is reviewed, documentation is current and residual risks have an owner.

## Related plans and evidence
- [DevOps roadmap](./README.md)
- [Engineering benchmark requirements](./ENGINEERING_BENCHMARK_REQUIREMENTS.md)
- [Stage 1 load testing](./STAGE_1_LOAD_TESTING.md)
- [Stage 2 observability](./STAGE_2_OBSERVABILITY.md)
- [Pharmacy Edge rollout](./PHARMACY_EDGE_ANSIBLE_ROLLOUT.md)
- [Offline capability matrix](./PHARMACY_OFFLINE_CAPABILITY_MATRIX.md)
- [Production operations runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.md)
