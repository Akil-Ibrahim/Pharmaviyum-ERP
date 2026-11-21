# P0 Pharmacist Workspace — implementation contract audit

**Audit baseline:** `main` at `d6aaeb5ce1c1ed7d39d2c13ac05abb55e0bb5a23` (2026-11-21).  
**Scope:** source-level inspection of POS, prescription, patient-purchase, generated-client and browser-test contracts. No application code was changed. No production database, patient data, payment provider or deployed runtime was accessed.

This document complements [P0 acceptance gates](./PHARMACIST_WORKSPACE_P0_ACCEPTANCE.md). It records what the current repository source actually exposes so implementation can be planned against real contracts rather than inferred screens or model names.

## 1. Current state

| Area | Verified source state | P0 implication |
|---|---|---|
| POS route | `/_authenticated/pos` mounts `Pos`; `src/features/pos/index.tsx` returns `null`. | Route exists, workspace UI does not. |
| Product search | `GET /api/v1/pos/products/search?q=&pharmacy_id=&limit=`; authenticated user; server calls `require_pharmacy_tenant`; returns `POSProductResponse[]`. | Usable backend contract for catalog search, subject to generated client and UI integration. |
| Lot lookup | `GET /api/v1/pos/products/{product_id}/lots?pharmacy_id=`; authenticated user and tenant check; returns lot number, expiry, on-hand/reserved/available quantities and missing-expiry flag. | UI must display lot-level stock and expiry uncertainty. |
| Checkout | `POST /api/v1/pos/checkout`; `SaleCreate` → `SaleResponse`; authenticated user and tenant check. | Existing transactional endpoint can support cash and external-payment initiation. |
| Sale read | `GET /api/v1/pos/sales/{sale_id}`; authenticated user; tenant authorization is checked against the sale's pharmacy. | Single-sale receipt/status refresh exists; no sale-list endpoint was found in this POS router. |
| Pending-sale cancellation | `POST /api/v1/pos/sales/{sale_id}/cancel`; tenant-scoped; only `awaiting_payment` sales can be cancelled. | This is not a completed-sale return/refund workflow. |
| External payment settlement | `POST /api/v1/pos/payments/webhook`; HMAC-SHA256 over raw body using `PAYMENT_WEBHOOK_SECRET`; pending payments transition to succeeded/failed and inventory reservation is committed/released. | Payment provider adapter, signature generation, retry and staging contract tests remain integration dependencies. |
| Stock receipt | `POST /api/v1/pos/inventory/receive`; tenant-scoped, idempotent single-lot receipt. | Not a supplier purchase-order, delivery-note, invoice or discrepancy lifecycle. |
| Prescription | `Prescription` model exists. `GET/POST /api/v1/prescriptions` in `pharmacy_entities.py` require `CurrentSuperuser`. | These endpoints are not a pharmacist prescription workflow. |
| Patient purchase history | `GET /api/v1/patient-purchases/` requires `CurrentSuperuser` and selects purchases globally without patient/pharmacy filtering. | Do not connect this endpoint to pharmacist-facing patient history. |
| Generated POS client | The repository script `scripts/generate-api-client.sh` generates to `frontend/shadcn-admin/src/client`; that output path and POS service/model files were not present in the inspected branch. The frontend package manifest does not declare `openapi-typescript-codegen`. | Establish a reproducible, pinned generation workflow and commit/use the generated contract before wiring UI. |
| Browser E2E | Playwright config targets `frontend/shadcn-admin/e2e`, Chromium and mobile Chromium. The inspected E2E suite contains authentication scenarios; no POS E2E scenario was found. | Add POS journey tests; green generic E2E CI is not POS acceptance evidence. |

## 2. POS API contract

### Search

`GET /api/v1/pos/products/search`

- Query: `q` (2–100 chars), `pharmacy_id` (required, positive), `limit` (1–100, default 20).
- Authorization: `CurrentUser` plus `require_pharmacy_tenant(pharmacy_id, user, db)`.
- Search fields: product name, SKU, INN, manufacturer, regulatory ID, GTIN, barcode, dosage strength and dosage form.
- Response fields include product identity, strength/form, pack units, manufacturer, INN, identifiers, price, available stock and medicinal-product ID.

### Lot lookup

`GET /api/v1/pos/products/{product_id}/lots?pharmacy_id={id}`

- Returns lot/inventory ID, lot number, expiry date, quantity, reserved quantity, available quantity and `expiry_date_missing`.
- Orders known expiries first and missing expiries last.
- **Important policy gap:** both search and checkout currently allow lots with `expires_at IS NULL`. The UI must not silently present missing-expiry stock as verified safe stock. Product/business owners must define whether missing-expiry lots are blocked, require an authorized exception, or are handled by a documented legacy-data policy before dispensing.

### Checkout

`POST /api/v1/pos/checkout`

Request schema:
- `pharmacy_id`
- `idempotency_key` (8–100 chars)
- `items[]` with unique `product_id` and positive `quantity`
- optional non-negative `discount_total`
- `payment_method`: `cash | card_terminal | online`
- `cash_received` required only for cash

Server behavior:
- Revalidates pharmacy membership and active sellable products.
- Calculates prices and totals server-side; rejects invalid discounts and insufficient cash.
- Locks inventory rows and allocates FEFO by `expires_at ASC NULLS LAST`.
- Uses a pharmacy-scoped idempotency key and PostgreSQL transaction advisory lock.
- Cash checkout decrements stock and completes the sale; card-terminal/online checkout reserves stock and creates an `awaiting_payment` sale.
- Persists sale items, lot allocations, payment state and an outbox event in the transaction.
- Rejects insufficient available stock without committing a partial sale.

Response schema contains receipt number, pharmacy, totals, sale status, timestamps, items with lot allocations, payments and cash change.

**Frontend must treat server response as authoritative.** Never calculate final price, stock availability, FEFO allocation, payment state or receipt identity as trusted client-side facts.

## 3. Prescription and patient linkage gap

The current `Sale` has pharmacy and cashier ownership but no `patient_id` or `prescription_id`. `SaleItem` links to product and lot allocations, not prescription lines. The `Prescription` model stores patient, optional product, prescription number, dosage, instructions, status and issue/expiry dates, but does not provide a dispense ledger or remaining quantity/refill accounting.

The current generic prescription list/create routes are superuser-only and use a basic schema. They do not establish pharmacist-level patient/pharmacy membership, prescription validity, medication/strength/form/quantity matching, partial dispensing, override authorization or audit reason.

Therefore, P0.2 requires a reviewed domain/API design and migration; it cannot be delivered by adding a prescription selector to the current POS screen.

## 4. Patient history boundary

`GET /api/v1/patient-purchases/`:
- Requires `CurrentSuperuser`.
- Applies pagination only.
- Queries `PatientPurchase` directly, without joining `Patient` or constraining `Patient.pharmacy_id`.
- Returns patient identifiers and purchase details.

This is a global administrative endpoint, not a pharmacist history API. A pharmacist-facing endpoint must derive pharmacy membership from the authenticated principal, validate the selected patient against that pharmacy, define handling for nullable legacy `Patient.pharmacy_id`, minimize returned fields, emit an audit event and include cross-tenant negative tests. Unassigned legacy patients must fail closed until reconciled.

## 5. Required implementation sequence

1. **P0.3 — Patient history API boundary:** define and test the server-derived pharmacy/patient scope first.
2. **P0.2 — Prescription and dispensing domain:** define sale/patient/prescription/dispense relationships, prescription validation, partial dispensing, authorized overrides, reversals and audit semantics.
3. **P0.1 — POS workspace:** implement the UI against pinned/generated API contracts; expose loading, empty, error, stock, lot, expiry, payment and receipt states. Keep prescription dispensing disabled until P0.2 is complete.
4. **P0.4 — Mortarium staged isolation:** validate patient switching, no-patient scope, sync/streaming, Redis memory, PostgreSQL checkpoints, caches, multi-instance behavior and secret rotation in a controlled synthetic environment.

## 6. Minimum browser and integration acceptance

- Pharmacist cannot search, read or transact against an unauthorized pharmacy.
- Search supports product name, INN, SKU/barcode, strength and form; results show stock and expiry caveats.
- FEFO allocation shown in the receipt matches the server response exactly.
- Cash checkout completes once; retry with the same key returns the same sale without a second stock decrement.
- Card-terminal/online checkout remains pending until a valid signed webhook settles or fails it.
- Failed payment and cancellation release the exact reservations once.
- Insufficient stock, expired lots, missing-expiry policy, stale price, duplicate submit and concurrent last-unit checkout have explicit UI/error behavior.
- Patient A → Patient B → no patient cannot leak history, prescription, cache or AI state.
- Prescription dispensing is blocked unless server-side prescription validation and dispense accounting succeed.
- Cross-tenant negative tests run against PostgreSQL; browser E2E uses synthetic data only.

## 7. Evidence limits

The latest inspected PR head is `01e9220c43b5e7f8d3de5f28f117a771f7600b9c`; the source audit baseline is current `main` at `d6aaeb5ce1c1ed7d39d2c13ac05abb55e0bb5a23`. The POS API files inspected on main match the reviewed branch source. CI passed for the documentation PR head, including integration tests, unit tests, RAG Safety Regression, frontend build/tests and Playwright E2E. The Playwright suite does not thereby establish POS browser acceptance.

No production runtime, database, real patient data, or external payment provider was accessed. This is a source-level contract audit, not a deployment or clinical/regulatory certification.

## Follow-up source audit — main 481a86aa

Current `main` includes PHI governance and patient repository tenant-scope changes. See [PHI access governance audit](../architecture/PHI_ACCESS_GOVERNANCE_AUDIT.md), [PHI read-surface inventory](../security/PHI_READ_SURFACE_INVENTORY.md), and regression coverage in `tests/unit/test_patient_repository_tenant_scope.py`. Pharmacy-scope predicates now exist in the reviewed Patient Repository paths. This does not provide a pharmacist-facing patient-history API or prove response minimization/read auditing. Keep P0.3: server-resolved pharmacy membership, fail-closed handling of unassigned legacy patients, minimal response fields, audited reads, pagination, and PostgreSQL cross-tenant negative tests. This is source-level evidence, not production validation.
