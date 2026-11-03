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

The importers are deliberately designed not to create sellable stock, prices, batches, or expiry dates. RxNorm and EMA data should continue to be treated as source reference data. Import should evolve toward a preview → match/deduplicate → review → approve → import process with source identifiers, source timestamps, and provenance.

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

Both an `Inventory` lot-oriented record and a `ProductBatch` model exist. Before implementing FEFO checkout, establish which model is authoritative for pharmacy-level stock, expiry, and lot traceability. Avoid maintaining two independent quantities without a reconciliation contract.

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
- Add typed create/update/detail/list contracts for canonical references and medicinal products.
- Add normalized duplicate checks and explicit conflict responses.
- Add review states for imported records; do not silently approve ambiguous matches.
- Add source mapping/provenance records before claiming multi-source aggregation.
- Keep reference records separate from local sellable products and stock.

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
- No automatic creation of inventory from external drug reference imports.
- No assertion that RxNorm, EMA, OpenFDA, or DrugBank proves local market authorization.
- No enabling of checkout until the backend transaction and its tests are implemented.
