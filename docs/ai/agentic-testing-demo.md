# Agentic testing demo

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
