# Mortarium Hallucination Detection and AI Safety Evaluation

## Purpose

This document defines the evaluation controls used to detect unsupported model claims, test adversarial behavior and prevent unsafe pharmaceutical answers from reaching the pharmacist. It complements, rather than replaces, the [Ragas pharmaceutical evaluation](./ragas-pharmaceutical-evaluation.md).

**Important boundary:** evaluation tools are quality signals. None proves that a clinical answer is safe, correct or suitable for a patient. The application remains fail-closed for authorization and deterministic pharmacy rules; the pharmacist remains responsible for professional decisions.

## Tool definitions and intended use

| Tool | Definition | What Mortarium uses it for | Execution boundary |
|---|---|---|---|
| **Ragas** | An evaluation framework for retrieval-augmented generation (RAG). | Measure faithfulness, answer relevancy, context precision and context recall; compare retrieval/prompt/model changes against a versioned dataset. | Offline evaluation and CI regression checks. Not in the production request path. |
| **DeepEval** | An LLM evaluation framework with pytest-style test cases and metrics, including hallucination and faithfulness. | Independently evaluate whether generated claims are supported by retrieved context; add repeatable LLM/agent regression cases and custom pharmaceutical criteria. | Isolated evaluation environment. Judge model and credentials must be explicitly configured; never implicitly reuse production credentials. |
| **Vectara HHEM (Hughes Hallucination Evaluation Model)** | A pretrained classifier that estimates factual consistency between a source/context and a generated statement or summary. | Add a second, model-based groundedness signal at sentence/claim level. Use it to flag candidate unsupported statements for review or abstention. | Optional isolated evaluation/scoring service; not a production dependency until resource, latency, model revision, threshold and Python/runtime compatibility are validated. |
| **Promptfoo** | A prompt/LLM evaluation and red-team CLI for running reproducible test cases and adversarial probes against an application or model endpoint. | Test prompt injection in retrieved documents, jailbreaks, data exfiltration attempts, unsafe medication requests, tool misuse and multilingual attacks. | On-demand or scheduled security evaluation against a dedicated non-production target. Never point red-team scans at production patient data. |
| **Pytest + deterministic pharmaceutical checks** | Conventional automated tests and rule-based assertions. | Enforce exact medication name/strength/form, negation polarity, citation IDs, tenant/patient scope, schema constraints and abstention behavior. | Fast CI gate. Critical invariants must not depend on an LLM judge. |

### What each tool does not prove

- Ragas and DeepEval use statistical and/or LLM-judge evaluation. Scores depend on the dataset, judge model, prompt and evaluator version.
- HHEM estimates context-to-answer consistency. It does not verify whether the source itself is authoritative, current, jurisdictionally applicable or clinically correct.
- Promptfoo finds weaknesses through configured probes. A clean scan does not prove that all attacks or failure modes are absent.
- A valid citation identifier is not evidence that the cited source entails the claim. Citation correctness needs claim-to-source verification.
- High aggregate scores must never compensate for a patient-isolation failure, wrong medication strength/form, lost negation or unsupported high-risk clinical claim.

## Evaluation lifecycle

1. **Build trusted context.** The API authenticates the pharmacist, resolves pharmacy scope and validates any selected patient. Model-generated arguments cannot establish identity or authorization.
2. **Retrieve evidence.** LangGraph RAG retrieves only documents allowed by the current pharmacy/patient scope. Preserve source IDs, source version, language and jurisdiction.
3. **Generate a candidate answer.** The model may only make evidence-bounded claims. Retrieved text is untrusted input, not system policy.
4. **Extract and verify claims.** Split the answer into independently checkable factual claims. Verify each citation against its cited source; do not accept a citation merely because its ID exists.
5. **Run evaluation signals.** Ragas and DeepEval measure groundedness/relevance; HHEM can provide an independent sentence-level consistency signal; deterministic checks validate pharmaceutical entities, negation and access scope.
6. **Apply a decision gate.** A policy layer—not the LLM—decides whether the candidate may be returned.
7. **Record safe telemetry.** Record evaluator/model/dataset versions, aggregate scores, decision codes and durations. Do not log prompts, completions, patient identifiers, prescriptions or retrieved clinical text.

## Decision policy

| Outcome | Meaning | Required behavior |
|---|---|---|
| **ALLOW** | All mandatory deterministic checks pass and evidence support meets calibrated thresholds. | Return cited answer with normal pharmacist-facing advisory language. |
| **WARNING** | A non-critical uncertainty exists, such as incomplete evidence or a low-confidence non-critical claim. | Clearly identify the limitation and show supporting sources; do not present uncertainty as fact. |
| **ABSTAIN** | Evidence is missing, conflicting, stale, not applicable to the jurisdiction, or a critical claim cannot be verified. | Do not invent a recommendation. Explain what evidence is missing and request pharmacist verification. |
| **BLOCK** | Authorization violation, cross-patient/cross-pharmacy evidence, unsafe tool action, malformed critical medication data or other hard policy violation. | Do not return the unsafe content or execute the action. Emit a sanitized security event. |

A numerical score alone must not decide whether a medication recommendation is safe. Thresholds must be calibrated on a pharmacist-reviewed validation set and versioned with the evaluator, model and dataset.

## Pharmaceutical test coverage

The golden set must use synthetic or properly de-identified examples and cover:

- medication name, active ingredient, strength/concentration, dosage form, route and units;
- contraindications, interactions, allergy statements and dose-related claims;
- preservation of negation and conditional language;
- claim-level citation entailment and source freshness;
- conflicting documents, missing evidence and safe abstention;
- Russian and English retrieval and response behavior, reported separately;
- prompt injection and malicious instructions embedded in retrieved documents;
- tool-call authorization, least privilege and argument tampering;
- cross-pharmacy and cross-patient retrieval, memory, cache and checkpoint isolation.

Never send patient identifiers, prescription text, patient records or other PHI to third-party LLM judges or red-team providers. Use synthetic fixtures and sanitized case identifiers.

## Repository integration and status

- **Ragas:** present in `requirements-eval.txt`; current CI runs a Ragas API/import check, pharmaceutical metric contract tests and golden-dataset validation. This is offline evaluation, not a production response filter.
- **DeepEval:** pinned as an isolated evaluation dependency in `requirements-eval-deepeval.txt`. CI performs an import/API smoke check. The actual judge-backed hallucination suite still requires an explicitly configured evaluation model and curated cases.
- **HHEM:** documented as an optional model-based evaluator. The model is not installed in the FastAPI production image and is not yet a live request-path gate. Before enabling it, validate its model revision, license, runtime/Python compatibility, CPU/GPU footprint, latency and pharmacist-reviewed threshold.
- **Promptfoo:** documented for on-demand red-team testing against a dedicated non-production endpoint. A target-specific configuration and credentials are intentionally not fabricated; no production endpoint or secret is embedded in the repository.
- **Decision gate:** this document defines the target policy. Do not claim it is active in production until the application code enforces it and integration tests prove ALLOW/WARNING/ABSTAIN/BLOCK behavior.

### DeepEval isolated environment

Install only in the evaluation environment:

```bash
uv pip install --python .venv-eval/bin/python -r requirements-eval-deepeval.txt
```

Use a dedicated evaluator model configured explicitly for the test run. Do not upload evaluation cases to a hosted reporting service unless privacy, retention, region and contractual controls have been reviewed.

### Promptfoo red-team workflow

Use the committed [Promptfoo configuration](../../promptfooconfig.yaml) against a dedicated non-production deployment. Set the following environment variables before running it: `MORTARIUM_EVAL_TARGET_URL` (full URL ending in `/api/v1/ai/query`), `MORTARIUM_EVAL_API_TOKEN` (least-privilege test-user bearer token), `MORTARIUM_EVAL_PHARMACY_ID` (numeric synthetic test tenant), and `OPENAI_API_KEY` (attacker/grader provider key). The API token must belong to a test account and the pharmacy ID must refer only to synthetic test data.

```bash
npx promptfoo@latest redteam init --no-gui
npx promptfoo@latest redteam run
npx promptfoo@latest redteam report
```

Review generated attacks before execution. The target URL, bearer token and pharmacy ID are environment-driven; the attacker/grader provider is explicitly set to `openai:gpt-5`. Keep all credentials in the CI secret store or local environment, never in YAML or committed files. Do not set the target URL to production. Red-team scans may generate harmful or adversarial prompts, so restrict access to artifacts and never use real patient data.

## Release gates

1. Deterministic CI must pass before any model-based evaluation is considered.
2. Patient/pharmacy isolation, medication strength/form, negation and high-risk unsupported-claim failures are non-compensatory blockers.
3. Ragas/DeepEval/HHEM results are compared against a versioned baseline; judge model, model revision, prompts, corpus/index revision and dataset version are recorded.
4. Promptfoo findings rated critical/high must be triaged and resolved or explicitly risk-accepted before release.
5. Production enablement requires a separately reviewed runtime decision gate, staged integration tests, latency/cost budget, fallback behavior and rollback plan.

## References

- [Ragas pharmaceutical evaluation](./ragas-pharmaceutical-evaluation.md)
- [Mortarium AI / LLM system design](./AI_LLM_SYSTEM_DESIGN.md)
- [OpenTelemetry privacy and instrumentation policy](../observability/opentelemetry.md)
- [DeepEval installation and metrics](https://deepeval.com/tutorials/tutorial-setup)
- [Vectara HHEM model](https://huggingface.co/vectara/hallucination_evaluation_model)
- [Promptfoo red-team quickstart](https://www.promptfoo.dev/docs/red-team/quickstart/)
