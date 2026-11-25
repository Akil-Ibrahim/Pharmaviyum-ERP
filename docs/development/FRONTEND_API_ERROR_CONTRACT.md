# Frontend API Error Contract

**Status:** Implemented frontend transport/error-handling contract  
**Scope:** `frontend/shadcn-admin/`  
**Last source review:** 2026-11-25

## 1. Problem statement

The frontend uses native `fetch()` in `src/lib/api-client.ts`, while the global TanStack Query configuration previously recognized HTTP failures primarily through Axios' `AxiosError`. The fetch client threw plain `Error` objects, losing the HTTP status and structured response payload. This mismatch is exercised by the active profile-avatar query: `useProfileAvatar` calls `fetchProfileAvatar`, which calls `apiFetchBlob`, inside TanStack Query.

That mismatch meant:
- HTTP 401/403 errors from the profile-avatar fetch query were not excluded by the Axios-only retry predicate.
- Query-cache global handling did not recognize fetch-originated 401/500 responses from that query.
- The default mutation error handler also could not reliably show backend `detail` messages if a fetch-based mutation used it.

## 2. Implemented contract

### Typed error

`src/lib/api-error.ts` defines `ApiError` with:
- `status`: HTTP response status;
- `payload`: parsed response payload, retained as `unknown`;
- `message`: readable server `detail`, or a status-based fallback.

The payload remains untrusted input. Consumers must narrow its shape before reading fields.

### Transport

Both `apiFetch` and `apiFetchBlob` throw `ApiError` for non-success HTTP responses (except the existing optional-blob 404/204 behavior). A 401 still clears the local authentication state before the typed error is thrown.

Network failures from `fetch` remain native transport errors because no HTTP response/status exists.

### Query retry policy

`src/lib/query-error-policy.ts` is the shared policy for both `ApiError` and legacy `AxiosError` instances:

| Failure | Retry behavior |
|---|---|
| 401 / 403 | Never retry |
| Other 4xx | Never retry |
| 408 / 429 | Retry, bounded to three retries |
| 5xx | Retry, bounded to three retries |
| Network failure without HTTP status | Retry, bounded to three retries |
| Development mode | Automatic retries disabled |

The policy is intentionally conservative for client errors. A retry is not a substitute for user correction, authorization, or an idempotent mutation contract.

### Global and mutation handling

- Query-cache handling recognizes both typed fetch errors and Axios errors by HTTP status.
- 401 clears the session and redirects to sign-in while preserving the current location as the redirect target.
- 5xx query failures show the global server-error notification and navigate to the error route in production.
- Mutation error notifications display a validated server title/detail where available; otherwise they use the typed error message or a generic fallback.
- 403 remains an authorization failure; it is not silently converted into sign-out.

## 3. Tests

Focused tests cover:
- `ApiError` status/payload/message preservation;
- `apiFetch` typed HTTP errors and 401 session reset;
- optional blob 404 behavior and 204 response handling;
- server detail/title display;
- no-retry behavior for 401/403/404/422;
- bounded retry behavior for 408/429, 5xx and network failures;
- compatibility with Axios errors;
- development-mode retry suppression.

## 4. Engineering constraints

- Do not inspect or branch on unvalidated response payload properties without type narrowing.
- Do not retry non-idempotent mutations automatically merely because a request failed; TanStack Query mutation retry remains unchanged.
- Do not retry authorization or validation failures.
- Do not log raw request/response bodies, patient data, prescription data, tokens, or tenant-sensitive payloads.
- Preserve server-provided status and safe user-facing detail; avoid exposing stack traces or internal diagnostics.
- Keep backend contracts and generated API artifacts authoritative; this change does not generate or alter the API client.

## 5. Validation status

Source and test files were updated in the same change. Local Bun lint, formatting, unit/browser tests and production build must pass in CI before this implementation is considered validated. No local command or browser test is claimed by this document.
