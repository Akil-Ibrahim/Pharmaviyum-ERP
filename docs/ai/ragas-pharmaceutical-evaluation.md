# Pharmaceutical RAG Evaluation

## Purpose and boundary

Pharmaviyum uses LangGraph for production RAG orchestration. Ragas is an
**offline evaluation dependency**, not a production request-path dependency.
Install it only in the evaluation environment:

```bash
uv run --with-requirements requirements-eval.txt python -m pytest tests/unit/ai/test_ragas_evaluation.py
```

The adapter targets the Ragas 0.4 collections API. Evaluator LLM and embeddings
are injected; production provider credentials are not read implicitly.

Ragas metrics are probabilistic LLM-judge measurements. They are regression
signals, not clinical validation, regulatory certification, or proof of safety.

## Standard Ragas metrics

- **Faithfulness** — fraction of answer claims supported by retrieved context.
- **Answer relevancy** — whether the response addresses the query.
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

Patient-context isolation is a deterministic authorization regression check.
It must also be tested at the retriever/database boundary with cross-pharmacy
and cross-patient decoy records. Do not use real patient data in the golden set.

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
