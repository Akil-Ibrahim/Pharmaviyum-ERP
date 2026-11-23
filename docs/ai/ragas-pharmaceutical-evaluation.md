# Pharmaceutical RAG Evaluation

[English](./ragas-pharmaceutical-evaluation.md) · [Русский](./ragas-pharmaceutical-evaluation.ru.md)

## Purpose and boundary

Pharmaviyum uses LangGraph for production RAG orchestration. Ragas is an
**evaluation-only dependency**, not a production runtime or request-path dependency.
It is declared in the `eval` dependency group in `pyproject.toml`, locked in
`uv.lock`, and installed explicitly by the CI evaluation job:

```bash
uv sync --frozen --group eval
uv run pytest tests/unit/ai/test_ragas_evaluation.py -v -m unit
```

The production installation does not select the `eval` group, so Ragas is not
installed in the production runtime image.

The adapter targets the Ragas 0.4 collections API. Evaluator LLM and embeddings
are injected; production provider credentials are not read implicitly.

Ragas metrics are probabilistic LLM-judge measurements. They are regression
signals, not clinical validation, regulatory certification, or proof of safety.

## Standard Ragas metrics

- **Faithfulness** — fraction of answer claims supported by retrieved context.
- **Answer relevancy** — cosine similarity between the query and questions inferred from the response; its valid range is `[-1, 1]`, so negative scores are valid and must not be clamped or rejected.
- **Faithfulness, context precision and context recall** — normalized scores in `[0, 1]`.
- **Context precision** — whether relevant retrieved chunks rank above noise.
- **Context recall** — whether retrieved context covers the reference answer.

Context precision and recall require a curated reference answer. Missing
reference data is reported as unavailable, never silently converted to zero.

## Pharmaceutical metrics

| Metric | Evaluation contract |
|---|---|
| Citation correctness | Every factual claim has a real citation ID and an independent entailment judge confirms that the cited source supports that claim. |
| Medication entity accuracy | Exact precision/recall/F1 over medication name, strength and dosage form. |
| Negation preservation | Labeled propositions retain their expected positive/negative polarity. |
| Clinical hallucination rate | Unsupported clinical claims divided by all labeled clinical claims; lower is better. |
| Patient-context isolation | Private retrieved sources must match the authenticated pharmacy and, for patient-level records, the requested patient. Any mismatch fails. |
| Multilingual retrieval | Gold-source recall is measured independently for Russian (ru) and English (en). |

Citation correctness and clinical hallucination rate require an injected
claim-support judge. If no judge is configured, the result is **unavailable**;
a syntactically valid citation is not treated as proof of entailment.

Medication entity and negation metrics require structured gold labels or
independently extracted predictions. They must not infer ground truth from the
same model output being evaluated.

Patient-context isolation is a deterministic authorization regression check,
not an authorization control. It must also be tested at the retriever/database
boundary with cross-pharmacy and cross-patient decoy records. The MCP
`get_patient_history` tool now binds its model-supplied patient selector to the
trusted selected patient and controlled purpose, and records metadata-only
allowed/denied PHI audit decisions. The deterministic RAG metric does not
replace those tool-level controls. Unit tests cover mismatch, missing purpose,
context propagation and audit-commit failure; database-backed MCP audit tests
and staged verification remain outstanding. Do not use real patient data in
the golden set.

## Dataset requirements

Maintain versioned, synthetic or de-identified golden cases with:
- language and jurisdiction labels;
- reference answer and gold source/chunk IDs;
- medication name, strength and dosage form labels;
- proposition-level negation labels;
- clinical claims and evidence labels;
- pharmacy/patient scope labels for synthetic isolation tests.

Keep Russian and English cases balanced and report scores separately by
language. Do not pool the two languages into one score that can hide a weak
language-specific result.

## Release gates

Use two separate gates:

1. **Fast deterministic CI:** medication entities, negation, patient isolation,
   gold-source recall, citation ID validity and dataset schema.
2. **Scheduled/on-demand LLM evaluation:** Ragas metrics, citation entailment
   and clinical claim support.

Critical failures are non-compensatory: any patient-scope violation, incorrect
medication strength/form, lost negation, or unsupported high-risk clinical
claim blocks promotion even if aggregate Ragas scores are high. Thresholds
must be calibrated against a pharmacist-reviewed validation set before being
used as production release criteria.

## Privacy

Evaluation datasets must not contain identifiable patient information. Do not
send patient identifiers, prescription text, prompts, retrieved patient records
or PHI to third-party judges. Store aggregate scores and sanitized case IDs;
apply access control and retention to detailed evaluation artifacts.