# Pharmaviyum ERP/CRM — End-to-End Validation and Mortarium AI/RAG Testing

## Purpose

Act as a senior Python backend engineer, AI/RAG engineer, QA engineer, and performance engineer working directly in GitHub Codespaces.

Repository: **Akil-Ibrahim/Pharmaviyum-ERP-CRM**

Validate and improve the actual application, backend APIs, pharmacy workflows, international drug-reference search, Mortarium AI/RAG quality and security, and performance. Work with existing code and real reference sources where available. Do not produce a static mockup or a theoretical-only report.

## 1. Safety and execution rules

Before making changes:

1. Inspect the current branch, working tree, recent commits, repository instructions, project structure, pyproject.toml, API routes, database configuration, and existing tests.
2. Preserve all existing user changes. Never reset, clean, or overwrite unrelated work.
3. Do not merge pull requests, push to main, modify production infrastructure, or change Render configuration.
4. Never run load tests against production, Render, or a public endpoint.
5. Never print secrets, tokens, passwords, connection strings, or personal patient information.
6. Never fabricate test results, measurements, successful transactions, or data-source coverage.
7. Use actual APIs, models, schemas, and authorization rules. Do not invent endpoints or claim unsupported functionality works.
8. Prefer pyproject.toml and the existing uv workflow. Do not introduce requirements.txt.
9. In user-facing reports, do not add an unnecessary label describing the data as synthetic. Report actual sources, environment, scope, and operations tested. Never imply production operations were tested when they were not.
10. If a prerequisite is missing or an operation is unsafe, document the blocker and continue with independent tests.
11. Start read-only. Do not enable writes until the target database, credentials, fixtures, rollback, and cleanup safety have been verified.
12. Do not commit secrets, patient records, sensitive payloads, or raw tokens in artifacts.

## 2. Phase A — Establish the real baseline

Record:
- Git branch and commit SHA.
- Python version and dependency manager.
- Available services and required environment variables, without exposing their values.
- Database and vector-store availability.
- Existing migrations and test fixtures.
- API routes and authentication/authorization requirements.
- Current test and load-test harnesses.
- Whether the application starts successfully.

Run existing targeted checks before changing code. Record actual commands, exit codes, failures, and blockers. Do not claim a clean baseline unless confirmed.

## 3. Phase B — Validate the pharmacy API and application

Inspect and test actual implementations of:
- Authentication and role-based access control.
- Dashboard and operational summary.
- POS product search and drug-reference search.
- Patients and authorized patient-history access.
- Prescriptions and dispensing-related functionality.
- Inventory, batches, expiry dates, and stock availability.
- Suppliers, procurement, orders, and receiving.
- Transfers between pharmacies.
- ERP integrations, synchronization events, and task status.
- Audit trails and operational error handling.

For every entity, establish which operations really exist: list, search, retrieve, create, update, cancel, and delete. Check validation, response schemas, pagination, permissions, error handling, transaction boundaries, and database consistency. Distinguish implemented features from placeholders and unsupported workflows.

## 4. Phase C — International drug reference data

Inspect the existing drug-catalog importer, search implementation, database schema, and POS integration. Use accessible real reference sources where available, for example:
- RxNorm for normalized drug concepts and terminology.
- openFDA for available drug-label and regulatory information.
- An appropriate official European medicine-information source for European records, where access and licensing permit.

For each source, record its name, version or retrieval date when available, coverage, license/usage restrictions, and import status. Verify:
- Generic and brand-name searches.
- Active ingredients and combination products.
- Strength, dosage form, and concentration.
- Package descriptions where available.
- Duplicate handling and normalized matching.
- Import idempotency and error recovery.
- Search ranking and response latency.
- Source provenance and jurisdiction.

Do not assume that any one source has complete international or European coverage. A drug-reference result must not automatically become a sellable local product. Checkout must respect local product linkage, price, available stock, batch/expiry rules, and implemented dispensing safeguards. Do not silently assume a country or regulatory jurisdiction when none has been specified.

## 5. Phase D — Mortarium AI/RAG security and quality

Inspect and run relevant tests if present:
- tests/unit/ai/test_mortarium_rag_security_contracts.py
- tests/security/test_rag_tenant_isolation.py
- tests/unit/ai/test_mortarium_rag_patient_smoke.py
- tests/unit/ai/test_mortarium_rag_core_contracts.py
- tests/unit/ai/test_rag_quality_metrics.py
- tests/test_rag.py
- tests/test_evaluation.py

Start with:
    uv run pytest tests/unit/ai/test_mortarium_rag_security_contracts.py tests/security/test_rag_tenant_isolation.py -q

Adjust only if the repository structure requires it and report the actual command used.

Evaluate the actual retriever, filters, prompts, citation handling, evaluation harness, and available model providers. Cover:
1. Evidence-supported pharmacy procedure questions.
2. Drug information with identifiable source citations.
3. Inventory availability and expiry-risk questions where connected data supports them.
4. Authorized access to relevant patient history where implemented.
5. Missing evidence and questions the system cannot reliably answer.
6. Conflicting, outdated, or jurisdiction-dependent information.
7. Prompt injection embedded in retrieved documents.
8. Attempts to retrieve information from another pharmacy or tenant.
9. Attempts to access patient records without authorization.
10. MCP tool authorization and unsafe tool requests where MCP is implemented.
11. Unsupported dosage or treatment claims.
12. Invalid, missing, or irrelevant citations.

The AI must distinguish retrieved facts from inference, identify uncertainty, respect access controls, and leave clinical decisions to qualified healthcare professionals. Do not invent patient records, tools, endpoints, retrieval results, or citations and present them as real.

### RAG metrics

Use existing evaluation utilities and datasets where possible. Report available:
- Recall@k, Precision@k, MRR, and NDCG@k.
- Answer relevance and groundedness.
- Citation precision and coverage.
- Unsupported-claim and guardrail-failure counts.
- Cross-tenant leakage and unauthorized-access results.
- Retrieval, reranking, generation, and total latency.
- Token usage, provider errors, and cost where measurable.

Do not substitute mocked-model latency for live-model performance. Identify provider and execution mode for every measurement. Use scripts/evaluate_rag_retrieval.py if prerequisites are available and safe.

## 6. Phase E — Validate a complete pharmacy working day

Use actual workflow documentation and this article:
https://medium.com/@ibrahimengpy/ai-in-the-pharmacy-how-technology-can-support-the-pharmacist-a755ba3a2c9a

Validate against actual APIs and implemented functionality:
1. Opening preparation at 07:30 for an 08:00 opening.
2. Customer service, drug search, and POS preparation.
3. Prescription review and dispensing safeguards.
4. Inventory availability and expiry checks.
5. Supplier orders, delivery documentation, and goods receipt.
6. Online orders and customer follow-up.
7. Pharmacy-to-pharmacy stock availability and transfer workflows.
8. Operational reports and unresolved issues.
9. End-of-shift reconciliation, task handover, and auditability.
10. Mortarium AI support at appropriate points throughout the day.

Do not mark a workflow passed because individual pages or endpoints merely respond. Verify state transitions and consistency where supported. For missing capabilities, identify the exact API/model/workflow gap rather than creating a fake successful test.

## 7. Phase F — API performance testing in Codespaces

Inspect and reuse:
- scripts/run_stage1_load_test.sh
- tests/load/k6/stage1_baseline.js
- docs/devops/STAGE_1_LOAD_TESTING.md

Use only a verified local environment and a dedicated test database. Begin with low-concurrency, read-only smoke testing; increase gradually only when the initial run is healthy.

Current pharmacy operating assumptions:
- 200 customer visits per branch per day.
- Public opening hours 08:00–21:00.
- Preparation starts at 07:30.
- Three register workstations and one manager-office workstation per branch.
- Six staff in the operating team with mixed schedules; do not assume all six are concurrent.
- Future network may include 50 branches.

Start with a smoke test, then use four concurrent primary-workstation workflows as an initial proxy. Test six concurrent staff workflows only if actual schedule/workflow evidence supports it. A virtual user represents a workflow, not one visitor or automatically one physical computer.

Measure where available:
- p50, p90, p95, and p99 latency.
- Requests per second and transaction throughput as separate metrics.
- HTTP status distribution, error rate, timeouts, and failed checks.
- CPU and memory.
- PostgreSQL connections, query latency, locks, and pool saturation.
- Redis/Valkey latency, connections, and errors.

Do not turn daily visitor counts into assumed peak throughput without stating assumptions. Do not enable writes until the target database, authentication, cleanup, and rollback safety are verified.

The existing order API may not implement a complete sale with line items, payment capture, receipt, batch allocation, and stock decrement. Verify this in code. Never call order creation a completed POS transaction unless all relevant steps are implemented and verified.

## 8. Phase G — Validate multi-pharmacy synchronization

Inspect tenant model, pharmacy membership, stock ownership, synchronization events, idempotency, and integration handlers before a network test.

Validate:
- Pharmacy-local stock remains local.
- Network-wide visibility respects user permissions.
- A sale in one branch does not decrement another branch's stock.
- Replayed events do not duplicate transactions.
- Failed events can be retried safely.
- Event ordering and version conflicts are handled.
- Sync status, timestamps, and errors are observable.
- Data from one tenant cannot leak into another.

Do not simulate 50 branches by repeatedly sending requests to one pharmacy ID. First establish a small isolated scenario with genuine tenant separation, then scale only if the data model and environment support it.

## 9. Phase H — Combined ERP and Mortarium load

Only after individual API and RAG checks pass, run low-concurrency combined tests. Separate measurements for ERP API, drug-reference search, database operations, RAG retrieval, LLM generation, MCP/external tool execution, and end-to-end Mortarium response time.

Observe resource contention, timeouts, connection-pool pressure, provider rate limits, and error propagation. Avoid high-volume LLM calls and uncontrolled provider costs.

## 10. Phase I — Fix and retest

For each confirmed failure:
1. Identify root cause from code, logs, and test evidence.
2. Make the smallest safe fix on the current working branch.
3. Add or update a regression test.
4. Run targeted tests, then relevant broader checks.
5. Inspect the final diff for unrelated changes and leaked secrets.
6. Preserve existing user work.
7. Do not merge or push to main.

Do not modify Render, production data, or GitHub Actions configuration for this task.

## 11. Final evidence-based report

Report:
1. Branch and commit SHA.
2. Environment and actual reference sources used.
3. Commands executed and exit status.
4. Tests passed and failed.
5. API and end-to-end workflow coverage.
6. RAG metrics, measurement method, and execution mode.
7. API performance metrics including p50/p95/p99 and errors where measured.
8. Database and infrastructure observations.
9. Security and tenant-isolation findings.
10. Defects fixed and regression tests added.
11. Unsupported workflows and blockers.
12. Exact commands to reproduce checks.
13. What was verified and what remains unverified.

Never fabricate results to fill gaps or present historical reports as newly executed tests. If an external model, database, official source, or service is unavailable, record the limitation and continue with independent checks.

## Short Copilot invocation

When the user asks to run the Pharmaviyum validation prompt, read this file in full and execute its phases in order. Start with repository inspection and a safe baseline. Work on the current branch, preserve uncommitted changes, use actual repository contracts, and report evidence as you progress. Do not merely summarize this document. Do not merge, push to main, alter Render, or run tests against production.
