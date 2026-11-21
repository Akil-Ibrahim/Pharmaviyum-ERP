# Pharmacy POS 2.0 and Drug Catalog — Initial Code Audit

**Audit branch:** `feature/pharmacy-pos-2`  
**Baseline:** `main` at `3d436a1b2280cb1e6d88a6c0664a1acf9b2c6dc9`  
**Scope:** read-only inspection of the existing application code and migration files. No production database was accessed or modified.

## Executive summary

Pharmaviyum already contains a meaningful pharmacy domain foundation. The correct approach is incremental extension, not a greenfield rewrite.

Existing components include:
- `DrugReference`, `DrugReferenceIngredient`, and `MedicinalProduct`.
- Local sellable `Product` records linked optionally to `MedicinalProduct`.
- `Inventory` and `ProductBatch` models.
- RxNorm and EMA import scripts.
- Local product search and reference-catalog search.
- A React POS screen with a local product search, a reference-only search, barcode input, a draft cart, quantity controls, discounts, and a payment dialog.

The critical functional gap is the persisted sale workflow. The current POS deliberately does not finalize a sale because the backend does not atomically persist sale lines, payment, receipt, and batch-level stock movements.

## Findings

### 1. Existing catalog model

Files:
- `src/pharmaviyum/models/drug_catalog.py`
- `src/pharmaviyum/schemas/drug_catalog.py`
- `src/pharmaviyum/api/v1/drug_catalog.py`

The current schema distinguishes a canonical drug reference from a medicinal product and allows a local `Product` to link to a medicinal product. This is a useful starting point.

Gaps to address:
- The reference model has no first-class external source mapping/provenance entity in the inspected model.
- Ingredient relationships currently represent a single linked `DrugReference` per medicinal product; the RxNorm and EMA importers explicitly skip multi-ingredient products. This limitation must remain explicit until combination products are modelled correctly.
- The catalog API currently exposes search only; it does not provide a controlled manual-create/review workflow.
- A catalog record is reference information, not a locally authorized sellable product, price, or stock record. The UI already communicates this distinction and should preserve it.

### 2. Existing importers

Files:
- `scripts/import_rxnorm_catalog.py`
- `scripts/import_ema_catalog.py`
- `tests/unit/catalog/test_rxnorm_import.py`
- `tests/unit/catalog/test_ema_import.py`

The importers now stage source records in `drug_catalog_source_records` rather than writing directly to `DrugReference` or `MedicinalProduct`. Each staged record carries a source identifier, the SHA-256 checksum of the exact downloaded archive/workbook as its source version, extraction time, source URL, a conservative licensing note, and a normalized payload. Re-running the same source file is idempotent for that source/version pair. New records remain `pending_review`; staging does not create or modify approved catalog entities, sellable products, prices, batches, inventory, or expiry dates. Multi-ingredient records remain excluded until the domain model supports them correctly.

RxNorm is not a complete international market catalogue. EMA Article 57 is European reference data, not proof of authorization in every country. DrugBank must not be enabled for commercial use without confirming the applicable license and API entitlement. OpenFDA is US regulatory data and must not be treated as global authorization evidence.

### 3. POS screen and sale persistence

Files:
- `frontend/shadcn-admin/src/features/pos/index.tsx`
- `src/pharmaviyum/api/v1/orders.py`
- `src/pharmaviyum/models/order.py`

The POS already supports local search, reference search, a draft cart, quantity adjustment, discounts, and payment preparation. The frontend currently blocks completion and displays a notice because a safe server-side transaction is not available.

The current `Order` API is not a POS checkout API:
- `Order` is patient-oriented and currently has no persisted line items.
- Order completion creates a single aggregate `PatientPurchase` record rather than itemized product/batch sales.
- The order amount uses a floating-point database field in the current migration.
- It does not allocate FEFO batches or persist payment/receipt/stock movements as one atomic business operation.

Do not enable the frontend's payment confirmation as a substitute. Implement a dedicated sale/checkout domain with transactional line items, payment state, receipt, batch allocation, and auditable stock movements.

### 4. Inventory and batch domain

Files:
- `src/pharmaviyum/models/inventory.py`
- `src/pharmaviyum/models/product_batch.py`
- `src/pharmaviyum/models/product.py`

`Inventory` is the authoritative pharmacy-level stock and lot record, consistent with ADR-0006: it carries `pharmacy_id`, `product_id`, `lot_number`, `expires_at`, on-hand quantity, and reserved quantity, and is referenced by the append-only `InventoryMovement` ledger. `ProductBatch` is a legacy compatibility model: it has no `pharmacy_id` and maintains a separate `available_quantity`; it is still referenced by `PatientPurchase`, dashboard queries, and seed code. It must not be used as the source of truth for pharmacy stock, FEFO allocation, or Edge-to-Central inventory mapping. Do not delete or backfill it in this change: first inventory every remaining reader/writer, define a migration for historical `PatientPurchase.batch_id` references, and prove that no operational path depends on its quantity fields. New pharmacy stock and integration work must resolve lots through `Inventory` and the shared movement service.

The `Product` model has legacy aggregate `stock` and a `Float` price. Preserve these fields during the compatibility period; use decimal arithmetic for new money-bearing transaction records and treat pharmacy/lot-level inventory as authoritative where already established.

### 5. API authorization and tenant scope

The inspected catalog search endpoint requires an authenticated active user. The current product create/update/delete endpoints use a superuser dependency. The inspected catalog and product search queries do not apply a pharmacy tenant filter, which may be appropriate for a shared global reference catalogue but must not be copied to pharmacy-owned sellable products or stock.

Before adding catalog management, define explicit permissions for catalog maintainers and keep pharmacy-scoped product/stock operations tenant-checked on the server. UI-only role checks are insufficient.

### 6. Migration and deployment safety

Files:
- `alembic/env.py`
- `alembic/versions/*`

The Alembic environment prefers FastAPI Cloud's `DATABASE_URL` and strips the unsupported asyncpg `channel_binding` option. The inspected migration chain contains historical branches and a merge revision; revision identifiers differ from some filenames. Migration changes must therefore be based on actual revision IDs and a verified graph, not filenames alone.

This audit did not connect to the production database, inspect its `alembic_version` value, or execute migrations. Before any schema change:
1. Verify `alembic heads` and `alembic history` in a reproducible local/staging environment.
2. Compare the deployed database's current revision with the repository graph.
3. Test upgrade and rollback behavior against a disposable Neon branch or isolated database.
4. Take/verify a restorable backup before any production rollout.
5. Never run destructive cleanup or rewrite applied migration history as part of the POS feature.

## Proposed implementation sequence

### A. Drug Catalog management
- Typed source-record create/list/review contracts and provenance storage are implemented.
- RxNorm and EMA importers now stage records with source identity and file-checksum versioning.
- Imported records remain pending review; duplicate source/version identities are skipped.
- Explainable match suggestions rank existing references/products; human review remains mandatory.
- The review API links a staged record to one existing canonical reference or medicinal product; it does not auto-create catalog entities.
- Keep reference records separate from local sellable products and stock.

The source review API also exposes `GET /drug-catalog/sources/{record_id}/matches`. It ranks existing canonical references and medicinal products using normalized ingredient, brand/product name, strength, dosage form, route, and country signals. Candidate scores include human-readable reasons and are suggestions only; this endpoint does not change review status or write catalog records. It is intentionally limited to pending source records.

### B. Local pharmacy product management
- Create or link a sellable `Product` only after local catalog review.
- Require pharmacy context for pharmacy-owned pricing and stock operations.
- Validate SKU and barcode/GTIN uniqueness at the correct scope.
- Preserve legacy fields while migrating new money operations to Decimal.

### C. Transactional POS checkout
- Introduce sale, sale item, payment, receipt, and stock movement contracts.
- Allocate eligible batches using FEFO with row-level locking or equivalent concurrency control.
- Reject expired, quarantined, recalled, or otherwise blocked stock.
- Use idempotency keys so retries cannot create duplicate sales.
- Commit sale lines, payment state, receipt, and stock movements atomically.
- Add void/return/refund workflows as auditable reversals.

### D. Validation
- Unit tests for matching, duplicate detection, and FEFO selection.
- API tests for authorization, tenant isolation, import review, and checkout invariants.
- Integration tests for rollback on payment or stock failure and concurrent last-unit sales.
- Playwright coverage for cashier workflows only after the backend contract exists.

## Explicit non-goals for this audit commit

- No production database changes.
- No automatic creation of approved catalog entities, local sellable products, or inventory from external reference imports.
- No assertion that RxNorm, EMA, OpenFDA, or DrugBank proves local market authorization.
- No enabling of checkout until the backend transaction and its tests are implemented.

## Admin source review queue

The authenticated frontend now includes a Catalog Review page backed by the superuser-only source-record endpoints:

- Lists up to 200 `pending_review` source records with source identity, version, extraction time, URL, license terms, and normalized payload.
- Requests explainable match suggestions on demand and displays confidence plus matching reasons.
- Requires an explicit candidate selection before approving or marking a record as a duplicate; rejection does not attach a target.
- Sends exactly one match target to the review API, matching the backend schema.
- Handles API errors in the page and refreshes the pending queue after a successful decision.

The UI role check is a convenience only. Backend `CurrentSuperuser` dependencies remain the security boundary. Review decisions do not create local sellable products, prices, batches, inventory, or stock movements and do not establish authorization for sale in a local market.

## Matching candidate retrieval and bounded hydration

The match endpoint now performs a lightweight first pass over reference IDs/INN names and ingredient-name rows, using the same fuzzy similarity threshold as the matching service. It then hydrates ORM objects, related ingredients, and medicinal products only for the best 250 reference IDs before computing explainable product-level scores and returning the top 10 suggestions.

This avoids materializing every DrugReference relationship graph in application memory for each review request. The lightweight name scan remains proportional to the catalog size; it deliberately preserves fuzzy matching rather than applying a restrictive exact/prefix-only SQL filter. A future database-specific trigram/full-text index can reduce scan cost after extension availability and query plans are verified on the target database.


## Follow-up audit: legacy ProductBatch dependency inventory

**Follow-up baseline:** current `main` inspected on 2026-11-21. This section records source-level findings only; it does not assert production row counts or production data quality.

### Confirmed read/write paths

| Surface | Observed dependency | Classification |
|---|---|---|
| `PatientPurchase.batch_id` and `batch` relationship | Nullable FK to `product_batches.id` with `ON DELETE SET NULL`; `batch_number` and `expiry_date` properties read through the relationship | Historical traceability/read |
| `api/v1/patient_purchases.py` | Serializes batch ID, batch number, and expiry date | API read |
| `api/v1/dashboard.py` | Patient medication query outer-joins `ProductBatch` to expose the historical purchase's expiry date | Dashboard read |
| `api/v1/pharmacy_entities.py::list_batches` | Superuser-only endpoint selects `ProductBatch` rows, optionally filtered by product; no pharmacy predicate exists because the model has no pharmacy owner | Legacy administrative read |
| `scripts/seed_database.py::seed_inventory` | Creates a demo `ProductBatch` with initial `available_quantity`; uses its batch number/expiry to create or locate a pharmacy-scoped `Inventory` row and records an opening movement | Demo/bootstrap write |
| `Product.batches` relationship | ORM relationship remains available | Compatibility mapping |

The inspected seed path initializes `ProductBatch.available_quantity` when creating a missing demo batch. For an existing batch it refreshes expiry metadata, while the paired `Inventory` record is treated as operational state. This is not evidence of a production-safe dual-write protocol.

The batch list endpoint is restricted to `CurrentSuperuser`, but it still returns unscoped legacy rows. Do not treat the current authorization check as a substitute for pharmacy ownership or tenant-scoped inventory access. The frontend's standalone batches route currently renders no page; this does not remove the backend endpoint or its API consumers.

### Domain boundary

- `Inventory` plus `InventoryMovement` is the pharmacy-scoped stock and lot ledger.
- `ProductBatch` is a global/legacy compatibility record and must not drive sellable quantity, FEFO allocation, reservations, or Edge synchronization.
- `PatientPurchase` is patient history. Its batch relationship is historical metadata, not a stock balance.
- A historical purchase must remain interpretable if its legacy batch row is eventually retired. The current `ON DELETE SET NULL` behavior can erase the relationship while leaving only the purchase row; that is not sufficient historical preservation by itself.

### Safe retirement sequence (design; not yet implemented)

1. **Freeze the legacy quantity contract.** Prohibit new operational code from reading or mutating `ProductBatch.available_quantity` as stock truth. Keep the field only for compatibility until all readers/writers are accounted for.
2. **Add immutable purchase snapshots.** Introduce nullable snapshot fields on `PatientPurchase` for the batch/lot identifier and expiry date captured at dispense time. Populate them from the linked batch where available. For rows without a linked batch, preserve null and report the gap; never infer a lot from current inventory.
3. **Dual-read validation.** Update history/API/dashboard readers to prefer purchase snapshots and use the legacy relationship only as a temporary fallback. Add tests for deleted/missing batch rows, null legacy references, and unchanged historical display.
4. **Reconcile before changing writers.** Produce a pharmacy/product/lot comparison between legacy batch metadata and `Inventory`; compare quantities only where a defensible mapping exists. Report unmatched, ambiguous, duplicate, expired, and cross-pharmacy cases separately. Do not auto-correct discrepancies.
5. **Remove unsafe administrative exposure.** Replace the unscoped legacy batch list with a pharmacy-scoped `Inventory`/lot query or explicitly deprecate and disable the legacy endpoint after its consumers are migrated. Preserve superuser access as an additional permission, not as tenant scope.
6. **Retire relationships in a later release.** Only after code search, API contract review, migration tests, and telemetry show no legacy reads/writes: remove the ORM relationship and FK in a forward-only migration. Retain the snapshot data and an auditable migration report.

### Required verification gates

- Static dependency scan proves there are no operational writes to `ProductBatch.available_quantity` outside the approved compatibility/seed path.
- Unit/API tests prove patient history remains stable after a legacy batch is absent.
- Tenant tests prove a pharmacy cannot enumerate another pharmacy's `Inventory` lots.
- Reconciliation tests cover one-to-one, unmatched, duplicate, and ambiguous lot mappings.
- Migration tests run upgrade from a representative pre-change schema and verify snapshot backfill counts, null counts, and referential integrity.
- A disposable staging database is used for migration rehearsal; production database state and backups are not assumed from source inspection.

**Status:** dependency inventory is partial and source-level. No snapshot migration, endpoint replacement, data reconciliation, production query, or production migration has been performed. ProductBatch retirement is not approved by this audit.

## Implementation status reconciliation — later source snapshot

This audit records the historical baseline at commit `3d436a1b2280cb1e6d88a6c0664a1acf9b2c6dc9`. Its statement that persisted POS checkout was a critical gap was accurate for that inspected baseline, but it is no longer an accurate description of the later source snapshot `c6d35b828c1958f1bcb9077bbd0b6a71ef94613b`.

The later snapshot includes a mounted `/api/v1/pos` router, transactional checkout, sale/payment/receipt records, FEFO allocation, inventory movement and outbox writes, a signed payment webhook, and integration tests in `tests/integration/test_pos_checkout.py`. The later backend implementation is therefore beyond the original audit's proposed POS step C.

This does **not** mean the complete pharmacy POS workflow is finished: the active React POS feature currently returns `null`; checkout is not linked to patient/prescription validation; returns/refunds and cashier-shift reconciliation were not established by the later source audit; and the standalone lot-receipt endpoint is not a supplier purchase-order receiving lifecycle.

For the current process-by-process evidence map, see [Pharmacy Workflow Implementation Traceability](../workflows/PHARMACY_WORKFLOW_TRACEABILITY.md). This addendum is source-level only; no production runtime or database was inspected.
