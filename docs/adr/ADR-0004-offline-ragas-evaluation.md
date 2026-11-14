# ADR-0004: Isolated Offline Ragas Evaluation

## Status
Accepted — Ragas is an offline evaluation dependency, not part of the production request path.

## Context
Mortarium uses LangGraph for production agent and RAG orchestration. Ragas provides evaluation metrics, but evaluator LLM calls, embeddings and reference datasets have different cost, privacy and reproducibility characteristics from live pharmacist requests. Installing evaluation frameworks into the production runtime would expand the attack surface and introduce unnecessary dependencies/provider calls.

## Decision
- Keep Ragas in the isolated evaluation dependency set (requirements-eval.txt).
- Run evaluation from CI or a controlled offline environment, not FastAPI request handling.
- Inject evaluator LLM and embedding adapters explicitly; do not implicitly reuse production credentials.
- Use synthetic or approved de-identified datasets. Never commit real patient records, prescriptions or clinical conversations.
- Pin and test the Ragas adapter API version.
- Treat LLM-judge metrics as regression evidence, not clinical validation or regulatory certification.
- Keep deterministic pharmacy-specific checks alongside Ragas: medication fields, negation polarity, patient-context isolation, citation IDs and source entailment.

## Consequences
Production dependencies and latency are not coupled to Ragas. Evaluation reproducibility requires recording dataset, corpus/index revision, evaluator model, prompt/template and dependency versions. Qualified pharmacy/clinical review remains necessary for threshold approval and adjudication. A passing evaluation suite does not independently authorize production rollout.

## References
- [Pharmaceutical RAG evaluation](../ai/ragas-pharmaceutical-evaluation.md)
- [Engineering benchmark requirements](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md)
- [LLM engineering standard](../llm_engineering_standards.md)
