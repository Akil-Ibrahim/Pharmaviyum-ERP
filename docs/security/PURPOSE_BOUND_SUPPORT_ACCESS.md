# Purpose-Bound Privileged Support Access

**Status:** Architecture proposal; not implemented or authorized for production use.  
**Scope:** Human platform-support access to patient-linked data across pharmacy tenants.  
**Related control:** `PHIAccessAudit` append-only audit records and `docs/security/PHI_READ_SURFACE_INVENTORY.md`.

## 1. Security objective

A platform-level role is not, by itself, permission to read or mutate patient data. Every privileged patient-data operation must be authorized against a short-lived, explicit grant that binds the actor, tenant, purpose, permitted action, and (where applicable) patient/resource scope.

This proposal does not grant access, change current authorization behavior, or establish legal/regulatory compliance.

## 2. Grant model

A support grant should be an immutable authorization envelope with at least:

| Attribute | Requirement |
|---|---|
| `grant_id` | Opaque unique identifier; never reused |
| `requested_by` | Authenticated support actor |
| `approved_by` | Distinct authorized approver for sensitive PHI access |
| `pharmacy_id` | Exactly one tenant; no wildcard or implicit global scope |
| `patient_id` | Optional; if absent, only explicitly approved tenant-level actions are possible |
| `purpose_code` | Controlled vocabulary, not free-form only |
| `reason` | Human-readable business justification; no clinical details |
| `allowed_actions` | Explicit allowlist, e.g. `read_patient_summary`, `read_dispensing_context`, `read_purchase_history`, `correct_nonclinical_metadata` |
| `starts_at`, `expires_at` | Short bounded validity interval; expiry mandatory |
| `status` | Requested, approved, denied, revoked, expired |
| `ticket_reference` | Support case reference, not a patient identifier |
| `created_at`, `decided_at` | Server-generated timestamps |

No wildcard tenant, wildcard action, non-expiring grant, self-approval, or grant inferred solely from `is_superuser` should be permitted.

## 3. Authorization decision

Every privileged PHI endpoint/service must call one shared policy boundary before loading patient-linked data:

1. Authenticate the actor and require the support capability.
2. Load the grant by opaque grant ID.
3. Verify status is approved and current server time is within its validity interval.
4. Verify actor, pharmacy, optional patient, purpose, and requested action match the grant exactly.
5. Verify the target patient/order/purchase belongs to the grant's pharmacy in the SQL predicate itself.
6. Deny by default on missing grant, ambiguous scope, expired/revoked grant, mismatch, or policy/audit persistence failure.
7. Pass a typed, immutable authorization context to the service/repository; do not pass a caller-controlled pharmacy ID as proof of authorization.

A grant is not a bearer token. Knowing its ID must not be sufficient to use it.

## 4. Approval and lifecycle

- Requester and approver must be different principals.
- Approver must have a separately defined support-approval capability.
- Approval records the exact tenant, purpose, resource scope, action set, and expiry; later edits require a new decision or a new grant.
- Revocation takes effect immediately and is checked on every operation, not only at session creation.
- Expiration is enforced server-side; client clocks are not trusted.
- Emergency/break-glass access, if required by operations, must be a distinct workflow with a narrow maximum duration, mandatory reason, high-severity audit, and retrospective review. It must not be an implicit superuser bypass.

## 5. Audit contract

Record both allowed and denied decisions in `PHIAccessAudit` or a versioned successor. Required metadata:

- actor, pharmacy, patient/resource (where known), action, decision, purpose;
- grant ID and approver ID;
- request/correlation ID and timestamp;
- denial reason code (bounded enum; no exception text or clinical payload).

Audit persistence is part of the authorization transaction boundary. If the audit record cannot be durably written, the PHI operation must fail closed. Never put patient IDs, grant IDs, reasons, prompts, or clinical content into metric labels.

The audit store must remain append-only at the database boundary. Application permissions should also deny UPDATE/DELETE to normal runtime roles; a trigger alone does not protect against a database owner or superuser who can disable it. Any privileged maintenance of audit storage must be separately controlled and externally evidenced.

## 6. Data access and transaction rules

- Scope patient/order/purchase queries by `pharmacy_id` in SQL before materialization.
- Mutations must include tenant scope in the initial SELECT and final UPDATE/DELETE predicate (or use an equivalent guarded statement).
- Keep grant validation, domain mutation, and audit write in one transaction where feasible.
- For external side effects, use a transactional outbox and include the authorization/grant reference in restricted audit metadata, not in public event payloads.
- Background jobs must carry a server-issued authorization context or re-authorize at execution time; a queued user-supplied tenant ID is not authorization.
- MCP and Edge requests must derive tenant identity from trusted enrollment/context and must not accept a caller-provided grant or tenant as authoritative.

## 7. API and domain boundaries

Avoid adding ad-hoc `is_superuser` checks to individual endpoints. Implement a shared policy service with a typed input similar to:

```text
authorize_support_access(
  actor,
  grant_id,
  pharmacy_id,
  patient_id?,
  purpose_code,
  action,
  request_context
) -> SupportAccessContext | Deny
```

The returned context should be immutable and contain the verified actor, tenant, resource scope, grant, purpose, action, and expiry. Repositories should accept this context (or a narrower trusted tenant context) rather than raw optional scope for privileged operations.

## 8. Required test matrix

- No grant; pending; denied; revoked; expired; not-yet-valid.
- Actor mismatch; self-approval; approver lacks capability.
- Wrong pharmacy; wrong patient; wrong purpose; wrong action.
- Patient belongs to another pharmacy, including a platform superuser attempting access.
- Grant ID guessed or replayed by another actor.
- Revocation between two requests and expiry at boundary time.
- Audit write failure causes denial and no domain read/mutation.
- Two-tenant database-backed tests prove no foreign row is materialized or mutated.
- Background job, MCP, export/report, and Edge execution cannot widen the grant.
- Concurrent use/revocation has deterministic transaction semantics.
- Audit UPDATE/DELETE are rejected by PostgreSQL and normal application DB role lacks those privileges.

## 9. Migration sequence

1. Inventory all privileged patient-level read and mutation surfaces; name an owner and action for each.
2. Define controlled purpose/action vocabularies and the support approver capability.
3. Add grant persistence, lifecycle constraints, and append-only decision history through reviewed migrations.
4. Implement the shared authorization service and unit tests.
5. Migrate one low-risk read surface behind a feature flag in non-production.
6. Add DB-backed two-tenant and grant lifecycle integration tests.
7. Migrate remaining patient, order, purchase, export, MCP, Edge, and background-job paths.
8. Remove implicit global superuser PHI access only after operational workflows have an approved replacement.
9. Verify audit retention, monitoring, alerting, and break-glass review.
10. Enable production behavior only after a separately approved deployment and migration plan.

## 10. Acceptance criteria

- [ ] No privileged PHI operation relies solely on `is_superuser`.
- [ ] Every support grant is tenant-bound, action-bound, purpose-bound, time-limited, and attributable to requester and approver.
- [ ] Every allow and deny decision is durably audited.
- [ ] Audit failure fails closed.
- [ ] SQL-level tenant predicates are present before data materialization and on mutations.
- [ ] Cross-tenant and lifecycle tests pass against PostgreSQL.
- [ ] MCP, Edge, exports, reports, and background jobs use the same authorization contract.
- [ ] Operational break-glass workflow has explicit controls and retrospective review.
- [ ] No production activation occurs without separate authorization.

## 11. Current implementation gap — 2026-11-22

A source review of `main` at `2616b4209fc037b1e4f1899b876478bf72258641` found partial route-level PHI audit, but the controls in this proposal are not implemented end to end:

- Only the AI-profile and pharmacist patient-history HTTP routes currently require explicit purpose and pharmacy membership and write `PHIAccessAudit` decisions. The legacy admin purchase listing and general patient/order routes are not fully purpose-bound/audited.
- MCP `get_patient_history` has trusted user/pharmacy/role context but no selected-patient or purpose binding. It accepts a model-supplied patient ID, can query another active patient within the same pharmacy, returns a broad clinical/demographic summary and does not write `PHIAccessAudit`.
- The Ansible Compose profile initializes PostgreSQL with `POSTGRES_USER` and reuses that credential in application `DATABASE_URL` connections for backend and workers. No separate non-superuser runtime role or privilege grants are provisioned by the current Ansible PostgreSQL role. Database triggers alone therefore do not prove append-only audit storage against the application credential.
- The Production Alembic guard requires `MIGRATION_DATABASE_URL`, but the current Ansible migration environment does not inject it; a separate least-privilege migration role/secret path remains outstanding.

These are source/configuration findings, not evidence of an incident or live Production exploitation. Do not enable unrestricted support access or claim complete PHI governance until the grant model, MCP patient/purpose binding, DB role separation, audit-failure behavior and database-backed negative tests are implemented and reviewed.

## 12. Known limitations

This is a design baseline, not an implementation. The existing PHI audit currently covers only selected endpoints; it is not yet a complete audit trail. Existing superuser-global behavior remains until each surface is migrated and operational support workflows are validated. No compliance certification is implied.
