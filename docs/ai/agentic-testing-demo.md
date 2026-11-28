# Agentic testing demo

## Product positioning

**Pharmaviyum Agentic QA** is an AI-powered QA Engineering Assistant and Agentic
Testing Platform. Its purpose is to help QA Engineers plan, execute, investigate,
and evaluate software tests. It augments QA engineering work; it does not replace
the QA Engineer or independently own release decisions.

The product has three complementary operating modes:

### 1. QA Copilot

An assistive mode in which the QA Engineer remains in control. Planned capabilities:

- Analyze requirements, user stories, acceptance criteria, and change descriptions.
- Identify ambiguities, missing acceptance criteria, risks, and affected areas.
- Draft structured test scenarios and test cases for human review.
- Suggest positive, negative, boundary, equivalence-partition, and risk-based cases.
- Help maintain traceability from requirement to scenario, execution, and finding.

### 2. Agentic Testing

A bounded execution mode in which an orchestrator coordinates validated test plans
and approved tools. Planned capabilities:

- Run approved UI and end-to-end scenarios through Playwright.
- Add API checks through explicitly registered, schema-validated tools.
- Support smoke, functional, regression, and negative test suites.
- Capture reproducible evidence: screenshots, traces, logs, request failures,
  step outcomes, and environment metadata.
- Retry only according to explicit policy; preserve the original failure and retry
  history rather than hiding flaky behavior.

The current implementation is only the deterministic LangGraph planning foundation
and the initial Playwright access-control E2E scenario. It does not yet generate
scenarios with an LLM or execute the backend-generated plan in a browser.

### 3. QA Intelligence

An analysis mode that helps QA Engineers interpret test outcomes and prioritize
follow-up work. Planned capabilities:

- Cluster related failures and identify likely duplicate defects.
- Suggest severity, impact, confidence, and reproduction steps with supporting evidence.
- Report coverage, requirement-to-test traceability, flaky-test trends, and
  reproducibility.
- Evaluate agent findings against deterministic test outcomes and known expected
  results.
- Present uncertain findings for human review instead of converting uncertainty
  into a definitive bug report.

## QA engineering workflow

The intended end-to-end workflow is:

1. **Requirement intake:** a QA Engineer supplies a requirement or change request.
2. **Risk analysis:** the assistant identifies affected workflows, assumptions,
   missing acceptance criteria, and risk areas.
3. **Scenario design:** candidate test cases are generated in a structured,
   validated format and reviewed by a human.
4. **Execution planning:** LangGraph validates the scenario, target origin,
   action allowlist, and execution limits.
5. **Test execution:** Playwright or another explicitly registered adapter executes
   the approved plan in an isolated test environment.
6. **Evidence collection:** each run produces correlated, bounded, machine-readable
   evidence and human-readable reproduction details.
7. **Result evaluation:** deterministic assertions determine pass/fail; AI may
   summarize evidence and propose findings but cannot override test assertions.
8. **Human review:** the QA Engineer confirms, rejects, edits, or escalates findings
   and decides whether results are sufficient for release.

## Test disciplines in the product roadmap

The platform is designed to assist with the following QA disciplines. These are
product goals, not claims that every capability is implemented today:

- Functional and regression testing.
- Smoke and sanity testing.
- UI and end-to-end testing.
- API and integration testing.
- Negative and error-handling testing.
- Boundary Value Analysis and Equivalence Partitioning.
- Risk-based testing and exploratory-test assistance.
- Accessibility and cross-browser checks as separately scoped capabilities.

## Verdict ownership and quality principles

- Deterministic assertions and observed execution evidence are authoritative for
  automated pass/fail status.
- An LLM-generated explanation, confidence score, or proposed bug is advisory.
- A test may be marked **blocked**, **inconclusive**, or **needs review**; do not
  force every run into pass/fail when evidence is insufficient.
- Preserve flaky retries and distinguish a first-attempt failure from a later pass.
- Findings must include evidence links or artifact references and a reproducible
  sequence where possible.
- The QA Engineer retains ownership of test acceptance, defect confirmation,
  severity approval, and release recommendations.
- Keep requirement, scenario, run, step, evidence, finding, and review identifiers
  linked for auditability.

## Product status language

Documentation, UI, and interview materials must distinguish three states:

- **Implemented:** present in the repository and covered by relevant tests.
- **In progress:** actively being built on a feature branch but not yet validated
  as complete.
- **Planned:** part of the target architecture or roadmap, not yet implemented.

Do not describe planned LLM scenario generation, browser-plan execution, API testing,
AI bug triage, or QA Intelligence as available until their implementations and tests
exist.

## Purpose

Build a reviewable demonstration of an AI-assisted browser-testing system on top of
Pharmaviyum's existing Playwright E2E suite. The demonstration is intended for
engineering interviews; it is not a production monitoring service and must not
interact with the private Production environment.

## Verified starting point

- The active frontend is `frontend/shadcn-admin`.
- Playwright Test is pinned in the frontend package and configured for Chromium desktop
  and Pixel 5 mobile emulation.
- Browser traces are retained on failure and screenshots are captured on failure.
- Existing E2E coverage includes sign-in rendering, required-field validation,
  mocked authentication API failure, and forgot-password validation.
- The authenticated route checks the local auth store and redirects visitors without
  an access token to `/sign-in`.
- Frontend CI runs `bun run test:e2e` in the pinned Playwright container.
- The frontend CI workflow triggers on pull requests targeting `main`, pushes to
  `main` and `deploy/fastapi-cloud-prep`, and manual `workflow_dispatch`.
  Pushes to this feature branch alone do not trigger that workflow.
- LangGraph is part of the project's AI/RAG architecture. Ragas evaluation and
  OpenTelemetry instrumentation are planned candidates; verify their actual
  dependencies and runtime wiring before describing them as implemented. None of
  these components is currently claimed as integrated into this browser-testing demo.

## Initial scenario

Start with a safe access-control scenario:

1. Open the application root route.
2. Verify that an unauthenticated browser is redirected to sign-in.
3. Verify that the sign-in page and its accessible controls render.
4. Collect browser console errors, uncaught page errors, and failed network requests.
   Playwright also retains a screenshot and trace when the test fails.
5. Attach the collected browser evidence as JSON to the Playwright test result.

A later authenticated Dashboard scenario must use a disposable local/test account or a
dedicated isolated Demo fixture. Do not embed shared Demo credentials in source code,
tests, logs, screenshots, or CI configuration.

## Proposed execution architecture

- **Playwright runner:** performs browser navigation and a deliberately small allowlist
  of browser actions. It is the source of truth for observed browser behavior.
- **Evidence collector:** records step outcomes, URL, console/page errors, failed network
  requests, screenshots, and traces. Evidence must be correlated to a single run ID.
- **LangGraph orchestrator (later phase):** manages run state, bounded retries, and
  transitions between planning, execution, observation, and reporting. The first
  deterministic scenario remains the baseline and fallback.
- **FastAPI run API (later phase):** accepts a scenario identifier and returns a run ID;
  it must not accept arbitrary shell commands or unrestricted browser scripts.
- **Evaluation harness (later phase):** compares agent findings with known expected
  outcomes and reports scenario success, finding precision/recall, evidence completeness,
  and reproducibility.

## Safety boundaries

- Use local/test infrastructure by default.
- Permit only explicitly configured local or isolated Demo base URLs. Reject Production
  targets and unknown origins before launching a browser.
- Never run write-load tests against public endpoints.
- Use synthetic data only; never access real patient, prescription, tenant, or Production
  data.
- Do not perform POS sales, dispensing, inventory mutations, procurement, or other
  business writes in the initial scenario.
- Bound navigation count, execution time, retries, and artifact size.
- Do not let an LLM invent selectors or execute arbitrary code without validation.
- Do not change deployment workflows, secrets, environment settings, or Production
  infrastructure as part of this prototype.

## Acceptance criteria for the first increment

- The unauthenticated Dashboard access guard is covered by a Playwright E2E test.
- The test uses a fresh browser context and does not call the real authentication API.
- Browser diagnostics are attached to the Playwright test result as JSON.
- The test is included in the existing frontend E2E CI workflow.
- No Production credentials or business data are used.

## Implemented orchestration foundation

The feature branch now contains a deterministic LangGraph planning graph under
`src/pharmaviyum/ai/agentic_testing/`:

- Pydantic contracts reject unknown fields and arbitrary browser actions.
- Scenarios are limited to eight declarative steps.
- Navigation accepts only same-origin absolute paths (for example, `/`), not
  absolute URLs or scripts.
- The graph requires an explicit origin allowlist and rejects missing or unmatched
  origins before producing an execution plan.
- The graph is side-effect-free: it validates and plans; it does not launch a browser,
  call an LLM, or write business data.
- Playwright remains the execution authority. The plan is not a test result and cannot
  mark a scenario as passed.

Focused unit tests cover valid planning, missing and mismatched origin configuration,
cross-origin navigation attempts, action allowlisting, extra-field rejection, and
execution-step limits.

## Deterministic run-result contract

The backend now defines a strict Pydantic result contract in
`src/pharmaviyum/ai/agentic_testing/results.py`:

- Each step records its index, allowlisted action, observed status, duration,
  optional observation/error, and bounded evidence references.
- A run records its scenario/run identifiers, timezone-aware start and finish
  timestamps, up to eight step outcomes, and an optional blocked reason.
- The verdict is derived deterministically: any failed step means failed; a
  blocked reason means blocked; skipped or missing steps mean inconclusive;
  only a non-empty set of all-passed steps means passed.
- The model rejects a caller-supplied verdict that disagrees with the derived
  result. AI-generated summaries cannot override this contract.

This is a result schema and verdict policy only. It does not yet execute browser
steps, persist runs, or ingest Playwright artifacts.

## Current boundary

This increment is the first backend orchestration slice, not a complete agentic test
service. FastAPI run endpoints, durable run storage/queueing, a Playwright execution
adapter, evidence ingestion, AI-assisted bug triage, and evaluation metrics remain
separate follow-up increments. Do not expose this graph as a public endpoint until
authentication, authorization, run quotas, and trusted environment configuration are
implemented and tested.
