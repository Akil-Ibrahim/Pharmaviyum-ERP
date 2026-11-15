# ADR-0005: Tenant-scoped pricing and pharmacy operational roles

- **Status:** Proposed
- **Date:** 2026-11-16
- **Owners:** Pharmaviyum engineering
- **Scope:** Product pricing, POS checkout, pharmacy membership authorization

## Context

The product catalog is currently global. `products.price` is a floating-point value on the global `Product` record, while inventory and sales are pharmacy-scoped. The POS search response and checkout currently read that global price. This cannot represent independent pharmacy price lists, country-specific currencies, or effective-dated price changes safely.

Sales already snapshot the charged unit price and line total in `sale_items` using PostgreSQL `NUMERIC`, which is the correct direction for immutable transaction history. The current `PharmacyMembership` model proves tenant membership but has no pharmacy-scoped role. A global user role is not a substitute for a role inside a particular pharmacy.

## Decision proposal

### 1. Separate catalog identity from pharmacy commercial terms

- Keep `Product` as a shared catalog/sellable-item identity; do not use its legacy `price` as the authoritative POS price.
- Introduce a pharmacy-scoped price-list model (proposed name: `PharmacyProductPrice`) with at least:
  - `pharmacy_id`, `product_id`
  - `currency_code` (ISO 4217)
  - `unit_price` using PostgreSQL `NUMERIC`, never binary floating point
  - effective-from/effective-to timestamps or dates
  - active/status metadata and audit timestamps
- Enforce tenant-aware uniqueness and prevent overlapping active price periods for the same pharmacy, product and currency.
- POS search and checkout must resolve the current effective price inside the authenticated pharmacy tenant. Checkout must snapshot currency and unit price on the sale/line so later price changes cannot rewrite history.
- Currency minor-unit rounding must follow the configured currency policy (for example, ISO 4217 exponent); do not globally assume two decimal places.
- Do not silently infer a pharmacy's currency from server locale, user locale, or deployment region.

### 2. Add pharmacy-scoped RBAC

- Add a role to `PharmacyMembership`; membership remains the tenant boundary.
- Define a small permission matrix for at least cashier, pharmacist, manager and pharmacy_admin. Permissions must be action-specific, not scattered role-name checks.
- Require explicit permission checks for checkout, inventory receiving/adjustment, discounts, sale cancellation/refund, price management and membership administration.
- Preserve the superuser platform-operator path separately from pharmacy roles.
- Do not treat the existing global `User.role` as pharmacy authorization.
- Provide a controlled membership/role assignment path and audit role changes before enforcing restrictive defaults.

## Migration and rollout plan

1. Inventory all existing pharmacy records, product prices, sale records, API consumers and membership provisioning paths.
2. Define the currency policy and explicitly assign a currency to every active pharmacy. If a pharmacy has no configured currency, POS pricing must fail closed with a clear configuration error; never guess.
3. Add the new price table and currency configuration using an additive migration. Backfill legacy prices only after each pharmacy's currency is explicitly known; mark migrated rows as legacy-origin and preserve source/audit metadata.
4. Add read-only price resolution and compare results against legacy POS pricing in tests/staging.
5. Switch POS search and checkout to tenant-scoped prices; retain `sale_items.unit_price` as the immutable transaction snapshot and add sale-level currency.
6. Add membership role data and an audited assignment/admin path. Backfill roles using an approved least-privilege policy; do not silently assign a privileged role to all existing members.
7. Enforce action permissions after migration and staging verification. Remove legacy global price reads only after all consumers have migrated.

## Consequences

- Each pharmacy can set its own prices and currency without duplicating the global medicinal catalog.
- Historical receipts remain stable when a price list changes.
- Cross-tenant price leakage becomes less likely because price lookup is scoped by pharmacy.
- Currency configuration becomes an explicit onboarding prerequisite.
- Migration requires staged rollout and cannot safely be completed by a blind `Float` to `Numeric` conversion.
- RBAC adds operational setup and requires a membership administration workflow.

## Security and data integrity

- Every price query and mutation must include the authenticated `pharmacy_id`; never trust a pharmacy identifier without membership authorization.
- Sale creation must snapshot price and currency inside the same transaction as inventory allocation and payment creation.
- Enforce non-negative prices, valid currency codes, effective-period consistency and tenant-scoped constraints at the database boundary where practical.
- Record actor, pharmacy, old value, new value and reason for price/role changes in an append-only audit trail.
- Do not expose another pharmacy's price list through catalog search, product detail, caching or AI tools.

## Validation evidence required before acceptance

- Migration upgrade/downgrade tests against PostgreSQL and a production-like snapshot.
- Multi-tenant tests proving identical products can have different prices/currencies in different pharmacies.
- Currency rounding tests for zero-, two- and three-decimal currencies.
- Tests proving historical sale totals do not change after price updates.
- Authorization matrix tests for every POS and inventory mutation, including cross-tenant denial.
- Concurrency/idempotency tests for checkout using a price resolved within the tenant.
- Staging evidence for existing pharmacy onboarding, price backfill and cashier workflows.

## Current implementation status

This ADR records a proposed target, not a claim of implementation. At authoring time:
- `Product.price` is global and SQL `Float`.
- `SaleItem.unit_price` and `line_total` are `NUMERIC(12,2)` snapshots.
- `PharmacyMembership` has `user_id`, `pharmacy_id` and `is_active`, but no pharmacy-scoped role.
- Pharmacy currency configuration and a role-management workflow are not established by the inspected models.

The ADR must remain **Proposed** until the currency policy, migration, authorization workflows and validation evidence are approved.

## Related implementation

- `src/pharmaviyum/models/product.py`
- `src/pharmaviyum/models/pharmacy_membership.py`
- `src/pharmaviyum/models/pos.py`
- `src/pharmaviyum/api/v1/pos.py`
- `src/pharmaviyum/modules/auth/tenant.py`
