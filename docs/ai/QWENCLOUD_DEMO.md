# Mortarium AI demo: QwenCloud provider and quota safeguards

**Status:** provider adapter and fail-closed application guard are present on `main`; this document describes a demo configuration profile, not proof of a live or production deployment.  
**Scope:** demo environment only. This document distinguishes implemented code from planned safeguards; a planned item is not an operational guarantee.

## 1. Demo objectives and boundaries

The demo uses **QwenCloud as its only cloud LLM provider**, with the configured model `qwen3.8-flash`. OpenRouter and additional LLM-provider fallbacks are intentionally out of scope.

The demo must:
- stay within the provider's free quota and avoid accidental paid usage;
- fail closed when the application is not explicitly configured for free-quota-only operation;
- expose bounded timeouts, output size, and observable token usage;
- keep the ERP and POS transaction path independent of LLM availability;
- allow model selection through configuration rather than LangGraph rewrites;
- keep embeddings as a separate capability with separate credentials and quota;
- use synthetic/demo data only unless the applicable privacy, security, and contractual controls have been approved for real patient data.

This is a demo deployment profile, not a claim that free-tier capacity, uptime, or quota is unlimited. Provider quota and expiry are controlled by the provider and must be checked in its console.

## 2. Configuration contract

Configure secrets in FastAPI Cloud, never in source control, issue comments, or logs.

| Variable | Demo value / purpose |
|---|---|
| `USE_CLOUD_LLM` | `true` |
| `CLOUD_LLM_PROVIDER` | `qwencloud` |
| `QWEN_API_KEY` | Secret API key from QwenCloud |
| `QWEN_BASE_URL` | `https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1` |
| `QWEN_MODEL` | `qwen3.8-flash` |
| `QWEN_FAST_MODEL` | `qwen3.8-flash` |
| `QWEN_COMPLEX_MODEL` | `qwen3.8-flash` |
| `QWEN_FREE_QUOTA_ONLY` | `true` to allow adapter initialization; defaults to `false` |
| `QWEN_TIMEOUT_SECONDS` | `30` |
| `QWEN_MAX_OUTPUT_TOKENS` | `500` |

The Qwen adapter uses the OpenAI-compatible LangChain client. Retries are disabled and requests have a finite timeout and output-token bound. Missing API credentials or `QWEN_FREE_QUOTA_ONLY=false` prevent the Qwen adapter from being constructed.

**Two independent controls are required:**
1. Application guard: `QWEN_FREE_QUOTA_ONLY=true` is required by the adapter.
2. Provider guard: enable the QwenCloud console's **Free quota only** option for the selected model.

The application flag does not query provider quota and cannot enforce provider billing policy by itself. The provider-console setting is the authoritative paid-usage control.

## 3. Current implementation status

| Capability | Status | Notes |
|---|---|---|
| QwenCloud provider adapter | Implemented on `main` | OpenAI-compatible LangChain `ChatOpenAI` adapter |
| Model selection by configuration | Implemented on `main` | Fast/main/complex model settings; no LangGraph rewrite for model ID changes |
| Fail-closed application free-quota flag | Implemented on `main` | Defaults to false; adapter refuses initialization unless explicitly enabled |
| Bounded timeout and output tokens | Implemented on `main` | Retries disabled |
| Token-usage callback/metrics | Source implementation present; end-to-end telemetry verification required | Operational telemetry, not an authoritative quota ledger |
| Provider-console Free quota only | Manual operator requirement | Must be enabled and checked in QwenCloud console |
| Per-request prompt/token budget | Existing code | Limits prompt sizing; it is not a daily provider quota |
| Shared daily Redis token cap | Planned; not yet implemented | Must reserve budget atomically before provider calls and reconcile actual usage |
| Concurrency-safe quota reservation | Planned; not yet implemented | Must work across all API/worker replicas |
| Explicit provider error classification | Planned; not yet implemented | Distinguish authentication, permission, quota/rate-limit, timeout, and provider/server failures |
| Provider circuit breaker / cooldown | Planned; not yet implemented | Prevent repeated calls during provider outages or quota exhaustion |
| Quota expiry/renewal operational check | Manual process; automation not yet implemented | Verify console balance, expiry, and terms before demo sessions |
| Automatic LLM fallback | Intentionally disabled | No OpenRouter or paid-provider fallback |

Do not describe planned controls as active until code, tests, and deployment configuration have all been verified.

## 4. Planned request and quota-control flow

The intended strict demo flow is:

1. Validate that the Qwen provider is enabled and free-quota-only application configuration is true.
2. Check the provider circuit state and local demo budget.
3. Atomically reserve an estimated token allowance in shared Redis before making the external request.
4. Reject the AI request if Redis is unavailable in strict mode, the budget is exhausted, or the circuit is open.
5. Call QwenCloud with bounded timeout/output tokens and no automatic retry.
6. On success, record provider-reported usage and reconcile the reservation.
7. On failure, release or conservatively settle the reservation according to whether the provider may have processed the request; classify the error and update circuit state.
8. Return a controlled AI-unavailable response to the AI caller. Do not block or roll back unrelated POS/database transactions because an AI call failed.

Redis quota accounting is an application-level safety budget. It cannot replace the QwenCloud console's billing/free-quota enforcement. Unknown usage must be handled conservatively rather than treated as zero.

### Error policy target

| Failure | Target behavior |
|---|---|
| 401 / invalid key | Stop retries; surface configuration error to operators; no provider fallback |
| 403 / permission or model access | Stop retries; operator action required |
| 429 / quota or rate limit | Open cooldown/circuit; reject further AI calls until safe to retry; no paid fallback |
| Timeout / connection failure | Bounded failure; conservative reservation handling; circuit protection |
| 5xx provider failure | Bounded failure and cooldown; no automatic provider switch |
| Redis unavailable | Fail closed for Qwen calls when strict quota mode is enabled |
| Local daily budget exhausted | Reject further AI generation until the budget window resets |

Provider response codes and structured error bodies must be verified against the actual QwenCloud API before finalizing classification logic.

## 5. RAG and embeddings are separate

QwenCloud in this demo is the **generation** provider. It does not implicitly configure the embedding model.

The current cloud embedding path is separately configured through the existing embedding provider and credentials. Before claiming cloud RAG is operational, verify:
- the selected embedding provider and model are configured;
- the embedding API key is present in the runtime;
- the embedding dimensions match the pgvector schema;
- ingestion and retrieval tests pass;
- tenant, pharmacy, and patient filters remain enforced.

Do not send patient-identifiable or other sensitive data to a free-tier endpoint without an approved privacy/security basis and provider terms.

## 6. Provider quota and expiry operations

Before each demo release or session:
- inspect the QwenCloud project, region, selected model, remaining free quota, and expiry date;
- confirm the provider-console **Free quota only** setting is enabled;
- verify that FastAPI Cloud has the expected Qwen environment variables without exposing secret values;
- run a small synthetic smoke test and inspect token-usage telemetry;
- stop demo AI calls if quota is exhausted or the free-quota entitlement has expired.

Do not assume that free quota renews automatically. When the displayed entitlement expires, re-check the provider console and current terms before continuing. Do not silently switch to a paid plan or another provider.

## 7. Validation and release gates

PR #244 must remain unmerged until:
- backend lint, formatting, type checks, and unit tests pass;
- frontend CI and security scans pass;
- focused tests cover missing key, free-quota guard disabled, model configuration, usage extraction, budget reservation/reconciliation, and provider error handling as those controls are implemented;
- a provider smoke test is performed only with an explicitly approved demo key and the provider-console free-only guard enabled.

A passing CI run does not prove that a live provider key, free quota, embedding service, or production deployment is configured correctly.

No production environment variables, production database, migrations, or deployment are changed by the PR work. Merge and deployment require separate explicit authorization.

## 8. Related documentation

- [FastAPI Cloud deployment runbook](../deployment/FASTAPI_CLOUD.md)
- [AI architecture](../ai_architecture.md)
- [RAG architecture audit](../rag_architecture_audit.md)
- [Engineering benchmark requirements](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md)
- [PR #244](https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/pull/244)
