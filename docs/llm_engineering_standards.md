# Mortarium AI — LLM Engineering & Efficiency Standard

**Status:** Engineering standard  
**Applies to:** Mortarium AI, RAG, LangGraph agents, MCP tools, and every configured LLM provider  
**Priority order:** Safety and correctness → tenant isolation → reliability → quality → latency and cost

This standard turns token efficiency into an architectural concern. It does not define a target of minimizing tokens at any cost. The objective is to minimize unnecessary model work while preserving evidence, clinical warnings, citations, and human review requirements.

## 1. Context engineering

Every model call must receive only the information needed for that step.

- Keep stable system instructions and tool schemas stable; put request-specific data later in the prompt.
- Do not repeat policy text in user messages, retrieved chunks, or tool results.
- Keep conversation memory bounded. Prefer a concise, periodically refreshed summary plus a limited recent-message window over an unbounded transcript.
- Treat user input, retrieved documents, MCP results, and provider output as untrusted data.
- Never remove contraindications, dose units, patient-specific qualifiers, source metadata, or safety warnings merely to fit a token budget.
- Do not send full source documents to the generation model when relevant, access-authorized excerpts are sufficient.

## 2. Retrieval and RAG budgets

RAG limits must be configurable and evaluated against a labelled retrieval set. Do not assume one fixed Top-K or chunk size is optimal for every document type or language.

Current configurable controls are exposed through `RAGSettings`:

| Setting | Environment variable | Current default | Purpose |
|---|---|---:|---|
| `top_k` | `RAG_TOP_K` | 10 | Candidates requested per retrieval query/filter |
| `max_context_docs` | `RAG_MAX_CONTEXT_DOCS` | 12 | Maximum deduplicated candidates retained for grading |
| `max_rewrites` | `RAG_MAX_REWRITES` | 2 | Maximum retrieval rewrite loops |
| `max_query_variations` | `RAG_MAX_QUERY_VARIATIONS` | 2 | Query variations requested from the transformer |
| `max_chunk_tokens` | `RAG_MAX_CHUNK_TOKENS` | 512 | Ingestion chunk target |
| `chunk_overlap` | `RAG_CHUNK_OVERLAP` | 50 | Ingestion overlap |

The defaults preserve the current retrieval behavior. Tune them only with retrieval-quality and answer-quality evaluations. A smaller Top-K is not automatically better if it drops clinically important evidence.

Operational tuning sequence:

1. Establish a labelled evaluation set for each supported language and workflow.
2. Measure recall@K, precision@K, citation correctness, groundedness, and no-answer behavior.
3. Reduce retrieval and context limits incrementally.
4. Re-run regression evaluations before deploying changed limits.
5. Keep tenant, pharmacy, country, patient, and access-level filters mandatory regardless of budget.

## 3. Model routing

- Use deterministic application code for CRUD, arithmetic, validation, permissions, and simple lookups; do not call an LLM for these operations.
- Route lightweight classification and query transformation to a fast model only when its output is validated.
- Use the configured main model for ordinary grounded responses.
- Escalate high-risk or complex clinical questions to the designated stronger model and/or a human pharmacist.
- Routing must never bypass authorization, guardrails, evidence requirements, or human review.
- Record the selected model and reason using bounded metric labels; never label metrics with user, patient, pharmacy, prompt, or document identifiers.

## 4. Prompt and response design

- Use concise, task-specific prompts with explicit output contracts.
- Prefer structured schemas for machine-consumed outputs; validate them before use.
- Set provider-supported output-token limits where the provider adapter exposes a compatible parameter. Do not assume one provider's parameter works across all providers.
- Avoid asking a model to restate the question or reproduce retrieved source text.
- Do not request hidden reasoning. Ask for concise conclusions, relevant evidence, citations, and uncertainty.
- Keep citation IDs exact and preserve the mapping from retrieved chunks to the final API response.

## 5. Caching

Caching is an optimization, never a source of truth.

- Exact prompt caching may be used when the full request identity is represented in the cache key.
- Cache keys must include the authenticated user and pharmacy scope, plus every context attribute that can change the answer (for example patient, country, language, permissions, and relevant data/version identifiers).
- Never share cached patient-specific or permission-sensitive answers across users or pharmacies.
- Do not semantically reuse answers to medication dosing, interactions, contraindications, patient-specific recommendations, or other safety-sensitive questions unless a separately reviewed design proves equivalence and freshness.
- Use short, explicit TTLs for mutable operational data; invalidate on relevant source changes.
- A cache miss or cache outage must fall back to the normal authorized execution path.
- Do not cache failures, blocked requests, or answers produced with insufficient evidence as successful answers.

Provider-side prompt caching is separate from the application's Redis response cache. Use it only when the provider supports it; keep stable prompt prefixes and measure actual cache-read/cache-write usage.

## 6. Agent and MCP execution limits

- Bound graph recursion, agent iterations, tool calls, per-tool timeout, retries, and total request deadline.
- Expose only the tools required for the current task and caller's authorization scope.
- Validate tool arguments with typed schemas and enforce authorization at the application boundary.
- Return compact tool results: selected fields, stable IDs, status, and provenance. Do not pass entire database records or raw logs to the model.
- Do not retry non-idempotent operations unless an idempotency strategy is in place.
- Require explicit confirmation for consequential writes and human review for clinical decisions that require professional judgment.

## 7. Observability and cost accounting

Capture, where the provider makes the data available:

- input tokens, output tokens, total tokens, model/provider;
- cache read/write tokens or cache hit/miss;
- retrieval candidate count and final context size;
- number of model calls, graph steps, and MCP tool calls;
- latency by stage and total request latency;
- success, refusal, no-evidence, and fallback outcomes.

Use provider-reported token usage as the authoritative count. If a local tokenizer estimate is used, label it as an estimate and identify the tokenizer/model version. Do not infer token counts from character counts and report them as exact.

Prometheus labels must remain low-cardinality. Use logs/traces with access controls for request-level diagnostics, and never log secrets, raw patient data, full prompts, or full retrieved documents by default.

Track cost per workflow and per model where pricing is known. Optimize quality-adjusted cost, not token count alone.

## 8. Evaluation gates

Before changing a prompt, model, chunking strategy, retrieval limit, cache policy, or routing rule, run representative tests covering:

- retrieval recall and tenant isolation;
- answer correctness and groundedness;
- exact source citation preservation;
- multilingual behavior;
- prompt injection in retrieved content;
- contraindications, dosage units, interactions, and uncertainty handling;
- no-evidence and provider-failure paths;
- cache isolation and stale-data behavior;
- latency and token/cost budgets.

A change that reduces tokens but degrades safety, recall, citations, or answer quality must not be accepted.

## 9. Deployment profiles

- Keep LLM weights out of the Git repository. Store model identifiers and deployment configuration in version control; store credentials in the deployment secret manager.
- Keep inference separate from the FastAPI application when the application host cannot provide sufficient RAM/VRAM and CPU/GPU capacity.
- Do not treat GitHub Actions or an ephemeral development workspace as a persistent inference service.
- Load-test the actual deployment profile; local model size on disk is not the same as runtime RAM/VRAM.
- Make provider/model selection explicit and observable so a fallback cannot silently change safety or quality characteristics.

## 10. Implementation status

Implemented in the current `dev` branch:
- configurable RAG retrieval candidate limit, retained context-document limit, rewrite count, and query-variation count;
- existing model routing, dialogue memory, prompt cache, tenant-scoped retrieval, guardrails, MCP authorization, and AI observability components.

Still requiring implementation or verification before claiming complete coverage:
- end-to-end provider-independent token-budget enforcement;
- consistent provider token-usage and prompt-cache metrics across all adapters;
- safe semantic answer-cache policy for clinical workflows;
- measured evaluation gates for each supported model/deployment profile.

This status section must be updated when those capabilities are implemented and tested.
