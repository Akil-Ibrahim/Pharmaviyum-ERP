# Mortarium AI — Model Routing and Provider Requirements

**Status:** Architecture requirements and implementation assessment  
**Scope:** Pharmaviyum ERP/CRM and the Mortarium pharmacy assistant  
**Canonical implementation references:** `src/pharmaviyum/ai/config.py`, `src/pharmaviyum/ai/dependencies.py`, `src/pharmaviyum/ai/harness/model_router.py`

## 1. Objective

Mortarium must use a provider-independent model-routing layer. The application must be able to select an appropriate model for a task and deployment profile without embedding provider-specific logic in pharmacy workflows.

The routing policy must balance:

1. Pharmacy/clinical safety and task correctness.
2. Required capabilities (tool calling, structured output, context window, language support).
3. Model quality measured on Pharmaviyum's reviewed evaluation datasets.
4. Availability and latency.
5. Token and request cost.
6. Data residency, privacy, and tenant policy.

Cost or latency must never override a safety or authorization requirement.

## 2. Product and agent boundary

Mortarium is one central pharmacy assistant with specialized pharmacy workflows, not a collection of independently deployed agents for every pharmacy role.

The existing `PharmacistAgent` and Agent Harness remain the application-level assistant/orchestration boundary. Workflows may specialize tasks such as medicine information, inventory lookup, procurement support, dispensing support, sales analysis, and operational guidance. Model selection is a capability of the shared routing layer, not a reason to create a separate agent for each task.

Deterministic business facts and transactions must come from authorized Pharmaviyum APIs, services, and databases. The LLM must not invent medicine availability, price, stock, batch status, prescription status, or transaction outcomes. POS, dispensing, FEFO, stock mutation, and other critical transactions remain controlled by deterministic business rules and authorization.

## 3. Current implementation — verified from repository code

The following describes source-code defaults and wiring, not the effective configuration of a running production deployment.

### 3.1 Chat model construction currently implemented

| Runtime path | Current model defaults in `ai/config.py` | Chat construction |
|---|---|---|
| Local Ollama | Fast: `qwen3.5:9b`; Main: `qwen3.5:9b`; Complex: `qwen3.5:9b` | Implemented via `ChatOllama` |
| Gemini cloud | Fast: `gemini-3.5-flash-lite`; Main: `gemini-3.5-flash`; Complex: `gemini-2.5-pro` | Implemented via `ChatGoogleGenerativeAI` |
| Groq cloud | Fast: `llama-3.1-8b-instant`; Main: `llama-3.1-70b-versatile`; Complex currently resolves to the same main model | Implemented via `ChatGroq` |
| OpenAI | Chat model settings exist (`gpt-4o-mini`, `gpt-4o`) | No OpenAI chat-model construction path in the current `_build_llm` factory |
| Anthropic | Model settings exist (`claude-3-5-sonnet-20241022`) | No Anthropic chat-model construction path in the current `_build_llm` factory |

OpenAI is also referenced by the embeddings setup for the non-Gemini cloud branch; this does not mean OpenAI chat completion is currently supported by the chat-model factory. Anthropic configuration alone does not establish a working Anthropic adapter.

### 3.2 Effective default selection

- `USE_CLOUD_LLM` defaults to `false`; without an overriding deployment environment variable, the code selects Ollama.
- `CLOUD_LLM_PROVIDER` defaults to `gemini` and currently accepts `gemini` or `groq` for the cloud chat path.
- The source defaults do not prove which provider or model is active in FastAPI Cloud. Effective production settings and provider health must be verified from deployment configuration and runtime telemetry without exposing secret values.
- The documented on-premises profile uses Ollama with Qwen3.5 9B. The actual local model tag is configurable.

### 3.3 Current routing behavior and limitations

The current `ModelRouter` selects `fast`, `main`, or `complex` using query-length, keyword, language, conversation-depth, and context heuristics. A safety-check flag selects the main or complex route.

The dependency wiring currently provides:
- `fast` → `get_llm_fast()`
- `main` → `get_llm_main()`
- `complex` → `get_llm_complex()`
- `fallback` → `get_llm_main()`

The current fallback is a fallback for a missing router key, not a verified provider-failure failover mechanism. It does not by itself demonstrate retries against a different provider after timeout, rate limiting, or provider outage. Current routing is not yet demonstrably cost-aware, latency-aware, quality-score-aware, or health-aware. The router's `context` handling must also avoid passing patient or prescription identifiers into logs or telemetry.

These limitations must remain visible in documentation until implementation and tests prove otherwise.

## 4. Target provider architecture

Introduce a provider adapter/registry boundary behind a stable internal interface. Provider-specific SDKs must be isolated inside adapters; pharmacy workflows and agent nodes must depend on the internal model interface and task policy, not vendor SDK classes.

Target provider families:

- **Ollama:** local/on-premises inference and deployments requiring local model execution.
- **Gemini:** supported cloud inference path.
- **Groq:** supported cloud inference path.
- **OpenAI:** optional future chat adapter; do not mark supported until implemented and tested.
- **Anthropic Claude:** optional future chat adapter; do not mark supported until implemented and tested.

Each registered model must declare metadata:
- provider and exact model identifier;
- routing roles/capabilities;
- supported languages;
- tool-calling and structured-output support;
- context and output-token limits;
- deployment region/data handling constraints;
- timeout and retry policy;
- measured quality profile for relevant pharmacy tasks;
- measured latency and cost profile;
- availability/health state.

Model names and provider availability change over time. Validate model IDs against provider documentation and the target account before enabling a profile. Keep model IDs configurable; do not scatter them through business logic.

## 5. Routing roles and policy

| Role | Intended use | Policy |
|---|---|---|
| `fast` | Classification, intent detection, query rewrite, low-risk short responses | Lowest acceptable latency/cost while meeting task-specific quality gates |
| `main` | Default pharmacy assistant reasoning and normal workflow orchestration | Default route for general tasks |
| `complex` | Multi-step reasoning, ambiguous medication questions, interactions, contraindications, safety-sensitive review | Must meet stricter pharmacy evaluation and capability requirements |
| `fallback` | Continuity during provider/model degradation | Must be independently configured and health-checked; must preserve safety, tenant, privacy, and residency constraints |

Routing inputs should be typed task metadata rather than raw prompt inspection alone:
- task category and risk tier;
- complexity estimate;
- language;
- required tools/output schema;
- context size;
- current provider health;
- remaining latency and token/cost budget;
- model evaluation eligibility for that task.

The router should return a structured decision containing the selected provider/model, role, bounded reason code, policy version, and fallback status. Do not record raw prompts, patient data, prescription content, or retrieved clinical text in routing logs.

## 6. Failover, resilience, and safety

The production routing implementation must provide:

1. Bounded timeouts and retries for transient provider failures.
2. Circuit breaking and provider health tracking.
3. A configured fallback chain across eligible models/providers, not merely a second name pointing to the same model.
4. Retry rules that account for idempotency and avoid duplicate tool side effects.
5. A clear failure response or human escalation when no eligible safe model is available.
6. No silent downgrade from a safety-qualified route to an unqualified fast model.
7. Tenant authorization and data-residency constraints applied before provider selection.
8. Explicit handling for rate limits, quota exhaustion, authentication errors, malformed structured output, and provider outages.
9. Model/provider switching through configuration/registry without changes to pharmacy business logic.
10. Startup/readiness diagnostics that report provider configuration and health without revealing API keys or other secrets.

Fallback is not permission to bypass deterministic business controls, clinical guardrails, RAG grounding, authorization, or pharmacist escalation.

## 7. Evaluation and release gates

Model routing must be evaluated with a versioned, pharmacist-reviewed Golden Dataset. Evaluate each eligible model and route by task category, language, and risk tier. Ragas may be used for supported RAG metrics, supplemented by deterministic and expert-reviewed pharmacy metrics.

### RAG and answer quality
- Faithfulness.
- Answer Relevancy.
- Context Precision and Context Recall.
- Context Entity Recall and Noise Sensitivity where supported by the pinned Ragas version.
- Answer Correctness and Semantic Similarity.
- Retrieval Recall@K, Precision@K, Hit Rate@K, MRR, and NDCG@K.
- Citation Correctness: each cited source must support the associated claim.

### Pharmacy-specific correctness and safety
- Medication Entity Accuracy.
- Active Ingredient Accuracy.
- Dosage and Strength Accuracy.
- Dosage Form and Route of Administration Accuracy.
- Negation Preservation.
- Contraindication Recall.
- Drug Interaction Accuracy.
- Clinical Hallucination Rate.
- Correct abstention and pharmacist-escalation rate.

### Routing, agent, and provider reliability
- Routing Decision Accuracy.
- Task Completion Rate.
- Tool Selection and Tool Argument Accuracy.
- Tool Execution Success Rate.
- Provider Availability / Error Rate.
- Fallback Activation Rate and Fallback Success Rate.
- End-to-End Latency P50/P95/P99 by task and route.
- Input/output token usage and cost per successful task.
- Timeout, retry, circuit-breaker, and escalation rates.

### Non-negotiable release gates
- Any confirmed cross-tenant disclosure, unauthorized tool execution, or sensitive-data leakage blocks release.
- Any critical medication safety failure blocks the affected model/route regardless of aggregate score.
- Averages must not hide failures in high-risk categories or languages.
- Thresholds must be set from reviewed baseline data, risk analysis, and pharmacist sign-off; do not invent universal pass percentages.
- Model, prompt, embedding, retrieval, or routing-policy changes trigger the relevant regression evaluations.

## 8. Observability and privacy

Use OpenTelemetry for end-to-end traces, metrics, and correlated logs across FastAPI, Agent Harness, LangGraph, RAG, MCP, database/cache boundaries, and provider calls.

Recommended bounded telemetry attributes include:
- route role (`fast`, `main`, `complex`, `fallback`);
- provider and configured model identifier;
- task category and risk tier;
- routing reason code and policy version;
- provider outcome/error category;
- latency, token counts, and cost where available;
- fallback attempted/succeeded.

Do not use tenant IDs, user IDs, patient IDs, prescription IDs, session IDs, raw prompts, model completions, or retrieved clinical text as metric labels or unrestricted span attributes. Apply redaction, access controls, retention limits, and region/data-residency review before production export.

## 9. Acceptance criteria

The target model-routing architecture is accepted only when:

- Provider adapters have contract tests and can be selected through configuration.
- The active deployment provider/model can be identified through a safe diagnostic and runtime telemetry.
- `fast`, `main`, `complex`, and `fallback` roles have explicit, tested mappings.
- Fallback is tested against simulated timeout, rate-limit, provider 5xx, and malformed-output failures.
- The fallback target is independently configured and satisfies the task's safety and data policy.
- Routing decisions are explainable through bounded reason codes.
- Cost, latency, provider health, and task-specific quality are measured and included in routing evaluation.
- Switching eligible providers does not require changes to pharmacy business workflows.
- RAG, pharmacy safety, tenant isolation, and agent metrics run in CI as appropriate quality gates.
- No sensitive patient or tenant data is exposed through logs, traces, metrics, or evaluation artifacts.

## 10. Implementation status summary

| Capability | Repository evidence | Status |
|---|---|---|
| Ollama chat adapter | `ChatOllama` in `ai/dependencies.py` | Implemented |
| Gemini chat adapter | `ChatGoogleGenerativeAI` in `ai/dependencies.py` | Implemented |
| Groq chat adapter | `ChatGroq` in `ai/dependencies.py` | Implemented |
| OpenAI chat adapter | Settings exist; no chat factory branch | Not implemented / verify before claiming support |
| Anthropic chat adapter | Settings exist; no chat factory branch | Not implemented / verify before claiming support |
| fast/main/complex routing | Heuristic `ModelRouter` and dependency wiring | Partially implemented |
| Missing-key fallback | `_get_model()` fallback to main/first registered model | Implemented, limited |
| Provider-outage failover | No demonstrated cross-provider failure path in inspected router/wiring | Missing / requires implementation |
| Cost/latency/health-aware routing | Not demonstrated in inspected router | Missing / requires implementation |
| Active production model verification | Cannot be established from source defaults alone | Needs deployment/runtime verification |
| Provider switch without business-logic changes | Adapter boundary is incomplete | Target requirement |

## References

- Current AI architecture: [`docs/ai_architecture.md`](../ai_architecture.md)
- OpenTelemetry: [`docs/observability/opentelemetry.md`](../observability/opentelemetry.md)
- Implementation: [`src/pharmaviyum/ai/config.py`](../../src/pharmaviyum/ai/config.py), [`dependencies.py`](../../src/pharmaviyum/ai/dependencies.py), [`model_router.py`](../../src/pharmaviyum/ai/harness/model_router.py)
