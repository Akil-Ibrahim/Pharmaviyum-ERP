# Pharmacy-Scoped RBAC Permission Specification

- **Status:** Draft for product and security review — not approved for implementation
- **Date:** 2026-11-26
- **Related ADR:** [ADR-0005 — Tenant-scoped pricing and pharmacy operational roles](../adr/ADR-0005-tenant-scoped-pricing-and-pharmacy-rbac.md)
- **Related governance:** [PHI Access Governance Audit](PHI_ACCESS_GOVERNANCE_AUDIT.md)

## 1. Purpose and scope

Define a reviewable, least-privilege permission model for users operating within a pharmacy tenant. This document is a policy proposal only. It does not authorize schema changes, migrations, API behavior changes, deployment, or the assignment of roles to existing users.

The policy separates:
- **Identity:** the authenticated User.
- **Tenant membership:** the user's active relationship to a Pharmacy.
- **Pharmacy role:** the operational role assigned to that membership.
- **Permission:** an explicit action the principal may perform within that pharmacy.
- **Platform operator:** a separately governed platform-level principal; not a pharmacy role.

A membership is not itself a role, and a role is not a substitute for patient ownership checks.

## 2. Proposed role set

| Role key | Intended responsibility |
|---|---|
| cashier | Execute ordinary point-of-sale workflows. |
| pharmacist | Perform pharmacy dispensing and authorized clinical workflows. |
| manager | Manage pharmacy operations, inventory, procurement and operational exceptions. |
| pharmacy_admin | Administer pharmacy membership, user access and pharmacy-level configuration. |

Role names and responsibilities are proposals pending product-owner approval. Do not add these values to persisted data until the assignment and migration policy is approved.

## 3. Permission naming convention

Use stable, action-oriented identifiers in the form resource.action. Suggested initial vocabulary:

| Domain | Permission identifiers |
|---|---|
| POS | pos.read, pos.checkout, pos.discount.apply, pos.sale.cancel, pos.refund |
| Catalog | catalog.read, catalog.manage |
| Inventory | inventory.read, inventory.receive, inventory.adjust, inventory.transfer |
| Defectura | defectura.read, defectura.create, defectura.approve |
| Procurement | procurement.read, procurement.create_order, procurement.approve_order, procurement.receive |
| Suppliers | suppliers.read, suppliers.manage |
| Clinical | patients.read, patients.update, prescriptions.read, prescriptions.dispense, clinical_records.read, clinical_records.update |
| Pharmacy administration | members.read, members.invite, members.role.assign, pharmacy.settings.read, pharmacy.settings.update |
| Audit | audit.read |

The vocabulary is a starting point, not a complete endpoint inventory. Each permission must map to concrete API operations and data classifications before enforcement.

## 4. Proposed role-to-permission matrix

Legend: **Allow** = proposed permission; **No** = deny by default; **Decision needed** = requires explicit product/security decision before implementation.

| Permission | Cashier | Pharmacist | Manager | Pharmacy Admin |
|---|---:|---:|---:|---:|
| pos.read | Allow | Allow | Allow | Allow |
| pos.checkout | Allow | Allow | Allow | Allow |
| pos.discount.apply | No | Decision needed | Allow | Decision needed |
| pos.sale.cancel | No | Decision needed | Allow | Decision needed |
| pos.refund | No | Decision needed | Allow | Decision needed |
| catalog.read | Allow | Allow | Allow | Allow |
| catalog.manage | No | Decision needed | Allow | Decision needed |
| inventory.read | Decision needed | Allow | Allow | Allow |
| inventory.receive | No | Decision needed | Allow | Decision needed |
| inventory.adjust | No | No | Allow | Decision needed |
| inventory.transfer | No | Decision needed | Allow | Decision needed |
| defectura.read | No | Allow | Allow | Decision needed |
| defectura.create | No | Allow | Allow | Decision needed |
| defectura.approve | No | No | Allow | Decision needed |
| procurement.read | No | Decision needed | Allow | Decision needed |
| procurement.create_order | No | Decision needed | Allow | Decision needed |
| procurement.approve_order | No | No | Allow | Decision needed |
| procurement.receive | No | Decision needed | Allow | Decision needed |
| suppliers.read | No | Decision needed | Allow | Decision needed |
| suppliers.manage | No | No | Allow | Decision needed |
| patients.read | No | Allow* | No | No |
| patients.update | No | Allow* | No | No |
| prescriptions.read | No | Allow* | No | No |
| prescriptions.dispense | No | Allow* | No | No |
| clinical_records.read | No | Allow* | No | No |
| clinical_records.update | No | Allow* | No | No |
| members.read | No | No | Decision needed | Allow |
| members.invite | No | No | Decision needed | Allow |
| members.role.assign | No | No | No | Allow** |
| pharmacy.settings.read | No | No | Allow | Allow |
| pharmacy.settings.update | No | No | Decision needed | Allow |
| audit.read | No | No | Decision needed | Decision needed |

* Clinical permissions are conditional, not blanket access: the authenticated user must have an active membership in the requested pharmacy; the patient must be owned by that pharmacy or have an explicitly approved care relationship; the requested action must be permitted; and required purpose-of-use and PHI access auditing must succeed. Missing or ambiguous patient ownership must fail closed.

** Pharmacy administrators must not be able to grant platform privileges or assign a role above their own administrative authority. Role assignment requires an auditable workflow and protection against self-escalation. The exact role-assignment boundary remains a decision gate.

**Important:** "Decision needed" is not an allow. Until resolved, deny the operation by default. Do not infer permissions from a role label or from UI visibility.

## 5. Authorization invariants

1. Every pharmacy-scoped request must resolve an authenticated active user and an active membership for the requested pharmacy.
2. The pharmacy identifier supplied by a client is untrusted until membership authorization succeeds.
3. Permission evaluation must be server-side and centralized; frontend navigation and hidden buttons are presentation only.
4. Every operation must check the specific action permission, not merely whether a user has a role.
5. Patient and prescription access requires additional patient-ownership and PHI policy checks. Pharmacy membership alone is insufficient.
6. A global is_superuser flag must not silently grant unrestricted clinical-data access. Platform support access requires a separately approved, time-bounded, reason-coded and audited policy.
7. Missing role, unknown permission, inactive membership, missing tenant context, ambiguous ownership, or authorization-service failure must deny access.
8. Role changes and membership activation/deactivation must be audited with actor, pharmacy, target user, old/new role, timestamp and reason.
9. Permissions must not be granted through implicit role inheritance. Any future composite-role behavior must be explicit, tested and documented.
10. Background jobs, MCP tools, exports, reports and integrations must use the same trusted tenant and permission context; they must not bypass API authorization.

## 6. Platform operator and break-glass policy

Platform operators are outside the four pharmacy roles. The existing superuser bypass in tenant resolution is a technical capability, not a sufficient governance policy.

Before enabling support access to tenant or patient data, define:
- a dedicated support permission separate from is_superuser;
- explicit pharmacy and resource scope;
- a reason code and support ticket/reference;
- time-bounded activation and automatic expiry;
- immutable allowed/denied access audit events;
- review by an independent authorized reviewer;
- prohibition on using support access for ordinary pharmacy workflows.

No global patient access should be introduced as part of the initial pharmacy RBAC rollout.

## 7. Data model direction — proposal only

Potential minimal direction:
- Keep User as the global identity.
- Extend PharmacyMembership with a non-null pharmacy role only after a safe backfill policy is approved.
- Keep the role enum/vocabulary constrained and versioned.
- Resolve permissions through one centralized policy service rather than scattered role comparisons.
- Consider a permission registry in code initially; a database-driven role-permission table is not required unless there is a concrete administrative requirement for runtime-customizable roles.

Do not implement both a role column and a separate role table without a demonstrated need. Avoid introducing a general-purpose policy engine for this small fixed role set.

## 8. Migration and rollout gates

Before any migration:
1. Inventory every existing membership and its current operational use.
2. Determine how each existing membership is classified; do not silently promote all users to pharmacy_admin or manager.
3. Decide the safe behavior for memberships that cannot be classified. Preferred default: no newly granted privileged permissions until reviewed.
4. Implement a controlled role-assignment path with audit events.
5. Add centralized permission checks in compatibility mode only if they do not change current access unexpectedly; then enforce after tests and explicit rollout approval.
6. Verify all pharmacy-scoped API routes, including POS, inventory, procurement, patients, prescriptions, reports, exports, AI/MCP tools and background jobs.
7. Add PostgreSQL migration tests, authorization matrix tests and cross-tenant negative integration tests.
8. Validate with synthetic data in Demo/staging before any production rollout.

Database migrations must follow the repository's approved migration workflow and environment guards. This specification does not authorize manual SQL or bypassing those guards.

## 9. Required test coverage

- Every role × permission combination, including all default-deny cases.
- Active and inactive memberships.
- One user with different roles in two pharmacies.
- Cross-pharmacy object identifiers supplied by a client.
- Missing, unknown and malformed role/permission values.
- Role assignment, self-escalation attempts and unauthorized privilege escalation.
- Patient with matching pharmacy, different pharmacy, null pharmacy and ambiguous ownership.
- Superuser/platform operator without an approved support grant.
- PHI audit success, denial and audit persistence failure.
- API, UI, MCP, background job, export and report access paths.
- Regression tests proving existing Dashboard and POS workflows remain functional.

## 10. Decisions required before implementation

| Decision | Proposed safe default | Approval required |
|---|---|---|
| Approve the four pharmacy roles | Keep role set limited to four | Product owner |
| Manager access to patient-level data | Deny; permit only operational aggregates without patient identifiers | Product + security |
| Pharmacy admin access to clinical data | Deny | Product + security |
| Pharmacist clinical access | Allow only within pharmacy ownership and PHI policy | Clinical + security |
| Cashier access to inventory quantities | Decide whether POS requires read-only stock visibility | Product |
| Discounts, refunds and cancellations | Manager only initially; pharmacist exceptions require explicit thresholds | Product |
| Pharmacy admin role assignment | No self-escalation; bounded role assignment | Product + security |
| Existing membership backfill | No automatic privileged role assignment | Product owner |
| Platform support access | Separate time-bound, audited grant | Security |
| Audit log visibility | Restricted, separately permissioned | Security |

## 11. Acceptance criteria

This specification can move from Draft to Approved only when:
- all decisions in Section 10 have named owners and explicit outcomes;
- the API/resource inventory is complete;
- the role assignment and legacy-membership backfill policy is documented;
- PHI access and platform support policies are aligned with the PHI governance audit;
- the implementation and migration plan has testable acceptance criteria.

Until then, ADR-0005 must remain Proposed, no role schema or permission enforcement should be introduced, and the current application behavior must not be represented as full pharmacy RBAC.
